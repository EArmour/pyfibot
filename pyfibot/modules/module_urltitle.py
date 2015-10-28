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
import urllib

from repoze.lru import ExpiringLRUCache

from bs4 import BeautifulSoup

import botcore
from util import pyfiurl

has_json = True

log = logging.getLogger("urltitle")
config = None
bot = None
handlers = []

global recursecount
recursecount = 0
global norepeat
norepeat = []

TITLE_LAG_MAXIMUM = 10

# Caching for url titles
cache_timeout = 300  # 300 second timeout for cache
cache = ExpiringLRUCache(10, cache_timeout)
CACHE_ENABLED = True


def init(botref):
    global config
    global bot
    global handlers
    bot = botref
    config = bot.config.get("module_urltitle", {})
    # load handlers in init, as the data doesn't change between rehashes anyways
    handlers = [(h, ref) for h, ref in globals().items() if h.startswith("_handle_")]


def __get_bs(url, headers = None):
    # Fetch the content and measure how long it took
    start = datetime.now()
    r = bot.get_url(url, headers=headers)
    end = datetime.now()

    if not r:
        return None

    duration = (end - start).seconds
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
            log.debug("Infinite (or just annoyingly long) recursion detected; aborting!")
            return
    else:
        recursecount = 0

    urls = pyfiurl.grab(title.encode("UTF-8"))
    if urls:
        log.info(urls)
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


def __get_title_tag(url):
    bs = __get_bs(url)
    if not bs:
        return False

    title = bs.find('title')
    if not title:
        return

    return title.text


def __get_length_str(secs):
    lengthstr = []
    hours, minutes, seconds = secs // 3600, secs // 60 % 60, secs % 60
    if hours > 0:
        lengthstr.append("%dh" % hours)
    if minutes > 0:
        lengthstr.append("%dm" % minutes)
    if seconds > 0:
        lengthstr.append("%ds" % seconds)
    if not lengthstr:
        lengthstr = ['0s']
    return ''.join(lengthstr)


def __get_age_str(published):
    now = datetime.now()

    # Check if the publish date is in the future (upcoming episode)
    if published > now:
        age = published - now
        future = True
    else:
        age = now - published
        future = False

    halfyears, days = age.days // 182, age.days % 365
    agestr = []
    years = halfyears * 0.5
    if years >= 1:
        agestr.append("%gy" % years)
    # don't display days for videos older than 6 months
    if years < 1 and days > 0:
        agestr.append("%dd" % days)
    # complete the age string
    if agestr and (years or days):
        agestr.append(" from now" if future else " ago")
    elif years == 0 and days == 0:  # uploaded TODAY, whoa.
        agestr.append("FRESH")
    # If it shouldn't happen, why is it needed? ;)
    # else:
    #     agestr.append("ANANASAKÄÄMÄ")  # this should never happen =)
    return "".join(agestr)


def command_cache(bot, user, channel, args):
    global CACHE_ENABLED
    if isAdmin(user):
        CACHE_ENABLED = not CACHE_ENABLED
        # cache was just disabled, clear it
        if not CACHE_ENABLED:
            cache.clear()
            bot.say(channel, 'Cache cleared')
        msg = 'Cache status: %s' % ('ENABLED' if CACHE_ENABLED else 'DISABLED')
        bot.say(channel, msg)


def handle_url(bot, user, channel, url, msg):
    """Handle urls"""

    if msg[msg.find(url) - 1] == '-':
        return
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

    # Check if the url already has a title cached
    if CACHE_ENABLED:
        title = cache.get(url)
        if title:
            log.debug("Cache hit")
            return _title(bot, channel, title, True)

    global handlers
    # try to find a specific handler for the URL
    for handler, ref in handlers:
        pattern = ref.__doc__.split()[0]
        if fnmatch.fnmatch(url, pattern):
            title = ref(url)
            if title is False:
                log.debug("Title disabled by handler.")
                return
            elif title:
                cache.put(url, title)
                # handler found, abort
                _title(bot, channel, title, True)
                recurse(bot, user, title, channel)
            else:
                # No specific handler, use generic (BUT DON'T)
                return


def _title(bot, channel, title, smart=False):
    """Say title to channel"""

    if not title:
        return

    info = None
    # tuple, additional info
    if type(title) == TupleType:
        info = title[1]
        title = title[0]
    # crop obscenely long titles
    if len(title) > 200:
        title = title[:200] + "..."

    if not info:
        return bot.say(channel, "%s" % title)
    else:
        return bot.say(channel, "%s [%s]" % (title, info))

# Some handlers does not have if not bs: return, but why do we even have this for every function
def _handle_tweet2(url):
    """http*://twitter.com/*/status/*"""
    return _handle_tweet(url)
	
	
def _handle_mobiletweet(url):
	"""http*://mobile.twitter.com/*/status/*"""
	return _handle_tweet(url)

	
def _handle_tweet(url):
    """http*://twitter.com/*/statuses/*"""
    tweet_url = "https://api.twitter.com/1.1/statuses/show.json?id=%s"
    test = re.match("https?://(mobile.)?twitter\.com\/(\w+)/status(es)?/(\d+)", url)
    #    matches for unique tweet id string
    infourl = tweet_url % test.group(4)

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
    api_key = config.get('google_apikey')

    api_url = 'https://www.googleapis.com/youtube/v3/videos'

    match = re.match("https?://youtu.be/([^?&]+)", url)
    if not match:
        match = re.match("https?://.*?youtube.com/watch\?.*?v=([^?&]+)", url)
    if match:
        params = {'id': match.group(1),
                  'part': 'snippet,contentDetails,statistics',
                  'fields': 'items(id,snippet,contentDetails,statistics)',
                  'key': api_key}

        r = bot.get_url(api_url, params=params)

        if not r.status_code == 200:
            error = r.json().get('error')
            if error:
                error = '%s: %s' % (error['code'], error['message'])
            else:
                error = r.status_code

            log.warning('YouTube API error: %s', error)
            return

        items = r.json()['items']
        if len(items) == 0: return

        entry = items[0]

        channel = entry['snippet']['channelTitle']

        title = entry['snippet']['title']

        # The tag value is an ISO 8601 duration in the format PT#M#S
        duration = entry['contentDetails']['duration'][2:].lower()

        return "YouTube: %s [by %s | %s]" % (title, channel, duration)


def _handle_steamgame(url):
    """http://store.steampowered.com/app/*"""
    bs = __get_bs(url, headers={'Cookie':'birthtime=725875201'})
    
    title = bs.find(itemprop="name").text.strip()

    try:
        price = bs.find(itemprop="price")['content']
        reception = bs.find("span", {'class': 'game_review_summary'}).text.strip().lower()
        return "Steam: %s -- $%s (Generally %s reviews)" % (title, price, reception)
    except (AttributeError, TypeError):  # Pre-release game
        releasedate = bs.find("div", {'class': 'game_area_comingsoon'}).find("h1").text.strip()
        try:
            price = bs.find(itemprop="price")['content']
            return "Steam: %s -- $%s (%s)" % (title, price, releasedate)
        except (AttributeError, TypeError):
            return "Steam: %s -- %s" % (title, releasedate)


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


def _handle_alko(url):
    """http://www.alko.fi/tuotteet/fi/*"""
    bs = __get_bs(url)
    if not bs:
        return
    name = bs.find('span', {'class': 'tuote_otsikko'}).string
    price = bs.find('span', {'class': 'tuote_hinta'}).string.split(" ")[0] + u"€"
    drinktype = bs.find('span', {'class': 'tuote_tyyppi'}).next
    return name + " - " + drinktype + " - " + price


def _handle_salakuunneltua(url):
    """*salakuunneltua.fi*"""
    return None


def _handle_vimeo(url):
    """*vimeo.com/*"""
    data_url = "http://vimeo.com/api/v2/video/%s.json"
    match = re.match("http(s?)://.*?vimeo.com/(\d+)", url)
    if not match:
        return None
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



def _handle_stackoverflow(url):
    """*stackoverflow.com/questions/*"""
    api_url = 'http://api.stackoverflow.com/1.1/questions/%s'
    match = re.match('.*stackoverflow.com/questions/([0-9]+)', url)
    if match is None:
        return
    question_id = match.group(1)
    content = bot.get_url(api_url % question_id, params={'site': 'stackoverflow'})

    try:
        data = content.json()
        item = data['items'][0]

        title = item['title']
        tags = '/'.join(item['tags'])
        score = item['score']
        return "%s - %dpts - %s" % (title, score, tags)
    except Exception, e:
        log.debug("Json parsing failed %s" % e)
        return


def _handle_imgur(url):
    """http*://*imgur.com*"""

    def create_title(data):
        section = data['data']['section']
        title = data['data']['title']

        if not title:
            # If title wasn't found, use title and section of first image
            title = data['data']['images'][0]['title']
            section = data['data']['images'][0]['section']

        # if section:
        #     return "%s (/r/%s)" % (title, section)
        return title

    client_id = config.get("imgur_clientid")
    api = "https://api.imgur.com/3"
    headers = {"Authorization": "Client-ID %s" % client_id}

    # regexes and matching API endpoints
    endpoints = [("imgur.com/r/.*?/(.*)", "gallery/r/all"),
                 ("i.imgur.com/(.*)\.(jpg|png|gif)", "gallery"),
                 ("imgur.com/gallery/(.*)", "gallery"),
                 ("imgur.com/a/([^\?]+)", "album"),
                 ("imgur.com/([^\./]+)", "gallery")]

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
        return "No endpoint found"

    r = bot.get_url("%s/%s/%s" % (api, endpoint, resource_id), headers=headers)
    if not r.content:
        if endpoint != "gallery/r/all":
            endpoint = "gallery/r/all"
            log.debug("switching to endpoint gallery/r/all because of empty response")
            r = bot.get_url("%s/%s/%s" % (api, endpoint, resource_id), headers=headers)
            if not r.content:
                log.warn("Empty response after retry!")
                return
        else:
            log.warn("Empty response!")
            return

    data = r.json()

    if data['status'] == 200:
        title = create_title(r.json())
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
            title = create_title(r.json())
        else:
            return None
    else:
        log.debug("imgur API error: %d %s" % (data['status'], data['data']['error']))
        return None

    if not title:
        return None
    
    return ("Imgur: %s" % title)

def _handle_liveleak(url):
    """http://*liveleak.com/view?i=*"""
    try:
        id = url.split('view?i=')[1]
    except IndexError:
        log.debug('ID not found')
        return

    bs = __get_bs(url)
    if not bs:
        return
    title = bs.find('span', 'section_title').text.strip()
    info = str(bs.find('span', id='item_info_%s' % id))

    added_by = '???'
    tags = 'none'
    date_added = '???'
    views = '???'

    # need to do this kind of crap, as the data isn't contained by a span
    try:
        added_by = BeautifulSoup(info.split('<strong>By:</strong>')[1].split('<br')[0]).find('a').text
    except:
        pass

    try:
        date_added = info.split('</span>')[1].split('<span>')[0].strip()
    except:
        pass

    try:
        views = __get_views(int(info.split('<strong>Views:</strong>')[1].split('|')[0].strip()))
    except:
        pass

    try:
        tags = BeautifulSoup(info.split('<strong>Tags:</strong>')[1].split('<br')[0]).text
    except:
        pass

    return '%s by %s [%s views - %s - tags: %s]' % (title, added_by, views, date_added, tags)


def _handle_dailymotion(url):
    """http://*dailymotion.com/video/*"""
    video_id = url.split('/')[-1].split('_')[0]
    params = {
        'fields': ','.join([
            'owner.screenname',
            'title',
            'modified_time',
            'duration',
            'rating',
            'views_total',
            'explicit'
        ]),
        'family_filter': 0,
        'localization': 'en'
    }
    api = 'https://api.dailymotion.com/video/%s'
    try:
        r = bot.get_url(api % video_id, params=params).json()

        lengthstr = __get_length_str(r['duration'])
        stars = "[%-5s]" % (int(round(r['rating'])) * "*")
        views = __get_views(r['views_total'])
        agestr = __get_age_str(datetime.fromtimestamp(r['modified_time']))
        if r['explicit']:
            adult = ' - XXX'
        else:
            adult = ''

        return "%s by %s [%s - %s - %s views - %s%s]" % (r['title'], r['owner.screenname'], lengthstr, stars, views, agestr, adult)
    except:
        return

def _handle_beeradvocate(url):
    '''http://*.beeradvocate.com/beer/profile/*'''
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


def _handle_ebay(url):
    """http*://*.ebay.*/itm/*"""
    try:
        item_id = url.split('/')[-1].split('?')[0]
    except IndexError:
        log.debug("Couldn't find item ID.")
        return

    app_id = config.get('ebay_appid', 'RikuLind-3b6d-4c30-937c-6e7d87b5d8be')
    # 77 == Germany, prices in EUR
    site_id = config.get('ebay_siteid', 77)
    currency = config.get('ebay_currency', 'e')

    api_url = 'http://open.api.ebay.com/shopping'
    params = {
        'callname': 'GetSingleItem',
        'responseencoding': 'JSON',
        'appid': app_id,
        'siteid': site_id,
        'version': 515,
        'ItemID': item_id,
        'IncludeSelector': 'ShippingCosts'
    }

    r = bot.get_url(api_url, params=params)
    # if status_code != 200 or Ack != 'Success', something went wrong and data couldn't be found.
    if r.status_code != 200 or r.json()['Ack'] != 'Success':
        log.debug("eBay: data couldn't be fetched.")
        return

    item = r.json()['Item']

    name = item['Title']
    # ConvertedCurrentPrice holds the value of item in currency determined by site id
    price = item['ConvertedCurrentPrice']['Value']
    location = '%s, %s' % (item['Location'], item['Country'])

    ended = ''
    if item['ListingStatus'] != 'Active':
        ended = ' - ENDED'

    if 'ShippingCostSummary' in item and \
       'ShippingServiceCost' in item['ShippingCostSummary'] and \
       item['ShippingCostSummary']['ShippingServiceCost']['Value'] != 0:
            price = '%.1f%s (postage %.1f%s)' % (
                price, currency,
                item['ShippingCostSummary']['ShippingServiceCost']['Value'], currency)
    else:
        price = '%.1f%s' % (price, currency)

    try:
        if item['QuantityAvailableHint'] == 'MoreThan':
            availability = 'over %i available' % item['QuantityThreshold']
        else:
            availability = '%d available' % item['QuantityThreshold']
        return '%s [%s - %s - ships from %s%s]' % (name, price, availability, location, ended)
    except KeyError:
        log.debug('eBay: quantity available not be found.')
        return '%s [%s - ships from %s%s]' % (name, price, location, ended)


def _handle_ebay_no_prefix(url):
    """http*://ebay.*/itm/*"""
    return _handle_ebay(url)


def _handle_ebay_cgi(url):
    """http*://cgi.ebay.*/ws/eBayISAPI.dll?ViewItem&item=*"""
    item_id = url.split('item=')[1].split('&')[0]
    fake_url = 'http://ebay.com/itm/%s' % item_id
    return _handle_ebay(fake_url)


def _handle_dealextreme(url):
    """http*://dx.com/p/*"""
    sku = url.split('?')[0].split('-')[-1]
    cookies = {'DXGlobalization': 'lang=en&locale=en-US&currency=EUR'}
    api_url = 'http://dx.com/bi/GetSKUInfo?sku=%s' % sku

    r = bot.get_url(api_url, cookies=cookies)

    try:
        data = r.json()
    except:
        log.debug('DX.com API error.')
        return

    if 'success' not in data or data['success'] is not True:
        log.debug('DX.com unsuccessful')
        return

    if 'products' not in data or len(data['products']) < 1:
        log.debug("DX.com couldn't find products")
        return

    product = data['products'][0]
    name = product['headLine']
    price = float(product['price'].replace(u'€', ''))

    if product['reviewCount'] > 0:
        reviews = product['reviewCount']
        stars = "[%-5s]" % (product['avgRating'] * "*")
        return '%s [%.2fe - %s - %i reviews]' % (name, price, stars, reviews)
    return '%s [%.2fe]' % (name, price)


def _handle_dealextreme_www(url):
    """http*://www.dx.com/p/*"""
    return _handle_dealextreme(url)


def _handle_instagram(url):
    """http*://instagram.com/p/*"""
    from instagram.client import InstagramAPI

    CLIENT_ID = '879b81dc0ff74f179f5148ca5752e8ce'

    api = InstagramAPI(client_id=CLIENT_ID)

    # todo: instagr.am
    m = re.search('instagram\.com/p/([^/]+)', url)
    if not m:
        return

    shortcode = m.group(1)

    r = bot.get_url("http://api.instagram.com/oembed?url=http://instagram.com/p/%s/" % shortcode)

    media = api.media(r.json()['media_id'])

    print(media)

    # media type video/image?
    # age/date? -> media.created_time  # (datetime object)

    # full name = username for some users, don't bother displaying both
    if media.user.full_name.lower() != media.user.username.lower():
        user = "%s (%s)" % (media.user.full_name, media.user.username)
    else:
        user = media.user.full_name

    if media.caption:
        return "%s: %s [%d likes, %d comments]" % (user, media.caption.text, media.like_count, media.comment_count)
    else:
        return "%s [%d likes, %d comments]" % (user, media.like_count, media.comment_count)


def _handle_hitbox(url):
    """http*://*hitbox.tv/*"""

   # Blog and Help subdomains aren't implemented in Angular JS and works fine with default handler
    if re.match("http://(help|blog)\.hitbox\.tv/.*", url):
        return

    # Hitbox titles are populated by JavaScript so they return a useless "{{meta.title}}", don't show those
    elif not re.match("http://(www\.)?hitbox\.tv/([a-z0-9]+)$", url):
        return False

    # For actual stream pages, let's fetch information via the hitbox API
    else:
        streamname = url.rsplit('/', 2)[2]
        api_url = 'http://api.hitbox.tv/media/live/%s' % streamname

        r = bot.get_url(api_url)

        try:
            data = r.json()
        except:
            log.debug('can\'t parse, probably wrong stream name')
            return False

        hitboxname = data['livestream'][0]['media_display_name']
        streamtitle = data['livestream'][0]['media_status']
        streamgame = data['livestream'][0]['category_name_short']
        streamlive = data['livestream'][0]['media_is_live']

        if streamgame is None:
            streamgame = ""
        else:
            streamgame = '[%s] ' % (streamgame)

        if streamlive == '1':
            return '%s%s - %s - LIVE' % (streamgame, hitboxname, streamtitle)
        else:
            return '%s%s - %s - OFFLINE' % (streamgame, hitboxname, streamtitle)

        return False


def _handle_google_play_music(url):
    """http*://play.google.com/music/*"""
    bs = __get_bs(url)
    if not bs:
        return False

    title = bs.find('meta', {'property': 'og:title'})
    description = bs.find('meta', {'property': 'og:description'})
    if not title:
        return False
    elif title['content'] == description['content']:
        return False
    else:
        return title['content']


def _handle_github(url):
    """http*://*github.com*"""
    bs = __get_bs(url)
    if not bs:
        return False

    repo = bs.find('a', {'class': 'js-current-repository'}).text.strip()
    desc = bs.find('div', {'class': 'repository-description'}).text.strip()
    return "GitHub: %s - %s" % (repo, desc)


def _handle_gitio(url):
    """http*://git.io*"""
    return __get_title_tag(url)

def _handle_vine(url):
    """http*://vine.co/v/*"""
    bs = __get_bs(url)
    log.error(bs)
    if not bs:
        return False

    desc = bs.find('meta', {'property': 'twitter:description'})
    title = bs.find('meta', {'property': 'twitter:title'})
    if not desc:
        return False
    else:
        return "%s: %s" % (desc['content'], title['content'])
