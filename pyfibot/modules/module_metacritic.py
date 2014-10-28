# -*- coding: utf-8 -*-

import urllib2
from bs4 import BeautifulSoup


def command_score(bot, user, channel, args):
    game = args.replace(' ', '+')

    req = urllib2.Request("http://www.metacritic.com/search/all/%s/results" % game)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:33.0) Gecko/20100101 Firefox/33.0')
    req.add_header('Host', 'www.metacritic.com')

    page = urllib2.urlopen(req).read()
    bs = BeautifulSoup(page)
    
    scoretag = bs.find(class_="metascore_w")
    try:
        score = scoretag.text
        titletag = bs.find(class_="product_title")
        title = titletag.text

        bot.say(channel, "Metacritic: %s -- Avg Score %s" % (title, score))
    except:
        bot.say(channel, "Couldn't find any Metacritic score for '%s'" % args)