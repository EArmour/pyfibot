# -*- coding: utf-8 -*-

import urllib2
from bs4 import BeautifulSoup


def command_urban(bot, user, channel, args):
    term = args.replace(' ', '+')
    page = urllib2.urlopen("http://www.urbandictionary.com/define.php?term=%s" % term).read()
    bs = BeautifulSoup(page)

    wordtag = bs.find(class_="word")
    try:
        word = wordtag.text
    except AttributeError:
        bot.say(channel, "No definition found for term \"%s\"" % args)

    deftag = bs.find(class_="meaning")
    definition = deftag.text

    bot.say(channel, "%s: %s" % (word, definition))