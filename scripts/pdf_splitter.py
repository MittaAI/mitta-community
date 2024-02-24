"""
MIT License

Copyright (c) 2023 Kord Campbell

Instructions for Using the PDF Splitter:

1. Ensure you have Python installed:
   - If you don't have Python installed, download and install it from https://www.python.org/downloads/.

2. Install PyPDF2 library:
   - If you haven't installed the PyPDF2 library, you can install it using pip:
     
     pip install PyPDF2
     
3. Place your PDF file in the same directory as this script or specify the full file path when prompted.

4. Run the script:
   - Open a terminal or command prompt.
   - Navigate to the directory containing this script (use `cd` command).
   - Run the script by entering:
     
     python pdf_splitter.py
     
5. Follow the prompts:
   - Enter the file name of the PDF you want to split (e.g., filename.pdf).
   - Enter a prefix for the output files. Each split PDF will be named using this prefix followed by page range (e.g., prefix_pages_1_to_5.pdf).

6. The script will split the PDF into multiple smaller PDFs based on the maximum size you specified (default is 25MB) or when a single page exceeds that size.

7. The resulting split PDFs will be saved in the same directory as the input PDF.

8. You can now use, share, or manage the split PDF files as needed.

Disclaimer: This script is provided under the MIT License. You are free to use, modify, and distribute it as per the license terms. Use it at your own discretion.
"""


import PyPDF2
import os
from io import BytesIO

def get_pdf_size(writer):
    """Get the size of the PDF currently in the writer."""
    temp_buffer = BytesIO()
    writer.write(temp_buffer)
    size = len(temp_buffer.getvalue())
    return size

def split_pdf(file_path, output_prefix, max_size=25*1024*1024):  # max_size in bytes
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        total_pages = len(reader.pages)
        start_page = 0

        while start_page < total_pages:
            writer = PyPDF2.PdfWriter()
            end_page = start_page
            current_size = 0

            while end_page < total_pages:
                writer.add_page(reader.pages[end_page])
                temp_size = get_pdf_size(writer)

                if temp_size > max_size:
                    if end_page == start_page:
                        # This means a single page is larger than the max size, so we have to include it.
                        end_page += 1
                    break
                else:
                    current_size = temp_size
                    end_page += 1

            output_filename = os.path.join(os.path.dirname(file_path), f"{output_prefix}_pages_{start_page + 1}_to_{end_page}.pdf")
            with open(output_filename, 'wb') as output_file:
                writer.write(output_file)
            
            start_page = end_page

if __name__ == "__main__":
    default_directory = os.path.expanduser("~/Desktop/mitta/")
    file_name = input("Enter the file name (e.g., filename.pdf): ")
    file_path = os.path.join(default_directory, file_name)
    output_prefix = input("Enter the prefix for the output files: ")
    split_pdf(file_path, output_prefix)