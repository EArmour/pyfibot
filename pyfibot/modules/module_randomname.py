# -*- coding: utf-8 -*-
"""Generates a random name

From Behind the Name
"""

from bs4 import BeautifulSoup as bs4
import urllib
import logging
log = logging.getLogger('rname')
from util import getnick

api = "http://www.behindthename.com/api/random.php?usage=%s&gender=%s&randomsurname=yes&number=1&key=ev465701"
genders = ['m','f','b']

def command_rname(bot, user, channel, args):
    inputs = args.split()
    
    gender = ""
    usage = ""
    
    for arg in inputs:
        if arg.lower() in genders:
            gender = arg
        else:
            usage += ' ' + arg
            
    usage = usage.strip()
            
    usage_codes = {
        "African": "afr",
        "Akan": "aka",
        "Albanian": "alb",
        "Algonquin": "alg",
        "Native American": "ame",
        "Amharic": "amh",
        "Ancient": "anci",
        "Apache": "apa",
        "Arabic": "ara",
        "Armenian": "arm",
        "Astronomy": "astr",
        "Indigenous Australian": "aus",
        "Aymara": "aym",
        "Azerbaijani": "aze",
        "Basque": "bas",
        "Bengali": "ben",
        "Berber": "ber",
        "Biblical": "bibl",
        "Bosnian": "bos",
        "Breton": "bre",
        "Bulgarian": "bul",
        "Catalan": "cat",
        "Ancient Celtic": "cela",
        "Celtic Mythology": "celm",
        "Chinese": "chi",
        "Choctaw": "cht",
        "Comanche": "com",
        "Coptic": "cop",
        "Cornish": "cor",
        "Cree": "cre",
        "Croatian": "cro",
        "Corsican": "crs",
        "Czech": "cze",
        "Danish": "dan",
        "Dutch": "dut",
        "English": "eng",
        "Esperanto": "esp",
        "Estonian": "est",
        "Ewe": "ewe",
        "Fairy": "fairy",
        "Filipino": "fil",
        "Finnish": "fin",
        "Flemish": "fle",
        "French": "fre",
        "Frisian": "fri",
        "Galician": "gal",
        "Ganda": "gan",
        "Georgian": "geo",
        "German": "ger",
        "Goth": "goth",
        "Greek": "gre",
        "Ancient Greek": "grea",
        "Greek Mythology": "grem",
        "Greenlandic": "grn",
        "Hawaiian": "haw",
        "Hillbilly": "hb",
        "Hippy": "hippy",
        "History": "hist",
        "Hungarian": "hun",
        "Ibibio": "ibi",
        "Icelandic": "ice",
        "Igbo": "igb",
        "Indian": "ind",
        "Indian Mythology": "indm",
        "Indonesian": "ins",
        "Inuit": "inu",
        "Iranian": "ira",
        "Irish": "iri",
        "Iroquois": "iro",
        "Italian": "ita",
        "Japanese": "jap",
        "Jewish": "jew",
        "Kazakh": "kaz",
        "Khmer": "khm",
        "Kikuyu": "kik",
        "Kreatyve": "kk",
        "Korean": "kor",
        "Kurdish": "kur",
        "Kyrgyz": "kyr",
        "Latvian": "lat",
        "Limburgish": "lim",
        "Literature": "lite",
        "Lithuanian": "lth",
        "Luhya": "luh",
        "Luo": "luo",
        "Macedonian": "mac",
        "Maltese": "mal",
        "Manx": "man",
        "Maori": "mao",
        "Mapuche": "map",
        "Mayan": "may",
        "Medieval": "medi",
        "Mongolian": "mon",
        "Mormon": "morm",
        "Mwera": "mwe",
        "Mythology": "myth",
        "Nahuatl": "nah",
        "Navajo": "nav",
        "Ndebele": "nde",
        "Norwegian": "nor",
        "Nuu-chah-nulth": "nuu",
        "Occitan": "occ",
        "Ojibwe": "oji",
        "Pacific/Polynesian": "pac",
        "Pakistani": "pak",
        "Pet": "pets",
        "Polish": "pol",
        "Popular Culture": "popu",
        "Portuguese": "por",
        "Punjabi": "pun",
        "Quechua": "que",
        "Rapper": "rap",
        "Romanian": "rmn",
        "Ancient Roman": "roma",
        "Roman Mythology": "romm",
        "Russian": "rus",
        "Sami": "sam",
        "Norse Mythology": "scam",
        "Scottish": "sco",
        "Serbian": "ser",
        "Shawnee": "sha",
        "Shona": "sho",
        "Sioux": "sio",
        "Norse Mythology": "slam",
        "Slovak": "slk",
        "Slovene": "sln",
        "Sotho": "sot",
        "Spanish": "spa",
        "Swahili": "swa",
        "Swedish": "swe",
        "Tagalog": "tag",
        "Tamil": "tam",
        "Telugu": "tel",
        "Ancient Germanic": "teua",
        "Thai": "tha",
        "Theology": "theo",
        "Tibetan": "tib",
        "Transformer": "trans",
        "Tswana": "tsw",
        "Tumbuka": "tum",
        "Turkish": "tur",
        "Ukrainian": "ukr",
        "?": "unkn",
        "Urdu": "urd",
        "American": "usa",
        "Various": "vari",
        "Vietnamese": "vie",
        "Welsh": "wel",
        "Witch": "witch",
        "Wrestler": "wrest",
        "Xhosa": "xho",
        "Yao": "yao",
        "Yoruba": "yor",
        "Zapotec": "zap",
        "Zulu": "zul",
    }
    
    matched = False
    for full, code in usage_codes.items():
        if usage.lower() == full.lower() or usage.lower() == code.lower():
            usage = code
            utext = full
            matched = True
            break
            
    if matched is False:
        return bot.say(channel, "No code found for '%s.' (http://www.behindthename.com/api/appendix2.php)" % usage)

    if gender.lower() == 'm':
        gtext = "a man"
    elif gender.lower() == 'f':
        gtext = "a woman"
    else:
        gender = 'both'
        gtext = "any gender"

    data = urllib.urlopen(api % (usage, gender))
    parsed = bs4(data,'xml')
    
    nick = getnick.get(user)

    return bot.say(channel, "%s: Random %s name for %s: %s" % (nick, utext, gtext, parsed.get_text().encode('utf8').strip()))