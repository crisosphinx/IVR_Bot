#!/usr/bin/env python3

import os
import time
import asyncio
import discord
from discord.ext import commands
from discord import Embed
import json

# Client
Client = discord.Client()

# Prefix for bots commands
bot_prefix = 'ivr '
client = commands.Bot(command_prefix=bot_prefix)

# Do we want a console debug
DEBUG = True


@client.event
async def on_ready():
    """
    When it boots, we will clear the chat AND print back information in the
    console regarding our bot.

    :return:
    """

    print('Bot Online!')
    print('Name: {}'.format(client.user.name))
    print('ID: {}'.format(client.user.id))


@client.event
async def on_message(message):
    _message = message
    message_channel = message.channel
    message_attachments = message.attachments
    message_author = message.author
    message_owner = message.author.id
    message = message.content

    if message_author != client.user and message.startswith('ivr '):
        async with message_channel.typing():
            await _message.delete()
            message = message.split("ivr ")[1]
            await message_channel.send("{0} sent: {1}".format(message_author, message))

    elif message == 'ping':

        before = time.monotonic()
        message = await message_channel.send("Pong!")
        _ping = round((time.monotonic() - before) * 1000, 6)
        await message.edit(content="Pong!  `{0} ms`".format(_ping))

        if DEBUG:
            print("Ping {0} ms".format(_ping))


@client.command(pass_context=True)
async def say(ctx, *args):
    """
    Tell the bot to say something.

    :param ctx: Context
    :param args: What the messages passed to the bot say. Join them.
    :return:
    """

    _message = ' '.join(args)
    await ctx.message.delete()
    await ctx.message.channel.send(_message)


# Permissions number: 125952
# --------------------------
# View Channels
# Send Messages
# Manage Messages
# Embed Links
# Attach Files
# Read Message History

# Our token path
if os.name == 'nt':
    try:
        json_path = 'I:\\IVR_token.json'
    except:
        json_path = 'C:\\IVR_token.json'
else:
    json_path = '/usr/bin/IVR_token.json'

# Launch our bot
with open(json_path, 'r') as f:
    token = json.load(f)

loop = asyncio.get_event_loop()
loop.run_until_complete(client.start(token['token']))
# client.run(token['token'])
