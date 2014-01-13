# -*- coding: utf-8 -*-

import requests
import json
from util import getnick

def command_assess(bot, user, channel, args):
    """.assess [topic] - WhatDoesTheInternetThink.net about whatever topic"""
    url = "http://www.whatdoestheinternetthink.net/core/getdata.php?query=%s&searchtype=1" % args
    headers = {"Host": "www.whatdoestheinternetthink.net", 
               "User-Agent": "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:22.0) Gecko/20100101 Firefox/22.0", 
               "Accept": "application/json, text/javascript, */*", 
               "Content-Type": "application/x-www-form-urlencoded",
               "Accept-Encoding": "gzip, deflate",
               "X-Requested-With": "XMLHttpRequest",
               "Referer": "http://www.whatdoestheinternetthink.net/"}
    
    data = requests.get(url, headers = headers)
    parsed = json.loads(data.content)
    
    try:
        pos = float(parsed[1]['positive'])
    except Exception:
        return bot.say(channel, "{0}: The internet has no opinion on that insignificant topic!".format(getnick.get(user)))
    
    neg = float(parsed[1]['negative'])
    neu = float(parsed[1]['indifferent'])
    
    total = pos + neg + neu
    posperc = int((pos / total) * 100)
    negperc = int((neg / total) * 100)
    neuperc = int((neu / total) * 100)
    
    return bot.say(channel, "{0}: The internet is {1}% positive, {2}% negative, and {3}% neutral about that!".format(getnick.get(user),posperc,negperc,neuperc))