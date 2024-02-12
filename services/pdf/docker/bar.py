import os
from doctr.io import DocumentFile
from doctr.models import ocr_predictor

def perform_ocr_on_split_pdf(original_filename, starting_page):
    # Construct the directory and file pattern
    base_name = original_filename.rsplit('.', 1)[0]
    dir_name = f'splits/{base_name}_pdf'
    
    # Construct the expected filename based on the starting page
    expected_file_pattern = f"{base_name}_pages_{starting_page}_"
    
    # Find the file that matches the pattern
    for file in os.listdir(dir_name):
        if file.startswith(expected_file_pattern):
            file_path = os.path.join(dir_name, file)
            print(f"Performing OCR on: {file_path}")
            
            # Initialize the OCR model
            model = ocr_predictor(pretrained=True)
            
            # Load the document
            doc = DocumentFile.from_pdf(file_path)
            
            # Perform OCR
            result = model(doc)
            
            # Process the result as needed
            print("OCR completed.")
            # Here, you can add code to handle the `result` object, e.g., print it, analyze it, etc.
            
            return result  # Or handle it as needed
    else:
        print(f"No file found starting with {expected_file_pattern} in {dir_name}")

# Example usage
original_filename = "nena.pdf"  # Replace 'example.pdf' with your actual PDF file name
starting_page = 100  # Adjust the starting page as needed
result = perform_ocr_on_split_pdf(original_filename, starting_page)

import json

# Assuming `result` is the OCR result obtained earlier
json_output = result.export()

# Define the path for the output file in the home directory
home_dir = os.path.expanduser("~")  # Gets the home directory
output_filename = os.path.join(home_dir, "ocr_nena_output.json")

# Write the JSON output to the file
with open(output_filename, 'w') as f:
    json.dump(json_output, f, indent=4)