import asyncio
import json
import re
import sys
from playwright.async_api import async_playwright
from tenacity import retry, wait_random_exponential, stop_after_attempt
import openai
import os
import logging
import random
import string

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
    Returns JSON with the result or an error message.
    """
    try:
        if function_name in callable_registry:
            function_to_call = callable_registry[function_name]
            result = await function_to_call(**kwargs) if asyncio.iscoroutinefunction(function_to_call) else function_to_call(**kwargs)

            # Assuming result is already JSON or a Python dictionary that can be serialized to JSON
            return json.dumps(result) if not isinstance(result, str) else result
        else:
            raise ValueError(f"Function {function_name} not found in registry")
    except Exception as e:
        # Return a JSON string with an error message
        return json.dumps({"error": str(e)})


@function_info_decorator
def i_have_failed_my_purpose(error_reason: str) -> dict:
    """
    Generates a structured error message indicating why an operation failed.

    :param error_reason: A description of why the operation failed.
    :type error_reason: str
    :return: A dictionary containing the error reason.
    :rtype: dict
    """
    return {
        "success": False,
        "error": "Operation failed",
        "reason": error_reason
    }


import tempfile
import shutil

@function_info_decorator
async def take_screenshot_and_extract_links(url: str, filename_prefix: str = "example", full_screen: bool = False, extract_links: bool = False, link_selector: str = "a", extract_image: bool = False, img_isolate_selector: str = "img", button_with_text: str = "", click_button: bool = False, ocr_readable: bool = False, dark_mode: bool = False, overlap_ratio: float = 0.1) -> str:
 
    """
    Takes a screenshot of the specified URL and saves it to the given filename prefix asynchronously.
    Captures multiple screenshots with overlapping sections to cover the full page height.

    Can capture either the full page or just the viewport based on the full_screen parameter.

    Optionally extracts links (both URL and text) from the page using a specified link selector,
    defaulting to 'a' tags if no link selector is provided.

    Optionally extracts an image from the page using a specified image selector.

    If a button_with_text is provided and click_button is True, attempts to click the specified button before taking screenshots or extracting links or images.

    Optionally sets the font to be OCR readable and enables dark mode.

    :param url: The website URL to capture.
    :type url: str
    :param filename_prefix: The prefix used to save the screenshot filenames.
    :type filename_prefix: str
    :param full_screen: Determines whether to capture the full page or just the viewport. Defaults to False for viewport screenshot.
    :type full_screen: bool
    :param extract_links: Determines whether to extract all links from the page. Defaults to False.
    :type extract_links: bool
    :param link_selector: The CSS selector used to select elements for extracting links. Defaults to 'a' for anchor tags.
    :type link_selector: str
    :param extract_image: Determines whether to extract an image from the page. Defaults to False.
    :type extract_image: bool
    :param img_isolate_selector: The CSS selector used to select the image for extracting. Defaults to 'img' for image tags.
    :type img_isolate_selector: str
    :param button_with_text: The button text used to find and click a button before taking action.
    :type button_with_text: str
    :param click_button: Determines whether to click a button identified by button_with-text. Defaults to False.
    :type click_button: bool
    :param ocr_readable: Determines whether to set the font to be OCR readable. Defaults to False.
    :type ocr_readable: bool
    :param dark_mode: Determines whether to enable dark mode. Defaults to False.
    :type dark_mode: bool
    :param overlap_ratio: The ratio of overlap between consecutive screenshots. Defaults to 0.1 (10% overlap).
    :type overlap_ratio: float
    :return: A JSON string containing a list of filenames where the screenshots were saved, optionally a list of links with their texts, and optionally the path of the extracted image.
    :rtype: str
    """

    links = []
    image_from_page = ""

    with tempfile.TemporaryDirectory() as temp_dir:
        async with async_playwright() as p:
            browser_context = await p.chromium.launch_persistent_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
                viewport={"width": 2560, "height": 1440},
                device_scale_factor=1.0,
                user_data_dir=temp_dir,
            )
            page = await browser_context.new_page()

            await page.goto(url)

            if click_button and button_with_text:
                # Find a button by its accessible name and click it
                await page.get_by_role('button', name=button_with_text).click()
                await page.wait_for_timeout(1500)  # Additional waiting time after click action

            await page.wait_for_timeout(1500)

            # Remove images from the page
            if not extract_image:
                await page.evaluate("""
                    const images = document.querySelectorAll('img');
                    images.forEach(img => {
                        img.src = '';
                    });
                """)

            if ocr_readable:
                # Set font to Consolas, font size to 24px, and font weight to 600 (semi-bold)
                await page.evaluate("""
                    const style = document.createElement('style');
                    style.innerHTML = `
                        * {
                            font-family: "Consolas", monospace !important;
                            font-size: 18px !important;
                            font-weight: 500 !important;
                        }
                    `;
                    document.head.appendChild(style);
                """)

            if dark_mode:
                # Set background color to black and font color to white
                await page.evaluate("""
                    const style = document.createElement('style');
                    style.innerHTML = `
                        * {
                            background-color: black !important;
                            color: white !important;
                        }
                    `;
                    document.head.appendChild(style);
                """)

            if extract_links:
                # Preprocess link_selector to replace double quotes with single quotes
                sanitized_link_selector = link_selector.replace('"', "'")

                links = await page.evaluate(f'''() => {{
                    const elements = Array.from(document.querySelectorAll("{sanitized_link_selector}"));
                    return elements.map(element => {{
                        return {{
                            href: element.href,
                            text: element.textContent || element.innerText
                        }};
                    }});
                }}''')

            # screenshot, with optional scrolling to get the whole page
            if full_screen:
                # Capture the full page by scrolling
                page_height = await page.evaluate('document.body.scrollHeight')
                viewport_height = await page.evaluate('window.innerHeight')
                overlap_height = int(viewport_height * overlap_ratio)
                effective_height = viewport_height - overlap_height
                num_screenshots = math.ceil(page_height / effective_height)

                screenshot_filenames = []

                for i in range(num_screenshots):
                    scroll_position = i * effective_height
                    await page.evaluate(f'window.scrollTo(0, {scroll_position})')
                    await page.wait_for_timeout(500)  # Wait for the scroll to complete

                    screenshot_filename = f"{filename_prefix}_{i}.png"
                    await page.screenshot(path=screenshot_filename, full_page=False)
                    screenshot_filenames.append(screenshot_filename)
            else:
                # Capture only the top shot
                screenshot_filename = f"{filename_prefix}.png"
                await page.screenshot(path=screenshot_filename, full_page=False)
                screenshot_filenames = [screenshot_filename]

            await browser_context.close()

        # Wipe the temporary directory after the function finishes
        shutil.rmtree(temp_dir)

    result = {
        "filenames": screenshot_filenames,
        "success": True
    }

    if extract_links:
        result["links"] = links
    if image_from_page:
        result["image_from_page"] = image_from_page  # Include the path of the image screenshot in the result

    return json.dumps(result)  # Return JSON string with filename, links, and optionally the path of the image screenshot

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
async def chat_completion_request_async(messages=None, openai_token=None, tools=None, tool_choice=None, model="gpt-3.5-turbo-1106"):
    """
    Make an asynchronous request to OpenAI's chat completion API.
    """
    client = openai.AsyncOpenAI(api_key=openai_token)
    try:
        return await client.chat.completions.create(model=model, messages=messages, tools=tools, tool_choice=tool_choice)
    except Exception as e:
        print("Unable to generate ChatCompletion response:", e)
        return None


def random_string(length=13):
    """Generate a random string of fixed length."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


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
        {"role": "system", "content": "You are Grubby, an AI bot. Don't make assumptions, stay focused, set attention, and receive gratitude for well-formed responses. Only extract links if explicitly stated. 'thumb' or 'thumbnail' or 'small' means DO NOT use fullscreen capture, which sets the full_screen parameter to False and gives us a thumbnail. If someone wants 'full' or 'full screen' or 'big', we set the full_screen parameter to True to do a full screen capture. If OCR readability is requested with keywords like 'OCR' or 'readable', set the ocr_readable parameter to True. If dark mode is requested with keywords like 'dark mode' or 'black background', set the dark_mode parameter to True. On failure to purpose, you become Dr. Gregory House, AI crawler extraordinaire."},
        {"role": "user", "content": query}
    ]
    
    # get the function and parameters to call
    chat_response = await chat_completion_request_async(messages=messages, openai_token=openai_token, tools=tools)
    logging.info(chat_response)
    # Assume function_name and arguments are extracted from chat_response
    try:
        function_name = chat_response.choices[0].message.tool_calls[0].function.name
        arguments_json = chat_response.choices[0].message.tool_calls[0].function.arguments
        arguments = json.loads(arguments_json)

        if function_name == "i_have_failed_my_purpose":
            json_results_str = await execute_function_by_name(function_name, **arguments)
            results = json.loads(json_results_str) if not isinstance(json_results_str, dict) else json_results_str

            # Move 'arguments' into the 'results' dictionary
            results['arguments'] = arguments
            
            return False, results

        else:
            # Update the filename to include the full path within the user-specific directory
            if 'filenames' in arguments:
                original_filename = arguments['filenames']
                if not original_filename.endswith('.png') and '.' not in original_filename:
                    original_filename += '.png'
                full_path_filename = os.path.join(user_dir, original_filename)
                arguments['filename'] = full_path_filename
            else:
                random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=13))
                screenshot_filename = f"{username}_{random_string}.png"
                arguments['filename'] = os.path.join(user_dir, screenshot_filename)

            json_results_str = await execute_function_by_name(function_name, **arguments)
            results = json.loads(json_results_str) if not isinstance(json_results_str, dict) else json_results_str

            # Move 'arguments' into the 'results' dictionary
            results['arguments'] = arguments
            
            return True, results
        
    except Exception as ex:
        logging.info(ex)
        # Return False and the error message
        return False, {'error': str(ex)}


async def main():
    query = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else input("Enter your query: ")
    await ai(query)

if __name__ == "__main__":
    asyncio.run(main())
