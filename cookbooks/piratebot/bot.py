import discord
import asyncio
import aiohttp
import os
from quart import Quart, request, render_template
from discord.ext import commands
import nest_asyncio
import random

import configparser

# Create a ConfigParser object
config = configparser.ConfigParser()
config.read('bot.conf')

# stuff
DISCORD_TOKEN = config.get('Credentials', 'discord_token')
MITTAAI_TOKEN = config.get('Credentials', 'mittaai_token')
PIPELINE_ID_BOT = config.get('Settings', 'pipeline_id_bot')
PIPELINE_ID_MEMORY = config.get('Settings', 'pipeline_id_memory')
PIPELINE_ID_HN = config.get('Settings', 'pipeline_id_hn')
CHANNEL_ID = config.get('Settings', 'channel_id')
NEWS_CHANNEL_ID = config.get('Settings', 'news_channel_id')
BOT_NAME = config.get('Settings', 'bot_name')

# Create a Discord bot instance
intents = discord.Intents.default()
intents.message_content = True

# async things
nest_asyncio.apply()

# init and add webserver to bot
app = Quart(__name__)
bot = discord.Client(command_prefix="!", intents=intents)

# say command
async def say(saying, channel):
    async with channel.typing():
        await asyncio.sleep(random.random() * 1)
        await channel.send(saying)
    return

# typing things
async def typing(channel):
    async with channel.typing():
        await asyncio.sleep(random.random() * 1)
    return

# upload image, file, etc
async def upload(file_handle, file_name, channel):
    async with channel.typing():
        await asyncio.sleep(random.random() * 2)
        await channel.send(file=discord.File(file_handle, file_name))

# setup async events
@app.before_serving
async def before_serving():
    loop = asyncio.get_event_loop()
    await bot.login(DISCORD_TOKEN)
    loop.create_task(bot.connect())

@bot.event
async def on_message(message):
    # check if we are allowed to interact with the current channel
    if str(message.channel.id) != str(CHANNEL_ID): 
        if str(message.channel.id) != str(NEWS_CHANNEL_ID):
            return

    # if author is the bot, we ignore it from here   
    if message.author == bot.user:
        return
    
    if int(message.channel.id) == int(NEWS_CHANNEL_ID):
        print("in the news channel")
        print(message.content.lower())
        if "news" in message.content.lower():
            await typing(message.channel)
            async with aiohttp.ClientSession() as session:
                url = f"https://mitta.ai/pipeline/{PIPELINE_ID_HN}/task?token={MITTAAI_TOKEN}"
                document = {"author": message.author.name, "channel_id": message.channel.id}
                async with session.post(url, json=document) as resp:
                    assert resp.status == 200
                    response = await resp.json()
        return


    try:
        await typing(message.channel)
        async with aiohttp.ClientSession() as session:
            url = f"https://mitta.ai/pipeline/{PIPELINE_ID_BOT}/task?token={MITTAAI_TOKEN}"
            document = {"message": message.content.lower(), "author": message.author.name, "channel_id": message.channel.id}

            async with session.post(url, json=document) as resp:
                assert resp.status == 200
                response = await resp.json()

                # get the pipeline's assistant_content
                await typing(message.channel)

    except Exception as ex:
        print(ex)
        await say("My endpoint handlers are offline. Standby.", message.channel)

@bot.event
async def on_ready():
    channel = bot.get_channel(int(CHANNEL_ID))
    emoji = ["🤣", "🐌", "🐾", "🐨", "💤", "🐼", "🤔", "🐰", "🐻", "🌿","🌼"]
    await channel.send(random.choice(emoji))

@app.route("/callback", methods=["POST"])
async def callback():
    try:
        data = await request.get_json()
        message = data.get("assistant_content")
        channel_id = int(data.get("channel_id")[0])

        # news posts
        if channel_id == int(NEWS_CHANNEL_ID):
            print(channel_id)
            channel = bot.get_channel(int(NEWS_CHANNEL_ID))
            await say(message, channel)
            return {"message": "Thank you."}
            
        if message is None:
            return {"error": "Missing 'message' in JSON payload"}, 400

        channel = bot.get_channel(int(CHANNEL_ID))
        await say(message, channel)

        async with aiohttp.ClientSession() as session:
            url = f"https://mitta.ai/pipeline/{PIPELINE_ID_MEMORY}/task?token={MITTAAI_TOKEN}"
            document = {"message": message.lower(), "author": f"{BOT_NAME}", "channel_id": channel_id}

            async with session.post(url, json=document) as resp:
                assert resp.status == 200
                response = await resp.json()

        return {"message": "Thank you."}
    except Exception as e:
        print(e)
        return {"error": str(e)}, 500

@app.route('/')
async def serve_index():
    return await render_template('index.html')

app.run(host='0.0.0.0')