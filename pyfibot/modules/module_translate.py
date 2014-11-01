# -*- coding: utf-8 -*-
import requests, json

gturl = "http://translate.google.com/translate_a/t"
gtheaders = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:27.0) Gecko/20100101 Firefox/27.0'}
gtbody = "client=gtranslate&sl=&tl=en&text=%s"


def command_translate(bot, user, channel, args):
    """.translate [text] - Translates text with Google Translate (language auto-detected"""
    gtrans = requests.post(gturl, data=gtbody % (args.encode('utf-8')), headers=gtheaders)
    jsondata = gtrans.json()
    translated = jsondata['sentences'][0]['trans']
    bot.say(channel, "From " + jsondata['src'] + ": " + translated)


def command_transliterate(bot, user, channel, args):
    """.transliterate [text] - Transliterates text with Google Translate (language auto-detected"""
    gtrans = requests.post(gturl, data=gtbody % (args.encode('utf-8')), headers=gtheaders)
    jsondata = gtrans.json()
    transliterated = jsondata['sentences'][0]['src_translit']
    if transliterated == "":
        bot.say(channel, "No transliteration available.")
    else:
        bot.say(channel, "From " + jsondata['src'] + ": " + transliterated)