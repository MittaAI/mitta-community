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
import asyncio
import aiofiles
import httpx

from uuid import uuid4
from datetime import datetime, timedelta

from quart import Quart, render_template, request, redirect, jsonify, Response, stream_with_context
from quart import send_from_directory
from quart_cors import cors

# App definition
app = Quart(__name__, static_folder='static')
app = cors(app, allow_origin=["http://localhost:5000", "https://convert.mitta.ai"])

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# Static files
@app.route('/static/<path:filename>')
async def custom_static(filename):
    static_folder_path = app.static_folder
    file_path = os.path.join(static_folder_path, filename)
    return await send_from_directory(static_folder_path, filename)

async def my_generator_function():
    yield "data: Hello\n\n"

@app.route('/stream')
async def stream_data():
    async def generator_wrapper():
        async for item in my_generator_function():
            yield item
    return Response(generator_wrapper(), content_type='text/event-stream')


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
    if 'file' in await request.files:
        file = (await request.files)['file']
        form_data = await request.form
        instructions = form_data.get('instructions', 'Convert to a 640 wide gif')
        uuid = form_data.get('uuid')
        if isinstance(uuid, list):
            uuid = uuid[0]
        
        # Log the received instructions for debugging
        logging.info(f"Received instructions '{instructions}' from '{uuid}'")

        # Define the endpoint and token
        pipeline = os.getenv('MITTA_PIPELINE')
        mitta_token = os.getenv('MITTA_TOKEN')

        # App Callback to /callback below
        if os.getenv('MITTA_DEV') == "True":
            app_callback = f"https://mitta-convert.ngrok.io/callback?token={mitta_token}"
        else:
            app_callback = f"https://convert.mitta.ai/callback?token={mitta_token}"

        # Prepare the JSON payload and encode it into bytes
        # httpx recent versions may not like non-encoded payloads
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
            return jsonify({"status": "success", "message": "File uploaded successfully"}), 200
        else:
            return jsonify({"status": "error", "message": "Failed to upload file"}), 500

    return jsonify({"status": "error", "message": "No file received"}), 404


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

    # Other variables, all expected to be lists
    access_uris = data.get('access_uri', [])
    uuid = data.get('uuid', [])
    filenames = data.get('filename', [])
    ffmpeg_results = data.get('ffmpeg_result', [])

    filename = filenames[0] if filenames else ''
    ffmpeg_result = ffmpeg_results[0] if ffmpeg_results else ''

    access_uri = access_uris[0] if access_uris and not ffmpeg_results else ''

    if isinstance(uuid, list):
        try:
            uuid = uuid[0]
        except:
            uuid = "anonymous"
    if not uuid:
        uuid = "anonymous"

    message_data = json.dumps({
        "status": "success", 
        "message": message, 
        "access_uri": access_uri,  # Directly include access_uri in the message
        "ffmpeg_result": ffmpeg_result,
        "filename": filename,
        "uuid": uuid 
    })

    logging.info(message_data)

    # Return
    return jsonify({"status": "success"}), 200


@app.route('/download/<filename>')
async def download_file(filename):
    download_dir = 'download'  # Same directory we used for saving the files
    return await send_from_directory(download_dir, filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
