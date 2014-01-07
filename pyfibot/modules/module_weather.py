# -*- coding: utf-8 -*-
from __future__ import print_function, division
import logging, json, os, sys
from datetime import datetime, timedelta
from util import getnick

log = logging.getLogger('weather')
defaults = {}
defaultsLower = {}
url = 'http://api.wunderground.com/api/%s/conditions/forecast/almanac/q/%s.json'

def init(bot):
    global defaults, defaultsLower, api_key
    
    config = bot.config.get('module_weather', {})
    api_key = config.get('wunderground_key')
    with open(os.path.join(sys.path[0], 'modules', 'module_weather_conf.json')) as configfile:
        defaults = json.load(configfile)
        #For case-insensitive matching
        defaultsLower = {key.lower():value for key,value in defaults.items()}

def command_weather(bot, user, channel, args):
    """.weather [set] (location) - Gets weather from Weather Underground (Can store per-user defaults). Also .fullweather, .forecast"""
    global defaults, defaultsLower
    nick = getnick.get(user)
    
    if not args:
        if nick in defaults:
            return get_weather(bot, nick, channel, defaults[nick], True)
        else:
            return bot.say(channel,"No location specified, and no default found! Use '.weather set [LOC]' to set a default.")
    
    splut = args.split(' ', 1)
    cmd = splut[0].lower();
    if cmd == "set":
        set_weather_default(bot, nick, channel, splut[1])
    elif cmd in defaultsLower:
        return get_weather(bot, nick, channel, defaultsLower[cmd], True)
    else:
        return get_weather(bot, nick, channel, args, True)

def set_weather_default(bot, nick, channel, args):
    global defaults, defaultsLower
    
    defaults[nick] = args
    defaultsLower[nick.lower()] = args
    with open(os.path.join(sys.path[0], 'modules', 'module_weather_conf.json'),'w') as file:
        json.dump(defaults, file)
    bot.say(channel,"Default location for {0} set to {1}".format(nick, args))

def command_fullweather(bot, user, channel, args):
    """.fullweather (location) - Gets more weather info from Weather Underground (wind speed and barometric pressure)"""
    global defaults, defaultsLower
    nick = getnick.get(user)
    
    if not args:
        if nick in defaults:
            parsed = get_weather(bot, nick, channel, defaults[nick], True)
        else:
            return bot.say(channel,"No location specified, and no default found! Use '.weather set [LOC]' to set a default.")
    elif args in defaultsLower:
        parsed = get_weather(bot, nick, channel, defaultsLower[args], True)
    else:
        parsed = get_weather(bot, nick, channel, args, True)
        
    info = parsed['current_observation']
    
    wind = info['wind_mph']
    direction = info['wind_dir']
    pressure = info['pressure_mb']
    
    if info['pressure_trend'] == "-":
        pressuretext = "downward"
    else:
        pressuretext = "upward"
    
    bot.say(channel, "Wind: %smph from the %s | Pressure: %smb, trending %s" % (wind, direction, pressure, pressuretext))
    
    history = info['history_url']
    
    bot.say(channel, "Station history at: %s" % history)
    
def command_forecast(bot, user, channel, args):
    """.forecast (location) - Gets next two forecast periods from Weather Underground"""
    global defaults, defaultsLower
    nick = getnick.get(user)
    
    if not args:
        if nick in defaults:
            parsed = get_weather(bot, nick, channel, defaults[nick], False)
        else:
            return bot.say(channel,"No location specified, and no default found! Use '.weather set [LOC]' to set a default.")
    elif args in defaultsLower:
        parsed = get_weather(bot, nick, channel, defaultsLower[args], False)
    else:
        parsed = get_weather(bot, nick, channel, args, False)
        
    info = parsed['forecast']['txt_forecast']['forecastday']
    
    current = info[0]['title']
    currentfc = info[0]['fcttext']
    
    next = info[1]['title']
    nextfc = info[1]['fcttext']
    
    bot.say(channel, "Forecast for %s: %s" % (current, currentfc))
    bot.say(channel, "For %s: %s" % (next, nextfc))
    
def command_records(bot, user, channel, args):
    """.records (location) - Gets the average and record temps for a location from Weather Underground"""
    global defaults, defaultsLower
    nick = getnick.get(user)
    
    if not args:
        if nick in defaults:
            parsed = get_weather(bot, nick, channel, defaults[nick], False)
        else:
            return bot.say(channel,"No location specified, and no default found! Use '.weather set [LOC]' to set a default.")
    elif args in defaultsLower:
        parsed = get_weather(bot, nick, channel, defaultsLower[args], False)
    else:
        parsed = get_weather(bot, nick, channel, args, False)
    
    airport = parsed['almanac']['airport_code']
    highInfo = parsed['almanac']['temp_high']
    lowInfo = parsed['almanac']['temp_low']
    
    highTemp = highInfo['record']['F']
    lowTemp = lowInfo['record']['F']
    highYear = highInfo['recordyear']
    lowYear = lowInfo['recordyear']
    
    degree_sign = u'\N{DEGREE SIGN}'
    bot.say(channel, "Today at %s: Highest %s (%s), Lowest %s (%s)" % (airport, str(highTemp) + degree_sign + 'F', highYear, str(lowTemp) + degree_sign + 'F', lowYear))
    
def get_weather(bot, nick, channel, args, output):
    global api_key
    
    location = args
    q = bot.get_url(url % (api_key, location))
    parsed = q.json()
    degree_sign = u'\N{DEGREE SIGN}'
    
    try:
        result = parsed['response']['results'][0]
        bestguess = result['zmw']
        guesscity = result['city']
        guessstate = result['state']
        if guessstate == "":
            guessstate = result['country_name']
        if output:
            bot.say(channel, 'Assuming you meant ' + guesscity + ', ' + guessstate + ', heeeeere\'s the weather!')
        
        q = bot.get_url(url % (api_key, 'zmw:' + bestguess))
        parsed = q.json()
    except KeyError:
        pass
    
    try:
        info = parsed['current_observation']
        
        location = info['observation_location']['full']
        temp = info['temp_f']
        tempc = info['temp_c']
        condition = info['weather']
        humidity = info['relative_humidity']
        
        if output:
            bot.say(channel, nick + ': [' + location + '] Temp: ' + str(temp) + degree_sign + 'F, ' + str(tempc) + degree_sign + 'C | Currently ' + condition + ' | Humidity of ' + humidity)
        return parsed
    except KeyError:
        error = parsed['response']['error']['description']
        bot.say(channel, "ERROR: %s [for query '%s']" % (error, location))
        pass
