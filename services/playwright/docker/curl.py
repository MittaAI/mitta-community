import json
import os
import subprocess

# Define the path to the configuration file
config_file_path = 'config.json'

# Check if the configuration file exists
if not os.path.exists(config_file_path):
    # If the file doesn't exist, prompt the user for the OpenAI token and the Mitta callback token
    openai_token = input("Enter your OpenAI token: ")
    mitta_callback_token = input("Enter your Mitta callback token: ")
    
    # Prepare the data to be written to the configuration file
    config_data = {
        "grub_token": "f00bar",
        "username": "hilarious-quetzal-of-excitement",
        "query": "crawl https://www.amazon.com/OVERTURE-Filament-Consumables-Dimensional-Accuracy/dp/B07PDV9RC8",
        "callback_url": f"https://kordless.ngrok.io/hilarious-quetzal-of-excitement/callback?token={mitta_callback_token}",
        "openai_token": openai_token
    }
    
    # Write the configuration data to the file
    with open(config_file_path, 'w') as config_file:
        json.dump(config_data, config_file, indent=4)
else:
    # If the file exists, read the current configuration
    with open(config_file_path, 'r') as config_file:
        config_data = json.load(config_file)

# Use the configuration data to set up the curl command
curl_command = [
    'curl', '-X', 'POST', 'http://localhost:5000/grub2',
    '-H', 'Content-Type: application/json',
    '-d', json.dumps(config_data)
]

# Execute the curl command
subprocess.run(curl_command)
