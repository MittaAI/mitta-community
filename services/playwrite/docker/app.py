import asyncio
import httpx
import logging
import os
import json
import random
import string
import io
from quart import Quart, jsonify, render_template, request, send_from_directory, redirect
from quart_cors import cors

from screenshot import ai

app = Quart(__name__, template_folder='templates', static_folder='static')
app = cors(app, allow_origin="*")  # Adjust CORS as needed

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'screenshots')

@app.route('/')
async def home_redirect():
    return redirect('https://mitta.ai', code=302)


@app.route('/grub2', methods=['POST'])
async def grub():
    document = await request.get_json()
    grub_token = os.getenv('GRUB_TOKEN')

    # Token check
    if not document or document.get('grub_token') != grub_token:
        return jsonify({'result': 'failed', 'reason': 'Invalid or missing token'}), 401

    # Extract necessary data
    username = document.get('username')
    query = document.get('query')
    callback_url = document.get('callback_url')
    openai_token = document.get('openai_token')

    # Remove the openai_token from the data object
    document.pop('openai_token', None)

    if not callback_url or not openai_token:
        return jsonify({'result': 'failed', 'reason': 'Missing callback URL or OpenAI token'}), 400

    # Respond immediately to the client
    asyncio.create_task(process_query_background(username, query, openai_token, UPLOAD_DIR, callback_url, document))
    
    return jsonify({'status': 'success', 'message': 'Query is being processed'}), 202


# ensure directory exists
def create_and_check_directory(directory_path):
    try:
        # Attempt to create the directory (and any necessary parent directories)
        os.makedirs(directory_path, exist_ok=True)
        logging.info(f"Directory '{directory_path}' ensured to exist.")
        
        # Check if the directory exists to verify it was created
        if os.path.isdir(directory_path):
            logging.info(f"Confirmed: The directory '{directory_path}' exists.")
        else:
            logging.error(f"Error: The directory '{directory_path}' was not found after creation attempt.")
    except Exception as e:
        # If an error occurred during the creation, log the error
        logging.error(f"An error occurred while creating the directory: {e}")


async def process_query_background(username, query, openai_token, upload_dir, callback_url, document):
    try:
        screenshot, additional_data = await ai(username=username, query=query, openai_token=openai_token, upload_dir=upload_dir)
        
        if screenshot:
            document.update(additional_data)  # Merge additional data into the payload
            
            # Perform the callback, including the screenshot and additional data
            await upload_file(callback_url, os.path.basename(screenshot), screenshot, document)
        else:
            # Handle cases where no screenshot is generated
            message = additional_data.get('error')
            await notify_failure(callback_url, document, message)
    except Exception as e:
        logging.error(f"Error processing query: {e}")
        await notify_failure(callback_url, document, str(e))


async def perform_callback(url, document):
    # logic to perform a callback
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=document)
            logging.info(f"Callback response: {response.status_code}")
        except Exception as e:
            logging.error(f"Error performing callback: {e}")


async def notify_failure(callback_url, document, message=None):
    logging.info(f"Notifying failure: {message}")
    
    # Add "aigrub_error" to the document if a message is provided
    if message:
        document["aigrub_error"] = message
    
    # Generate a 13-character long string consisting of lowercase letters and digits
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=13))
    json_filename = f"json_data_{random_string}.json"

    # Dump to file    
    with open(json_filename, 'w') as json_file:
        json.dump(document, json_file)

    # Re-open the file to read its content for uploading
    with open(json_filename, 'rb') as json_file:
        async with httpx.AsyncClient() as client:
            # make the callback with the json file
            response = await client.post(callback_url, files={'json_data': ('json_data.json', json_file, 'application/json')})
            logging.info(f"Notification response: {response.text}")

    os.remove(json_filename)


async def upload_file(callback_url, output_file, output_file_path, document):
    logging.info(f"Uploading file: {output_file}")

    # Prepare JSON data
    json_data = json.dumps(document).encode('utf-8')  # Ensure user_document is properly encoded

    # Guess MIME type
    mime_type, _ = mimetypes.guess_type(output_file_path)
    mime_type = mime_type or 'application/octet-stream'

    async with httpx.AsyncClient() as client:
        with open(output_file_path, 'rb') as f:
            files = {
                'file': (output_file, f, mime_type),
                'json_data': ('json_data.json', json_data, 'application/json')
            }
            response = await client.post(callback_url, files=files)

    if response.status_code == 200:
        logging.info("File uploaded successfully.")
    else:
        logging.error(f"Failed to upload file: {response.text}")

    # remove the screenshot after upload
    os.remove(output_file_path)


# Endpoint to download screenshots
@app.route('/screenshots/<filename>')
async def get_screenshot(filename):
    return await send_from_directory('screenshots', filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
