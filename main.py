#!/usr/bin/env python3


import time
from math import floor, ceil
import re
import json
import datetime
import asyncio
import discord
from discord import message, user, channel, Client, DMChannel, Embed, Color, File, Intents
from discord.ext import commands
from discord.ext.commands import bot
from discord.utils import get
from Documents.formatter import *
from Platform import Utilities


# Intents
Intents = Intents().all()

# Prefix for bot
client = commands.Bot(command_prefix=Utilities.SettingsRead()()['CALLS'])
bot_channel = None


async def retrieve_channel(ctx, requested_channel: str) -> channel:
    _server = None
    if type(ctx) is bot.Bot:
        _server = [x for x in ctx.guilds if x.name == "Universe Hub"][0]
    if _server is not None:
        _all_channels = dict()
        for key in _server.channels:
            _all_channels.setdefault(key.name, key)
        if requested_channel in _all_channels.keys():
            return _all_channels[requested_channel]
        else:
            try:
                return ctx.channel
            except AttributeError:
                return None


class CheckMsg(object):
    def __init__(self, ctx=None, authid=None) -> None:
        """
        Class runs a check and returns a boolean based on the author id.
        :param ctx: Context of message
        :param authid: Authors id number
        """
        self.ctx = ctx
        self.authid = authid

    def dm_check(self, _msg=None) -> bool:
        """
        Run a check to see if the message is not from the bot
        :param _msg: Passed message
        :return:
        """
        if isinstance(self.ctx.channel, DMChannel):
            return self.non_bot(_msg) and self.auth_msg(_msg)

    @staticmethod
    def non_bot(_msg=None) -> bool:
        """
        Determine if the message is not from the bot.
        :param _msg: Message in question
        :return:
        """
        return len(_msg.content) != 0 and not _msg.author.bot

    def auth_msg(self, _msg=None) -> bool:
        """
        Determine if the message is owned by the owner
        :param _msg: Message in question
        :return:
        """
        return _msg.author.id == self.authid

    @staticmethod
    def force_bot(_msg) -> bool:
        """
        Forces the bot to be the message author. ;)
        :return:
        """
        return True


@client.event
async def on_ready() -> None:
    global bot_channel

    utc = str(datetime.datetime.utcnow()).split('.')[0]
    bot_channel = await retrieve_channel(client, "bot-channel")
    info_to_print = """
    ```
    Bot Online!
    Name:     {0}
    ID:       {1}
    Booted:   {2} UTC
    ```
    """.format(client.user.name, client.user.id, utc)
    await bot_channel.send(info_to_print)


@client.event
async def on_message(msg):
    """
    On message, have the bot do something.
    :param msg:
    :return:
    """
    ctx = await client.get_context(msg)
    _author = msg.author
    _content = msg.content
    _checkmsg = CheckMsg(ctx, _author.id)

    def chunker(seq, size):
        return (seq[pos:pos + size] for pos in range(0, len(seq), size))

    def restructure(_long_str: str, _amt: int) -> list:
        r = re.compile("[^\n]+")
        got = r.findall(_long_str)
        _ret = list()
        for item in chunker(got, _amt):
            _ret.append("\n".join(item))
        return _ret

    if _content.lower().startswith(("?def", "!def")):
        _start = _content.split(" ")[0]
        if _start.startswith("!"):
            _c = bot_channel
        else:
            _c = _author

        _msg = _content.split(" ")[1]
        _return = Utilities.DefinitionUnity(_msg)(True)
        if _return:
            reconfigure = dict()
            _key = str()
            for each in _return[3:]:
                if "‣" in each:
                    _key = each
                else:
                    reconfigure.setdefault(_key, []).append(each)
            _first_message = Embed()
            _first_message.title = _return[0]
            _first_message.url = _return[1]
            _first_message.description = _return[2]

            async with msg.channel.typing():
                for key in reconfigure:
                    value = reconfigure[key]
                    # determine the amount of characters in properties of the key
                    _combined_lines = "\n".join(value)
                    _amount_chars = len(_combined_lines)
                    if _amount_chars <= 6000:
                        # do work with fields equal to 1024 for each set
                        _message1 = _first_message
                        _message1.url = _return[1]

                        if _amount_chars <= 1024:
                            _message1.add_field(name=key, value=_combined_lines, inline=True)
                            await _c.send(embed=_message1)

                            _first_message = Embed()
                            _first_message.title = "Continued"
                            _first_message.description = "..."

                        else:
                            # _line_split = ceil(len(_combined_lines) / 1024)
                            _result = restructure(_long_str=_combined_lines, _amt=6)
                            # 🗹
                            for each in _result:
                                if each:
                                    _message1.add_field(name=key, value=each, inline=True)
                            await _c.send(embed=_message1)

                            _first_message = Embed()
                            _first_message.title = "Continued"
                            _first_message.description = "..."

                    else:
                        # We want to split the fields across multiple embeds
                        _result1 = restructure(_long_str=_combined_lines, _amt=6000)
                        for each in _result1:
                            _message2 = _first_message
                            _message2.url = _return[1]
                            _result2 = restructure(_long_str=each, _amt=6)
                            for _each in _result2:
                                if _each:
                                    _message2.add_field(name=key, value=_each, inline=True)
                            await _c.send(embed=_message2)

                            _first_message = Embed()
                            _first_message.title = "Continued"
                            _first_message.description = "..."

        else:
            await _author.send("Term could not be found.")

        if _checkmsg.dm_check(msg):
            pass
        elif _checkmsg.non_bot(msg):
            await msg.delete()

    elif _content.startswith(("!download", "?download")):
        _start = _content.split(" ")[0]
        if _start.startswith("!"):
            _c = bot_channel
        else:
            _c = _author

        _dls = Utilities.JsonRead()()["Downloads"]
        _get = _content.split(" ")[1]
        for each in list(_dls.keys()):
            if _get.lower() in each.lower():
                _download = _dls[each]
                if "." in _get:
                    _year, _edition, _type = each.split(".")
                    _ver = _type.split("-")[0]
                    _type = _type.split("-")[1]
                    embed = Embed()
                    embed.url = _download
                    embed.title = "{0}.{1}.{2} {3} Download".format(_year, _edition, _ver, _type)
                    embed.description = "Link to the UnityHub {0}.{1}.{2}f1 {3} download.".format(
                        _year, _edition, _ver, _type
                    )
                else:
                    embed = Embed()
                    embed.url = _download
                    embed.title = each
                    embed.description = "Download link to {0}.".format(each)
                await _c.send(embed=embed)

        if _checkmsg.dm_check(msg):
            pass
        elif _checkmsg.non_bot(msg):
            await msg.delete()

    elif _content.startswith(("!website", "?website")):
        _start = _content.split(" ")[0]
        if _start.startswith("!"):
            _c = bot_channel
        else:
            _c = _author
        _web = Utilities.JsonRead()()["Websites"]
        _get = _content.split(" ")[1]
        for each in list(_web.keys()):
            if _get.lower() in each.lower():
                _website = _web[each]
                embed = Embed()
                embed.url = _website
                embed.title = each
                embed.description = "Website link for {0}.".format(each)
                await _c.send(embed=embed)

        if _checkmsg.dm_check(msg):
            pass
        elif _checkmsg.non_bot(msg):
            await msg.delete()

    else:
        await client.process_commands(msg)


# Permissions number: 125952
# --------------------------
# View Channels
# Send Messages
# Manage Messages
# Embed LinksW
# Attach Files
# Read Message History

json_path = find_file('Tokens')

# Launch our bot
with open(json_path, 'r') as f:
    token = json.load(f)

loop = asyncio.get_event_loop()
loop.run_until_complete(client.start(token['ivrBot']))  # client.run(token['token'])
