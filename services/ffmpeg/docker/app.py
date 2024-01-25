import os
import json
import asyncio
import httpx
import shlex
import subprocess

from urllib.parse import urlparse
from werkzeug.utils import secure_filename
from quart import Quart, request, redirect, jsonify

app = Quart(__name__)

@app.route('/')
async def home_redirect():
    return redirect('https://mitta.ai', code=302)


@app.route('/convert', methods=['POST'])
async def convert():
  ffmpeg_token = os.getenv('FFMPEG_TOKEN')
  data = await request.get_json()
  
  # token check
  if not data.get('ffmpeg_token'):
    return jsonify({'result': 'failed: must include token'})
  else:
    if data.get('ffmpeg_token') != ffmpeg_token:
      return jsonify({'result': 'failed: bad token'})
  
  # parameters
  uid = data.get('uid')
  file_url = data.get('mitta_uri')
  callback_url = data.get('callback_url')
  ffmpeg_command = data.get('ffmpeg_command')
  output_file = data.get('output_file')

  # Creating user-specific directory
  user_dir = os.path.join("upload", uid)
  os.makedirs(user_dir, exist_ok=True)

  # Saving received data to data.json in the user's directory
  data_file_path = os.path.join(user_dir, 'data.json')
  with open(data_file_path, 'w') as file:
    json.dump(data, file)

  # Download the file
  local_file_path = await download_file(file_url, user_dir)
  
  print(ffmpeg_command)

  try:
    # Processing with FFmpeg
    asyncio.create_task(run_ffmpeg(ffmpeg_command, user_dir, callback_url, uid))
    return jsonify({'result': 'success'})
  except:
    return jsonify({'result': 'failed: task did not run'})


async def download_file(url, directory):
  local_filename = secure_filename(os.path.basename(urlparse(url).path))
  file_path = os.path.join(directory, local_filename)

  async with httpx.AsyncClient(timeout=30) as client:
    response = await client.get(url, follow_redirects=True)

    response.raise_for_status()  # Ensure the request was successful

    with open(file_path, 'wb') as f:
      async for chunk in response.aiter_bytes(chunk_size=8192):
        f.write(chunk)
  
  return file_path


def is_safe_filename(filename):
  # Check for dangerous characters or patterns
  return ".." not in filename and not filename.startswith('/')


async def run_ffmpeg(ffmpeg_command, user_directory, callback_url, uid):
  # Split the command string into arguments
  args = shlex.split(ffmpeg_command)

  # Check if the first argument is 'ffmpeg' and remove it if present
  if args[0] == 'ffmpeg':
    args = args[1:]

  # Change to the user directory
  original_directory = os.getcwd()
  os.chdir(user_directory)

  # Add 'ffmpeg' at the beginning of the command
  ffmpeg_command = ['ffmpeg'] + args

  # change to logging
  # print(f"Executing FFmpeg command in {user_directory}: {' '.join(ffmpeg_command)}")

  # Execute the FFmpeg command
  process = subprocess.run(ffmpeg_command, capture_output=True, text=True)

  try:
      # Execute the FFmpeg command without changing the global working directory
      process = subprocess.run(args, cwd=user_directory, capture_output=True, text=True)

      # Handle FFmpeg execution result
      if process.returncode != 0:
          # FFmpeg command failed, manually raise an exception
          raise subprocess.CalledProcessError(process.returncode, process.args, output=process.stdout, stderr=process.stderr)

      # Success path: Check for the output file and proceed with upload
      output_file_path = os.path.join(user_directory, output_file)
      if os.path.exists(output_file_path):
          await upload_file(callback_url, output_file_path)
      else:
          # Output file missing
          await notify_failure(callback_url, "FFmpeg succeeded but output file is missing.")

  except subprocess.CalledProcessError as e:
      # Handle FFmpeg failure
      await notify_failure(callback_url, f"FFmpeg command failed: {e.stderr}")



async def notify_failure(callback_url, message):
    async with httpx.AsyncClient() as client:
        data = {'ffmpeg_result': message}
        await client.post(callback_url, data=data)


async def upload_file(callback_url, output_file):
    async with httpx.AsyncClient() as client:
        with open(output_file, 'rb') as f:
            files = {'file': (os.path.basename(output_file), f)}
            data = {'filename': os.path.basename(output_file)}
            response = await client.post(callback_url, files=files, data=data)

        if response.status_code != 200:
            await notify_failure(callback_url, "Failed to upload the file after FFmpeg processing.")
        else:
            # Handle successful upload if needed
            pass

    # Cleanup
    os.remove(output_file)

if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0', port=5000)

