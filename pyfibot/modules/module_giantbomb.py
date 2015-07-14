# -*- coding: utf-8 -*-
import logging
import json
import urllib
import os
import sys
from threading import Thread

from twisted.internet import reactor
import requests
from bs4 import BeautifulSoup as bs4
from soupy import Soupy, Q

requests.packages.urllib3.disable_warnings()

log = logging.getLogger('giantbomb')
t = None
videos = {}
getvids_callLater = None
bot = None
config = None

VIDEO_NAMES = {'ql': 'Quick Look', 'sub': 'Premium Video', 'feature': 'Feature', 'bombastica': 'Encyclopedia Bombastica',
                'event': 'Event Video', 'unfinished': 'Unfinished'}
VIDEO_URLS = {'ql': 'http://www.giantbomb.com/videos/quick-looks/', 'sub': 'http://www.giantbomb.com/videos/premium/',
                'feature': 'http://www.giantbomb.com/videos/features/', 'bombastica': 'http://www.giantbomb.com/videos/encyclopedia-bombastica/',
                'event': 'http://www.giantbomb.com/videos/events/', 'unfinished': 'http://www.giantbomb.com/videos/unfinished/'}
PODCAST_NAMES = {'premcast': 'Premium Podcast', 'bombcast': 'Bombcast', 'beast': 'Beastcast', 'presents': 'GB Presents'}
PODCAST_URLS = {'premcast': 'http://www.giantbomb.com/podcasts/premium/', 'bombcast':'http://www.giantbomb.com/podcasts/',
                'beast': 'http://www.giantbomb.com/podcasts/beastcast/', 'presents': 'http://www.giantbomb.com/podcasts/giant-bomb-presents/'}
CHANNEL = "#giantbomb"

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
    if getvids_callLater is not None:
        try:
            log.info("Stopping previous scraping thread")
            getvids_callLater.cancel()
        except Exception, e:
            log.error("Exception occurred stopping scraping thread")
            log.error(e)


def command_gb(bot, user, channel, args):
    """.gb upcoming - Returns any posted upcoming items at GiantBomb.com (it's a website about video games)"""
    global videos
    if args:
        cmds = args.split()
        subcommand = cmds[0]
        if subcommand == "ql":
            bot.say(channel, "Latest QL: %s" % videos['ql'])
        elif subcommand == "upcoming":
            page = bs4(urllib.urlopen("http://www.giantbomb.com/"))
            upcoming = page.find("dl", {"class": "promo-upcoming"})
            if not upcoming:
                bot.say(channel, "No items on the upcoming list! Alert @GiantBombStats!")
            slots = upcoming.find_all("dd")
            bot.say(channel, "%d Upcoming Items (times in EST):" % len(slots))
            for slot in slots:
                text = slot.find("h4").text
                time = slot.find("p").text
                bot.say(channel, "%s - %s" % (text, time))


def getvids(botref):
    """This function is launched from rotator to collect and announce new items from feeds to channel"""
    global CHANNEL, videos, bot

    bot = botref
    change = False

    for type, url in VIDEO_URLS.iteritems():
        if check_latest(type, url):
            change = True

    for type, url in PODCAST_URLS.iteritems():
        if check_podcast(type, url):
            change = True

    page = bs4(urllib.urlopen("http://www.giantbomb.com/news/"))
    latestname = page.find(class_ = "title").string
    if not latestname == videos['article']:
        deck = page.find(class_ = "deck")
        latestdesc = deck.string
        link = deck.parent['href']
        bot.say(CHANNEL, "[New Article] %s - %s http://www.giantbomb.com%s" % (latestname, latestdesc, link))
        log.info("New Article: %s" % latestname)
        videos['article'] = latestname
        change = True

    page = bs4(urllib.urlopen("http://www.giantbomb.com/reviews/"))
    titletag = page.find(class_ = "title")
    latestname = titletag.string
    if not latestname == videos['review']:
        deck = page.find(class_ = "deck")
        byline = page.find(class_ = "byline").string
        author = byline[byline.index("by") + 3:]
        latestdesc = deck.string
        link = deck.parent['href']
        scorespan = titletag.findNextSibling()
        scoreclass = scorespan['class'][2]
        score = scoreclass[scoreclass.find('-')+1:]
        score = 'Unscored' if score == '0' else '%s-Star' % score
        bot.say(CHANNEL, "[New %s Review by %s] %s - %s http://www.giantbomb.com%s" % (score, author, latestname,
                                                                                         latestdesc, link))
        log.info("New Review: %s" % latestname)
        videos['review'] = latestname
        change = True

    livetwitter = "https://api.twitter.com/1.1/statuses/user_timeline.json?screen_name=giantbomblive&count=1"
    bearer = config.get('twitter_bearer')
    data = bot.get_url(livetwitter,headers={'Authorization':'Bearer ' + bearer})
    parsed = data.json()
    latesttweet = parsed[0]['id']
    if not latesttweet == videos['tweet']:
        text = parsed[0]['text']
        bot.say(CHANNEL, "LIVE STREAM %s" % text[10:])
        log.info("New Livestream Tweet")
        videos['tweet'] = latesttweet
        change = True

    mixlr = requests.get("https://api.mixlr.com/users/jeff-gerstmann?source=embed&include_comments=false")
    mdata = mixlr.json()
    url = mdata['url']
    live = mdata['is_live']
    if live and not videos['mixlrlive']:
        latestmixlr = mdata['broadcasts'][0]['title']
        bot.say(CHANNEL, "Jeff is LIVE on Mixlr: %s - %s" % (latestmixlr, url))
        log.info("New Mixlr Broadcast")
        videos['mixlr'] = latestmixlr
        videos['mixlrlive'] = True
        change = True
    elif videos['mixlrlive'] and not live:
        videos['mixlrlive'] = False
        change=True

    if change:
        with open(os.path.join(sys.path[0], 'modules', 'module_giantbomb_conf.json'),'w') as datafile:
            json.dump(videos, datafile)

def check_latest(type, url):
    global CHANNEL, videos, bot

    page = Soupy(urllib.urlopen(url))
    namenode = page.find(class_ = "title")
    latestname = namenode.text.val()
    if not latestname == videos[type]:
        latestdesc = page.find(itemprop = "description").text.val()
        link = namenode.parent['href'].val()
        bot.say(CHANNEL, "[New %s] %s - %s http://www.giantbomb.com%s" % (VIDEO_NAMES[type], latestname, latestdesc,
                                                                          link))
        log.info("New %s: %s" % (VIDEO_NAMES[type], latestname))
        videos[type] = latestname
        return True
    return False

def check_podcast(type, url):
    global CHANNEL, videos, bot

    page = Soupy(urllib.urlopen(url))
    namenode = page.find("h2")
    latestname = namenode.text.val()
    if not latestname == videos[type]:
        latestdesc = page.find(class_="deck").text.val().strip()
        bot.say(CHANNEL, "[New %s] %s - %s %s" % (PODCAST_NAMES[type], latestname, latestdesc, url))
        log.info("New %s: %s" % (PODCAST_NAMES[type], latestname))
        videos[type] = latestname
        return True
    return False

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
