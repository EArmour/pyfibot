# -*- coding: utf-8 -*-
from twisted.internet import reactor
from twisted.internet import task
import logging, json, urllib, os, sys, requests
from threading import Thread
from bs4 import BeautifulSoup as bs4

log = logging.getLogger('giantbomb')
t = None
videos = {}
getvids_callLater = None
bot = None
config = None

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
    
def init(botref):
    global config
    global bot
    bot = botref
    config = bot.config.get("module_urltitle", {})
    
def finalize():
    if getvids_callLater != None:
        log.info("Stopping previous scraping thread")
        getvids_callLater.cancel()
    
def command_gb(bot, user, channel, args):
    """.gb [ql|feature|sub|article|review|bombastica] - Returns the latest item on Giant Bomb on that type"""
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
        elif (subcommand == "bombastica"):
            bot.say(channel, "Latest Bombastica: %s" % videos['bombastica'])
    
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
        if latestname[0:1] == "Q":
            qltype = "QL"
        else:
            qltype = "Unfinished"
        bot.say(channel, "[New %s] %s - %s http://www.giantbomb.com%s" % (qltype, latestname, latestdesc, link))
        log.info("New %s: %s" % (qltype, latestname))
        videos['ql'] = latestname
        change = True
        
    page = bs4(urllib.urlopen("http://www.giantbomb.com/videos/subscriber/"))
    name = page.find(class_ = "title")
    latestname = name.string
    if not latestname == videos['sub']:
        latestdesc = page.find(itemprop = "description").string
        link = name.parent['href']
        bot.say(channel, "[New Subscriber Video] %s - %s http://www.giantbomb.com%s" % (latestname, latestdesc, link))
        log.info("New Sub Video: %s" % latestname)
        videos['sub'] = latestname
        change = True
        
    page = bs4(urllib.urlopen("http://www.giantbomb.com/videos/features/"))
    name = page.find(class_ = "title")
    latestname = name.string
    if not latestname == videos['feature']:
        latestdesc = page.find(itemprop = "description").string
        link = name.parent['href']
        bot.say(channel, "[New Feature] %s - %s http://www.giantbomb.com%s" % (latestname, latestdesc, link))
        log.info("New Feature: %s" % latestname)
        videos['feature'] = latestname
        change = True

    page = bs4(urllib.urlopen("http://www.giantbomb.com/news/"))
    latestname = page.find(class_ = "title").string
    if not latestname == videos['article']:
        deck = page.find(class_ = "deck")
        latestdesc = deck.string
        link = deck.parent['href']
        bot.say(channel, "[New Article] %s - %s http://www.giantbomb.com%s" % (latestname, latestdesc, link))
        log.info("New Article: %s" % latestname)
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
        log.info("New Review: %s" % latestname)
        videos['review'] = latestname
        change = True
        
    page = bs4(urllib.urlopen("http://www.giantbomb.com/videos/encyclopedia-bombastica/"))
    name = page.find(class_ = "title")
    latestname = name.string
    if not latestname == videos['bombastica']:
        latestdesc = page.find(itemprop = "description").string
        link = name.parent['href']
        bot.say(channel, "[New Bombastica] %s - %s http://www.giantbomb.com%s" % (latestname, latestdesc, link))
        log.info("New Bombastica: %s" % latestname)
        videos['bombastica'] = latestname
        change = True

    livetwitter = "https://api.twitter.com/1.1/statuses/user_timeline.json?screen_name=giantbomblive&count=1"
    bearer = config.get('twitter_bearer')
    data = bot.get_url(livetwitter,headers={'Authorization':'Bearer ' + bearer})
    parsed = data.json()
    
    latesttweet = parsed[0]['id']
    if not latesttweet == videos['tweet']:
        text = parsed[0]['text']
        bot.say(channel, "LIVE STREAM %s" % text[10:])
        log.info("New Livestream Tweet")
        videos['tweet'] = latesttweet
        change = True

    mixlr = requests.get("https://api.mixlr.com/users/jeff-gerstmann?source=embed&include_comments=false")
    mdata = mixlr.json()
    url = mdata['url']
    latestmixlr = mdata['broadcasts'][0]['title']
    if not latestmixlr == videos['mixlr']:
        bot.say(channel, "Jeff is LIVE on Mixlr: %s - %s" % (latestmixlr, url))
        log.info("New Mixlr Broadcast")
        videos['mixlr'] = latestmixlr
        change = True

    if change:
        with open(os.path.join(sys.path[0], 'modules', 'module_giantbomb_conf.json'),'w') as datafile:
            json.dump(videos, datafile)
#     else:
#         log.info("No changes found")

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