# -*- coding: utf-8 -*-
"""
IT'S HEEEEERE
"""

import logging
import time
import urllib

from bs4 import BeautifulSoup as bs4
import requests


log = logging.getLogger("steam")
storeurl = "http://store.steampowered.com/"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:22.0) Gecko/20100101 Firefox/22.0", "Accept": "*/*", "Host": "sapi.techieanalyst.net", "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "Content-Length": "26"}

def command_flashdeals(bot, user, channel, args):
    store = bs4(urllib.urlopen(storeurl))
    
    flashes = store.find(class_ = "flashdeals_row")
    links = flashes.find_all('a')
    
#     script = store.find_all('script')
#     endunix = script[11].string[143:153]
#     countdown = int(endunix) - int(time.time())
#     timer = time.strftime('%H:%M:%S', time.gmtime(countdown))
    
#     bot.say(channel, "Current FLASH DEALS (%s remaining):" % timer)

    bot.say(channel, "Current FLASH DEALS:")

    for flash in links:       
        gname = get_name(flash)
        gprice = get_price(flash)
        bot.say(channel, "%s - %s" % (gname, gprice))
        
def get_name(flash):
    id = flash['href'][34:-1]    
    r = requests.post('http://sapi.techieanalyst.net/search_result.php', data='search=%s&standalone=0' % id, headers = headers)
    
    s = bs4(r.text)
    name = s.find(class_ = "txtb1").string
    
    return name
    
def get_price(flash):
    price = flash.find(class_ = "discount_final_price").string
    
    return price
    