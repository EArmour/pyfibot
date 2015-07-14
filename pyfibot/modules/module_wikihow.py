# -*- coding: utf-8 -*-

import json, requests

def command_how(bot, user, channel, args):
    """".how (times) - Gives you random instructions from wikiHow, by default 3 steps"""
    if args:
        try:
            times = int(args) if int(args) < 11 else 3
        except:
            times = 3
    else:
        times = 3

    q = bot.get_url("http://bifrost.me/api/steps?count=%s" % times)
    parsed = q.json()

    for i in range(0, times):
        bot.say(channel, "Step %d: %s" % (i + 1, parsed[str(i + 1)]))
