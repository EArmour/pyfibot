# -*- coding: utf-8 -*-
from __future__ import print_function, division
import logging, json
from datetime import datetime, timedelta
from util import getnick

log = logging.getLogger('openweather')
url = 'http://api.wunderground.com/api/7773d26ca4446975/conditions/forecast/q/%s.json'
default_location = 'YZF'
defaults = {}

def init(bot):
    global defaults
    
    config = bot.config.get('module_openweather', {})
    default_location = config.get('default_location', 'YZF')
    log.info('Using %s as default location' % default_location)
    with open('/usr/pyfibot/pyfibot/modules/module_openweather_conf.json') as configfile:
        defaults = json.load(configfile)

def command_weather(bot, user, channel, args):
    global defaults
    
    if not args:
        if user in defaults:
            return get_weather(bot, user, channel, defaults[user], True)
        else:
            return bot.say(channel,"No location specified, and no default found! Use '.weather set [LOC]' to set a default.")
    
    splut = args.split(' ', 1)
    cmd = splut[0]
    if cmd == "set":
        set_weather_default(bot, user, channel, splut[1])
    else:
        get_weather(bot, user, channel, args, True)

def set_weather_default(bot, user, channel, args):
    global defaults
    
    defaults[user] = args
    bot.say(channel,"Default location for {0} set to {1}".format(getnick.get(user), args))
    with open('/usr/pyfibot/pyfibot/modules/module_openweather_conf.json','w') as file:
        json.dump(defaults, file)
    
def command_fullweather(bot, user, channel, args):
    global defaults
    
    if not args:
        if user in defaults:
            parsed = get_weather(bot, user, channel, defaults[user], True)
        else:
            return bot.say(channel,"No location specified, and no default found! Use '.weather set [LOC]' to set a default.")
    else:
        parsed = get_weather(bot, user, channel, args, True)
        
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
    global defaults
    
    if not args:
        if user in defaults:
            parsed = get_weather(bot, user, channel, defaults[user], False)
        else:
            return bot.say(channel,"No location specified, and no default found! Use '.weather set [LOC]' to set a default.")
    else:
        parsed = get_weather(bot, user, channel, args, False)
        
    info = parsed['forecast']['txt_forecast']['forecastday']
    
    current = info[0]['title']
    currentfc = info[0]['fcttext']
    
    next = info[1]['title']
    nextfc = info[1]['fcttext']
    
    bot.say(channel, "Forecast for %s: %s" % (current, currentfc))
    bot.say(channel, "For %s: %s" % (next, nextfc))
    
def get_weather(bot, user, channel, args, output):
    location = args
        
    q = bot.get_url(url % location)
    parsed = q.json()
    degree_sign= u'\N{DEGREE SIGN}'
    
    try:
        result = parsed['response']['results'][0]
        bestguess = result['zmw']
        guesscity = result['city']
        guessstate = result['state']
        if output:
            bot.say(channel, 'Assuming you meant ' + guesscity + ', ' + guessstate + ', heeeeere\'s the weather!')
        
        q = bot.get_url(url % bestguess)
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
            bot.say(channel, getnick.get(user) + ': [' + location + '] Temp: ' + str(temp) + degree_sign + 'F, ' + str(tempc) + degree_sign + 'C | Currently ' + condition + ' | Humidity of ' + humidity)
        return parsed
    except KeyError:
        error = parsed['response']['error']['description']
        bot.say(channel, "ERROR: %s [for query '%s']" % (error, location))
        pass
