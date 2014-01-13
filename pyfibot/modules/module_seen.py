# -*- coding: utf-8 -*-
# TODO: Enable aliases
import logging, json, os, sys
from datetime import datetime
from util import getnick

log = logging.getLogger('seen')
users = []

def init(bot):
    global users
    
    with open(os.path.join(sys.path[0], 'modules', 'module_seen_users.json')) as userfile:
        users = json.load(userfile)
        
def command_seen(bot, user, channel, args):
    """.seen [nick] - Returns the last time a user was active, and what they were doing"""
    global users
    
    user = args.lower()
    
    try:
        then = datetime.strptime(users[user]['time'], "%Y-%m-%d %H:%M:%S")
    except KeyError:
        return bot.say(channel, "No record of user '%s' found!" % args)
    now = datetime.now()
    diff = now-then
    diff = str(diff).split('.')[0] #remove microseconds
    
    if users[user]['msg']:
        msg = "with message '%s'" % users[user]['msg']
    else:
        msg = "" 
    
    bot.say(channel, "%s was last seen %s ago, %s %s" % (args, diff, users[user]['action'], msg))

    with open(os.path.join(sys.path[0], 'modules', 'module_seen_users.json'),'w') as userfile:
        json.dump(users, userfile, indent=2)

def handle_privmsg(bot, user, channel, msg):
    update_user(user, "chatting", msg)
    
def handle_userJoined(bot, user, channel):
    update_user(user, "joining")
    
def handle_userLeft(bot, user, channel, message):
    update_user(user, "leaving", message)

def handle_userKicked(bot, kickee, channel, kicker, message):
    update_user(kickee + "!", "kicked by %s" % kicker, message)
    
def handle_userRenamed(bot, oldnick, newnick):
    update_user(oldnick, "changing name to %s" % newnick)    

def handle_action(bot, user, channel, data):
    update_user(user, "performing an action", data)
    
def update_user(user, action, msg=None):
    global users
    users[getnick.get(user).lower()] = {'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        'action': action,
                                        'msg': msg}