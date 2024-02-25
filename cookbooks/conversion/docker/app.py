"""
This Python file is part of the MittaAI platform, developed by Kord Campbell and copyrighted by MittaAI. 
It is released under the BSD license, promoting both open-source usage and distribution while allowing for 
commercial use. The application serves as a reference service for processing various media conversion tasks, 
leveraging a combination of asynchronous web frameworks and Google Cloud Pub/Sub for efficient, distributed 
communication and task management.

Description:
The application, built on Quart, provides an asynchronous web server that handles media conversion requests 
via websockets and HTTP endpoints. Users can submit files for conversion, specifying instructions through 
a web interface. The application then processes these files using a MittaAI pipeline, offloading tasks to 
external services or infrastructure. Utilizing Google Cloud Pub/Sub, the system can communicate across 
distributed instances, ensuring that callbacks and responses are routed to the correct client session, 
even in complex, load-balanced deployments.

Usage:
- Clients connect to the service, submitting media files along with conversion instructions.
- The service queues these requests for processing, and invokes MittaAI API pipeline calls.
- Upon completion, results are communicated back to the client through websockets or direct HTTP responses, 
  facilitated by a Pub/Sub mechanism that ensures messages reach the correct instance handling the client's session.

This architecture allows for scalable, efficient processing of media files, catering to a broad range of conversion 
tasks while maintaining high availability and responsiveness. This code is meant to illustrate how to build async
pipeline use with MittaAI.

https://mitta.ai

Copyright:
- MittaAI, Kord Campbell, 2024
- BSD License

"""

import os
import json
import base64
import logging
import datetime
import random
import asyncio
import aiofiles
import queue

from urllib.parse import urlparse, unquote

from uuid import uuid4

from google.cloud import pubsub_v1

from quart import Quart, websocket, render_template, request, redirect, jsonify
from quart import send_from_directory
from quart_cors import cors
import httpx

app = Quart(__name__, static_folder='static')
app = cors(app, allow_origin=["http://localhost:5000", "https://convert.mitta.ai"])

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Thread-safe queue for inter-thread communication
inter_thread_queue = queue.Queue()

# Asyncio queue for processing messages
message_queue = asyncio.Queue()

# Connected websockets; managed by UUID
connected_websockets = {}

# Ensure these environment variables are set in your environment
project_id = os.getenv('MITTA_PROJECT')
topic_id = "convert-notice"
subscription_id = "convert-notice-sub"

# Initialize Publisher and Subscriber clients
publisher = pubsub_v1.PublisherClient()
subscriber = pubsub_v1.SubscriberClient()

# Define Pub/Sub topic and subscription paths
topic_path = publisher.topic_path(project_id, topic_id)
subscription_path = subscriber.subscription_path(project_id, subscription_id)

async def publish_message_async(topic_path, message_data):
    # Ensure this operation does not block by running it in the background
    loop = asyncio.get_running_loop()
    try:
        # Use a thread pool executor to perform the blocking publish operation
        result = await loop.run_in_executor(None, lambda: publisher.publish(topic_path, message_data).result())
        logging.info(f"Message published with ID: {result}")
    except Exception as e:
        logging.error(f"Failed to publish message: {e}")

def pub_sub_callback(message):
    inter_thread_queue.put(message)

async def transfer_messages_to_async_queue():
    while True:
        if not inter_thread_queue.empty():
            message = inter_thread_queue.get()
            await message_queue.put(message)
        else:
            await asyncio.sleep(0.5)  # Adjust sleep time as needed

async def process_pubsub_messages():
    # Define the token
    mitta_token = os.getenv('MITTA_TOKEN')
    
    while True:
        message = await message_queue.get()
        data = json.loads(message.data.decode("utf-8"))
        logging.info(f"Processed message: {data}")
        client_uuid = data.get('uuid', None)

        try:
            # Check if client_uuid is connected before processing
            if client_uuid in connected_websockets:
                # Check for 'access_uri' in the message for file download process
                if "access_uri" in data and data.get('access_uri'):
                    download_dir = 'download'
                    os.makedirs(download_dir, exist_ok=True)
                    filename = data["filename"]
                    filepath = os.path.join(download_dir, filename)
                    access_uri = f"{data.get('access_uri')}?token={mitta_token}"
                    logging.info(f"Downloading file from: {access_uri}")

                    async with httpx.AsyncClient() as client:
                        response = await client.get(access_uri)

                        if response.status_code == 200:
                            async with aiofiles.open(filepath, 'wb') as f:
                                await f.write(response.content)
                            logging.info(f"File downloaded successfully: {filepath}")

                            # Update access_uri to point to the service's download handler
                            new_access_uri = f"https://mitta-convert.ngrok.io/download/{filename}" if os.getenv('MITTA_DEV') == "True" else f"https://convert.mitta.ai/download/{filename}"
                            data["access_uri"] = new_access_uri

                    # Broadcast the message with updated access_uri
                    await broadcast(data, client_uuid)
                else:
                    # If no access_uri, simply broadcast the data as it is
                    await broadcast(data, client_uuid)

                # Acknowledge and mark the message handling as done
                message.ack()
            else:
                logging.info(f"UUID {client_uuid} not connected. Message not broadcasted.")
                
        except Exception as e:
            logging.error(f"Error processing message for UUID {client_uuid}: {e}")
        
        finally:
            # Ensure task_done is called to maintain the queue's task count
            message_queue.task_done()

def start_pubsub_listener():
    subscriber.subscribe(subscription_path, callback=pub_sub_callback)

# Adjusted Broadcast messages to connected clients based on UUID
async def broadcast(message, recipient_id=None):
    if recipient_id:
        ws = connected_websockets.get(recipient_id)
        if ws:
            await ws.send_json(message)

# Initialize app with the queue
@app.before_serving
async def startup():
    asyncio.get_running_loop().create_task(transfer_messages_to_async_queue())
    asyncio.get_running_loop().create_task(process_pubsub_messages())
    start_pubsub_listener()

# Websocket handling
@app.websocket('/ws')
async def ws():
    unique_id = str(uuid4())  # Generate a unique ID for the session
    ws_obj = websocket._get_current_object()
    connected_websockets[unique_id] = ws_obj  # Store the WebSocket object with the unique ID

    try:
        await ws_obj.send_json({'uuid': unique_id})
        while True:
            # Awaiting any message from the client, could be used for further communication
            await websocket.receive()
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
    finally:
        connected_websockets.pop(unique_id, None)  # Remove the WebSocket from the dictionary on disconnect


# Static files
@app.route('/static/<path:filename>')
async def custom_static(filename):
    static_folder_path = app.static_folder
    file_path = os.path.join(static_folder_path, filename)
    return await send_from_directory(static_folder_path, filename)


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
    current_date = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00") # card publish
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
            await broadcast({"status": "success", "message": "File uploaded successfully!"}, uuid)
            return jsonify({"status": "success", "message": "File uploaded successfully"}), 200
        else:
            await broadcast({"status": "success", "message": "File upload failed. Try again in a few seconds."}, uuid)
            return jsonify({"status": "error", "message": "Failed to upload file"}), 500

    await broadcast({"status": "error", "message": "No file received."}, uuid)
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
    }).encode("utf-8")

    # Publish the message
    await publish_message_async(topic_path, message_data)

    # Return
    return jsonify({"status": "success"}), 200


@app.route('/download/<filename>')
async def download_file(filename):
    download_dir = 'download'  # Same directory we used for saving the files
    return await send_from_directory(download_dir, filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
