#!/usr/bin/env python3

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
            _c = await retrieve_channel(ctx, "bot-channel")
        else:
            _c = _author

    if _content.lower().startswith(("?def", "!def")):
        _msg = _content.split("def ")[1].replace(" ", "")
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
        if _get.lower() == "list":
            await _c.send("```\n" + "\n".join(list(_dls.keys())) + "```")
        else:
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
        if _get.lower() == "list":
            await _c.send("```\n" + "\n".join(list(_web.keys())) + "```")
        else:
            for each in list(_web.keys()):
                if _get.lower() == each.lower():
                    if "Intro" in each or "Compendium" in each or "RecommendedPrograms" in each or "Documentation" in each:
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
        if _get.lower() == "list":
            await _c.send("```\n" + "\n".join(list(_teach.keys())) + "```")
        else:
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

    elif _content.lower().startswith(("?what is ", "!what is")):
        _word = _content.split("what is ")[1]
        _info = Utilities.DefineWord()(_word)
        embed = Embed()
        embed.title = _info[0]
        embed.url = _info[1]
        embed.description = "Definition of {0}.".format(_info[0])
        for each in list(_info[2].keys()):
            if len(_info[2][each]) > 0:
                embed.add_field(name=each, value=" - " + "\n - ".join(_info[2][each]), inline=True)

        await _author.send(embed=embed)

    elif _content.lower().startswith(("!get example ", "?get example ")):
        _get_example = _content.split("get example ")[1].replace(" ", "")
        _ex = Utilities.GetRandomExample()(_get_example)
        if _ex:
            _embed = Embed()
            _embed.title = _get_example
            _embed.description = _ex
            await _c.send(embed=_embed)

    elif _content.lower().startswith(("!list examples", "?list examples")):
        _all_ex = list(Utilities.ExamplesRead()().keys())
        await _c.send("```\n" + "\n".join(_all_ex) + "```")

    elif _content.lower().startswith(("!show ", "?show ")):
        _info = _content.split(" ")[1].replace(" ", "")
        _images = Utilities.LinkRead()()['images']
        if _info.lower() == "list":
            await _c.send("```\n" + "\n".join(list(_images.keys())) + "```")

        else:
            for _each in _images.keys():
                if _info.lower() == _each.lower():
                    _embed = Embed()
                    _embed.set_image(url=_images[_each])
                    _embed.title = "Instructions"
                    await _c.send(embed=_embed)

    elif _content.lower().startswith("?grade "):
        _info = _content.split("grade ")[1]
        await _author.send("Please enter name as it appears in Google Classroom: ")
        _name = await client.wait_for("message", check=CheckMsg().non_bot)
        # _get_grades = GoogleComm.AttainGoogleClass(_classname=_info).grades(_name.content)
        _get_grades = GoogleComm.ThreadClass(_info, _name.content)
        _get_grades.daemon = True
        _get_grades.start()
        _get_grades.join()
        _results = _get_grades.results
        for _assignment in _results[_name.content]:
            _assignment_name = list(_assignment.keys())[0]
            _embed = Embed()
            _embed.title = _assignment_name
            _embed.url = _assignment[_assignment_name][1]
            _embed.description = _assignment[_assignment_name][0]
            await _author.send(embed=_embed)

    elif _content.lower().startswith(("?cwc ", "!cwc ")):
        _cwc = Utilities.LinkRead()()["CreateWCode"]
        _info = "".join(_content.split(" ")[1:])
        if _info.lower() == "list":
            await _c.send("```\n" + "\n".join(list(_cwc.keys())) + "```")
        else:
            for _each in _cwc.keys():
                if _info.lower() == _each.lower():
                    _embed = Embed()
                    _embed.title = "Create With Code Course: {0}".format(_each)
                    _embed.url = _cwc[_each]
                    _embed.description = "Link to the {0} course.".format(_info)
                    await _c.send(embed=_embed)

    elif _content.lower().startswith(("?troubleshooting ", "!troubleshooting ", "?troubleshoot ", "!troubleshoot ")):
        _trbl = Utilities.LinkRead()()["Troubleshooting"]
        _info = " ".join(_content.split(" ")[1:])
        if _info.lower() == "list":
            await _c.send("```\n" + "\n".join(list(_trbl.keys())) + "```")
        else:
            for _each in _trbl.keys():
                if _info.lower() == _each.lower():
                    _embed = Embed()
                    _embed.title = _each
                    _embed.url = _trbl[_each]
                    _embed.description = "Link to the troubleshooting for: {0}.".format(_info)
                    await _c.send(embed=_embed)

    elif _content.lower().startswith(("!help", "?help")):
        if len(_content.split("help")[1]) == 0:
            _all_cmds = """
? help
?/!troubleshooting / ?/!troubleshoot [name]
?/!cwc [list / name]
?grade [class name]
?/!show [name]
?/!list examples
?/!get example [name]
?/!what is [word]
?/!def [C# term]
?/!about
?/!website [list / name]
?/!download [list / name]
when is my next class? [class name]

----  ----  ----  ----  ----  ----  ----
!ivr addinstructor
!ivr addexample
!ivr remlink
!ivr numberusers / usercount / countuser / numberuser
!ivr version
"""
            await _author.send("```{0}```".format(_all_cmds))

            _doc = Utilities.LinkRead()()["Documentation"]
            _website = "https://docs.google.com/document/d/{0}".format(_doc)
            embed = Embed()
            embed.url = _website
            embed.title = "Documentation for Bot"
            embed.description = "Website link for {0}.".format("Documentation")
            await _author.send(embed=embed)

        else:
            _get_word = _content.split("help ")[1]
            if _get_word.lower() == "help":
                await _author.send("{0} can help you with any specific command or relaying all commands to you.".format(
                    _get_word
                ))

            elif _get_word.lower() in ("troubleshooting", "troubleshoot"):
                await _author.send(
                    "{0} takes exactly one argument. Please type the associated troubleshoot you require.\n- {1}".format(
                        _get_word,
                        "\n- ".join(list(Utilities.LinkRead()()["Troubleshooting"].keys()))
                    ))

            elif _get_word.lower() == "cwc":
                await _author.send(
                    "{0} takes exactly one argument. Please type the associated course you require.\n- {1}".format(
                        _get_word,
                        "\n- ".join(list(Utilities.LinkRead()()["CreateWCode"].keys()))
                    ))

            elif _get_word.lower() == "grade":
                await _author.send(
                    "{0} takes exactly one argument. Please add your course name.".format(_get_word))

            elif _get_word.lower() == "show":
                await _author.send(
                    "{0} takes exactly one argument. Please specify one of the following images.\n- {1}".format(
                        _get_word,
                        "\n- ".join(list(Utilities.LinkRead()()["Images"].keys()))
                    ))

            elif _get_word.lower() == "list examples":
                await _author.send(
                    "{0} will list all examples to query from.".format(_get_word)
                )

            elif _get_word.lower() == "get example":
                await _author.send(
                    "{0} takes exactly one argument. Please specify the example you wish to get!\n- {1}".format(
                        _get_word,
                        "\n- ".join(list(Utilities.ExamplesRead()().keys()))
                    )
                )

            elif _get_word.lower() == "what is":
                await _author.send(
                    "{0} takes exactly one argument. " +
                    "Please specify any word that you wish to get the definition of.".format(
                        _get_word
                    )
                )

            elif _get_word.lower() == "def":
                await _author.send(
                    "{0} takes exactly one argument. You need to specify the C# term you need clarified.".format(
                        _get_word
                    )
                )

            elif _get_word.lower() == "about":
                await _author.send(
                    "{0} takes exactly one argument. You need to specify the instructor to learn about:\n- {1}".format(
                        _get_word,
                        "\n- ".join(list(Utilities.LinkRead()()["Instructors"].keys()))
                    )
                )

            elif _get_word.lower() == "website":
                await _author.send(
                    "{0} takes exactly one argument. You need to specify the website you with to go to.\n- {1}".format(
                        _get_word,
                        "\n- ".join(list(Utilities.LinkRead()()["Websites"].keys()))
                    )
                )

            elif _get_word.lower() == "download":
                await _author.send(
                    "{0} takes exactly one argument. You need to specify the download you want.\n- {1}".format(
                        _get_word,
                        "\n- ".join(list(Utilities.LinkRead()()["Downloads"].keys()))
                    )
                )

    else:
        await client.process_commands(msg)

    if msg.content.startswith(("!", "?")):
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
