import time
import json
import sys

import asyncio
from playwright.async_api import async_playwright

from tenacity import retry, wait_random_exponential, stop_after_attempt

from function_wrapper import function_info_decorator, tools

import openai

# Set your OpenAI API key here
openai.api_key = ""

from function_wrapper import callable_registry

# helper functions
def extract_urls(query):
    # This regex is designed to match most URLs
    url_pattern = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')
    urls = url_pattern.findall(query)
    return urls


async def execute_function_by_name(function_name, **kwargs):
    if function_name in callable_registry:
        function_to_call = callable_registry[function_name]
        # Ensure the function call is awaited if it's async
        if asyncio.iscoroutinefunction(function_to_call):
            return await function_to_call(**kwargs)
        else:
            return function_to_call(**kwargs)
    else:
        raise ValueError(f"Function {function_name} not found in registry")


# dynamically called functions for imaging pages
@function_info_decorator
async def thumbnail(url: str, path: str="example.png") -> str:
    """
    Takes a screenshot of the specified URL and saves it to the given path asynchronously.

    :param url: The website URL to capture.
    :type url: str
    :param path: The path to save the screenshot, defaults to "example.png".
    :type path: str
    :return: The path where the screenshot was saved.
    :rtype: str
    """
    print(url)
    async with async_playwright() as p:
        browser = await p.webkit.launch()
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1280, "height": 2560})
        await page.goto(url)
        await page.screenshot(path=path)
        await browser.close()
    return path


@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
async def chat_completion_request_async(messages, tools=None, tool_choice=None, model="gpt-3.5-turbo-1106"):
    client = openai.AsyncOpenAI(api_key=openai.api_key)
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return None


async def ai(query=""):
    # Your existing setup code remains the same
    messages = [
        {"role": "system", "content": "Don't make assumptions..."},
        {"role": "user", "content": query}
    ]

    # call chat completion
    chat_response = await chat_completion_request_async(messages=messages, tools=tools) 

    if chat_response:
        function_name = chat_response.choices[0].message.tool_calls[0].function.name
        arguments_json = chat_response.choices[0].message.tool_calls[0].function.arguments
        arguments = json.loads(arguments_json)

        try:
            # Now using await for asynchronous function call
            await execute_function_by_name(function_name, **arguments)
        except ValueError as e:
            print(e)
    else:
        extracted_urls = extract_urls(query)
        await thumbnail(url=extracted_urls[0])


async def main():
    if len(sys.argv) > 1:
        query = ' '.join(sys.argv[1:])
    else:
        query = input("Enter your query: ")

    await ai(query)

if __name__ == "__main__":
    asyncio.run(main())

