#!/usr/bin/env python3

import re
from discord import Embed
from discord.ext import commands
from Documents.formatter import *
from Platform import Utilities, GoogleComm
import textwrap
import MessageChecker


# Prefix for bot
client = commands.Bot(command_prefix=Utilities.SettingsRead()()['CALLS'])


def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def restructure(_long_str: str, _amt: int) -> list:
    r = re.compile("[^\n]+")
    got = r.findall(_long_str)
    _ret = list()
    for item in chunker(got, _amt):
        _ret.append("\n".join(item))
    return _ret


async def website_caller(_content, _c, _sheets):
    _web = Utilities.LinkRead()()["Websites"]
    _get = "".join(_content.split(" ")[1:])
    if _get.lower() == "list":
        await _c.send("```\n" + "\n".join(list(_web.keys())) + "```")
    else:
        for _each in list(_web.keys()):
            if _get.lower() == _each.lower():
                if (
                        "Intro" in _each or "Compendium" in _each or
                        "RecommendedPrograms" in _each or "Documentation" in _each or
                        "ComputerRecommendations" in _each
                ):
                    _website = "https://docs.google.com/document/d/{0}".format(_web[_each])
                else:
                    _website = _web[_each]
                embed = Embed()
                embed.url = _website
                embed.title = _each
                embed.description = "Website link for {0}.".format(_each)
                await _c.send(embed=embed)
                _sheets.updatevalue(name=_each)


async def about_caller(_content, _c, _sheets):
    _teach = Utilities.LinkRead()()["Instructors"]
    _get = "".join(_content.split(" ")[1:])
    if _get.lower() == "list":
        await _c.send("```\n" + "\n".join(list(_teach.keys())) + "```")
    else:
        for _each in list(_teach.keys()):
            if _get.lower() == _each.lower():
                _website = _teach[_each]
                embed = Embed()
                embed.url = _website
                embed.title = _each
                embed.description = "Website link for {0}.".format(_each)
                await _c.send(embed=embed)
                _sheets.updatevalue(name=_each)


async def class_caller(_content, _c) -> str:
    _classname = _content.split("when is my next class? ")[1]
    _work = GoogleComm.AttainGoogleClass(_classname)()
    # Perhaps... Separate the code below into a method elsewhere...? Let's ponder about what can be reused here...
    _week = list(_work.keys())[0]
    if _week != 'Complete':
        _assignments = list(_work[_week].keys())
        _final_info = convert_to_output(week=_week, assignments=_work[_week])

    else:
        _final_info = "\nYou've completed this class.\n"

    return _final_info


async def whatis_caller(_content, _c, _sheets) -> Embed:
    _word = _content.split("what is ")[1]
    _info = Utilities.DefineWord()(_word)
    embed = Embed()
    embed.title = _info[0]
    embed.url = _info[1]
    embed.description = "Definition of {0}.".format(_info[0])
    for each in list(_info[2].keys()):
        if len(_info[2][each]) > 0:
            embed.add_field(name=each, value=" - " + "\n - ".join(_info[2][each]), inline=True)

    _sheets.updatevalue(name=_word)
    return embed


async def download_caller(_content, _c, _sheets):
    if "Unity" in _content:
        _get = _content.split(" ")[2:]
        _year = str()
        _os = str()
        for each in _get:
            if each.isdigit():
                _year = each
            else:
                _os = each
        _download = Utilities.GetLatestUnityInstaller(_os, _year)()
        embed = Embed()
        embed.url = _download[1]
        embed.title = " ".join(_content.split(" ")[1:])
        embed.description = f"Download link to Unity version {_download[0]} for {_os}."
        await _c.send(embed=embed)
    else:
        _dls = Utilities.LinkRead()()["Downloads"]
        _get = "".join(_content.split(" ")[1:])
        if _get.lower() == "list":
            await _c.send("```\n" + "\n".join(list(_dls.keys())) + "```")
        else:
            for _each in list(_dls.keys()):
                if _get.lower() in _each.lower():
                    _download = _dls[_each]
                    if "." in _get:
                        _year, _edition, _type = _each.split(".")
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
                        embed.title = _each
                        embed.description = "Download link to {0}.".format(_each)
                    await _c.send(embed=embed)
                    _sheets.updatevalue(name=_each)


async def example_caller(_content, _c, _sheets):
    _get_example = _content.split("get example ")[1].replace(" ", "")
    _ex = Utilities.GetRandomExample()(_get_example)
    if _ex:
        _embed = Embed()
        _embed.title = _get_example
        _embed.description = _ex
        await _c.send(embed=_embed)
    _sheets.updatevalue(name=_get_example)


async def define_caller(_content, _c, _sheets):
    _msg = _content.split("def ")[1].replace(" ", "")
    _return = Utilities.DefinitionUnity(_msg)(True)
    if _return:
        second_sent = False
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

        lines = textwrap.wrap(_return[2], 2048, break_long_words=False)
        _first_message.description = lines[0]

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
                        if len(lines) > 1 and not second_sent:
                            _first_message.description = lines[1]
                            second_sent = True
                        else:
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
                        if len(lines) > 1 and not second_sent:
                            _first_message.description = lines[1]
                            second_sent = True
                        else:
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
                        if len(lines) > 1 and not second_sent:
                            _first_message.description = lines[1]
                            second_sent = True
                        else:
                            _first_message.description = "..."

        _sheets.updatevalue(name=_return[0])
        return True


async def grade_caller(_content, _author):
    _info = _content.split("grade ")[1]
    await _author.send("Please enter name as it appears in Google Classroom: ")
    _name = await client.wait_for("message", check=MessageChecker.CheckMsg().non_bot)
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


async def showimage_caller(_content, _c, _sheets):
    _info = _content.split(" ")[1].replace(" ", "")
    _images = Utilities.LinkRead()()['Images']
    if _info.lower() == "list":
        await _c.send("```\n" + "\n".join(list(_images.keys())) + "```")

    else:
        for _each in _images.keys():
            if _info.lower() == _each.lower():
                _embed = Embed()
                _embed.set_image(url=_images[_each])
                _embed.title = "Instructions"
                await _c.send(embed=_embed)
                _sheets.updatevalue(name=_each)


async def cwc_caller(_content, _c, _sheets):
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
                _sheets.updatevalue(name=_each)


async def troubleshoot_caller(_content, _c, _sheets):
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
                _sheets.updatevalue(name=_each)


async def help_caller(_content, _c, _sheets):
    if len(_content.split("h")[1]) == 0:
        _all_cmds = """
    ?/!h [command name]
    ?/!troubleshooting / ?/!troubleshoot [name]
    ?/!cwc [list / name]
    ?grade [class name]
    ?/!show [name]
    ?/!list examples
    ?/!get example [name]
    ?/!what is [word]
    ?/!def [C# term]
    ?/!about [instructor]
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
        await _c.send("```{0}```".format(_all_cmds))

        _doc = Utilities.LinkRead()()["Websites"]["Documentation"]
        _website = "https://docs.google.com/document/d/{0}".format(_doc)
        embed = Embed()
        embed.url = _website
        embed.title = "Documentation for Bot"
        embed.description = "Website link for {0}.".format("Documentation")
        await _c.send(embed=embed)

    else:
        _get_word = _content.split("h ")[1]
        _sheets.updatevalue(name=_get_word)
        if _get_word.lower() == "h":
            await _c.send(
                "```{0} can help you with any specific command or relaying all commands to you.```".format(
                    _get_word
                )
            )

        elif _get_word.lower() in ("troubleshooting", "troubleshoot"):
            await _c.send(
                "```{0} takes exactly one argument. ".format(_get_word) +
                "Please type the associated troubleshoot you require.\n- {0}```".format(
                    "\n- ".join(list(Utilities.LinkRead()()["Troubleshooting"].keys()))
                ))

        elif _get_word.lower() == "cwc":
            await _c.send(
                "```{0} takes exactly one argument. ".format(_get_word) +
                "Please type the associated course you require.\n- {0}```".format(
                    "\n- ".join(list(Utilities.LinkRead()()["CreateWCode"].keys()))
                ))

        elif _get_word.lower() == "grade":
            await _c.send(
                "```{0} takes exactly one argument. Please add your course name.```".format(_get_word))

        elif _get_word.lower() == "show":
            await _c.send(
                "```{0} takes exactly one argument. Please specify one of the following images.\n- {1}```".format(
                    _get_word,
                    "\n- ".join(list(Utilities.LinkRead()()["Images"].keys()))
                ))

        elif _get_word.lower() == "list examples":
            await _c.send(
                "```{0} will list all examples to query from.```".format(_get_word)
            )

        elif _get_word.lower() == "get example":
            await _c.send(
                "```{0} takes exactly one argument. Please specify the example you wish to get!\n- {1}```".format(
                    _get_word,
                    "\n- ".join(list(Utilities.ExamplesRead()().keys()))
                )
            )

        elif _get_word.lower() == "what is":
            await _c.send(
                "```{0} takes exactly one argument. ".format(_get_word) +
                "Please specify any word that you wish to get the definition of.```"
            )

        elif _get_word.lower() == "def":
            await _c.send(
                "```{0} takes exactly one argument. You need to specify the C# term you need clarified.```".format(
                    _get_word
                )
            )

        elif _get_word.lower() == "about":
            await _c.send(
                "```{0} takes exactly one argument. ".format(_get_word) +
                "You need to specify the instructor to learn about:\n- {0}```".format(
                    "\n- ".join(list(Utilities.LinkRead()()["Instructors"].keys()))
                )
            )

        elif _get_word.lower() == "website":
            await _c.send(
                "```{0} takes exactly one argument. ".format(_get_word) +
                "You need to specify the website you with to go to.\n- {0}```".format(
                    "\n- ".join(list(Utilities.LinkRead()()["Websites"].keys()))
                )
            )

        elif _get_word.lower() == "download":
            await _c.send(
                "```{0} takes exactly one argument.".format(_get_word) +
                "You need to specify the download you want.\n- {0}```".format(
                    "\n- ".join(list(Utilities.LinkRead()()["Downloads"].keys()))
                )
            )
