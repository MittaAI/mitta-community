# powered by easyocr

import easyocr
from quart import Quart, request, jsonify
import random
import re
import logging
import httpx
from httpx import TimeoutException
from io import BytesIO
import torch
import asyncio

logging.basicConfig(filename='ocr.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

app = Quart(__name__)

@app.route('/read', methods=['POST'])
async def read():
    if request.method == 'POST':
        data = await request.get_json()  # Assuming the data is sent as JSON in the request body
        mitta_uris = data.get('mitta_uri')
        page_nums = data.get('page_nums')
        callback_url = data.get('callback_url')

        if not mitta_uris or not page_nums:
            return jsonify({"status": "failed", "error": "Both `mitta_uri` and `page_nums` are required."}), 400

        if not isinstance(mitta_uris, list) or not isinstance(page_nums, list):
            return jsonify({"status": "failed", "error": "`mitta_uri` and `page_nums` must be lists."}), 400

        if len(mitta_uris) != len(page_nums):
            return jsonify({"status": "failed", "error": "The number of `mitta_uri` and `page_nums` must be the same."}), 400

        if callback_url:
            asyncio.create_task(process_ocr(mitta_uris, page_nums, callback_url))
            return jsonify({"status": "success"}), 200
        else:
            all_recognized_text, all_coordinates, all_page_nums = await process_ocr(mitta_uris, page_nums)
            return jsonify({"texts": all_recognized_text, "coords": all_coordinates, "page_nums": all_page_nums}), 200

async def process_ocr(mitta_uris, page_nums, callback_url=None):
    all_recognized_text = []
    all_coordinates = []
    all_page_nums = []

    for mitta_uri, page_num in zip(mitta_uris, page_nums):
        log_line = f"Received POST request to /read with: '{mitta_uri}', page number: {page_num}. Responding with texts."
        app.logger.info(log_line)

        try:
            # Download the image from the provided URL using HTTPX with a timeout of 60 seconds
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(mitta_uri)
                image_bytes = response.read()
        except TimeoutException:
            app.logger.error(f"Timeout occurred while downloading image from '{mitta_uri}'")
            if callback_url:
                await notify_failure(callback_url, f"Timeout occurred while downloading image from '{mitta_uri}'")
            continue

        # Initialize the EasyOCR reader
        reader = easyocr.Reader(['en'], gpu=True, verbose=True)

        try:
            # Perform text recognition
            result = reader.readtext(image_bytes, paragraph=True, height_ths=5, width_ths=0.8, detail=1)
        finally:
            # Delete the reader object
            del reader
            # Release the GPU memory
            torch.cuda.empty_cache()

        # Sort the recognized text based on the vertical position (top to bottom)
        sorted_result = sorted(result, key=lambda x: x[0][0][1])

        # Extract the recognized text and bounding box coordinates
        recognized_text = [item[1] for item in sorted_result]
        coordinates = [item[0] for item in sorted_result]

        all_recognized_text.append(recognized_text)
        all_coordinates.append(coordinates)
        all_page_nums.append(page_num)

    if callback_url:
        await send_callback(callback_url, all_recognized_text, all_coordinates, all_page_nums)
    else:
        return all_recognized_text, all_coordinates, all_page_nums

async def send_callback(callback_url, all_recognized_text, all_coordinates, all_page_nums):
    data = {
        "texts": all_recognized_text,
        "coords": all_coordinates,
        "page_nums": all_page_nums
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(callback_url, json=data)
            response.raise_for_status()
            app.logger.info(f"Callback sent successfully to {callback_url}")
    except httpx.HTTPStatusError as e:
        app.logger.error(f"HTTP error occurred while sending callback: {e}")
    except Exception as e:
        app.logger.error(f"Unexpected error occurred while sending callback: {e}")

async def notify_failure(callback_url, error_message):
    data = {
        "status": "failed",
        "error": error_message
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(callback_url, json=data)
            response.raise_for_status()
            app.logger.info(f"Failure notification sent successfully to {callback_url}")
    except httpx.HTTPStatusError as e:
        app.logger.error(f"HTTP error occurred while sending failure notification: {e}")
    except Exception as e:
        app.logger.error(f"Unexpected error occurred while sending failure notification: {e}")

if __name__ == '__main__':
    app.run(debug=True)