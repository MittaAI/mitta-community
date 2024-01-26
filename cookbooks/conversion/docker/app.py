import os
import json

from uuid import uuid4

from quart import Quart, websocket, render_template, request, jsonify
from quart_cors import cors
import httpx

app = Quart(__name__, static_folder='static')
app = cors(app, allow_origin=["http://localhost:8080", "https://ai.mitta.ai"])

@app.route('/', methods=['GET', 'POST'])
@app.route('/convert', methods=['GET', 'POST'])
async def home():
    instructions = "Convert to a 640 wide black and white gif"  # Default instructions or retrieve from request
    if request.method == 'POST':
        form_data = await request.form
        instructions = form_data.get('instructions', instructions)

    return await render_template('index.html', instructions=instructions)


@app.route('/upload', methods=['POST'])
async def upload():
    mitta_token = os.getenv('MITTA_TOKEN')
    if 'file' in await request.files:
        file = (await request.files)['file']
        instructions = (await request.form).get('instructions', 'Convert to a 640 wide black and white gif')
        uuid = (await request.form).get('uuid')
        
        # Prepare the JSON payload
        json_payload = {
            "ffmpeg_request": instructions,
            "uuid": uuid
        }
        # Convert it to JSON string
        json_data = json.dumps(json_payload)

        # Prepare the file to be uploaded to the external handler
        files = {'file': (file.filename, file.read(), file.content_type)}
        
        # Use 'data' or 'json' as the field name, depending on your endpoint's expectation
        data = {'json': json_data}  

        # Define the endpoint and token
        pipeline = os.getenv('PIPELINE')
        url = f"https://mitta.ai/pipeline/{pipeline}/task?token={mitta_token}"

        # Send the file using httpx
        async with httpx.AsyncClient(timeout=30) as client:  # Timeout of 30 seconds
            response = await client.post(url, files=files, data=data)

        # Check the response from the external handler
        if response.status_code == 200:
            await broadcast({"status": "success", "message": "File uploaded successfully!"})
            return jsonify({"status": "success", "message": "File uploaded successfully"})
        else:
            await broadcast({"status": "success", "message": "File upload failed, sorry."})
            return jsonify({"status": "error", "message": "Failed to upload file"})

    return jsonify({"status": "error", "message": "No file received"})


@app.route('/callback', methods=['POST'])
async def callback():
    data = await request.get_json()
    await broadcast({"status": "success", "message": "Showing the image...", "convert_uri": data.convert_uri})
    return jsonify({"status": "success"})


connected_websockets = {}

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
    if recipient_id:
        # If a recipient ID is provided, only send to that WebSocket
        ws = connected_websockets.get(recipient_id)
        if ws:
            await ws.send_json(message)
    else:
        # If no recipient ID is provided, broadcast to all connected WebSockets
        for ws in connected_websockets.values():
            await ws.send_json(message)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
