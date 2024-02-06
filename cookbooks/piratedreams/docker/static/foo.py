from urllib.parse import urlparse, unquote

def extract_filename_from_url(url):
    print(f"Original URL: {url}")  # Debug print
    
    url = url.strip()  # Strip whitespace and newlines
    parsed_url = urlparse(url)
    print(f"Parsed URL: {parsed_url}")  # Debug print
    
    path = parsed_url.path
    decoded_path = unquote(path)
    print(f"Decoded Path: {decoded_path}")  # Debug print
    
    filename = decoded_path.split('/')[-1]
    
    return filename

# Example usage with a print statement to debug
url_example = "https://example.com/path/to/image.png\n"  # Example with a newline character
filename = extract_filename_from_url(url_example.strip())
print(f"Extracted Filename: '{filename}'")  # Note the quotes to visualize if any invisible character is part of the output

