# -*- coding: utf-8 -*-
"""
Roll stuff!
"""

import random as rand


def command_roll(bot, user, channel, args):
    if args == "coin":
        result = rand.randrange(0,2)
        if result is 1:
            txt = "Heads!"
        else:
            txt = "Tails!"
        return bot.say(channel, txt)
    else:
        params = args.replace('D','d').split('d')
         
    count = int(params[0])
    sides = int(params[1])
    
    if count > 30:
        return bot.say(channel, "Don't be dumb, %s" % getNick(user))
    
    results = []
    total = 0
    
    for i in range(count):
        result = rand.randrange(1,sides+1)
        results.append(result)
        total += result

    bot.say(channel, "%s D%s: %s = %s" % (count, sides, str(results), str(total)))