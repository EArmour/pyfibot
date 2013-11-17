# -*- coding: utf-8 -*-

from util import pyfiurl
from modules import module_urltitle
import botcore
import logging

log = logging.getLogger('goog')
cx = None

url = "https://www.googleapis.com/customsearch/v1?q=%s&cx=%s&num=1&safe=off&key=AIzaSyCaXV2IVfhG1lZ38HP7Xr9HzkGycmsuSDU"

def init(bot):
    global cx
    config = bot.config.get('module_goog', {})
    cx = config.get('cx', '')
    if not cx:
        log.warning("Google custom search ID not found in config!")
    
def command_goog(bot, user, channel, args):
    """.goog [query] - Searches Google and returns the first result"""
    global cx
    if not cx:
        return
    
    if args:
        query = args
    else:
        return bot.say(channel, "No search query!")
    
    search = bot.get_url(url % (query, cx))
    parsed = search.json()
    
    results = parsed['searchInformation']['totalResults']
    
    if results == '0':
        return bot.say(channel, "Google found nothing for query: %s" % query)
        
#     time = parsed['searchInformation']['formattedSearchTime']
    firstURL = parsed['items'][0]['link']
    title = parsed['items'][0]['title']
    
    bot.say(channel, "Google: %s - %s" % (title, firstURL))
    
#     module_urltitle.init(bot.factory)
#     module_urltitle.handle_url(bot, user, channel, firstURL, args)