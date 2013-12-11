# -*- coding: utf-8 -*-
"""
IT'S HEEEEERE
"""

import logging
import time
import urllib
import urllib2

from bs4 import BeautifulSoup as bs4
import requests

log = logging.getLogger("steam")
storeurl = "http://store.steampowered.com/"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:22.0) Gecko/20100101 Firefox/22.0", "Accept": "*/*", "Host": "sapi.techieanalyst.net", "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "Content-Length": "26"}

def command_price(bot, user, channel, args):
    search = args.replace(" ","+")
#     req = urllib2.Request("http://store.steampowered.com/search/?term=%s&category1=998" % search, headers={"User-Agent":"Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11"})
#     db = bs4(urllib2.urlopen(req).read())
    db = bs4(urllib.urlopen("http://store.steampowered.com/search/?term=%s&category1=998" % search))
    row = db.find(class_ = "search_result_row")
    appid = row['href'][34:40].strip("/")
    xml = requests.get("http://steamsales.rhekua.com/xml/sales/app_%s.xml" % appid)
    pricehist = bs4(xml.text)
    
    log.info(row.find(class_ = "search_price").contents)
    price = row.find(class_ = "search_price").contents[2].string
    name = row.find(class_ = "search_name").h4.text
    
    log.info(name)
    log.info(appid)
    log.info(price)
    current = float(price[1:])
    
    lowest = current
    date = "never"
    for entry in pricehist.find_all('set'):
        price = float(entry['value'])
        if price < lowest:
            lowest = price
            date = entry['name']
        elif price == lowest:
            if not date == "never":
                date = entry['name']
    
    if lowest == current:
        bot.say(channel, name + " has never been cheaper than the $" + str(current) + " it is right now!")
    else:
        bot.say(channel, name + " is $" + str(current) + " now, but was $" + str(lowest) + " on " + date)
        

def command_flashdeals(bot, user, channel, args):
#     store = bs4(urllib.urlopen(storeurl))
#     
#     flashes = store.find(class_ = "flashdeals_row")
#     links = flashes.find_all('a')
    
#     script = store.find_all('script')
#     endunix = script[11].string[143:153]
#     countdown = int(endunix) - int(time.time())
#     timer = time.strftime('%H:%M:%S', time.gmtime(countdown))
    
#     bot.say(channel, "Current FLASH DEALS (%s remaining):" % timer)

    bot.say(channel, "There's no Steam sale on, silly!")

#     for flash in links:       
#         gname = get_name(flash)
#         gprice = get_price(flash)
#         bot.say(channel, "%s - %s" % (gname, gprice))
        
def get_name(flash):
    gameid = flash['href'][34:40]
    gameid = gameid.strip("/")
    r = requests.get('http://store.steampowered.com/apphoverpublic/%s?l=english' % gameid)
    hover = bs4("<html><head><title>Work</title></head><body>" + r.text + "</body></html>")
    name = hover.find('h4').string
    
    return name
    
def get_price(flash):
    price = flash.find(class_ = "discount_final_price").string
    
    return price
    