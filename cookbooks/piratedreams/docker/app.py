import os
import json
import logging
import datetime
import random
import asyncio
from urllib.parse import urlparse, unquote

from uuid import uuid4

from quart import Quart, websocket, render_template, request, redirect, jsonify, send_from_directory
from quart_cors import cors
import httpx

app = Quart(__name__, static_folder='static')
app = cors(app, allow_origin=["http://localhost:5000", "https://dreams.mitta.ai"])

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@app.route('/static/<path:filename>')
async def custom_static(filename):
    static_folder_path = app.static_folder
    file_path = os.path.join(static_folder_path, filename)
    return await send_from_directory(static_folder_path, filename)


@app.route('/', methods=['GET', 'POST'])
async def dream():
    # Initialize the default instructions
    instructions = [
        "A native is offering me a coconut.",
        "I see a chest here, locked and half buried.",
        "A storm approaches and I need shelter!",
        "There be sand in my boots!",
        "Where is my map?",
        "There is a cave in the cliffs."
    ]

    # AI suggested
    instructions.extend([
        "A parrot lands on my shoulder, squawking mysteries.",
        "I find a rusty old key amongst the seaweed.",
        "There is an abandoned campsite with a flickering lantern.",
        "A shipwreck lies off the shore, barely visible through the fog.",
        "Strange footprints lead away from the waters edge.",
        "I spot a distant sail on the horizon.",
        "A mysterious bottle with a message inside washes up.",
        "I hear the sound of singing from over the dunes.",
        "An old, weathered sign points to Treasure Cove.",
        "A monkey thief has run off with my hat!",
        "The moon reveals a path not seen by day.",
        "A hidden map piece flutters in the wind, stuck in a palm tree.",
        "I uncover a spyglass, buried in the sand.",
        "A mysterious giggle from the trees, playful and light.",
        "A finely crafted necklace found in the sand, still warm.",
        "Footprints lead to a secluded spot, beside them, an exotic bloom.",
        "The echo of a soft song, drawing me towards a hidden cove.",
        "A shell bikini is here, and then a tap on my shoulder."
    ])
    random.shuffle(instructions)

    # Generate a random number between 1 and 2
    num = random.randint(1, 14)

    # Template the filename with the random number
    pirate_filename = f"pirate{num}.png"

    if request.method == 'POST':
        form_data = await request.form
        posted_instruction = form_data.get('instructions')

        # If a new instruction is posted, add it to the top of the list
        if posted_instruction and posted_instruction not in instructions:
            instructions.insert(0, posted_instruction)

    # Pass the (possibly updated) instructions list to the template
    current_date = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00") # card publish
    return await render_template('index.html', instructions=instructions, current_date=current_date, pirate_filename=pirate_filename)



@app.route('/ask', methods=['POST'])
async def ask():
    # Define the endpoint and token
    pipeline = os.getenv('MITTA_PIPELINE')
    mitta_token = os.getenv('MITTA_TOKEN')

    form_data = await request.form
    instructions = form_data.get('instructions', 'Hello there, Mr. Pirate!')
    uuid = form_data.get('uuid')
    
    # Log the received instructions for debugging
    logging.info(f"Received instructions: {instructions}")
    logging.info(f"UUID: {uuid}")

    # Prepare the JSON payload and encode it into bytes
    # httpx recent versions may not like non-encoded payloads
    if os.getenv('MITTA_DEV') == "True":
        callback = f"https://kordless.ngrok.io/callback?token={mitta_token}"
        logging.info("in dev")
    else:
        callback = f"https://dreams.mitta.ai/callback?token={mitta_token}"

    json_data = {
        "user_document": {"uuid": uuid},
        "instructions": instructions,
        "callback_uri": callback
    }

    with open(f'json_data_{uuid}.json', 'w') as json_file:
        json.dump(json_data, json_file)

    # Prepare the file to be uploaded to the external handler
    files = {
        'json_data': ('json_data.json', open(f'json_data_{uuid}.json', 'rb'), 'application/json')
    }

    # dev on dev
    if os.getenv('MITTA_DEV'):
        # comment out the ngrok one if you are testing to production pipelines
        # url = f"https://kordless.ngrok.io/pipeline/{pipeline}/task?token={mitta_token}"
        url = f"https://mitta.ai/pipeline/{pipeline}/task?token={mitta_token}"
    else:
        url = f"https://mitta.ai/pipeline/{pipeline}/task?token={mitta_token}"
    
    # Send the file using httpx
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, files=files)

    # remove the file
    os.remove(f'json_data_{uuid}.json')
    logging.info(response.status_code)
    # Check the response from the external handler
    if response.status_code == 200:
        print(f"JSON task response: {response.json()}")
        await broadcast({"status": "success", "message": "Received request!"}, uuid)
        return jsonify({"status": "success", "message": "Request received"}), 200
    else:
        await broadcast({"status": "success", "message": "Pipeline failure."})
        return jsonify({"status": "error", "message": "Failed to send to pipeline"}), 401


def extract_filename_from_url(url):
    parsed_url = urlparse(url)
    path = parsed_url.path
    decoded_path = unquote(path)
    filename = decoded_path.split('/')[-1]
    
    return filename


async def download_uri_content(uri, token, download_dir='download'):
    """
    Asynchronously downloads content from a given URI and saves it locally.
    
    Args:
    - uri: The URI from which to download the content.
    - token: Authentication token required for the download.
    - download_dir: The directory where the downloaded content will be saved.
    
    Returns:
    - filepath: The path to the saved file.
    - success: Boolean indicating the success of the download.
    """
    # Ensure the download directory exists
    os.makedirs(download_dir, exist_ok=True)

    # Extract the filename from the URI
    filename = extract_filename_from_url(uri)
    filepath = os.path.join(download_dir, filename)

    # Asynchronously download the file
    async with httpx.AsyncClient() as client:
        download_url = f"{uri}?token={token}"
        response = await client.get(download_url)

        if response.status_code == 200:
            with open(filepath, 'wb') as file:
                file.write(response.content)
            return filepath, True
        else:
            logging.error(f"Failed to download file from {uri}")
            return None, False


@app.route('/callback', methods=['POST'])
async def callback():
    data = await request.get_json()
    logging.info(data)

    # Extract specific fields
    audio_uris = data.get('audio_uri', [])
    image_uris = data.get('image_uri', [])

    # Ensure uris are lists for consistency
    audio_uris = audio_uris if isinstance(audio_uris, list) else [audio_uris]
    image_uris = image_uris if isinstance(image_uris, list) else [image_uris]

    # Extract UUID or use 'anonymous' if not present
    user_document = data.get('user_document', {})
    uuid = user_document.get('uuid', 'anonymous') if isinstance(user_document, dict) else 'anonymous'

    # Initialize response_data with fields not to be included directly
    exclude_keys = ['audio_uri', 'image_uri', 'user_document']
    response_data = {key: value for key, value in data.items() if key not in exclude_keys}

    # Ensure UUID is always included
    response_data['uuid'] = uuid

    # Environment variable for token, reused for both URIs
    token = os.getenv('MITTA_TOKEN')

    # Download audio_uri content if provided
    audio_access_uris = []
    for audio_uri in audio_uris:
        audio_filepath, audio_success = await download_uri_content(audio_uri, token)
        if audio_success:
            audio_filename = os.path.basename(audio_filepath)
            if os.getenv('MITTA_DEV'):
                audio_access_uri = f"http://localhost:5000/download/{audio_filename}"
            else:
                audio_access_uri = f"https://dreams.mitta.ai/download/{audio_filename}"
            audio_access_uris.append(audio_access_uri)

    if audio_access_uris:
        response_data.update({
            "audio_filenames": [os.path.basename(uri) for uri in audio_uris],
            "audio_access_uris": audio_access_uris,
        })

    # Download mitta_uri content if provided, but only the first image
    image_access_uris = []
    if image_uris:
        image_uri = image_uris[0]  # Only process the first URI
        image_filepath, image_success = await download_uri_content(image_uri, token)
        if image_success:
            image_filename = os.path.basename(image_filepath)
            if os.getenv('MITTA_DEV'):
                image_access_uri = f"http://localhost:5000/download/{image_filename}"
            else:
                image_access_uri = f"https://dreams.mitta.ai/download/{image_filename}"
            image_access_uris.append(image_access_uri)

    if image_access_uris:
        response_data.update({
            "image_filename": os.path.basename(image_uris[0]),
            "image_access_uri": image_access_uris[0],
        })

    # Broadcast the data with lists of URIs
    await broadcast(response_data, recipient_id=uuid)

    return jsonify(response_data), 200
    return jsonify(response_data), 200


@app.route('/download/<filename>')
async def download_file(filename):
    download_dir = 'download'  # Same directory you used for saving the files
    return await send_from_directory(download_dir, filename, as_attachment=True)


# build list of sockets - needs to move to storage
connected_websockets = {}


@app.websocket('/ws')
async def ws():
    logging.info("entering wait for data")

    # Wait until we get data
    data = await websocket.receive_json() 
    unique_id = data.get('uuid', str(uuid4()))

    # Store the Websocket
    ws_obj = websocket._get_current_object()
    connected_websockets[unique_id] = ws_obj

    try:
        await ws_obj.send_json({'uuid': unique_id})
        while True:
            data = await websocket.receive()
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
    finally:
        connected_websockets.pop(unique_id, None)




async def broadcast(message, recipient_id=None):
    logging.info(message)
    logging.info(recipient_id)
    if recipient_id:
        # If a recipient ID is provided, only send to that WebSocket
        ws = connected_websockets.get(recipient_id)
        if ws:
            await ws.send_json(message)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)