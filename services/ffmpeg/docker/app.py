# ffmpeg service container
# All rights reserved. Copyright 2024, MittaAI
# MIT License

import os
import json
import asyncio
import httpx
import shlex
import subprocess
import logging

from urllib.parse import urlparse
from werkzeug.utils import secure_filename
from quart import Quart, request, redirect, jsonify

app = Quart(__name__)

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'upload')


def create_and_check_directory(directory_path):
    try:
        # Attempt to create the directory (and any necessary parent directories)
        os.makedirs(directory_path, exist_ok=True)
        logging.info(f"Directory '{directory_path}' ensured to exist.")
        
        # Check if the directory exists to verify it was created
        if os.path.isdir(directory_path):
            logging.info(f"Confirmed: The directory '{directory_path}' exists.")
        else:
            logging.error(f"Error: The directory '{directory_path}' was not found after creation attempt.")
    except Exception as e:
        # If an error occurred during the creation, log the error
        logging.error(f"An error occurred while creating the directory: {e}")


@app.route('/')
async def home_redirect():
    return redirect('https://mitta.ai', code=302)


@app.route('/convert', methods=['POST'])
async def convert():
  logging.info(f"Current working directory: {os.getcwd()}")
  logging.info(f"Base directory: {BASE_DIR}")
  logging.info(f"Uploads directory: {UPLOAD_DIR}")

  ffmpeg_token = os.getenv('FFMPEG_TOKEN')
  data = await request.get_json()
  
  # token check
  if not data.get('ffmpeg_token'):
    return jsonify({'result': 'failed: must include token'})
  else:
    if data.get('ffmpeg_token') != ffmpeg_token:
      return jsonify({'result': 'failed: bad token'})
  
  # parameters
  user_id = data.get('user_id')
  user_document = data.get('user_document', {})
  file_url = data.get('mitta_uri')
  callback_url = data.get('callback_url')
  ffmpeg_command = data.get('ffmpeg_command')
  input_file = data.get('input_file')
  output_file = data.get('output_file')

  # lightly check command for problems
  if ".." in ffmpeg_command or ".." in input_file:
    return jsonify({'result': 'failed: command stopped at security checkpoint. No callback will occur.'})

  # Creating user-specific directory\
  user_dir = os.path.join(UPLOAD_DIR, user_id)
  logging.info(f"User's directory: {user_dir}")
  create_and_check_directory(user_dir)

  # Download the file
  local_file_path = await download_file(file_url, user_dir)
  logging.info(f"local file path: {local_file_path}")

  # log the request
  logging.info(f"User request resulted in the command: {ffmpeg_command}")
  
  try:
    # Processing with FFmpeg
    asyncio.create_task(run_ffmpeg(ffmpeg_command, user_dir, callback_url, input_file, output_file, user_id, user_document))
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


async def run_ffmpeg(ffmpeg_command, user_directory, callback_url, input_file, output_file, user_id, user_document):
  logging.info(f"Current working directory: {os.getcwd()}")
  logging.info(f"Uploads directory: {UPLOAD_DIR}")
  logging.info(f"User directory: {user_directory}")
  logging.info(f"Callback: {callback_url}")

  # Split the command string into arguments
  args = shlex.split(ffmpeg_command)

  # Check if the first argument is 'ffmpeg' and remove it if present
  # first step of security handling
  if args[0] == 'ffmpeg':
    args = args[1:]

  # check both the input file and output file for ..
  # second step of security handling
  if any(s in output_file for s in ["/", ".."]) or any(s in input_file for s in ["/", ".."]):
      await notify_failure(callback_url, 'failed: command stopped at security checkpoint')

  # Update paths for the input and output files within the command arguments
  if input_file in args:
      input_index = args.index(input_file)  # Find the index of the input file
      args[input_index] = os.path.join(user_directory, input_file)  # Replace with full path

  if output_file in args:
      output_index = args.index(output_file)  # Find the index of the output file
      args[output_index] = os.path.join(user_directory, output_file)  # Replace with full path

  # Add 'ffmpeg' back at the beginning of the command
  args = ['ffmpeg'] + args

  logging.info(f"Final command list: {args}")
  logging.info(f"ffmpeg_command is: {ffmpeg_command}")

  # change to logging
  logging.info(f"Executing FFmpeg command in {user_directory}: {''.join(ffmpeg_command)}")

  try:
      # Execute the FFmpeg command without changing the global working directory
      # process = subprocess.run(' '.join(ffmpeg_command), cwd=user_directory, shell=True, capture_output=True, text=True)

      process = subprocess.run(args, cwd=user_directory, capture_output=True, text=True)
      logging.info("subprocess ran")
      # Handle FFmpeg execution result
      if process.returncode != 0:
          # FFmpeg command failed, manually raise an exception
          raise subprocess.CalledProcessError(process.returncode, process.args, output=process.stdout, stderr=process.stderr)

      # Success path: Check for the output file and proceed with upload
      output_file_path = os.path.join(user_directory, output_file)
      if os.path.exists(output_file_path):
          logging.info("uploading file")
          await upload_file(callback_url, output_file_path, user_document)
      else:
          logging.info("file missing")
          # Output file missing
          await notify_failure(callback_url, "FFmpeg succeeded but output file is missing.")

  except subprocess.CalledProcessError as e:
      # Handle FFmpeg failure
      await notify_failure(callback_url, f"FFmpeg command failed: {e.stderr}")

  except Exception as e:
      logging.info(e)
      # Catch-all for any other exceptions during the process
      await notify_failure(callback_url, f"An unexpected error occurred: {e}")


async def notify_failure(callback_url, message):
    logging.info(f"Notifying failure: {message}")
    async with httpx.AsyncClient() as client:
        json_data = {'ffmpeg_result': message, 'filename': "None"}
        response = await client.post(callback_url, json=json_data)
        logging.info(f"Notification response: {response.text}")


async def upload_file(callback_url, output_file, user_document):
    logging.info(f"output_file: {output_file}")
    async with httpx.AsyncClient() as client:
        with open(output_file, 'rb') as f:
            files = {'file': (output_file, f)}
            json_data = {
              'filename': output_file,
              'user_document': user_document
            }
            
            response = await client.post(callback_url, files=files, json=json_data)

        if response.status_code != 200:
            await notify_failure(callback_url, "Failed to upload the file after FFmpeg processing.")
        else:
            # Handle successful upload if needed
            pass

    # Cleanup
    os.remove(output_file)

if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0', port=5000)

