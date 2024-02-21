import asyncio
import httpx
import logging
import os
import json
import random
import string
import io
import mimetypes
from quart import Quart, jsonify, render_template, request, send_from_directory, redirect
from quart_cors import cors

from grub2 import ai

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
    document.pop('grub_token')

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
    
    return jsonify({'status': 'success', 'message': 'Query is being processed', 'callback_url': callback_url}), 202


async def process_query_background(username, query, openai_token, upload_dir, callback_url, document):
    success, additional_data = await ai(username=username, query=query, openai_token=openai_token, upload_dir=upload_dir)
    
    if success:
        document.update(additional_data)  # Merge additional data into the payload

        # Perform the callback, including the screenshot and additional data
        await upload_file(callback_url, document)
    else:
        # Handle cases where no screenshot is generated
        message = f"{additional_data.get('error')}: {additional_data.get('reason')}"
        await notify_failure(callback_url, document, message)
    

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


async def upload_file(callback_url, document):
    """
    Uploads files specified in the document to the callback URL.
    Expects 'filename' and optionally 'image_from_page' in the document.
    """
    logging.info("in upload_file")
    files_to_upload = []
    # Prepare JSON data
    json_data = json.dumps(document).encode('utf-8')  # Encode document to JSON
    
    # Add JSON data to the files to upload
    files_to_upload.append(('json_data', ('json_data.json', json_data, 'application/json')))
    
    # Check and add 'filename' if it exists in document
    if 'filename' in document:
        file_path = document['filename']
        output_file = os.path.basename(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        mime_type = mime_type or 'application/octet-stream'
        files_to_upload.append(('file', (output_file, open(file_path, 'rb'), mime_type)))
    
    # Check and add 'image_from_page' if it exists in document
    if 'image_from_page' in document:
        image_path = document['image_from_page']
        image_file = os.path.basename(image_path)
        mime_type, _ = mimetypes.guess_type(image_path)
        mime_type = mime_type or 'application/octet-stream'
        files_to_upload.append(('image', (image_file, open(image_path, 'rb'), mime_type)))
    
    # Perform the upload
    async with httpx.AsyncClient() as client:
        response = await client.post(callback_url, files=files_to_upload)
    
    # Log the response and clean up
    if response.status_code == 200:
        logging.info("Files uploaded successfully.")
    else:
        logging.error(f"Failed to upload files: {response.text}")
    
    # Close and remove files
    for _, file_tuple in files_to_upload:
        if file_tuple[0] != 'json_data':  # Skip json_data as it's not a file needing closing
            os.remove(file_tuple[1].name)  # Remove the file from the filesystem


# Endpoint to download screenshots
@app.route('/screenshots/<filename>')
async def get_screenshot(filename):
    return await send_from_directory('screenshots', filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
