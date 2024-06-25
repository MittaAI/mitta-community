from flask import Flask, request, jsonify, redirect
import nltk
import random
from typing import List, Union

app = Flask(__name__)

# Download necessary NLTK data
nltk.download('punkt')

def load_tokenizer(tokenizer_path):
    return nltk.data.load(tokenizer_path)

def preprocess_text(text):
    return text.replace("\n", " ").replace("\r", " ").replace("\t", " ") \
               .replace("\\", " ").strip()

def create_chunks(tokenized_text, length, min_length):
    chunks = []
    current_chunk = []

    for token in tokenized_text:
        if len(' '.join(current_chunk) + ' ' + token) <= length:
            current_chunk.append(token)
        else:
            chunks.append(current_chunk)
            current_chunk = [token]

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def create_overlapping_chunks(chunks, overlap):
    overlapped_chunks = []

    for i in range(len(chunks)):
        if i == 0:
            overlapped_chunks.append(chunks[i])
        else:
            overlapped_chunk = chunks[i-1][-overlap:] + chunks[i]
            overlapped_chunks.append(overlapped_chunk)

    return overlapped_chunks

def chunk_with_page_filename(texts: Union[List[str], List[List[str]]], 
                             filenames: Union[str, List[str]], 
                             length: int = 512, 
                             min_length: int = 100, 
                             start_page: int = 1, 
                             overlap: int = 0, 
                             tokenizer_path: str = 'tokenizers/punkt/english.pickle', 
                             flatten_output: bool = False):
    if not isinstance(texts, list) or not isinstance(filenames, list):
        raise TypeError("The values for 'texts' and 'filename' need to be lists.")

    if not all(isinstance(item, str) or isinstance(item, list) for item in texts):
        raise TypeError("The elements in 'texts' should be either strings or lists of strings.")

    # If texts is a single list, convert it to a list of lists
    if isinstance(texts[0], str):
        texts = [texts]

    # If filenames is a single string, convert it to a list with one element
    if isinstance(filenames, str):
        filenames = [filenames]

    if len(filenames) != len(texts):
        raise ValueError("When 'texts' is a list of lists, the outer list length should match the length of 'filenames'.")

    tokenizer = load_tokenizer(tokenizer_path)
    all_texts_chunks = []

    for text_list, filename in zip(texts, filenames):
        texts_chunks = []
        carry_forward_chunk = []
        for text in text_list:
            preprocessed_text = preprocess_text(text)
            tokenized_text = tokenizer.tokenize(preprocessed_text)
            chunks = create_chunks(tokenized_text, length, min_length)
            
            if carry_forward_chunk:
                chunks[0] = carry_forward_chunk + chunks[0]
                carry_forward_chunk = []
            for chunk in chunks:
                if len(' '.join(chunk)) < min_length:
                    carry_forward_chunk.extend(chunk)
                else:
                    texts_chunks.append(chunk)
            if carry_forward_chunk:
                texts_chunks.append(carry_forward_chunk)
        if overlap:
            texts_chunks = create_overlapping_chunks(texts_chunks, overlap)
        
        all_texts_chunks.append(texts_chunks)

    segmented_texts = []
    page_numbers = []
    chunk_numbers = []
    filenames_out = []

    current_page_number = start_page

    for texts_chunks, filename in zip(all_texts_chunks, filenames):
        page_chunks = []
        current_chunk_number = 1

        for chunk in texts_chunks:
            page_chunks.append(' '.join(chunk))
            page_numbers.append(current_page_number)
            chunk_numbers.append(current_chunk_number)
            filenames_out.append(filename)
            current_chunk_number += 1

        segmented_texts.append(page_chunks)
        current_page_number += 1

    if flatten_output:
        segmented_texts = [chunk for page_chunks in segmented_texts for chunk in page_chunks]
        page_numbers = [page_num for page_nums in page_numbers for page_num in [page_nums]]
        chunk_numbers = [chunk_num for chunk_nums in chunk_numbers for chunk_num in [chunk_nums]]
        filenames_out = [filename for filenames in filenames_out for filename in [filenames]]
    else:
        expanded_filenames = [[filename] * len(chunks) for filename, chunks in zip(filenames, all_texts_chunks)]
        expanded_page_numbers = [[page_num] * len(chunks) for page_num, chunks in zip(range(start_page, start_page + len(all_texts_chunks)), all_texts_chunks)]
        expanded_chunk_numbers = [list(range(1, len(chunks) + 1)) for chunks in all_texts_chunks]
        
        segmented_texts = expanded_filenames
        page_numbers = expanded_page_numbers
        chunk_numbers = expanded_chunk_numbers
        filenames_out = expanded_filenames

    return {
        "chunks": segmented_texts,
        "page_nums": page_numbers,
        "chunk_nums": chunk_numbers,
        "filenames": filenames_out
    }

# Add redirect for root path
@app.route('/')
def root_redirect():
    return redirect('https://mitta.ai', code=302)

@app.route('/chunk', methods=['POST'])
def chunk():
    data = request.json
    texts = data.get('texts')
    filenames = data.get('filenames')
    length = data.get('length', 512)
    min_length = data.get('min_length', 100)
    start_page = data.get('start_page', 1)
    overlap = data.get('overlap', 0)
    flatten_output = data.get('flatten_output', False)

    try:
        result = chunk_with_page_filename(
            texts=texts,
            filenames=filenames,
            length=length,
            min_length=min_length,
            start_page=start_page,
            overlap=overlap,
            flatten_output=flatten_output
        )
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)