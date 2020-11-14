#!/usr/bin/env python3

import asyncio
import discord
from discord.ext import commands

# Client
Client = discord.Client()
bot_prefix = 'ivr '
client = commands.Bot(command_prefix=bot_prefix)


@client.event
async def delete_messages(messages=None, channel=None):
    """
    Delete messages in channel / specify the amount to delete if you wish.

    :param messages: A list of message to delete.
    :param channel: Which channel to delete the messages from.
    :return:
    """

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
async def bot_send_message(orig_msg=None, msg=None, chl=None, bot_chl=None, author=None):
    """
    Send a message with the bot. Comes with the ability to delete the message, send a message, and so much more.

    :param orig_msg: The original message to delete.
    :param msg: A new message to send.
    :param chl: The channel in which to send the message on.
    :param bot_chl: The bot channel in which to send the message to, for logging.
    :param author: The original messages author.
    :return:
    """

    if chl is not None:
        async with chl.typing():
            if orig_msg is not None:
                await orig_msg.delete()
            if msg is not None:
                await chl.send(msg)
            if bot_chl is not None and author is not None:
                await bot_chl.send("{0} sent: {1}".format(author, msg))
            elif bot_chl is not None and author is None:
                await bot_chl.send("In {0}, I sent: {1}".format(chl, msg))

    else:
        if orig_msg is not None:
            await orig_msg.delete()
        if bot_chl is not None and author is not None:
            await bot_chl.send("{0} sent: {1}".format(author, msg))
        elif bot_chl is not None and author is None:
            await bot_chl.send("In {0}, I sent: {1}".format(chl, msg))
