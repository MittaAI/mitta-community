from quart import Quart, websocket, render_template, request, jsonify
import httpx
import json

app = Quart(__name__, static_folder='static')

connected_websockets = set()

@app.route('/')
async def home():
    return await render_template('index.html')

@app.route('/upload', methods=['POST'])
async def upload():
    if 'file' in await request.files:
        file = (await request.files)['file']
        instructions = (await request.form).get('instructions', '')

        # Prepare the JSON payload
        json_payload = {
            "ffmpeg_request": instructions
        }
        # Convert it to JSON string
        json_data = json.dumps(json_payload)

        # Prepare the file to be uploaded to the external handler
        files = {'file': (file.filename, file.read(), file.content_type)}
        
        # Use 'data' or 'json' as the field name, depending on your endpoint's expectation
        data = {'json': json_data}  

        # Define the endpoint and token
        url = "https://convert-gupc3iri5a-uc.a.run.app/pipeline/zeXeO6d0IiQdF/task?token=a__rJ26YLXqC0G80iGmMn3uKqHwORQOvfnS4dd2n"

        # Send the file using httpx
        async with httpx.AsyncClient(timeout=30) as client:  # Timeout of 30 seconds
            response = await client.post(url, files=files, data=data)

        # Check the response from the external handler
        if response.status_code == 200:
            return jsonify({"status": "success", "message": "File uploaded successfully"})
        else:
            return jsonify({"status": "error", "message": "Failed to upload file"})

    return jsonify({"status": "error", "message": "No file received"})

@app.route('/callback', methods=['POST'])
async def callback():
    data = await request.get_json()
    await broadcast(data)
    return jsonify({"status": "success"})

@app.websocket('/ws')
async def ws():
    connected_websockets.add(websocket._get_current_object())
    try:
        while True:
            await websocket.receive()  # Just keeping the connection open
    except:
        pass
    finally:
        connected_websockets.remove(websocket._get_current_object())

async def broadcast(message):
    for ws in connected_websockets:
        await ws.send_json(message)

if __name__ == '__main__':
    app.run()
