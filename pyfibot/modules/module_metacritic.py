# -*- coding: utf-8 -*-

import urllib2
from bs4 import BeautifulSoup


def command_score(bot, user, channel, args):
    game = args.replace(' ','+')
    page = urllib2.urlopen("http://www.metacritic.com/search/all/%s/results" % game).read()
    bs = BeautifulSoup(page)
    
    scoretag = bs.find(class_ = "metascore_w")
    score = scoretag.text
    titletag = scoretag.previous_sibling.previous_sibling
    title = titletag.contents[0].text
    
    bot.say(channel, "MetaCritic: %s -- Avg Score %s" % (title, score))