# Bot Install Guide
This guide will walk through setting up a Discord bot that uses a MittaAI pipeline to store conversations. It can also be configured to post new stories from Hacker News when asked about "news".

![pirate](https://mitta.ai/images/pirate.png)

## Video Guide
Watch the video guide before beginning installation.

[![Pirate Bot](https://img.youtube.com/vi/VNqnvoCx9Wg/0.jpg)](https://www.youtube.com/watch?v=VNqnvoCx9Wg)

## Prerequisites
- You will need a [MittaAI](https://mitta.ai) account
- You will need a [Discord](https://discord.com) account and server to set up a bot
- You need to know a little bit of Python, but not much
- It's useful to have [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) installed on your system
- You may need to deploy this code somewhere to run. It works best on a server.

## Installation
### Set Up a Conda Environment
Open a terminal on your computer.

Create and activate a new Conda environment using Python 3.11:
```
conda create -n piratebot python=3.11
conda activate piratebot
```

### Check the Repo Out
You need to have `git` installed to check the repo out:

```
git clone https://github.com/MittaAI/mitta-community.git
```

Change to the `mitta-community/cookbooks/piratebot` directory in your shell to continue.

### Install Dependencies
Use pip to install required packages:
```
pip install -r requirements.txt
```

### Configure a Discord Bot
Login to your Discord account in a browser and navigate to your server on the left.

1. Navigate to the [Discord Developer Portal](https://discord.com/developers/applications)
1. Click New Application
1. Type in a name for the bot. Click to agree to the terms and then create the app
1. Click on 'bot' to the left, then click on 'reset token'
1. One the token is reset, it will show up. Copy it.
1. Back in your terminal, copy the `bot.conf.sample` file to `bot.conf`
1. Edit the file and update the token for Discord

Now we need to invite the bot to your Discord server.

1. Back in the Discord Developer Portal, click on `OAuth2`, then `URL Generator`
1. Check the `bot` box under `scopes`
1. Ensure at least `Send Messges`, `Read Message History`, and `Attach Files` is checked under `Bot Permissions`
1. Copy the generated URL at the bottom.
1. Paste the URL into a new tab in your browser.
1. Select your server from the pulldown and then click `continue`.
1. Click `Authorize`
1. Ensure your bot has been added to the server. The bot will be inactive until you start it.

Finally, copy the channel you want the bot in and responding to messages.

1. In Discord, right click on the channel you want the bot to monitor. Click `copy channel ID` at the bottom.
1. Edit the `bot.conf` file and then update the channel_id value with the channel ID you copied.

### Configure the Pipeline
To add the bot pipelines to MittaAI, navigate to your [pipelines page](https://mitta.ai/pipelines).

1. Click `Import` and navigate to the bot directory in the file chooser
1. Select the `pipeline_memories.json` file and then click `open`
1. The pipeline may prompt you for information related to secure tokens. Enter the tokens or values as needed.
1. Click `Import` again and then do the same thing for `pipeline_bot.json`
1. Click on the `crayfish` node and then click on `edit node`
1. Change the callback URL to whatever you need to to receive the callback. See below.

If you don't have a way to expose a port on your local machine, or you don't know how to deploy a server somewhere that runs this code, you can do this locally using Ngrok:

1. Navigate to [Ngrok](https://ngrok.io) and then signup for an account.
1. Navigate to Ngrok's [setup and installation](https://dashboard.ngrok.com/get-started/setup) page.
1. To run Ngrok on the local instance of the bot, do the following:

```
cd /path_to_ngrok/
./ngrok http 5000
```

1. Copy the forwarding address
1. On the MittaAI `crayfish` node detail page, update the callback_url with the new forwarding address
1. Click save.

### Finish the Configuration
Assuming you've determined where to send the callback from MittaAI, continue the configuration by doing the following:

1. Navigate to both the `pirate-bot` and `pirate-memories` pipelines and then copy the ID of each pipeline.
1. If you like, you can add the [hackerbot](https://github.com/MittaAI/mitta-community/blob/main/cookbooks/hackerbot) pipeline. If you don't want to use it, just put a fake news_channel_id and pipeline_id_hn in for those values.
1. Put each of the IDs for the pipelines in the `bot.conf` file. The pipeline config names are labeled to match.
1. Finally, navigate to your [settings](https://mitta.ai/settings) on MittaAI and copy your token.
1. Edit the config file and put your MittaAI token in the correct location.
1. Save the config file.

### Launch the Bot
As covered above, the bot will need an external callback handler mapped to your local machine to function correctly. If the bot is deployed onto a dedicated server on the Internet, you will need to provide a URL to the callback handler that either has the IP address or named address of the server, plus the port number you are running it on.

You may need to deal with firewalls as well. If you don't know anything about running servers, try checking out [Google Cloud](https://cloud.google.com/). There are scripts in the `scripts` directory that will let you start a bot on a Google cloud server that will cost you about $20 a month. Some editing require. Pop into [SlothAI's Discord](https://discord.gg/SxwcVGQ8j9) for help.

To launch the bot locally, run the following:

```
python bot.py
```

Navigate to your Discord channel and you should see the bot has posted an emoji. Each time you save the `bot.py` file, the bot should post an emoji to the channel.

### Future Work
Future work on this repo will include adding image posting, PDF posting, image generation and more. Stay tuned!
