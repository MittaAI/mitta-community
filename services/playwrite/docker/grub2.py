import asyncio
import json
import re
import sys
from playwright.async_api import async_playwright
from tenacity import retry, wait_random_exponential, stop_after_attempt
import openai
import os

# Import helper functions and decorators
from function_wrapper import function_info_decorator, tools, callable_registry

# storage
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'screenshots')

# ensure directory exists
def create_and_check_directory(directory_path):
    try:
        # Attempt to create the directory (and any necessary parent directories)
        os.makedirs(directory_path, exist_ok=True)
        logging.info(f"Directory '{directory_path}' ensured to exist.")
        
        # Check if the directory exists to verify it was created
        if os.path.isdir(directory_path):
            logging.info(f"Confirmed: The directory '{directory_path}' exists.")
        else:
            logging.error(f"Error: The directory '{directory_path}' was not found after creation attempt.")
    except Exception as e:
        # If an error occurred during the creation, log the error
        logging.error(f"An error occurred while creating the directory: {e}")


def extract_urls(query):
    """
    Extract URLs from the given query string.
    """
    url_pattern = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')
    return url_pattern.findall(query)


async def execute_function_by_name(function_name, **kwargs):
    """
    Execute a function by its name if it exists in the callable_registry.
    """
    if function_name in callable_registry:
        function_to_call = callable_registry[function_name]
        return await function_to_call(**kwargs) if asyncio.iscoroutinefunction(function_to_call) else function_to_call(**kwargs)
    else:
        raise ValueError(f"Function {function_name} not found in registry")

# dynamic functions called by AI
@function_info_decorator
async def thumbnail(url: str, filename: str = f"example.png") -> str:
    """
    Takes a screenshot of the specified URL and saves it to the given filename asynchronously.

    :param url: The website URL to capture.
    :type url: str
    :param filename: The filename used to save the screenshot, defaults to "example.png".
    :type filename: str
    :return: The filename where the screenshot was saved.
    :rtype: str
    """
    async with async_playwright() as p:
        browser = await p.webkit.launch()
        page = await browser.new_page()
        await page.goto(url)
        await page.screenshot(path=path)
        await browser.close()
    return path


@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
async def chat_completion_request_async(messages, tools=None, tool_choice=None, model="gpt-3.5-turbo-1106"):
    """
    Make an asynchronous request to OpenAI's chat completion API.
    """
    client = openai.AsyncOpenAI(api_key=openai.api_key)
    try:
        return await client.chat.completions.create(model=model, messages=messages, tools=tools, tool_choice=tool_choice)
    except Exception as e:
        print("Unable to generate ChatCompletion response:", e)
        return None


async def ai(username="anonymous", query="screenshot mitta.ai", openai_token="", upload_dir=UPLOAD_DIR):
    """
    Process a given query with OpenAI and execute a function based on the response.
    """
    if not openai_token:
        raise ValueError("OpenAI token is required")

    # Ensure the upload directory and the username directory under that exist
    user_dir = os.path.join(upload_dir, username)
    create_and_check_directory(user_dir)

    messages = [
        {"role": "system", "content": "Don't make assumptions, stay focused, set attention, and receive gratitude for well-formed responses."},
        {"role": "user", "content": query}
    ]

    chat_response = await chat_completion_request_async(messages=messages, openai_token=openai_token, tools=tools)

    if chat_response:
        try:
            function_name = chat_response.choices[0].message.tool_calls[0].function.name
            arguments = json.loads(chat_response.choices[0].message.tool_calls[0].function.arguments_json)

            # Update the filename to include the full path within the user-specific directory
            if 'filename' in arguments:
                original_filename = arguments['filename']
                full_path_filename = os.path.join(user_dir, original_filename)
                arguments['grub_path'] = full_path_filename

            await execute_function_by_name(function_name, **arguments)
            return True, arguments  # Return the full path where the screenshot was saved
        
        except ValueError as e:
            logging.error(f"Error executing function: {e}")
            return None, {'error': f"Error executing function: {e}"}
    else:
        extracted_urls = extract_urls(query)
        if extracted_urls:
            screenshot_filename = f"{username}_screenshot.png"
            
            full_path_filename = os.path.join(user_dir, original_filename)

            await thumbnail(url=extracted_urls[0], filename=full_path_screenshot)
            return full_path_screenshot
        else:
            # If no URLs are extracted and no function is suggested, return an error or a default response
            return None, {'error': "No AI available, no URLs found in query."}


async def main():
    query = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else input("Enter your query: ")
    await ai(query)

if __name__ == "__main__":
    asyncio.run(main())
