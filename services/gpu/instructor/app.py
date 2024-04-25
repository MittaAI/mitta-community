from InstructorEmbedding import INSTRUCTOR
from flask import Flask, request, jsonify
import logging
import requests
import uuid
import os

logging.basicConfig(filename='instructor.log', level=logging.INFO)

app = Flask(__name__)

# Load embedding models
xl = INSTRUCTOR('hkunlp/instructor-xl')
large = INSTRUCTOR('hkunlp/instructor-large')

@app.route('/embed', methods=['POST'])
def embed():

    # set the flag to indicate we're running to the shutdown script
    process_id = str(uuid.uuid4())[:8]  # Generate a unique process ID
    
    current_path = os.path.dirname(os.path.abspath(__file__))
    process_file = f"{current_path}/PROCESS-{process_id}"

    with open(process_file, "w") as file:
        file.write("Processing")

    if request.method == 'POST':
        data = request.json  # Assuming the data is sent as JSON in the request body
        payload_data = data.get('data')
        model = data.get('model')
        callback_url = data.get('callback_url')
        output_fields = data.get('output_fields')
        batch_size = data.get('batch_size', 30)  # Default batch size is 30

        if not payload_data or not model or not callback_url or not output_fields:
            return jsonify({"error": "Missing required parameters"}), 400

        for field_name, input_data in payload_data.items():
            for i in range(0, len(input_data), batch_size):
                batch = input_data[i:i + batch_size]
                embeddings = []

                if model == "instructor-xl":
                    batch_embeddings = xl.encode(batch).tolist()
                else:
                    batch_embeddings = large.encode(batch).tolist()
                embeddings.extend(batch_embeddings)

                # Prepare the response data for the current batch
                response_data = {
                    "embeddings": {field_name: embeddings},
                    "output_fields": output_fields,
                    "batch_index": i // batch_size,  # Include the batch index
                    "total_batches": (len(input_data) + batch_size - 1) // batch_size  # Include the total number of batches
                }

                log_line = f"Processed batch {i // batch_size + 1} for field '{field_name}'. Sending callback."
                app.logger.info(log_line)

                try:
                    # Send the response data back to the callback URL for the current batch
                    response = requests.post(callback_url, json=response_data, timeout=60)
                    response.raise_for_status()
                except requests.RequestException as e:
                    app.logger.error(f"Failed to send callback for batch {i // batch_size + 1}: {str(e)}")
                    # You can choose to handle this error differently, e.g., retry or continue to the next batch

        os.remove(process_file)  # Delete the PROCESS file for the thread
        
        return jsonify({"status": "success"}), 202

if __name__ == '__main__':
    app.run(debug=True)
