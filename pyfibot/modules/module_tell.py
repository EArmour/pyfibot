# -*- coding: utf-8 -*-
import logging, json, os, sys
from datetime import datetime
from util import getnick

log = logging.getLogger('tell')
tells = []

def init(bot):
    global tells

    with open(os.path.join(sys.path[0], 'modules', 'module_tell_messages.json')) as tellfile:
        tells = json.load(tellfile)

def command_tell(bot, user, channel, args):
    """.tell [nick] [message] - Instructs the bot to relay a message to a user when they next join the channel"""
    global tells
    splut = args.split(' ', 1)

    if len(splut) < 2:
        bot.say(channel, "You must provide both a username and a message!")
        return

    nick = splut[0]
    fnick = getnick.get(user)

    tells.append({'to': nick,
                  'from': fnick,
                  'channel': channel,
                  'message': splut[1]})

    bot.say(channel, "%s: I will tell that to %s next time I see him!" % (fnick, nick))

    with open(os.path.join(sys.path[0], 'modules', 'module_tell_messages.json'), 'w') as tellfile:
        json.dump(tells, tellfile, indent=2)


def command_ptest(bot, user, channel, args):
    bot.say(channel, bot.who)


def handle_userJoined(bot, user, channel):
    check_messages(bot, user)


def handle_userRenamed(bot, oldnick, newnick):
    check_messages(bot, newnick)


def check_messages(bot, user):
    global tells
    nick = getnick.get(user).lower()

    found = False
    for i, tell in enumerate(tells):
        if tell["to"].lower() == nick:
            bot.say(str(tell["channel"]), "%s: Hey, %s says: %s" % (tell["to"], tell["from"], tell["message"]))
            tells.remove(tell)
            found = True

    if found:
        with open(os.path.join(sys.path[0], 'modules', 'module_tell_messages.json'), 'w') as tellfile:
            json.dump(tells, tellfile, indent=2)