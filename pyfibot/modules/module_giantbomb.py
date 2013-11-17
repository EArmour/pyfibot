# -*- coding: utf-8 -*-
from twisted.internet import reactor
from twisted.internet import task
import logging, json, urllib, os, sys, threading
from bs4 import BeautifulSoup as bs4

log = logging.getLogger('giantbomb')
t = None
videos = {}

def init(bot):
    global videos, t
    with open(os.path.join(sys.path[0], 'modules', 'module_giantbomb_conf.json')) as datafile:
        videos = json.load(datafile)
        
    log.info("Loaded cached video names")
    
    if (t != None):
        log.info("Stopped")
        t.stop();
    
def command_gb(bot, user, channel, args):
    global t, videos
    with open(os.path.join(sys.path[0], 'modules', 'module_giantbomb_conf.json')) as datafile:
        videos = json.load(datafile)
    log.info(videos['article'])

    log.info("Started")
    t = task.LoopingCall(getvids, bot)
    t.start(30, now=True)
    t.stop()
    
def getvids(bot):
    """This function is launched from rotator to collect and announce new items from feeds to channel"""
    global videos
    
    change = False
    page = bs4(urllib.urlopen("http://www.giantbomb.com/videos/quick-looks/"))
    latestname = page.find(itemprop = "name").string
    if not latestname == videos['ql']:
        latestdesc = page.find(itemprop = "description").string
        bot.say("#giantbomb", "[New QL] %s - %s http://www.giantbomb.com/videos/quick-looks/" % (latestname, latestdesc))
        videos['ql'] = latestname
        change = True
        
    page = bs4(urllib.urlopen("http://www.giantbomb.com/videos/subscriber/"))
    latestname = page.find(itemprop = "name").string
    if not latestname == videos['sub']:
        latestdesc = page.find(itemprop = "description").string
        bot.say("#giantbomb", "[New Subscriber Video] %s - %s http://www.giantbomb.com/videos/subscriber/" % (latestname, latestdesc))
        videos['sub'] = latestname
        change = True
        
    page = bs4(urllib.urlopen("http://www.giantbomb.com/videos/features/"))
    latestname = page.find(itemprop = "name").string
    if not latestname == videos['feature']:
        latestdesc = page.find(itemprop = "description").string
        bot.say("#giantbomb", "[New Feature] %s - %s http://www.giantbomb.com/videos/features/" % (latestname, latestdesc))
        videos['feature'] = latestname
        change = True
      
    log.info(videos['article'])   
    page = bs4(urllib.urlopen("http://www.giantbomb.com/news/"))
    latestname = page.find(class_ = "title").string
    if not latestname == videos['article']:
        deck = page.find(class_ = "deck")
        latestdesc = deck.string
        link = deck.parent['href']
        log.info(link)
        bot.say("#asandbox", "[New Article] %s - %s http://www.giantbomb.com%s" % (latestname, latestdesc, link))
        bot.say("#giantbomb", "[New Article] %s - %s http://www.giantbomb.com%s" % (latestname, latestdesc, link))
        videos['article'] = latestname
        change = True

    log.info(latestname)
    log.info(videos['article'])

    if change:
        with open(os.path.join(sys.path[0], 'modules', 'module_giantbomb_conf.json'),'w') as datafile:
            json.dump(videos, datafile)
    
# def rotator_getvids(bot, delay):
#     """Timer for methods/functions"""
#     try:
#         global t, getvids_callLater
#         t = Thread(target=getvids, args=(bot,))
#         t.daemon = True
#         t.start()
#         t.join()
#         getvids_callLater = reactor.callLater(delay, rotator_getvids, bot, delay)
#     except Exception, e:
#         log.error('Error in rotator_output')