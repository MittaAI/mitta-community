# powered by easyocr

import easyocr
from quart import Quart, request, jsonify
import random
import re
import logging
from PIL import Image
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
        page_numbers = data.get('page_numbers')

        if not mitta_uris or not page_numbers:
            return jsonify({"status": "failed", "error": "Both `mitta_uri` and `page_numbers` are required."}), 400

        if not isinstance(mitta_uris, list) or not isinstance(page_numbers, list):
            return jsonify({"status": "failed", "error": "`mitta_uri` and `page_numbers` must be lists."}), 400

        if len(mitta_uris) != len(page_numbers):
            return jsonify({"status": "failed", "error": "The number of `mitta_uri` and `page_numbers` must be the same."}), 400

        all_recognized_text = []
        all_coordinates = []
        all_page_numbers = []

        for mitta_uri, page_number in zip(mitta_uris, page_numbers):
            log_line = f"Received POST request to /read with: '{mitta_uri}', page number: {page_number}. Responding with texts."
            app.logger.info(log_line)

            # Download the image from the provided URL using HTTPX
            async with httpx.AsyncClient() as client:
                response = await client.get(mitta_uri)
                image_bytes = response.read()

            # Create a PIL Image object from the downloaded image bytes
            image = Image.open(BytesIO(image_bytes))

            # Initialize the EasyOCR reader
            reader = easyocr.Reader(['en'], gpu=True, verbose=True)

            # Perform text recognition
            result = reader.readtext(image, paragraph=True, height_ths=5, width_ths=0.8, detail=1)
            app.logger.info(result)

            # Sort the recognized text based on the vertical position (top to bottom)
            sorted_result = sorted(result, key=lambda x: x[0][0][1])

            # Extract the recognized text and bounding box coordinates
            recognized_text = [item[1] for item in sorted_result]
            coordinates = [item[0] for item in sorted_result]

            all_recognized_text.append(recognized_text)
            all_coordinates.append(coordinates)
            all_page_numbers.append(page_number)

        return jsonify({"texts": all_recognized_text, "coords": all_coordinates, "page_numbers": all_page_numbers}), 200

if __name__ == '__main__':
    app.run(debug=True)