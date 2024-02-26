"""
This is a reference web server for handling non-blocking clients.

https://mitta.ai

Copyright:
- MittaAI, Kord Campbell, 2024
- BSD License
"""

import os
import json
import base64
import logging
import random
import mimetypes

import io
import asyncio
import aiofiles
import httpx

from uuid import uuid4, UUID
from datetime import datetime, timedelta

from google.cloud import storage
from google.api_core.exceptions import Forbidden

from quart import Quart, render_template, request, redirect, jsonify, Response, stream_with_context, session, send_from_directory, send_file
from quart_cors import cors

# App definition
app = Quart(__name__, static_folder='static')
app = cors(app, allow_origin=["http://localhost:5000", "https://convert.mitta.ai"])
app.config['SESSION_COOKIE_MAX_AGE'] = timedelta(seconds=30)
app.secret_key = os.getenv('MITTA_SECRET', 'f00bar')

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# File storage handling
async def upload_to_storage(uuid, filename=None, content=None, content_type=None):
    logging.info("upload_to_storage")
    gcs = storage.Client()
    bucket = gcs.bucket(os.getenv('MITTA_BUCKET'))
    blob_name = f"{uuid}/{filename}"
    blob = bucket.blob(blob_name)

    if content:
        blob.upload_from_string(content, content_type=content_type)
    else:
        raise ValueError("No content provided for upload.")
    
    return f"gs://{bucket.name}/{blob.name}"


async def download_and_upload(access_uri, uuid, filename):
    async with httpx.AsyncClient() as client:
        mitta_url = f"{access_uri}?token={os.getenv('MITTA_TOKEN')}"
        logging.info(mitta_url)
        response = await client.get(mitta_url)

        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', 'application/octet-stream')
            new_access_uri = await upload_to_storage(
                uuid=uuid,
                filename=filename,
                content=response.content,
                content_type=content_type
            )

            # Construct the new access URI based on the MITTA_DEV environment variable
            base_url = "https://mitta-convert.ngrok.io" if os.getenv('MITTA_DEV') == "True" else "https://convert.mitta.ai"
            new_access_uri = f"{base_url}/download/{uuid}/{filename}"
            
            logging.info(f"File uploaded successfully to GCS: {new_access_uri}")
            return new_access_uri
        else:
            logging.error(f"Failed to download file from {access_uri}")
            return None

async def upload_data_json_to_storage(uuid, data):
    loop = asyncio.get_running_loop()
    gcs = storage.Client()
    bucket = gcs.bucket(os.getenv('MITTA_BUCKET'))
    blob_name = f"{uuid}/data.json"
    blob = bucket.blob(blob_name)
    # Ensure data is a string for upload_from_string
    data_str = json.dumps(data) if not isinstance(data, str) else data
    # Pass content_type as part of args in run_in_executor
    await loop.run_in_executor(None, blob.upload_from_string, data_str, 'application/json')


async def generate_uuid_and_upload_data_json():
    user_uuid = str(uuid4())
    session['uuid'] = user_uuid
    data = {"uuid": user_uuid, "message": "Connection established."}
    await upload_data_json_to_storage(user_uuid, data)
    return user_uuid

async def ensure_data_json_uploaded(uuid):
    loop = asyncio.get_running_loop()
    client = storage.Client()
    bucket = client.bucket(os.getenv('MITTA_BUCKET'))
    blob = bucket.blob(f"{uuid}/data.json")

    # Check if the blob exists to prevent overwriting
    exists = await loop.run_in_executor(None, blob.exists)
    if not exists:
        data = {"uuid": uuid, "message": "Setting up secure connection."}
        await upload_data_json_to_storage(uuid, data)

# Ack and login routes
@app.route('/ack', methods=['POST'])
async def ack():
    # Use the session's UUID instead of one provided by the client
    if 'uuid' not in session:
        return jsonify({"error": "Session UUID not found"}), 400

    uuid = session['uuid']
    
    # Prepare the data to reset or update the file contents
    data = {"uuid": uuid}
    
    # Call the function to upload data.json to the storage
    await upload_data_json_to_storage(uuid, data)
    
    return jsonify({"message": "Acknowledgement received", "uuid": uuid})


@app.route('/login', methods=['GET'])
async def login():
    user_uuid = await generate_uuid_and_upload_data_json()
    return jsonify({"uuid": user_uuid})


# File handling and validation of UUID
async def fetch_data_json_content(uuid):
    try:
        client = storage.Client()
        bucket = client.bucket(os.getenv('MITTA_BUCKET'))
        blob = bucket.blob(f"{uuid}/data.json")
        content = blob.download_as_text()
        return content
    except Exception as ex:
        logging.error(f"Error fetching data.json for UUID {uuid}: {ex}")
        return None

async def my_generator_function(uuid=None):
    while True:
        await ensure_data_json_uploaded(uuid)
        content = await fetch_data_json_content(uuid)
        if content:
            yield f"data: {content}\n\n"
        else:
            yield f"data: Hello, {uuid}.\n\n"
        await asyncio.sleep(3)


def is_valid_uuid(uuid_to_test, version=4):
    try:
        uuid_obj = UUID(uuid_to_test, version=version)
        return str(uuid_obj) == uuid_to_test
    except ValueError:
        return False

async def uuid_in_session(uuid):
    return session.get('uuid') == uuid


# Main Quart routes
@app.route('/stream')
async def stream_data():
    uuid = request.args.get('uuid', None)
    if uuid and is_valid_uuid(uuid) and await uuid_in_session(uuid):
        async def generator_wrapper():
            async for item in my_generator_function(uuid):
                yield item
        return Response(generator_wrapper(), content_type='text/event-stream')
    else:
        return Response("event: error\ndata: Invalid or missing UUID.\n\n", content_type='text/event-stream')


@app.route('/', methods=['GET', 'POST'])
async def convert():
    # Initialize the default instructions
    instructions = [
        "Rotate image by 90 degrees",
        "Flip image horizontally",
        "Convert image to JPEG with quality 85",
        "Scale landscape image to 320 tall, then crop to 320 wide",
        "Shrink the image by 50%",
        "Convert image to a PNG",
        "Change image to grayscale",
        "Apply a nice sepia tone to the image",
        "Increase saturation by 50%",
        "Apply a slight brown tint and then decrease staturation by 50%",
        "Convert audio to MP3 format",
        "Grab first 10 seconds of audio and MP3 it",
        "Resize video to 1080p HD resolution and keep aspect ratio",
        "Extract first video frame as PNG",
        "Create a 5-second GIF from video",
        "Extract audio from video as MP3",
        "Convert to MP4 with H.264 encoding",
        "Trim video to first 10 seconds",
        "Convert to 360p WebM format",
        "Increase playback speed by 2x",
        "Create a thumbnail at the first minute",
        "Normalize audio in a video file"
    ]


    if request.method == 'POST':
        form_data = await request.form
        posted_instruction = form_data.get('instructions')

        logging.info(posted_instruction)
        # If a new instruction is posted, add it to the top of the list
        if posted_instruction and posted_instruction not in instructions:
            instructions.insert(0, posted_instruction)
        
        logging.info(instructions)

    # encode instructions
    encoded_instructions = base64.b64encode(json.dumps(instructions).encode('utf-8')).decode('utf-8')

    # Pass the (possibly updated) instructions list to the template
    current_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00") # card publish
    return await render_template('index.html', instructions=encoded_instructions, current_date=current_date)


@app.route('/upload', methods=['POST'])
async def upload():
    form_data = await request.form
    uuid = form_data.get('uuid')
    
    files = await request.files
    file = files.get('file')

    if file:
        instructions = form_data.get('instructions', 'Convert to a 640 wide gif')
        logging.info(f"Received instructions '{instructions}' from '{uuid}'")

        # Define the endpoint and token
        pipeline = os.getenv('MITTA_PIPELINE')
        mitta_token = os.getenv('MITTA_TOKEN')

        # App Callback to /callback below
        if os.getenv('MITTA_DEV') == "True":
            app_callback = f"https://mitta-convert.ngrok.io/callback?token={mitta_token}"
        else:
            app_callback = f"https://convert.mitta.ai/callback?token={mitta_token}"

        # Prepare the JSON payload
        json_data = {
            "uuid": uuid,
            "ffmpeg_request": instructions,
            "app_callback_uri": app_callback
        }

        with open(f'json_data_{uuid}.json', 'w') as json_file:
            json.dump(json_data, json_file)

        # Prepare the file to be uploaded to the external handler
        files = {
            'file': (file.filename, file.read(), file.content_type),
            'json_data': ('json_data.json', open(f'json_data_{uuid}.json', 'rb'), 'application/json')
        }

        # Mitta Pipeline URL
        url = f"https://mitta.ai/pipeline/{pipeline}/task?token={mitta_token}"

        # Send the file using httpx
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, files=files)

        # remove the file
        os.remove(f'json_data_{uuid}.json')

        # Check the response from the external handler
        if response.status_code == 200:
            return jsonify({"status": "success", "message": "File uploaded successfully."}), 200
        else:
            return jsonify({"status": "error", "message": "Failed to upload file."}), 500

    return jsonify({"status": "error", "message": "No file received."}), 404


@app.route('/callback', methods=['POST'])
async def callback():
    data = await request.get_json()
    logging.info("in callback")
    logging.info(data)

    # Define the token
    mitta_token = os.getenv('MITTA_TOKEN')

    # Compare the provided token with the expected token
    token = request.args.get('token', default=None)

    # Check the tokens match
    if token != mitta_token:
        logging.info("Authentication failed")
        # If tokens do not match, return an error response
        return jsonify({'status': 'error', 'message': "Authentication failed"}), 401

    # uuid and message
    message = "Processing."  # Default message

    # Iterate through the keys in the data dictionary
    for key, value in data.items():
        if 'message' in key:
            message = value

    # Grab the UUID
    uuid = data.get('uuid', [])
    if isinstance(uuid, list):
        try:
            uuid = uuid[0]
        except:
            return jsonify({"status": "error", "message": "Can't access the UUID."})

    # Other variables, all expected to be lists
    access_uris = data.get('access_uri', [])
    filenames = data.get('filename', [])
    ffmpeg_results = data.get('ffmpeg_result', [])

    # Check filename and result
    filename = filenames[0] if filenames else ''
    ffmpeg_result = ffmpeg_results[0] if ffmpeg_results else ''

    # Get any valid access_uris
    access_uri = access_uris[0] if access_uris and not ffmpeg_results else ''

    # Attempt to download and upload the file, receiving a new access URI if successful
    if access_uri:
        access_uri = await download_and_upload(access_uri, uuid, filename)
        message = "Downloading the file. Look at the bottom if you are on an iPhone, the top if you are in a browser."

    # Use the new_access_uri in the message_data
    message_data = {
        "status": "success", 
        "message": message,
        "access_uri": access_uri,
        "ffmpeg_result": ffmpeg_result,
        "filename": filename,
        "uuid": uuid 
    }

    # Use the upload_to_storage function to upload the JSON data
    await upload_data_json_to_storage(uuid, message_data)

    # Return
    return jsonify({"status": "success"}), 200


# Static files
@app.route('/static/<path:filename>')
async def custom_static(filename):
    static_folder_path = app.static_folder
    file_path = os.path.join(static_folder_path, filename)
    return await send_from_directory(static_folder_path, filename)


# Define a directory for temporary downloads
DOWNLOAD_DIR = 'downloads'

@app.route('/download/<path:filename>')
async def download_file(filename):
    bucket_name = os.getenv('MITTA_BUCKET')
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(filename)

    # Construct a local path for the downloaded file
    download_path = os.path.join(DOWNLOAD_DIR, filename)
    os.makedirs(os.path.dirname(download_path), exist_ok=True)  # Ensure the directory exists

    # Download the file from GCS to the local path
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: blob.download_to_filename(download_path))

    # Check if the file was downloaded successfully
    if not os.path.exists(download_path):
        abort(404, "File not found")

    # Guess the file's MIME type
    content_type, _ = mimetypes.guess_type(download_path)
    if content_type is None:
        content_type = "application/octet-stream"

    # Serve the file from the local file system
    return await send_from_directory(os.path.dirname(download_path), os.path.basename(download_path), as_attachment=True, mimetype=content_type)



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
