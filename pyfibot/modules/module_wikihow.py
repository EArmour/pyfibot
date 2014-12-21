# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup as bs4
import re, random, requests

def command_how(bot, user, channel, args):
    """".how (times) - Gives you random instructions from wikiHow, by default 3 steps"""
    if args:
        try:
            times = args if int(args) < 11 else 3
        except:
            times = 3
    else:
        times = 3

    steps = [None] * times

    for i in range(0, times):
        page = bs4(requests.get("http://www.wikihow.com/Special:Randomizer").text)

        stepsection = page.find("div", {"id": "steps"})
        if stepsection: # Only one 'method'
            allsteps = stepsection.find("ol").findChildren("li", recursive = False)
        else: # Multiple 'methods', each with their own list of steps
            for x in range(1, 5):
                try:
                    stepsection  = page.find("div", {"id": "steps_%d" % x})
                    try:
                        # Possible for a Method to have no actual steps, just a paragraph, so check for the list
                        allsteps = stepsection.find("ol").findChildren("li", recursive = False)
                        break
                    except:
                        continue
                except:
                    break

        steps[i] =  str(allsteps[random.randint(0, len(allsteps) - 1)]).decode('utf-8')

    for i, step in enumerate(steps):
        step = bs4(step)
        boldtag = step.find("b", {"class": "whb"})
        boldtext = boldtag.text
        bot.say(channel, "Step %d: %s" % (i + 1, boldtext))
