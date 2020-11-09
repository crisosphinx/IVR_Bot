import asyncio
import discord
from discord.ext import commands

# Client
Client = discord.Client()
bot_prefix = 'ivr '
client = commands.Bot(command_prefix=bot_prefix)


@client.event
async def delete_messages(messages=None, channel=None):
    if messages is None:
        _m = list()
    else:
        _m = messages

    _m.append(await channel.send("Messages will be removed in 5 seconds..."))
    await asyncio.sleep(1)
    await _m[1].edit(content="Messages will be removed in 4 seconds...")
    await asyncio.sleep(1)
    await _m[1].edit(content="Messages will be removed in 3 seconds...")
    await asyncio.sleep(1)
    await _m[1].edit(content="Messages will be removed in 2 seconds...")
    await asyncio.sleep(1)
    await _m[1].edit(content="Messages will be removed in 1 seconds...")
    await asyncio.sleep(1)
    await channel.delete_messages(_m)


@client.event
async def bot_send_message(orig_message=None, message=None, channel=None):
    await orig_message.delete()
    await channel.send(message)
