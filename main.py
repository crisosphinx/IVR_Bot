#!/usr/bin/env python3

import json
import datetime
import asyncio
from discord import channel, Intents
from discord.ext import commands
from discord.ext.commands import bot
from Documents.formatter import *
from Platform import Utilities, GoogleComm
import botcommands
import MessageChecker

# Intents.
Intents = Intents().all()

# Prefix for bot
client = commands.Bot(command_prefix=Utilities.SettingsRead()()['CALLS'])
bot_channel = None


async def retrieve_channel(ctx, requested_channel: str) -> channel:
    _server = None
    if type(ctx) is bot.Bot:
        _server = [x for x in ctx.guilds if x.name == "Universe Hub"][0]
    else:
        _server = [x for x in client.guilds if x.name == ctx.guild.name][0]
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
    _checkmsg = MessageChecker.CheckMsg(ctx, _author.id)
    _sheets = GoogleComm.AttainGoogleSheet(document_id=Utilities.LinkRead()()["Websites"]["Sheets"])

    if _checkmsg.dm_check(msg):
        _c = _author
    else:
        _start = _content.split(" ")[0]
        if _start.startswith("!"):
            _c = await retrieve_channel(ctx, "universe-bot")
        else:
            _c = _author

    if _content.lower().startswith(("!ping", "?ping")):
        await _c.send("Pong! {0} ms".format(round(client.latency, 1)))
        _sheets.updatevalue('ping')

    if _content.lower().startswith(("?def", "!def")):
        if await botcommands.define_caller(_content, _c, _sheets):
            pass
        else:
            await _author.send("Term could not be found.")

    elif _content.startswith(("!download", "?download")):
        await botcommands.download_caller(_content, _c, _sheets)

    elif _content.startswith(("!website", "?website")):
        await botcommands.website_caller(_content, _c, _sheets)

    elif _content.startswith(("!about", "?about")):
        await botcommands.about_caller(_content, _c, _sheets)

    elif _content.lower().startswith("when is my next class? "):
        await ctx.send(await botcommands.class_caller(_content, _c))

    elif _content.lower().startswith(("?what is ", "!what is")):
        await _author.send(embed=await botcommands.whatis_caller(_content, _c, _sheets))

    elif _content.lower().startswith(("!get example ", "?get example ")):
        await botcommands.example_caller(_content, _c, _sheets)

    elif _content.lower().startswith(("!list examples", "?list examples")):
        _all_ex = list(Utilities.ExamplesRead()().keys())
        await _c.send("```\n" + "\n".join(_all_ex) + "```")

    elif _content.lower().startswith(("!show ", "?show ")):
        await botcommands.showimage_caller(_content, _c, _sheets)

    elif _content.lower().startswith("?grade "):
        await botcommands.grade_caller(_content, _author)

    elif _content.lower().startswith(("?cwc ", "!cwc ")):
        await botcommands.cwc_caller(_content, _c, _sheets)

    elif _content.lower().startswith(("?troubleshooting ", "!troubleshooting ", "?troubleshoot ", "!troubleshoot ")):
        await botcommands.troubleshoot_caller(_content, _c, _sheets)

    elif _content.lower().startswith(("!h", "?h")):
        await botcommands.help_caller(_content, _c, _sheets)

    else:
        await client.process_commands(msg)

    if msg.content.startswith(("!", "?")):
        if msg.content.count("!") == 1 or msg.content.count("?") == 1:
            if _checkmsg.dm_check(msg):
                pass
            elif _checkmsg.non_bot(msg):
                _tempmsg = await _c.send("Deleting messages in 3 seconds...")
                await asyncio.sleep(3)
                await msg.delete()
                await _tempmsg.delete()


@client.command(name="addinstructor", pass_context=True)
async def addinstructor(ctx):
    _msg = ctx.message.content.split("addinstructor ")[1]
    _name = _msg.split(" ")[0]
    _link = " ".join(_msg.split(" ")[1:])
    if await test_instructor(ctx):
        Utilities.LinkWrite(_location="Instructors", _name=_name, _example=_link)()

    else:
        await not_instructor(ctx)


@client.command(name="addexample", pass_context=True)
async def addexample(ctx):
    _msg = ctx.message.content.split("addexample ")[1]
    _name = _msg.split(" ")[0]
    _example = " ".join(_msg.split(" ")[1:])
    if await test_instructor(ctx):
        Utilities.ExamplesWrite(_name=_name, _example=_example)()

    else:
        await not_instructor(ctx)


@client.command(name="addlink", pass_context=True)
async def addlink(ctx):
    _msg = ctx.message.content.split("addlink ")[1]
    _location, _name, _link = _msg.split(" ")
    if await test_instructor(ctx):
        Utilities.LinkWrite(_location=_location, _name=_name, _example=_link)()

    else:
        await not_instructor(ctx)


@client.command(name="remlink", pass_context=True)
async def remlink(ctx):
    _msg = ctx.message.content.split("remlink ")[1]
    _location, _name = _msg.split(" ")
    if await test_instructor(ctx):
        Utilities.LinkPop(_location=_location, _name=_name)()

    else:
        await not_instructor(ctx)


@client.command(name="numberusers", aliases=["usercount", "countuser", "numberuser"], pass_context=True)
async def countthem(ctx):
    _server = ctx.guild
    _cnt = _server.member_count
    if await test_instructor(ctx):
        await ctx.channel.send("There are {0} users in this server.".format(_cnt))

    else:
        await not_instructor(ctx)


@client.command(name="version", pass_context=True)
async def version(ctx):
    _ver = Utilities.SettingsRead()()['VERSION']
    await ctx.author.send("Bot is running software version: {0}".format(_ver))


async def not_instructor(ctx):
    _msg = await ctx.channel.send("You do not have permissions to use this command.")
    await asyncio.sleep(3)
    await _msg.delete()

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
