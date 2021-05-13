#!/usr/bin/env python3

import os
import re
import json
import datetime
import asyncio
from discord import channel, DMChannel, Embed, Intents
from discord.ext import commands
from discord.ext.commands import bot
from Documents.formatter import *
from Platform import Utilities, GoogleComm


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


async def retrieve_roles(_user=None) -> list:
    """
    Retrieves the authors roles in a list format with only names listed.
    :param _user: Passed user to get roles from and return
    :return:
    """
    _roles = _user.roles
    return [x.name for x in _roles]


async def test_instructor(ctx) -> bool:
    """
    User has enquired about receiving help. User will attain all possible info.
    :param ctx: Passed context in which a message was sent.
    :return:
    """
    _author = ctx.author
    _roles = await retrieve_roles(_author)
    if (
        "Instructor" in _roles or
        "Teacher" in _roles
    ):
        return True


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
    Version:  {3}
    Booted:   {2} UTC
    ```
    """.format(
        client.user.name,
        client.user.id,
        utc,
        Utilities.SettingsRead()()["VERSION"]
    )
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

    if _checkmsg.dm_check(msg):
        _c = _author
    else:
        _start = _content.split(" ")[0]
        if _start.startswith("!"):
            _c = bot_channel
        else:
            _c = _author

    if _content.lower().startswith(("?def", "!def")):
        _msg = "".join(_content.split(" ")[1:])
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

            async with _c.typing():
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

    elif _content.startswith(("!download", "?download")):
        _dls = Utilities.LinkRead()()["Downloads"]
        _get = "".join(_content.split(" ")[1:])
        for each in list(_dls.keys()):
            if _get.lower() in each.lower():
                _download = _dls[each]
                if "." in _get:
                    _year, _edition, _type = each.split(".")
                    _ver = _type.split(" ")[0]
                    _type = _type.split(" ")[1]
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

    elif _content.startswith(("!website", "?website")):
        _web = Utilities.LinkRead()()["Websites"]
        _get = "".join(_content.split(" ")[1:])
        for each in list(_web.keys()):
            if _get.lower() == each.lower():
                if "Intro" in each or "Compendium" in each:
                    _website = "https://docs.google.com/document/d/{0}".format(_web[each])
                else:
                    _website = _web[each]
                embed = Embed()
                embed.url = _website
                embed.title = each
                embed.description = "Website link for {0}.".format(each)
                await _c.send(embed=embed)

    elif _content.startswith(("!about", "?about")):
        _teach = Utilities.LinkRead()()["Instructors"]
        _get = "".join(_content.split(" ")[1:])
        for each in list(_teach.keys()):
            if _get.lower() == each.lower():
                _website = _teach[each]
                embed = Embed()
                embed.url = _website
                embed.title = each
                embed.description = "Website link for {0}.".format(each)
                await _c.send(embed=embed)

    elif _content.lower().startswith("when is my next class? "):
        _classname = _content.split("when is my next class? ")[1]
        _work = GoogleComm.AttainGoogleClass(_classname)()
        # Perhaps... Separate the code below into a method elsewhere...? Let's ponder about what can be reused here...
        _week = list(_work.keys())[0]
        if _week != 'Complete':
            _assignments = list(_work[_week].keys())
            _final_info = convert_to_output(week=_week, assignments=_work[_week])

        else:
            _final_info = "\nYou've completed this class.\n"

        await ctx.send(_final_info)

    elif _content.lower().startswith("!get example "):
        _get_example = _content.split("!get example ")[1].replace(" ", "")
        _ex = Utilities.GetRandomExample()(_get_example)
        if _ex:
            _embed = Embed()
            _embed.title = _get_example
            _embed.description = _ex
            await _c.send(embed=_embed)

    elif _content.lower().startswith(("!show ", "?show ")):
        _info = _content.split(" ")[1].replace(" ", "")
        _images = Utilities.LinkRead()()['images']
        _embed = Embed()
        _embed.set_image(url=_images[_info])
        _embed.title = "Instructions"
        await _c.send(embed=_embed)

    elif _content.lower().startswith("?grade "):
        _info = _content.split(" ")[1]
        await _author.send("Please enter name as it appears in Google Classroom: ")
        _name = await client.wait_for("message", check=CheckMsg().non_bot)
        _get_grades = GoogleComm.AttainGoogleClass(_classname=_info).grades()
        for _assignment in _get_grades[_name.content]:
            _embed = Embed()
            _embed.title = _assignment
            _embed.description = _get_grades[_name.content][_assignment]
            await ctx.send(embed=_embed)

    else:
        await client.process_commands(msg)

    if msg.content.startswith(("!", "?")):
        if _checkmsg.dm_check(msg):
            pass
        elif _checkmsg.non_bot(msg):
            await msg.delete()


@client.command(name="addinstructor", pass_context=True)
async def addinstructor(ctx):
    _msg = ctx.message.content.split("addinstructor ")[1]
    _name = _msg.split(" ")[0]
    _link = " ".join(_msg.split(" ")[1:])
    if await test_instructor(ctx):
        Utilities.LinkWrite(_name=_name, _example=_link)()


@client.command(name="addexample", pass_context=True)
async def addexample(ctx):
    _msg = ctx.message.content.split("addexample ")[1]
    _name = _msg.split(" ")[0]
    _example = " ".join(_msg.split(" ")[1:])
    if await test_instructor(ctx):
        Utilities.ExamplesWrite(_name=_name, _example=_example)()


@client.command(name="version", pass_context=True)
async def version(ctx):
    _ver = Utilities.SettingsRead()()['VERSION']
    await ctx.author.send("Bot is running software version: {0}".format(_ver))


@client.command(name="whatis", pass_context=True)
async def define(ctx):
    _msg = ctx.message.content
    _author = ctx.author
    _word = _msg.split("whatis ")[1]
    _info = Utilities.DefineWord()(_word)
    embed = Embed()
    embed.title = _info[0]
    embed.url = _info[1]
    embed.description = "Definition of {0}.".format(_info[0])
    for each in list(_info[2].keys()):
        if len(_info[2][each]) > 0:
            embed.add_field(name=each, value=" - " + "\n - ".join(_info[2][each]), inline=True)

    await ctx.message.delete()
    await _author.send(embed=embed)


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
