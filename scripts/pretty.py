"""
MIT License

Copyright (c) 2023 MittaAI, Kord Campbell

Description:
This Python script takes an input JSON file, pretty-prints its contents, and saves the formatted JSON to an output file.
"""

import json

input_file = input("Enter the input JSON file name: ")

try:
    with open(input_file, 'r') as input_json_file:
        data = json.load(input_json_file)

    output_file = input_file
    with open(output_file, 'w') as output_json_file:
        json.dump(data, output_json_file, indent=4)

    print(f'JSON in {input_file} has been prettified and saved to {output_file}')
except FileNotFoundError:
    print(f'File not found: {input_file}')
except Exception as e:
    print(f'An error occurred: {str(e)}')
