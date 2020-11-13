#!/usr/bin/env python3

import os
import time
import datetime
import json
import asyncio
import discord
from discord.ext import commands
from discord import Embed
from Communications import comm, classroomComm
from globalVars import *
from Documents.documentation import *

# Client
Client = discord.Client()

# Prefix for bots commands
bot_prefix = 'ivr '
client = commands.Bot(command_prefix=bot_prefix)
bot_channel = 772649542818463744  # #bot-channel
bot_logger = 772639596286050324  # #bot-log
rules_channel = 772633892783390780  # #rules

# TODO: Clean up this code to make it more friendly. We want the very best, clean code to reference and dissect.


@client.event
async def on_ready() -> None:
    """
    When it boots, we will clear the chat AND print back information in the
    console regarding our bot.

    :return:
    """

    global bot_channel
    global bot_logger
    global rules_channel

    # RE-INSTANTIATE THE CHANNEL ITSELF AS A CHANNEL, NOT AN INT
    bot_channel = client.get_channel(bot_channel)
    bot_logger = client.get_channel(bot_logger)
    rules_channel = client.get_channel(rules_channel)

    classes = classroomComm.CourseInfo().roster()
    if DEBUG:
        print(classes)

    utc = str(datetime.datetime.utcnow()).split('.')[0]
    info_to_print = """
```
Bot Online!
Name:     {0}
ID:       {1}
Booted:   {2} UTC

Google Classroom API
====================
Available courses ({3}):
{4}
```
""".format(client.user.name, client.user.id, utc, classes[0], classes[1])
    await bot_channel.send(info_to_print)
    if DEBUG:
        print(info_to_print)


@client.event
async def on_message(msg) -> None:
    """
    When a message is sent, react...

    :param msg: Passed message in dictionary format.
    :return:
    """

    _message = msg                                  # Raw message
    message_channel = msg.channel                   # Messages channel
    message_attachments = msg.attachments           # Any attachments added to message
    message_author = msg.author                     # Messages author
    message_owner = msg.author.id                   # Messages author ID
    message = msg.content                           # Content of the message (str)
    guild = _message.guild                          # This was easier than expected... >_> gets the discord server name

    # Determine that the message was not sent by the bot...
    if message_author != client.user and message.startswith('ivr '):
        message = message.split("ivr ")[1]

        # Send the message through the bot.
        await comm.bot_send_message(
            orig_msg=_message, msg="{0}".format(message),
            chl=message_channel, bot_chl=bot_logger,
            author=message_author
        )

    # Post the rules
    elif message_author != client.user and message.startswith('!rules'):
        await comm.bot_send_message(
            orig_msg=_message, msg=RULES,
            chl=rules_channel, bot_chl=bot_channel
        )

    # Pong bot in whichever channel it was pinged in. Add milliseconds.
    elif message == 'ping':
        before = time.monotonic()
        message = await message_channel.send("Pong!")

        # Calculate the ping time.
        _ping = int(round((time.monotonic() - before) * 1000, 6))
        await comm.bot_send_message(
            orig_msg=message, msg="Pong!  `{0} ms`".format(_ping),
            chl=message_channel
        )

        if DEBUG:
            print("Ping {0} ms".format(_ping))

    # Clear the channel this was posted in.
    elif message.startswith('empty channel'):
        _m = list()
        _amount = message.split('empty channel')[1]
        if _amount == "":
            _amount = 100
        else:
            _amount = int(_amount)
        deleted = await message_channel.purge(limit=_amount)
        _what_to_send = 'Deleted {0} message(s) from {1}.'.format(len(deleted), message_channel)
        _m.append(await message_channel.send(_what_to_send))
        if DEBUG:
            print("Attempting to delete {0} messages...".format(_amount))
            print(_what_to_send)

        await comm.delete_messages(messages=_m, channel=message_channel)

    # Directly message user that pinged for help, with information.
    elif message == 'help':
        hello = """
```
Hello {0},

Welcome to {1}! This is the {1} Bot. If you require
a particular role, please ask the staff for that
role. I am here to offer information if needed.

• AltSpace events are every 4:00 P.M. EST on Sat.,
• Office hours are at 12:00 P.M. - 1:00 P.M. on Sat.,
• If you require office hour earlier in the week,
  contact one of the instructors for assistance.
```
""".format(message_author, guild)
        await message_author.send(hello)
        await comm.bot_send_message(
            orig_msg=_message, msg="Sending help inquiry to... {0}.".format(message_author),
            chl=bot_logger
        )
        if DEBUG:
            print("\nSending direct message to... {0}.".format(message_author))

    # Attain information and send the information to the user requesting it.
    elif message.lower().startswith("when is my next class?"):
        # When is my next class? [class name]
        # Perhaps we can get the class names, request an input, then type it out... Maybe better naming conventions
        # For the class names should be put in order...?
        _class_name = message.split("? ")[1]
        _work = classroomComm.CourseInfo().get_class_work(_class_name)

        # Perhaps... Separate the code below into a method elsewhere...? Let's ponder about what can be reused here...
        _week = list(_work.keys())[0]
        if _week != 'Complete':
            _assignments = list(_work[_week].keys())
            _final_info = convert_to_output(week=_week, assignments=_work[_week])

        else:
            _final_info = "\nYou've completed this class.\n"

        await message_author.send(_final_info)
        try:
            await comm.bot_send_message(
                orig_msg=_message, msg="Send week schedule to {0}.".format(message_author),
                chl=bot_logger
            )

        # If a user has messaged the bot directly... Just pass the error.
        except discord.errors.Forbidden:
            pass

    elif message == "list classes":
        classroomComm.main()


def convert_to_output(week=str(), assignments=None) -> str:
    """
    Convert the passed information and turn it into a document to send back to the user

    :param week: Which week is next.
    :param assignments: The dictionary of assignments due.
    :return:
    """

    # assignments = _work[week]
    names = list(assignments.keys())
    num_asgnmnts = len(names)
    i = 1
    months = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December"
    }

    formatted_doc = list()
    formatted_doc.append("**{0}**".format(week))
    while i <= num_asgnmnts:
        assignment = names[i-1]
        date = assignments[assignment][0].split("-")
        _formatted_date = "{0} {1}, {2}".format(months[int(date[1])], resolve_suffix(int(date[2])), date[0])
        _assign = """
Assignment {0})
    - {1}
    - Due: {2}
    - Link: _{3}_
""".format(i, assignment, _formatted_date, assignments[assignment][1])
        formatted_doc.append(_assign)
        i += 1

    doc = "".join(formatted_doc)

    return doc


def resolve_suffix(number=int()) -> str:
    """
    Pass a number and get the correct suffix attached to it and return said number

    :param number: pass an integer
    :return:
    """
    number_suffix = ["th", "st", "nd", "rd"]

    if number % 10 in [1, 2, 3] and number not in [11, 12, 13]:
        return "{0}{1}".format(number, number_suffix[number % 10])
    else:
        return "{0}{1}".format(number, number_suffix[0])

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
    json_path = 'I:\\IVR_token.json'
    if not os.path.isfile(json_path):
        json_path = 'C:\\Users\\jeff3\\Desktop\\IVR_token.json'
else:
    json_path = '/usr/bin/IVR_token.json'

# Launch our bot
with open(json_path, 'r') as f:
    token = json.load(f)

loop = asyncio.get_event_loop()
loop.run_until_complete(client.start(token['token']))  # client.run(token['token'])
