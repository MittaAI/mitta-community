# powered by easyocr

import easyocr
from quart import Quart, request, jsonify
import random
import re
import logging
import httpx
from io import BytesIO

logging.basicConfig(filename='ocr.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

app = Quart(__name__)

@app.route('/read', methods=['POST'])
async def read():
    if request.method == 'POST':
        data = await request.get_json()  # Assuming the data is sent as JSON in the request body
        mitta_uris = data.get('mitta_uri')
        page_nums = data.get('page_nums')

        if not mitta_uris or not page_nums:
            return jsonify({"status": "failed", "error": "Both `mitta_uri` and `page_nums` are required."}), 400

        if not isinstance(mitta_uris, list) or not isinstance(page_nums, list):
            return jsonify({"status": "failed", "error": "`mitta_uri` and `page_nums` must be lists."}), 400

        if len(mitta_uris) != len(page_nums):
            return jsonify({"status": "failed", "error": "The number of `mitta_uri` and `page_nums` must be the same."}), 400

        all_recognized_text = []
        all_coordinates = []
        all_page_nums = []

        for mitta_uri, page_num in zip(mitta_uris, page_nums):
            log_line = f"Received POST request to /read with: '{mitta_uri}', page number: {page_num}. Responding with texts."
            app.logger.info(log_line)

            # Download the image from the provided URL using HTTPX
            async with httpx.AsyncClient() as client:
                response = await client.get(mitta_uri)
                image_bytes = response.read()

            # Initialize the EasyOCR reader
            reader = easyocr.Reader(['en'], gpu=True, verbose=True)

            # Perform text recognition
            result = reader.readtext(image_bytes, paragraph=True, height_ths=5, width_ths=0.8, detail=1)
            app.logger.info(result)

            # Sort the recognized text based on the vertical position (top to bottom)
            sorted_result = sorted(result, key=lambda x: x[0][0][1])

            # Extract the recognized text and bounding box coordinates
            recognized_text = [item[1] for item in sorted_result]
            coordinates = [item[0] for item in sorted_result]

            all_recognized_text.append(recognized_text)
            all_coordinates.append(coordinates)
            all_page_nums.append(page_num)

        return jsonify({"texts": all_recognized_text, "coords": all_coordinates, "page_nums": all_page_nums}), 200

if __name__ == '__main__':
    app.run(debug=True)