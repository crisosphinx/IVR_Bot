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

# Client
Client = discord.Client()

# Prefix for bots commands
bot_prefix = 'ivr '
client = commands.Bot(command_prefix=bot_prefix)
bot_channel = 772649542818463744  # #bot-channel
rules_channel = 772633892783390780  # #rules

SEND_SPECIFIC = """
```
Welcome to Universe!

We are an online institution for mentoring, instructing and
teaching students on the aspects of 3D Game Design and
Development utilizing Unity!


We offer the following programs, which are ever evolving as we grow larger:

• Introduction to Unity,
• AltSpace World Building with Unity,
• Virtual Reality Application Development,
• [More coming soon],




Please follow the following rules when part of this server:

»  This is a place of respect, please
   respect the wishes of other users.

»  Harassment, Discrimination of any 
   sort, Sexism, Excessive Immaturity,
   Abrasive Behavior and Toxicity are
   not tolerated. 

»  Constructive criticism (critique) is
   key to a happy experience, criticism
   in the non-constructive way will not
   be tolerated.

»  If a user asks you to stop, or asks
   you to change topic, please do so.
   Try to keep this place comfortable
   for everyone. Remember, behind the
   computer screen is a person!

»  Do not advertise other servers. You
   may only advertise the server if it
   has been give the "okay" by staff.

»  In order to view content on this server,
   you must be assigned any role. Roles are
   added after you have been added to the
   class roster.

»  No memes unless otherwise prompted.

»  All nicknames must be mentionable.
   Please follow the following format:
   [Your name] / [AltSpace Username]
   EX. Jeff / Criso

»  In terms of NSFW content on this server,
   please do not post any of it - this includes
   in developing your games, applications, etc. 
```
"""


@client.event
async def on_ready():
    """
    When it boots, we will clear the chat AND print back information in the
    console regarding our bot.

    :return:
    """

    global bot_channel
    global rules_channel

    # RE-INSTANTIATE THE CHANNEL ITSELF AS A CHANNEL, NOT AN INT
    bot_channel = client.get_channel(bot_channel)
    rules_channel = client.get_channel(rules_channel)

    classes = classroomComm.main()
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
async def on_message(msg):
    _message = msg
    message_channel = msg.channel
    message_attachments = msg.attachments
    message_author = msg.author
    message_owner = msg.author.id
    message = msg.content
    guild = _message.guild  # this was easier than expected... >_>

    if message_author != client.user and message.startswith('ivr '):
        message = message.split("ivr ")[1]
        await comm.bot_send_message(
            orig_msg=_message, msg="{0}".format(message),
            chl=message_channel, bot_chl=bot_channel,
            author=message_author
        )

    elif message_author != client.user and message.startswith('!rules'):
        await comm.bot_send_message(
            orig_msg=_message, msg=SEND_SPECIFIC,
            chl=rules_channel, bot_chl=bot_channel
        )

    elif message == 'ping':
        before = time.monotonic()
        message = await message_channel.send("Pong!")
        _ping = int(round((time.monotonic() - before) * 1000, 6))
        await comm.bot_send_message(
            orig_msg=message, msg="Pong!  `{0} ms`".format(_ping),
            chl=message_channel
        )

        if DEBUG:
            print("Ping {0} ms".format(_ping))

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
        if DEBUG:
            print("\nSending direct message to... {0}.".format(message_author))

    elif message.lower().startswith("when is my next class?"):
        # Do stuff
        _class_name = message.lower().split(message.lower())[1]
        # classroomComm.getNextClassSessionDate()
        # classroomComm.getNextClassWork()
        classroomComm.CourseInfo().query_info(_class_name)

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
loop.run_until_complete(client.start(token['token']))
# client.run(token['token'])
