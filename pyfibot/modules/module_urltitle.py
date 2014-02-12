# -*- coding: utf-8 -*-
"""Displays HTML page titles

Smart title functionality for sites which could have clear titles,
but still decide show idiotic bulk data in the HTML title element

Items needed in config.yml under module_urltitle:
    twitter_bearer: Twitter API bearer token (https://dev.twitter.com/docs/auth/application-only-auth)
    imgur_clientid: Imgur API client id (http://api.imgur.com/)
"""

from __future__ import print_function, division

from datetime import datetime
import fnmatch
import json
import logging
import re
from types import TupleType
import urlparse

from bs4 import BeautifulSoup

import botcore
from util import pyfiurl


has_json = True

log = logging.getLogger("urltitle")
config = None
bot = None

global recursecount
recursecount = 0
global norepeat
norepeat = []

TITLE_LAG_MAXIMUM = 10

def init(botref):
    global config
    global bot
    bot = botref
    config = bot.config.get("module_urltitle", {})

def __get_bs(url):
    # Fetch the content and measure how long it took
    start = datetime.now()
    r = bot.get_url(url)
    end = datetime.now()

    if not r:
        return None

    duration = (end-start).seconds
    if duration > TITLE_LAG_MAXIMUM:
        log.error("Fetching title took %d seconds, not displaying title" % duration)
        return None

    content_type = r.headers['content-type'].split(';')[0]
    if content_type not in ['text/html', 'text/xml', 'application/xhtml+xml']:
        log.debug("Content-type %s not parseable" % content_type)
        return None

    content = r.content
    if content:
        return BeautifulSoup(content)
    else:
        return None
    
def recurse(bot, user, title, channel):
    #Kinda hacky method of preventing infinite loops (only the original url has a user attribute)
    #Mainly a problem with Twitter posts that have an image attached, since they essentially link to themselves
    global recursecount
    global norepeat
    if user is "":
        recursecount = recursecount + 1
        if recursecount == 3:
            bot.say(channel, "Infinite (or just annoyingly long) recursion detected; aborting!")
            return
    else:
        recursecount = 0
    
    urls = pyfiurl.grab(title.encode("UTF-8"))
    if urls:
        user = ""
        for url in urls:
            if url in norepeat:
                break
            else:
                norepeat.append(url)
            msg = url
            handle_url(bot, user, channel, url, msg)
    else:
        norepeat = []

def handle_url(bot, user, channel, url, msg):
    """Handle urls"""

    if msg.startswith("-"):
        return
    if re.match("http://.*?\.imdb\.com/title/tt([0-9]+)/?", url):
        return  # IMDB urls are handled elsewhere
    if re.match("(http:\/\/open.spotify.com\/|spotify:)(album|artist|track)([:\/])([a-zA-Z0-9]+)\/?", url):
        return  # spotify handled elsewhere

    if channel.lstrip("#") in config.get('disable', ''):
        return
    
    # hack, support both ignore and ignore_urls for a while
    for ignore in config.get("ignore_urls", []):
        if fnmatch.fnmatch(url, ignore):
            log.info("Ignored URL: %s %s", url, ignore)
            return
    for ignore in config.get("ignore_users", []):
        if fnmatch.fnmatch(user, ignore):
            log.info("Ignored url from user: %s, %s %s", user, url, ignore)
            return

    # a crude way to handle the new-fangled shebang urls as per
    # http://code.google.com/web/ajaxcrawling/docs/getting-started.html
    # this can manage twitter + gawker sites for now
    url = url.replace("#!", "?_escaped_fragment_=")

    # try to find a specific handler for the URL
    handlers = [(h, ref) for h, ref in globals().items() if h.startswith("_handle_")]

    for handler, ref in handlers:
        pattern = ref.__doc__.split()[0]
        if fnmatch.fnmatch(url, pattern):
            title = ref(url)
            if title:
                # Handler Found!
                _title(bot, channel, title, True)
                recurse(bot, user, title, channel)

#     log.debug("No specific handler found, using generic")
#     # Fall back to generic handler
#     bs = __get_bs(url)
#     if not bs:
#         log.debug("No BS available, returning")
#         return
# 
#     title = bs.find('title')
#     # no title attribute
#     if not title:
#         log.debug("No title found, returning")
#         return
# 
#     try:
#         # remove trailing spaces, newlines, linefeeds and tabs
#         title = title.string.strip()
#         title = title.replace("\n", " ")
#         title = title.replace("\r", " ")
#         title = title.replace("\t", " ")
# 
#         # compress multiple spaces into one
#         title = re.sub("[ ]{2,}", " ", title)
# 
#         # nothing left in title (only spaces, newlines and linefeeds)
#         if not title:
#             return
# 
#         # Cache generic titles
#         cache.put(url, title)
# 
#         if config.get("check_redundant", True) and _check_redundant(url, title):
#             log.debug("%s is redundant, not displaying" % title)
#             return
# 
#         ignored_titles = ['404 Not Found', '403 Forbidden']
#         if title in ignored_titles:
#             return
#         else:
#             return _title(bot, channel, title)
# 
#     except AttributeError:
#         # Need a better way to handle this. Happens with empty <title> tags
#         pass

def _title(bot, channel, title, smart=False, prefix=None):
    """Say title to channel"""

    if not title:
        return

    if not prefix and smart is False:
        prefix = "Title:"
    info = None
    # tuple, additional info
    if type(title) == TupleType:
        info = title[1]
        title = title[0]
    # crop obscenely long titles
    if len(title) > 200:
        title = title[:200] + "..."

    if not prefix:    
        return bot.say(channel, title)
    else:
        return bot.say(channel, "%s %s" % (prefix, title))

# Some handlers does not have if not bs: return, but why do we even have this for every function
def _handle_tweet2(url):
    """http*://twitter.com/*/status/*"""
    return _handle_tweet(url)

def _handle_tweet(url):
    """http*://twitter.com/*/statuses/*"""
    tweet_url = "https://api.twitter.com/1.1/statuses/show.json?id=%s"
    test = re.match("https?://twitter\.com\/(\w+)/status(es)?/(\d+)", url)
    #    matches for unique tweet id string
    infourl = tweet_url % test.group(3)

    bearer = config.get('twitter_bearer')
    data = bot.get_url(infourl,headers={'Authorization':'Bearer ' + bearer})
    json = data.json()
    
    text = json['text']
    user = json['user']['screen_name']
    name = json['user']['name']

    retweets  = json['retweet_count']
    favorites = json['favorite_count']
    created   = json['created_at']
    created_date = datetime.strptime(created, "%a %b %d %H:%M:%S +0000 %Y")
    tweet_age = datetime.now()-created_date
    
    tweet = "@%s (%s): %s" % (user, name, text)
    
    return tweet

def _handle_tco(url):
    """http://t.co/*"""
    api = "http://api.longurl.org/v2/expand?url=%s&format=json"

    data = bot.get_url(api % url,headers={'User-Agent':'GrimmBotGamma/1.0'})
    dest = data.json()['long-url']
    
    if fnmatch.fnmatch(dest, '*twitter.com/*/photo/1'):
        return
        
    return "[Shortened Link] Resolves to: %s" % dest
    
def _handle_tinyurl(url):
    """http://tinyurl.com/*"""
    return _handle_tco(url)

def _handle_youtube_shorturl(url):
    """http*://youtu.be/*"""
    return _handle_youtube_gdata(url)

def _handle_youtube_gdata_new(url):
    """http*://youtube.com/watch#!v=*"""
    return _handle_youtube_gdata(url)

def _handle_youtube_gdata(url):
    """http*://*youtube.com/watch?*v=*"""
    gdata_url = "http://gdata.youtube.com/feeds/api/videos/%s"

    match = re.match("https?://youtu.be/(.*)", url)
    if not match:
        match = re.match("https?://.*?youtube.com/watch\?.*?v=([^&]+)", url)
    if match:
        infourl = gdata_url % match.group(1)
        params = {'alt': 'json', 'v': '2'}
        r = bot.get_url(infourl, params=params)

        if not r.status_code == 200:
            log.info("Video too recent, no info through API yet.")
            return

        entry = r.json()['entry']

        ## Author
        author = entry['author'][0]['name']['$t']
        ## Title
        title = entry['title']['$t']
        
#         ## Rating in stars
#         try:
#             rating = entry.get('gd$rating', None)['average']
#         except TypeError:
#             rating = 0.0
# 
#         stars = int(round(rating)) * "*"
# 
#         ## View count
#         try:
#             views = int(entry['yt$statistics']['viewCount'])
# 
#             import math
#             millnames=['','k','M','Billion','Trillion']
#             millidx=max(0,min(len(millnames)-1, int(math.floor(math.log10(abs(views))/3.0))))
#             views = '%.0f%s'%(views/10**(3*millidx),millnames[millidx])
#         except KeyError:
#             # No views at all, the whole yt$statistics block is missing
#             views = 'no'
# 
#         ## Age restricted?
#         # https://developers.google.com/youtube/2.0/reference#youtube_data_api_tag_media:rating
#         rating = entry['media$group'].get('media$rating', None)

        ## Content length
        secs = int(entry['media$group']['yt$duration']['seconds'])
        lengthstr = []
        hours, minutes, seconds = secs // 3600, secs // 60 % 60, secs % 60
        if hours > 0:
            lengthstr.append("%dh" % hours)
        if minutes > 0:
            lengthstr.append("%dm" % minutes)
        if seconds > 0:
            lengthstr.append("%ds" % seconds)

#         ## Content age
#         published = entry['published']['$t']
#         published = datetime.strptime(published, "%Y-%m-%dT%H:%M:%S.%fZ")
#         age = datetime.now() - published
#         halfyears, days = age.days // 182, age.days % 365
#         agestr = []
#         years = halfyears * 0.5
#         if years >= 1:
#             agestr.append("%gy" % years)
#         # don't display days for videos older than 6 months
#         if years < 1 and days > 0:
#             agestr.append("%dd" % days)
#         # complete the age string
#         if agestr and days != 0:
#             agestr.append(" ago")
#         elif years == 0 and days == 0:  # uploaded TODAY, whoa.
#             agestr.append("FRESH")
#         else:
#             agestr.append("ANANASAKÄÄMÄ")  # this should never happen =)

        return "YouTube: %s [by %s | %s]" % (title, author, "".join(lengthstr))

def _handle_steamgame(url):
    """http://store.steampowered.com/app/*"""
    log.info("Handling Steam game!")
    bs = __get_bs(url)
    
    title = bs.find(itemprop = "name").text.strip()
    price = bs.find(itemprop = "price").text.strip()
    
    return("Steam: %s -- %s" % (title, price))

def _handle_steamsharedfile(url):
    """http://steamcommunity.com/sharedfiles/filedetails/?id=*"""
    bs = __get_bs(url)
    
    crumbs = bs.find(class_="breadcrumbs")
    mediatype = crumbs.contents[3].text
    
    if mediatype == "Videos":
        pagetype = "Video of %s" % bs.find("div", {'class': 'screenshotAppName'}).contents[0].text
        descr = bs.find("div", {'class': 'nonScreenshotDescription'}).contents[0].string.strip('"')
    elif mediatype == "Screenshots":
        pagetype = "Screenshot of %s" % bs.find("div", {'class': 'screenshotAppName'}).contents[0].text
        descr = bs.find("div", {'class': 'screenshotDescription'}).contents[0].string.strip('"')
    elif mediatype == "Artwork":
        pagetype = "Fanart of %s" % bs.find("div", {'class': 'screenshotAppName'}).contents[0].text
        descr = bs.find("div", {'class': 'workshopItemTitle'}).text
    elif mediatype == "Guides":
        pagetype = "%s Guide" % crumbs.contents[1].text
        descr = bs.find("div", {'class': 'workshopItemTitle'}).text
    elif mediatype == "Workshop":
        pagetype = "%s Workshop" % crumbs.contents[1].text
        descr = bs.find("div", {'class': 'workshopItemTitle'}).text
    elif mediatype == "Games":
        pagetype = "Steam Greenlight"
        descr = bs.find("div", {'class': 'workshopItemTitle'}).text
    
    return "%s: %s" % (pagetype, descr)

def _handle_steamscreenshot(url):
    """http://steamcommunity.com/id/*/screenshot/*"""
    return _handle_steamsharedfile(url)

def _handle_twitch(url):
    """http://www.twitch.tv/*"""
    #TODO: Add Hitbox.tv
    if "/popout" in url:
        url = url[:-7]
        
    apiurl = "https://api.twitch.tv/kraken/channels/%s"
    jsonurl = apiurl % url[url.rfind("/") + 1:]
    data = bot.get_url(jsonurl)
    json = data.json()
    
    title = json['status']
    name = json['display_name']
    game = json['game']
    
    return "Twitch: %s playing %s: %s" % (name, game, title)

def _handle_vimeo(url):
    """*vimeo.com/*"""
    data_url = "http://vimeo.com/api/v2/video/%s.json"
    match = re.match("https?://.*?vimeo.com/(\d+)", url)
    if match:
        infourl = data_url % match.group(1)
        r = bot.get_url(infourl)
        info = r.json()[0]
        title = info['title']
        user = info['user_name']

        secs = info['duration']
        lengthstr = []
        hours, minutes, seconds = secs // 3600, secs // 60 % 60, secs % 60
        if hours > 0:
            lengthstr.append("%dh" % hours)
        if minutes > 0:
            lengthstr.append("%dm" % minutes)
        if seconds > 0:
            lengthstr.append("%ds" % seconds)

        return "Vimeo: %s [by %s | %s]" % (title, user, "".join(lengthstr))


def _handle_stackoverflow(url, site="Stackoverflow"):
    """*stackoverflow.com/questions/*"""
    api_url = 'https://api.stackexchange.com/2.1/questions/%s?site=stackoverflow'
    match = re.match('.*stackoverflow.com/questions/([0-9]+)', url)
    if match is None:
        return
    question_id = match.group(1)
    content = bot.get_url(api_url % question_id)
    if not content:
        log.debug("No content received")
        return
    try:
        data = content.json()
        title = data['items'][0]['title']
        tags = "/".join(data['items'][0]['tags'])
        score = data['items'][0]['score']
        answers = data['items'][0]['answer_count']
        return "StackExhange: %s - %dpts - %s answers" % (title, score, answers)
    except Exception, e:
        return "Json parsing failed %s" % e

def _handle_imgur(url):
    """http://*imgur.com*"""
    client_id = config.get("imgur_clientid")
    api = "https://api.imgur.com/3/"
    headers = {"Authorization": "Client-ID %s" % client_id}

    # regexes and matching API endpoints
    endpoints = [("imgur.com/r/.*?/(.*)", "gallery/r/all"),
                 ("i.imgur.com/(.*)\.(jpg|png|gif)", "gallery"),
                 ("imgur.com/gallery/(.*)", "gallery"),
                 ("imgur.com/a/([^\?]+)", "album"),
                 ("imgur.com/([^\./]+)", "gallery"),
                 ("*.imgur.com/", "userpage")
        ]

    title = None
    endpoint = None
    for regex, _endpoint in endpoints:
        match = re.search(regex, url)
        if match:
            resource_id = match.group(1)
            endpoint = _endpoint
            log.debug("using endpoint %s for resource %s" % (endpoint, resource_id))
            break

    if not endpoint:
        log.debug("No matching imgur endpoint found for %s" % url)
        return

    r = bot.get_url("%s/%s/%s" % (api, endpoint, resource_id), headers=headers)
    data = r.json()

    log.debug(data)

    if data['status'] == 200:
        title = r.json()['data']['title']
        # append album size to album urls if it's relevant
        if endpoint == "album":
            imgcount = len(data['data']['images'])
            if imgcount > 1:
                title += " [%d images]" % len(data['data']['images'])
    elif data['status'] == 404 and endpoint != "gallery/r/all":
        endpoint = "gallery/r/all"
        log.debug("Not found, seeing if it is a subreddit image")
        r = bot.get_url("%s/%s/%s" % (api, endpoint, resource_id), headers=headers)
        data = r.json()
        if data['status'] == 200:
            title = r.json()['data']['title']
    else:
        log.debug("imgur API error: %d %s" % (data['status'], data['data']['error']))
        return None

    if not title:
        return None

    return ("Imgur: %s" % title)

def _handle_amazon(url):
    '''http://*.amazon.com/*'''
    bs = __get_bs(url)
    
    try:
        titletag = bs.find("#btAsinTitle")
        pricetag = bs.find("#actualPriceValue")
        title = titletag[0].text.strip()
        log.info(title)
    except Exception:
        titletag = bs.find("h1", id = "title")
        pricetag = bs.find(class_ = "offer-price")
        log.info(titletag.contents)
    
    try:
        title = titletag.contents[0].string.strip()
        price = pricetag.text
        pricedisp = price[price.index('$'):]
    except Exception:
        pricetag = bs.find("span", id = "priceblock_ourprice")
        
    try:
        price = pricetag.text
        pricedisp = price[price.index('$'):]
    except Exception:
        pricedisp = "$?.??"
        
    return("Amazon: %s -- %s" % (title, pricedisp))

def _handle_newegg(url):
    '''http://www.newegg.com/Product/Product.aspx?Item=*'''
    pid = url[url.index('=')+1:]
    if len(pid) > 15:
        pid = pid[:pid.index('&')]
        
    r = bot.get_url('http://www.ows.newegg.com/Products.egg/' + pid)
    
    data = r.json()
    
    title = data['Title']
    pricedisp = data['FinalPrice']
        
    return("Newegg: %s -- %s" % (title, pricedisp))
    

def _handle_beeradvocate(url):
    '''http://beeradvocate.com/beer/profile/*'''
    bs = __get_bs(url)
    
    head = bs.find(class_ = "titleBar").h1.text.split('-')
    name = head[0].strip()
    company = head[1].strip()
    score = bs.find(class_ = "BAscore_big").text
    
#     for thing in bs.find(class_="titleBar").contents:
#         log.info(thing[0])
    
    return("BeerAdvocate: %s by %s [BA Score %s]" % (name, company, score))
    
def _handle_ocremix(url):
    '''http://ocremix.org/remix/*'''
    bs = __get_bs(url)
    
    info = bs.find(class_ = "middle-column-full").h1.text.split("'")
    game = info[0].strip()[7:]
    name = info[1].strip()
    
    artist = bs.find('a', href=re.compile('^/artist/')).text
    
    return("OCRemix: %s, remix of %s by %s" % (name, game, artist))
