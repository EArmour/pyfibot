# -*- coding: utf-8 -*-

from util import pyfiurl
from modules import module_urltitle
import botcore

url = "https://www.googleapis.com/customsearch/v1?q=%s&cx=016962746194547451353:iq9kv7rfvsi&num=1&safe=off&key=AIzaSyCaXV2IVfhG1lZ38HP7Xr9HzkGycmsuSDU"

def command_goog(bot, user, channel, args):
    if args:
        query = args
    else:
        return bot.say(channel, "No search query!")
    
    search = bot.get_url(url % query)
    parsed = search.json()
    
    results = parsed['searchInformation']['totalResults']
    
    if results == '0':
        return bot.say(channel, "Google found nothing for query: %s" % query)
        
    time = parsed['searchInformation']['formattedSearchTime']
    firstURL = parsed['items'][0]['link']
    
    bot.say(channel, "Google: %s" % firstURL)
    
    module_urltitle.init(bot.factory)
    module_urltitle.handle_url(bot, user, channel, firstURL, args)