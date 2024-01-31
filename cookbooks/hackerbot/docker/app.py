import os
import json
import logging
import datetime

from uuid import uuid4

from quart import Quart, websocket, render_template, request, redirect, jsonify
from quart_cors import cors
import httpx

app = Quart(__name__, static_folder='static')
app = cors(app, allow_origin=["https://72f3-173-174-35-128.ngrok-free.app", "http://localhost:5000", "https://ai.mitta.ai"])

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@app.route('/news/static/<path:filename>')
async def custom_static(filename):
    static_folder_path = app.static_folder
    file_path = os.path.join(static_folder_path, filename)
    return await send_from_directory(static_folder_path, filename)


@app.route('/', methods=['GET', 'POST'])
async def home():
    return redirect("https://mitta.ai")


@app.route('/news', methods=['GET', 'POST'])
async def crawl():
    # Initialize the default instructions
    instructions = [
        "Most popular current article",
        "Latest AI advancements",
        "Startup funding rounds",
        "Cybersecurity trends",
        "Silicon Valley news",
        "Emerging technologies 2024",
        "Tech industry layoffs",
        "Blockchain and cryptocurrency updates",
        "New software releases",
        "Tech regulation and policy changes",
        "Remote work tools and trends",
        "Data privacy and GDPR",
        "Quantum computing developments",
        "Electric vehicle innovations",
        "Space technology and SpaceX",
        "Big data and analytics",
        "Augmented reality (AR) and virtual reality (VR) news",
        "Renewable energy tech",
        "Tech IPOs and stock market",
        "5G and wireless technology",
        "Robotics and automation",
        "Elon Musk's tiny penis"
    ]

    if request.method == 'POST':
        form_data = await request.form
        posted_instruction = form_data.get('instructions')

        # If a new instruction is posted, add it to the top of the list
        if posted_instruction and posted_instruction not in instructions:
            instructions.insert(0, posted_instruction)

    # Pass the (possibly updated) instructions list to the template
    current_date = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00") # card publish
    return await render_template('index.html', instructions=instructions, current_date=current_date)


@app.route('/news/upload', methods=['POST'])
async def upload():
    form_data = await request.form
    instructions = form_data.get('instructions', 'Get news about AI')
    uuid = form_data.get('uuid')
    
    # Log the received instructions for debugging
    logging.info(f"Received instructions: {instructions}")
    logging.info(f"UUID: {uuid}")


    # Prepare the JSON payload and encode it into bytes
    # httpx recent versions may not like non-encoded payloads
    json_data = {
        "user_document": {"uuid": uuid},
        "news_request": instructions
    }

    with open(f'json_data_{uuid}.json', 'w') as json_file:
        json.dump(json_data, json_file)

    # Prepare the file to be uploaded to the external handler
    files = {
        'json_data': ('json_data.json', open(f'json_data_{uuid}.json', 'rb'), 'application/json')
    }

    # Define the endpoint and token
    pipeline = os.getenv('NEWS_PIPELINE')
    mitta_token = os.getenv('MITTA_TOKEN')
    url = f"https://mitta.ai/pipeline/{pipeline}/task?token={mitta_token}"
    logging.info(url)
    
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


def extract_value(data, key):
    print(data)
    value = data.get(key, [])
    
    if isinstance(value, list):
        if value and isinstance(value[0], list):
            if value[0]:
                return value[0][0]
            return None
        elif value:
            return value[0]
        return None
    return value


@app.route('/news/callback', methods=['POST'])
async def callback():
    data = await request.get_json()
    logging.info("in callback")
    logging.info(data)

    # uuid and message
    message = data.get('message', "Received data.")
    summary = extract_value(data, 'summary')
    comments = extract_value(data, 'comments')
    hn_url = extract_value(data, 'hn_url')
    story_url = extract_value(data, 'story_url')
    title = extract_value(data, 'title')
    access_uri = extract_value(data, 'access_uri')
    
    # covert uri, if available
    convert_uris = data.get('convert_uri', [])
    filenames = data.get('filename', [])

    # don't show message if we have data
    if summary or comments or hn_url or story_url:
        message = None

    # get uuid
    user_document = data.get('user_document', {})
    if isinstance(user_document, dict):
        uuid = user_document.get('uuid', 'anonymous')
    else:
        uuid = 'anonymous'

    logging.info(uuid)

    # Check if convert_uri is provided and download the file
    filename = ''
    access_uri = ''
    if convert_uris:
        # Ensure the download directory exists
        download_dir = 'download'
        os.makedirs(download_dir, exist_ok=True)

        # Download the first file in the list
        convert_uri = convert_uris[0]
        logging.info(convert_uri)
        logging.info(filenames)
        if filenames:
            # use the first file only
            filename = filenames[0]
            filepath = os.path.join(download_dir, filename)

            async with httpx.AsyncClient() as client:
                mitta_token = os.getenv('MITTA_TOKEN')
                mitta_url = f"{convert_uri}?token={mitta_token}"
                response = await client.get(mitta_url)

                if response.status_code == 200:
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                else:
                    logging.error(f"Failed to download file from {convert_uri}")
                    return jsonify({"status": "failed"}), 404

            access_uri = f"https://ai.mitta.ai/news/download/{filename}"
            message = None
            logging.info(access_uri)

    await broadcast(
        {
            "status": "success",
            "message": message,
            "title": title,
            "comments": comments,
            "hn_url": hn_url,
            "story_url": story_url,
            "summary": summary,
            "filename": filename,
            "access_uri": access_uri,
            "uuid": uuid
        },
        recipient_id=uuid
    )

    return jsonify({"status": "success"}), 200


connected_websockets = {}

from quart import send_from_directory

@app.route('/news/download/<filename>')
async def download_file(filename):
    download_dir = 'download'  # Same directory you used for saving the files
    return await send_from_directory(download_dir, filename, as_attachment=True)


@app.websocket('/ws')
async def ws():
    unique_id = str(uuid4())  # Generate a unique ID for the session
    ws_obj = websocket._get_current_object()
    connected_websockets[unique_id] = ws_obj  # Store the WebSocket object with the unique ID

    try:
        await ws_obj.send_json({'uuid': unique_id})
        while True:
            data = await websocket.receive()
    except:
        pass
    finally:
        connected_websockets.pop(unique_id, None)  # Remove the WebSocket from the dictionary on disconnect


async def broadcast(message, recipient_id=None):
    logging.info(message)
    if recipient_id:
        # If a recipient ID is provided, only send to that WebSocket
        ws = connected_websockets.get(recipient_id)
        if ws:
            await ws.send_json(message)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
