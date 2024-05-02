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
import time

from google.cloud import storage
from google.api_core.exceptions import Forbidden
from google.cloud import datastore
from google.cloud import ndb

from quart import Quart, render_template, request, redirect, jsonify, url_for, Response, stream_with_context, session, send_from_directory, send_file
from quart_cors import cors

# App definition
app = Quart(__name__, static_folder='static')
app = cors(app, allow_origin=["http://localhost:5000", "https://nbtx.ai"])
app.config['SESSION_COOKIE_MAX_AGE'] = timedelta(seconds=30)
app.secret_key = os.getenv('MITTA_SECRET', 'f00bar22222')

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


#################
# Storage methods
#################

# Initialize the NDB client
client = datastore.Client()
context = ndb.Context(client)
context.set_cache_policy(False)
context.set_memcache_policy(False)
ndb.model._default_model_class = ndb.Model

# Define the URLs class
class URLs(ndb.Model):
    url = ndb.StringProperty(required=True)
    name = ndb.StringProperty(required=True)
    crawl_type = ndb.StringProperty(required=True)
    next_crawl_date = ndb.DateTimeProperty(required=True)

# Function to store a URLs instance
def store_url(url, name, crawl_type, next_crawl_date):
    try:
        # Create a new URLs instance
        url_instance = URLs(
            url=url,
            name=name,
            crawl_type=crawl_type,
            next_crawl_date=next_crawl_date
        )
        
        # Save the URLs instance to the Datastore
        url_key = url_instance.put()
        
        logging.error(f"URLs instance stored successfully. Key: {url_key}")
        
        return url_key
    
    except Exception as e:
        logging.error(f"Error storing URLs instance: {str(e)}")
        return None

# File storage handling
async def upload_to_storage(uuid, filename=None, content=None, content_type=None):
    gcs = storage.Client()
    bucket = gcs.bucket(os.getenv('MITTA_BUCKET'))
    blob_name = f"{uuid}/{filename}"
    blob = bucket.blob(blob_name)

    if content:
        blob.upload_from_string(content, content_type=content_type)
    else:
        raise ValueError("No content provided for upload.")
    
    return f"gs://{bucket.name}/{blob.name}"


# File download and upload to storage
async def move_to_storage(access_uri, uuid, filename):
    async with httpx.AsyncClient() as client:
        mitta_url = f"{access_uri}?token={os.getenv('MITTA_TOKEN')}"
        response = await client.get(mitta_url)

        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', 'application/octet-stream')
            bucket = await upload_to_storage(
                uuid=uuid,
                filename=filename,
                content=response.content,
                content_type=content_type
            )

            # Construct the new access URI based on the MITTA_DEV environment variable
            base_url = "https://mitta-convert.ngrok.io" if os.getenv('MITTA_DEV') == "True" else "https://convert.mitta.ai"
            access_uri = f"{base_url}/download/{uuid}/{filename}"
            return access_uri
        else:
            logging.error(f"Failed to download file from {bucket}")
            return None


# Read JSON data from storage
async def fetch_data_json_from_storage(uuid):
    client = storage.Client()
    bucket = client.bucket(os.getenv('MITTA_BUCKET'))
    blob = bucket.blob(f"{uuid}/data.json")
    
    if not blob.exists():  # Check if the blob exists
        logging.info(f"data.json for UUID {uuid} does not exist. Initializing storage.")
        # Initialize the storage with a default message
        await upload_data_json_to_storage(uuid, {"message": "Initialized storage."})
        return None  # Return None or the default message as per your logic

    try:
        content = blob.download_as_text()
        return content
    except Exception as ex:
        logging.error(f"Error fetching data.json for UUID {uuid}: {ex}")
        return None


# Write JSON data to storage
# Storage is set to retain directory/files for 1 day
async def upload_data_json_to_storage(uuid, message):
    if 'message_id' not in message:
        message['message_id'] = str(uuid4())  # Assign a unique message_id
    if 'uuid' not in message:
        message['uuid'] = uuid

    loop = asyncio.get_running_loop()
    gcs = storage.Client()
    bucket = gcs.bucket(os.getenv('MITTA_BUCKET'))
    blob_name = f"{uuid}/data.json"
    blob = bucket.blob(blob_name)
    data_str = json.dumps(message)  # Serialize the message

    # Pass content_type as part of args in run_in_executor
    await loop.run_in_executor(None, blob.upload_from_string, data_str, 'application/json')


################################
#Auth create UUID and data store
################################

async def gen_uuid_write_json_data():
    uuid = str(uuid4())
    session['uuid'] = uuid
    data = {"uuid": uuid}
    await upload_data_json_to_storage(uuid, data)
    return uuid


@app.route('/login', methods=['GET'])
async def login():
    # Attempt to get the client's IP address from the X-Forwarded-For header
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    client_ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.remote_addr
    logging.info(f"Client IP: {client_ip}")

    # Render the login.html template
    # Note: UUID generation is moved to the POST handler
    return await render_template('login.html')


@app.route('/login', methods=['POST'])
async def process_login():
    # Extract JSON data from the request
    data = await request.get_json()

    # Generate user_uuid here for use in response
    user_uuid = await gen_uuid_write_json_data()

    # Log the generated user_uuid
    logging.info(f"Generated user UUID: {user_uuid}")

    # Respond with JSON including the UUID and indicating the client should redirect
    response = {
        "success": True, 
        "cookieValue": user_uuid,  # Assuming this will be used as a cookie value on the client-side
        "redirectUrl": "/"  # The URL to redirect the client to
    }
    return jsonify(response)

# Ensure logging is configured to see output
logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    app.run(debug=True)



########################
# Event stream managment
########################

connections = {}
historic_queue = []

# Client payload pickup and transfer
async def notify_clients():
    current_time = datetime.now()
    for uuid, (queue, last_active) in list(connections.items()):
        content = await fetch_data_json_from_storage(uuid)
        message_id = None  # Initialize message_id outside the try-except block

        # Attempt to decode the JSON content and extract the message_id
        if content:
            try:
                message = json.loads(content)
                message_id = message.get('message_id')
            except json.JSONDecodeError as e:
                logging.error(f"Error decoding JSON for UUID {uuid}: {e}")
                content = None  # Invalidate content if there's a JSON error

        # Remove the connection if it's inactive, and also clean up related historic_queue entries
        if current_time - last_active > timedelta(minutes=5):
            logging.info(f"Removing inactive connection {uuid}")
            connections.pop(uuid)  # Remove the inactive connection
            if message_id and message_id in historic_queue:
                historic_queue.remove(message_id)  # Remove message_id from historic_queue if present
            continue  # Skip further processing for this UUID

        # Process and send the message if it's valid and not already in historic_queue
        if content and message_id and message_id not in historic_queue:
            logging.info("content uploaded to queue")
            logging.info(content)
            await queue.put(content)
            historic_queue.append(message_id)
    await asyncio.sleep(2)


# Start and stop the queue fetch process
@app.before_serving
async def start_background_tasks():
    async def broadcast():
        while True:
            await asyncio.sleep(2)
            await notify_clients()
    asyncio.create_task(broadcast())


# Event stream
async def event_stream(uuid):
    queue = asyncio.Queue()
    connections[uuid] = (queue, datetime.now())  # Store queue with current timestamp

    try:
        while True:
            data = await queue.get()
            # Refresh the timestamp each time data is sent
            connections[uuid] = (queue, datetime.now())
            data_json = json.dumps(data) if not isinstance(data, str) else data
            yield f"id: {uuid}\nevent: message\ndata: {data_json}\n\n"
            await asyncio.sleep(3)
    except GeneratorExit:
        logging.info(f"Client disconnect {uuid}")
        connections.pop(uuid, None)
        raise


# Check for valid UUID
def is_valid_uuid(uuid, version=4):
    try:
        uuid_obj = UUID(uuid, version=version)
        return str(uuid_obj) == uuid
    except ValueError:
        return False


# Your updated /events route
@app.route('/events')
async def events():
    uuid = request.args.get('uuid', None)
    client_version = request.args.get('ver', None)

    if uuid and is_valid_uuid(uuid):
        logging.info(f"Establishing event stream for {uuid}")
        return Response(event_stream(uuid), content_type='text/event-stream')
    else:
        logging.error("Invalid or missing UUID")
        return '', 400


@app.route('/ack', methods=['GET', 'POST'])
async def ack():
    # Try to grab the UUID from the cookie
    uuid = request.cookies.get('uuid', None)

    # Check if the UUID is valid
    if uuid is None or not is_valid_uuid(uuid):
        # If not, redirect to the login page
        return redirect(url_for('login'))

    # Check if the UUID is in a session
    uuid_in_session = session.get('uuid')
    if uuid != uuid_in_session:
        return redirect(url_for('login'))

    await upload_data_json_to_storage(uuid, {})    
    return jsonify({"status": "success", "message": "Download event removed from storage."}), 200


@app.route('/', methods=['GET', 'POST'])
async def convert():
    # Try to grab the UUID from the cookie
    uuid = request.cookies.get('uuid', None)

    # Check if the UUID is valid
    if uuid is None or not is_valid_uuid(uuid):
        # If not, redirect to the login page
        return redirect(url_for('login'))

    # Check if the UUID is in a session
    uuid_in_session = session.get('uuid')
    if uuid != uuid_in_session:
        return redirect(url_for('login'))

    # ensure we have a file for this uuid
    await upload_data_json_to_storage(uuid, {})
    
    # Set the instruction list
    instructions = [
        "Where can I swim, float or paddle in New Braunfels?",
        "What restaurants do you recommend?",
        "I'm looking for a place to stay.",
        "I'd like to visit some parks.",
        "What are your entertainment options?",
        "Are there any bands playing soon?",
        "Where can I get good BBQ?",
        "Tell me about the history and heritage of this town!"
    ]

    if request.method == 'POST':
        form_data = await request.form
        posted_instruction = form_data.get('instructions')

        # If a new instruction is posted, add it to the top of the list
        if posted_instruction and posted_instruction not in instructions:
            instructions.insert(0, posted_instruction)

    # encode instructions
    encoded_instructions = base64.b64encode(json.dumps(instructions).encode('utf-8')).decode('utf-8')

    # Pass the (possibly updated) instructions list to the template
    current_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00") # card publish
    return await render_template('index.html', instructions=encoded_instructions, current_date=current_date)


@app.route('/chat', methods=['POST'])
async def chat():
    form_data = await request.form  # Correctly await the form data
    user_query = form_data.get('query', '')  # Now you can use .get() since form_data is not a coroutine

    # Assuming a function that processes the user query and returns a bot response
    # This function needs to be defined or imported
    bot_response = await process_user_query(user_query)

    # Render the chat page, passing the user query and the bot's response
    return await render_template('chat.html', user_query=user_query, bot_response=bot_response)

async def process_user_query(query):
    # This is a placeholder function to simulate processing the query
    # Replace this with actual logic to handle the user's query
    return f"Simulated response to '{query}'"


@app.route('/upload', methods=['POST'])
async def upload():
    # Try to grab the UUID from the cookie
    uuid = request.cookies.get('uuid', None)

    # Check if the UUID is valid
    if uuid is None or not is_valid_uuid(uuid):
        # If not, redirect to the login page
        return redirect(url_for('login'))

    # Check if the UUID is in a session
    uuid_in_session = session.get('uuid')
    if uuid != uuid_in_session:
        return redirect(url_for('login'))

    await upload_data_json_to_storage(uuid, {"message": "Received upload request."})

    # Get the calling info from the client
    form_data = await request.form    
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



@app.route('/crawl', methods=['GET', 'POST'])
async def crawl():

    if request.method == 'GET':
        # Serve the HTML page when accessed via a GET request
        logging.info("serving admin.html")
        return await render_template('admin.html')

    # The following code handles the POST request:
    uuid = request.cookies.get('uuid', None)
    if uuid is None or not is_valid_uuid(uuid):
        # If not, redirect to the login page
        return redirect(url_for('login'))

    uuid_in_session = session.get('uuid')
    if uuid != uuid_in_session:
        return redirect(url_for('login'))

    data = await request.get_json()

    logging.info(data)

    url = data.get('url')
    name = data.get('name')
    crawl_type = data.get('crawl_type')
    frequency_hours = data.get('frequency_hours')

    logging.info(frequency_hours)

    if frequency_hours is None:
        return jsonify({"status": "error", "message": "Frequency hours must be provided."}), 400

    # Convert frequency_hours to an integer
    try:
        frequency_hours = int(frequency_hours)
    except ValueError:
        return jsonify({"status": "error", "message": "Frequency hours must be a valid integer."}), 400

    # Calculate the next crawl date based on the current time and frequency
    next_crawl_date = datetime.now() + timedelta(hours=frequency_hours)

    # Store the URLs instance
    url_key = store_url(url, name, crawl_type, next_crawl_date)


    if url_key:
        return jsonify({"status": "success", "message": "URL stored successfully."}), 200
    else:
        return jsonify({"status": "error", "message": "Failed to store URL."}), 500


@app.route('/callback', methods=['POST'])
async def callback():
    data = await request.get_json()

    # Grab the UUID
    uuid = data.get('uuid', [])
    if isinstance(uuid, list):
        try:
            uuid = uuid[0]
        except:
            return jsonify({"status": "error", "message": "Can't access the UUID."})

    # Define the token
    mitta_token = os.getenv('MITTA_TOKEN')

    # Compare the provided token with the expected token
    token = request.args.get('token', default=None)

    # Check the tokens match
    if token != mitta_token:
        logging.info("Authentication failed to callback.")
        # If tokens do not match, return an error response
        return jsonify({'status': 'error', 'message': "Authentication failed"}), 401


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
        access_uri = await move_to_storage(access_uri, uuid, filename)

    # Get any valid access_uris
    messages = data.get('message', [])
    
    if messages:
        message = messages[0]
    else:
        message = 'What can I convert for you?'

    # Hot wire the ffmpeg_result to message
    # We only get this when there is an error
    if ffmpeg_result:
        message = ffmpeg_result

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

    # Try to grab the UUID from the cookie
    uuid = request.cookies.get('uuid', None)

    # Check if the UUID is valid
    if uuid is None or not is_valid_uuid(uuid):
        # If not, redirect to the login page
        return redirect(url_for('login'))

    # Check if the UUID is in a session
    uuid_in_session = session.get('uuid')
    if uuid != uuid_in_session:
        return redirect(url_for('login'))

    static_folder_path = app.static_folder
    file_path = os.path.join(static_folder_path, filename)
    return await send_from_directory(static_folder_path, filename)


# Define a directory for temporary downloads
DOWNLOAD_DIR = 'downloads'

@app.route('/download/<path:filename>')
async def download_file(filename):
    # Special case for specific filename - TODO remove later
    download_path = os.path.join('static', filename)
    if filename == "zbczhpAw97bAm.png":
        if os.path.exists(download_path):
            content_type = "image/png"
            return await send_from_directory(os.path.dirname(download_path), os.path.basename(download_path), as_attachment=True, mimetype=content_type)

    # no need to check session as the filenames are randomized
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
