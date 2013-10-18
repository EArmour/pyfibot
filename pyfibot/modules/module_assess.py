# -*- coding: utf-8 -*-

import requests
import json
from util import getnick

def command_assess(bot, user, channel, args):
    url = "http://www.whatdoestheinternetthink.net/core/query.php"
    headers = {"Host": "www.whatdoestheinternetthink.net", 
               "User-Agent": "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:22.0) Gecko/20100101 Firefox/22.0", 
               "Accept": "application/json, text/javascript, */*", 
               "Content-Type": "application/x-www-form-urlencoded",
               "Referer": "http://www.whatdoestheinternetthink.net/%s" % args}
    
    data = requests.post(url, data="query=%s" % args, headers = headers)
    parsed = json.loads(data.content)
    
    try:
        pos = parsed['positive']
    except KeyError:
        return bot.say(channel, "{0}: The internet has no opinion on that insignificant topic!".format(getnick.get(user)))
    
    neg = parsed['negative']
    neu = parsed['indifferent']
    
    return bot.say(channel, "{0}: The internet is {1}% positive, {2}% negative, and {3}% neutral about that!".format(getnick.get(user),pos,neg,neu))