# -*- coding: utf-8 -*-
"""
Gets appox TF2 backpack value (probably wildy inaccurate!)
"""

import urllib

from bs4 import BeautifulSoup as bs4
import requests


# steamcomurl = 'http://steamcommunity.com/id/%s/?xml=1'
bpackurl = 'http://backpack.tf/id/%s'

def command_value(bot, user, channel, args):
    steamname = args
    
#     steamxml = bs4(urllib.urlopen(steamcomurl % steamname),'xml')
#     try:
#         steamid = steamxml.steamID64.string
#         nick = steamxml.steamID.string
#     except AttributeError:
#         bot.say(channel,"Sorry, couldn't parse that Steam name. It should be the name in your Steam profile url!")
#         return
    
#     headercomp = {"User-Agent": "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:22.0) Gecko/20100101 Firefox/22.0", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.5", "Accept-Encoding": "gzip, deflate", "Referer": "http://b-web.org/tf2/", "Content-Type": "application/x-www-form-urlencoded"}
#     r = requests.post('http://b-web.org/tf2/process/', data='steamAccountName=%s' % steamid, headers = headercomp)
    
    bpackpage = bs4(urllib.urlopen(bpackurl % steamname))
    try:
        dispvalue = bpackpage.find(id='dollarvalue').string
        bot.say(channel,"%s's TF2 backpack is maybe worth something like $%s! (According to %s)" % (steamname, dispvalue, bpackurl % steamname))
    except AttributeError:
        bot.say(channel,"Sorry, couldn't parse that Steam name. It should be the name in your Steam profile url!")