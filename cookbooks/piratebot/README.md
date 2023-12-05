# PirateBot Install Guide

## Prerequisites
- ensure you have Conda installed on your system
- You will need a Discord account to set up a bot

## Installation
1. Set Up Conda Environment:
	- Create and activate a new Conda environment using Python 3.11:
	```
	conda create -n piratebot python=3.11
	conda activate piratebot
	```

2. Install Dependencies
	- Use pip to install required packages:
	```
	pip install -r requirements.txt
	```

3. Configure Discord Bot:
	- Set up a bot on your Discord account and retrieve the token.
	- Detailed instructions will be provided in a forthcoming video.

4. Set Up Configuration File:
	- Copy `bot.conf.sample` to `bot.conf`.
	- Edit `bot.conf` to include your tokens and pipeline IDs

5. Run the Bot:
	- Start the bot using the following command:
	```
	python ./bot.py
	```
