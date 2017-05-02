# -*- coding: utf-8 -*-
from __future__ import print_function, division
import logging, json, os, sys
from datetime import datetime, timedelta
from util import getnick

log = logging.getLogger('weather')
defaults = {}
defaultsLower = {}
url = 'http://api.wunderground.com/api/%s/conditions/forecast/almanac/q/%s.json'
degree_sign = u'\N{DEGREE SIGN}'

def init(bot):
    global defaults, defaultsLower, api_key
    
    config = bot.config.get('module_weather', {})
    api_key = config.get('wunderground_key')
    with open(os.path.join(sys.path[0], 'modules', 'module_weather_conf.json')) as configfile:
        defaults = json.load(configfile)
        #For case-insensitive matching
        defaultsLower = {key.lower():value for key,value in defaults.items()}

def command_weather(bot, user, channel, args):
    """.weather [set] (location) - Gets weather from Weather Underground (Can store per-user defaults). Also .fullweather, .forecast, .records"""
    global defaults, defaultsLower
    nick = getnick.get(user)
    
    if not args:
        if nick == "ashandarei":
            return bot.say(channel,"ashandarei: I dunno, probably like a perfect 72" + degree_sign + "F, you jerk")
        if nick in defaults:
            return get_weather(bot, nick, channel, defaults[nick], True)
        else:
            return bot.say(channel,"No location specified, and no default found! Use '.weather set [LOC]' to set a default.")
    
    splut = args.split(' ', 1)
    cmd = splut[0].lower()
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
        json.dump(defaults, file, indent=2, sort_keys=True)
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
    elif args.lower() in defaultsLower:
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
    elif args.lower() in defaultsLower:
        parsed = get_weather(bot, nick, channel, defaultsLower[args], False)
    else:
        parsed = get_weather(bot, nick, channel, args, False)
    
    time = parsed['current_observation']['local_time_rfc822']
    hour = int(time[17:19])

    if hour > 20: # After 8pm, start with tomorrow day
        start = 2
    elif hour > 14: # After 2pm, until 8pm, show tonight and tomorrow day
        start = 1
    else: # Before 2pm, show today and tonight
        start = 0
    
    forecast = parsed['forecast']['txt_forecast']['forecastday']
    
    firstName = forecast[start]['title']
    firstFcast = forecast[start]['fcttext']
    
    nextName = forecast[start + 1]['title']
    nextFcast = forecast[start + 1]['fcttext']
    
    bot.say(channel, "Forecast for %s: %s" % (firstName, firstFcast))
    bot.say(channel, "For %s: %s" % (nextName, nextFcast))
    
def command_records(bot, user, channel, args):
    """.records (location) - Gets the average and record temps for a location from Weather Underground"""
    global defaults, defaultsLower
    nick = getnick.get(user)
    
    if not args:
        if nick in defaults:
            parsed = get_weather(bot, nick, channel, defaults[nick], False)
        else:
            return bot.say(channel,"No location specified, and no default found! Use '.weather set [LOC]' to set a default.")
    elif args.lower() in defaultsLower:
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

    temp = parsed['current_observation']['temp_f']

    bot.say(channel, "Today at %s: Highest %s (%s), Lowest %s (%s) - Currently %s" % (airport, str(highTemp) +
                                                                                      degree_sign + 'F',
                                                                        highYear, str(lowTemp) + degree_sign + 'F',
                                                                        lowYear, str(temp) + degree_sign + 'F'))
    
def command_time(bot, user, channel, args):
    """.time (location) - Gets the current time and time zone of a location"""
    global defaults, defaultsLower
    nick = getnick.get(user)

    if not args:
        if nick in defaults:
            parsed = get_weather(bot, nick, channel, defaults[nick], False)
        else:
            return bot.say(channel,"No location specified! I hope you already know what time it is where you are.")
    elif args.lower() in defaultsLower:
        parsed = get_weather(bot, nick, channel, defaultsLower[args], False)
    else:
        parsed = get_weather(bot, nick, channel, args, False)
        
    try:
        info = parsed['current_observation']
        
        location = info['display_location']['full']
        time = info['local_time_rfc822']
        zone = info['local_tz_long']
        bot.say(channel, "In %s, it is currently %s (%s)" % (location, time, zone))
    except KeyError:
        error = parsed['response']['error']['description']
        bot.say(channel, "ERROR: %s [for query '%s']" % (error, location))
        pass
    
def command_weatherbattle(bot, user, channel, args):
    """.weatherbattle [user1] [user2] - Compares the temperature for two users and declares a winner!"""
    global defaults, defaultsLower
    degree_sign = u'\N{DEGREE SIGN}'
    
    splut = args.split(' ', 1)
    name1 = splut[0].lower().strip();
    name2 = splut[1].lower().strip();
    
    if name1 and name2 in defaultsLower:
        json1 = get_weather(bot, splut[0], channel, defaultsLower[name1], False)
        json2 = get_weather(bot, splut[1], channel, defaultsLower[name2], False)
    else:
        return bot.say(channel,"No stored location found for one or both of those users!")
            
    temp1 = json1['current_observation']['temp_f']
    temp2 = json2['current_observation']['temp_f']
    
    if temp1 > temp2:
        return bot.say(channel, "%s wins with %s to %s's %s!" % (splut[0], str(temp1) + degree_sign + 'F', splut[1], str(temp2) + degree_sign + 'F'))
    elif temp2 > temp1:
        return bot.say(channel, "%s wins with %s to %s's %s!" % (splut[1], str(temp2) + degree_sign + 'F', splut[0], str(temp1) + degree_sign + 'F'))
    else:
        return bot.say(channel, "It's a tie at %s!? I think someone is cheating the system!" % (str(temp1) + degree_sign + 'F'))
    
def get_weather(bot, nick, channel, args, output):
    global api_key
    
    location = args
    q = bot.get_url(url % (api_key, location))
    parsed = q.json()

    
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
        feels = info['feelslike_f']
        feelsc = info['feelslike_c']
        condition = info['weather']
        humidity = info['relative_humidity']
        
        if output:
            bot.say(channel, nick + ': [' + location + '] ' + fmt_temp(temp, tempc) + ' (Feels Like ' + fmt_temp(feels, feelsc) + ') | Currently ' + condition + ' | Humidity of ' + humidity)
        return parsed
    except KeyError:
        error = parsed['response']['error']['description']
        bot.say(channel, "ERROR: %s [for query '%s']" % (error, location))
        pass

def fmt_temp(f, c):
    degree_sign = u'\N{DEGREE SIGN}'
    return str(f) + degree_sign + 'F, ' + str(c) + degree_sign + 'C'
