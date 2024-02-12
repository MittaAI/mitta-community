import os
import fitz  # PyMuPDF

def split_pdf_into_chunks(pdf_filename, chunk_size=1, offset=1, total_pages=1):
    """
    Splits a PDF into chunks of a specified size.
    
    :param pdf_filename: Path to the source PDF file.
    :param chunk_size: Number of pages in each chunk. Default is 1.
    :param offset: Starting page offset. Default is 1 (first page of the PDF).
    :param total_pages: Number of pages to process starting from the offset. Default is 1.
    """
    # Adjust the offset to zero-based indexing
    offset -= 1
    
    # Check if the PDF file exists
    if not os.path.isfile(pdf_filename):
        print(f"File {pdf_filename} not found.")
        return
    
    # Create the base directory 'splits' if it doesn't exist
    if not os.path.exists('splits'):
        os.mkdir('splits')
    
    # Prepare the directory name based on the PDF filename
    base_name = pdf_filename.rsplit('.', 1)[0]
    dir_name = f'splits/{base_name}_pdf'
    
    # Create a directory for the current PDF if it doesn't exist
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)
    
    # Open the PDF file
    doc = fitz.open(pdf_filename)
    
    # Determine the number of pages to process
    end_page = offset + total_pages
    if end_page > len(doc):
        end_page = len(doc)
    
    # Split the PDF into specified chunks
    for start_page in range(offset, end_page, chunk_size):
        last_page = min(start_page + chunk_size, end_page) - 1
        
        # Define the output filename
        output_filename = f"{dir_name}/{base_name}_pages_{start_page+1}_to_{last_page+1}.pdf"
        
        # Create a new PDF document for the chunk
        doc_chunk = fitz.open()
        for page_num in range(start_page, last_page + 1):
            page = doc.load_page(page_num)
            doc_chunk.insert_pdf(doc, from_page=page_num, to_page=page_num)
        
        # Save the chunk
        doc_chunk.save(output_filename)
        doc_chunk.close()
    
    # Close the original PDF document
    doc.close()
    print(f"PDF split into chunks successfully. Files are saved in {dir_name}")

# Example usage
pdf_filename = "nena.pdf"  # Replace 'input.pdf' with your actual PDF file name
chunk_size = 1  # Define the desired chunk size
offset = 100 # Start from the first page
total_pages = 1  # Number of pages to process

split_pdf_into_chunks(pdf_filename, chunk_size, offset, total_pages)