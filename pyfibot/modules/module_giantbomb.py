# -*- coding: utf-8 -*-
from twisted.internet import reactor
from twisted.internet import task
import logging, json, urllib, os, sys
from threading import Thread
from bs4 import BeautifulSoup as bs4

log = logging.getLogger('giantbomb')
t = None
videos = {}
getvids_callLater = None

def event_signedon(bot):
    global getvids_callLater, videos
    
    with open(os.path.join(sys.path[0], 'modules', 'module_giantbomb_conf.json')) as datafile:
        videos = json.load(datafile)
    log.info("Loaded cached video names")
    
    if getvids_callLater != None:
        log.info("Stopping previous scraping thread")
        getvids_callLater.cancel()
    rotator_getvids(bot, 300)
    
def handle_privmsg(bot, user, channel, cmd):
    global videos
    msg = cmd[1:]
    if(user == channel):
        if(msg == "startgb"):
            bot.say(channel, "GB scraper started!")
            with open(os.path.join(sys.path[0], 'modules', 'module_giantbomb_conf.json')) as datafile:
                videos = json.load(datafile)
            log.info("Loaded cached video names")
            if getvids_callLater != None:
                log.info("Stopping previous scraping thread")
                getvids_callLater.cancel()
            rotator_getvids(bot, 300)
    
def finalize():
    if getvids_callLater != None:
        log.info("Stopping previous scraping thread")
        getvids_callLater.cancel()
    
def command_gb(bot, user, channel, args):
    global videos
    if args:
        subcommand = args.split()[0]
        if (subcommand == "ql"):
            bot.say(channel, "Latest QL: %s" % videos['ql'])
        elif (subcommand == "feature"):
            bot.say(channel, "Latest Feature: %s" % videos['feature'])
        elif (subcommand == "sub"):
            bot.say(channel, "Latest Subscriber Content: %s" % videos['sub'])
        elif (subcommand == "article"):
            bot.say(channel, "Latest Article: %s" % videos['article'])
        elif (subcommand == "review"):
            bot.say(channel, "Latest Review: %s" % videos['review'])
    
def getvids(bot):
    """This function is launched from rotator to collect and announce new items from feeds to channel"""
    global videos
    
    change = False
    channel = "#giantbomb"

    page = bs4(urllib.urlopen("http://www.giantbomb.com/videos/quick-looks/"))
    name = page.find(class_ = "title")
    latestname = name.string
    if not latestname == videos['ql']:
        latestdesc = page.find(itemprop = "description").string
        link = name.parent['href']
        bot.say(channel, "[New QL] %s - %s %s" % (latestname, latestdesc, link))
        log.info("New QL")
        videos['ql'] = latestname
        change = True
        
    page = bs4(urllib.urlopen("http://www.giantbomb.com/videos/subscriber/"))
    name = page.find(class_ = "title")
    latestname = name.string
    if not latestname == videos['sub']:
        latestdesc = page.find(itemprop = "description").string
        link = name.parent['href']
        bot.say(channel, "[New Subscriber Video] %s - %s %s" % (latestname, latestdesc, link))
        log.info("New Sub Video")
        videos['sub'] = latestname
        change = True
        
    page = bs4(urllib.urlopen("http://www.giantbomb.com/videos/features/"))
    name = page.find(class_ = "title")
    latestname = name.string
    if not latestname == videos['feature']:
        latestdesc = page.find(itemprop = "description").string
        link = name.parent['href']
        bot.say(channel, "[New Feature] %s - %s %s" % (latestname, latestdesc, link))
        log.info("New Feature")
        videos['feature'] = latestname
        change = True

    page = bs4(urllib.urlopen("http://www.giantbomb.com/news/"))
    latestname = page.find(class_ = "title").string
    if not latestname == videos['article']:
        deck = page.find(class_ = "deck")
        latestdesc = deck.string
        link = deck.parent['href']
        bot.say(channel, "[New Article] %s - %s http://www.giantbomb.com%s" % (latestname, latestdesc, link))
        log.info("New Article")
        videos['article'] = latestname
        change = True

    page = bs4(urllib.urlopen("http://www.giantbomb.com/reviews/"))
    latestname = page.find(class_ = "title").string
    if not latestname == videos['review']:
        deck = page.find(class_ = "deck")
        byline = page.find(class_ = "byline").string
        author = byline[byline.index("by") + 3:]
        latestdesc = deck.string
        link = deck.parent['href']
        bot.say(channel, "[New Review by %s] %s - %s http://www.giantbomb.com%s" % (author, latestname, latestdesc, link))
        log.info("New Review")
        videos['review'] = latestname
        change = True

    if change:
        with open(os.path.join(sys.path[0], 'modules', 'module_giantbomb_conf.json'),'w') as datafile:
            json.dump(videos, datafile)
    else:
        log.info("No changes found")
    
def rotator_getvids(bot, delay):
    """Timer for methods/functions"""
    try:
        global t, getvids_callLater
        t = Thread(target=getvids, args=(bot,))
        t.daemon = True
        t.start()
        getvids_callLater = reactor.callLater(delay, rotator_getvids, bot, delay)
    except Exception, e:
        log.error('Error in rotator_getvids')
        log.error(e)