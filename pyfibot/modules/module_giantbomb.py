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
VIDEO_CODES = {'ql': '3', 'sub': '10', 'feature': '8', 'bombastica': '12', 'event': '6', 'unfinished': '13'}
VIDEO_URL = "http://www.giantbomb.com/api/videos/?api_key=%s&format=json&limit=1&video_type=%s&sort=publish_date:desc"
PODCAST_NAMES = {'premcast': 'Premium Podcast', 'presents': 'GB Presents'}
PODCAST_URLS = {'premcast': 'http://www.giantbomb.com/podcasts/premium/', 'presents': 'http://www.giantbomb.com/podcasts/giant-bomb-presents/'}
CHANNEL = "#giantbomb"


def event_signedon(bot):
    global getvids_callLater, videos

    with open(os.path.join(sys.path[0], 'modules', 'module_giantbomb_conf.json')) as datafile:
        videos = json.load(datafile)
    log.info("Loaded cached video names")

    if getvids_callLater != None:
        log.info("Stopping previous scraping thread")
        getvids_callLater.cancel()
    rotator_getvids(bot, 500)

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
            rotator_getvids(bot, 500)


def init(botref):
    global config, bot, apikey, bearer
    bot = botref
    config = bot.config.get("module_giantbomb", {})
    apikey = config.get("apikey")
    twitconfig = bot.config.get("module_urltitle", {})
    bearer = twitconfig.get('twitter_bearer')


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
        if subcommand == "upcoming":
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
    global CHANNEL, videos, bot, apikey, bearer

    bot = botref
    change = False

    for type, code in VIDEO_CODES.iteritems():
        if check_latest(type, code):
            change = True

    page = bs4(urllib.urlopen("http://www.giantbomb.com/feeds/news/"), "xml")
    latestitem = page.rss.channel.item
    latestname = latestitem.title.text
    if not latestname == videos['article']:
        link = latestitem.link.text
        bot.say(CHANNEL, "[New Article] %s - %s" % (latestname, link))
        log.info("New Article: %s" % latestname)
        videos['article'] = latestname
        change = True

    data = requests.get("http://www.giantbomb.com/api/promos/?api_key=%s&format=json&limit=5&sort=date_added:desc" %
                        apikey)
    response = data.json()
    promos = response['results']
    for promo in promos:
        podcastid = promo['id']
        if podcastid == videos['podcast']:
            break
        elif promo['resource_type'] == 'podcast':
            latestname = promo['name']
            latestdesc = promo['deck']
            url = promo['link']
            bot.say(CHANNEL, "[New Podcast] %s - %s %s" % (latestname, latestdesc, url))
            log.info("New Podcast: %s" % latestname)
            videos['podcast'] = podcastid
            change = True
            break

    data = requests.get("http://www.giantbomb.com/api/reviews/?api_key=%s&format=json&limit=1&sort=publish_date:desc" % apikey)
    response = data.json()
    review = response['results'][0]
    releaseid = review['release']['id']
    if not releaseid == videos['review']:
        gamename = review['release']['name']
        deck = review['deck']
        author = review['reviewer']
        link = review['site_detail_url']
        score = review['score']
        score = 'Unscored' if score == '0' else '%s-Star' % score
        bot.say(CHANNEL, "[New %s Review by %s] %s - %s %s" % (score, author, gamename,
                                                                                         deck, link))
        log.info("New Review: %s" % gamename)
        videos['review'] = releaseid
        change = True

    livetwitter = "https://api.twitter.com/1.1/statuses/user_timeline.json?screen_name=giantbomblive&count=1"
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
    code = mdata['url']
    live = mdata['is_live']
    if live and not videos['mixlrlive']:
        latestmixlr = mdata['broadcasts'][0]['title']
        bot.say(CHANNEL, "Jeff is LIVE on Mixlr: %s - %s" % (latestmixlr, code))
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

def check_latest(type, code):
    global videos, bot, apikey

    try:
        data = requests.get(VIDEO_URL % (apikey, code))
        json = data.json()
        video = json['results'][0]
        vidid = video['id']
        if not vidid == videos[type]:
            name = video['name']
            deck = video['deck']
            link = video['site_detail_url']
            bot.say(CHANNEL, "[New %s] %s - %s %s" % (VIDEO_NAMES[type], name, deck,
                                                                              link))
            log.info("New %s: %s" % (VIDEO_NAMES[type], name))
            videos[type] = vidid
            return True
        return False
    except:
        log.error("Failed checking for latest %s at %s:" % (type, code))
        return False


def check_podcast(type, url):
    global CHANNEL, videos, bot, apikey

    page = Soupy(urllib.urlopen(url))
    try:
        namenode = page.find("h2")
        latestname = namenode.text.val()
        if not latestname == videos[type]:
            latestdesc = page.find(class_="deck").text.val().strip()
            bot.say(CHANNEL, "[New %s] %s - %s %s" % (PODCAST_NAMES[type], latestname, latestdesc, url))
            log.info("New %s: %s" % (PODCAST_NAMES[type], latestname))
            videos[type] = latestname
            return True
        return False
    except:
        log.error("Failed checking for latest %s at %s" % (type, url))
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
