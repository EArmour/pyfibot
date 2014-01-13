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
    global users
    
    user = args.lower()
    
    try:
        then = datetime.strptime(users[user]['time'], "%Y-%m-%d %H:%M:%S")
    except KeyError:
        return bot.say(channel, "No record of user '%s' found!" % args)
    now = datetime.now()
    diff = now-then
    diff = str(diff).split('.')[0] #remove microseconds
    
    bot.say(channel, "%s last seen %s ago, %s with message '%s'" % (args, diff, users[user]['action'], users[user]['msg']))

    with open(os.path.join(sys.path[0], 'modules', 'module_seen_users.json'),'w') as userfile:
        json.dump(users, userfile, indent=2)

def handle_privmsg(bot, user, channel, msg):
    update_user(user, "chatting", msg)
    
# def handle_userJoined(bot, user, channel):
#     update_user(user, "joining", channel)
    
def handle_userLeft(bot, user, channel, message):
    update_user(user, "leaving", message)

def handle_userKicked(bot, kickee, channel, kicker, message):
    update_user(kickee + "!", "kicked by %s" % kicker, message)
    
def handle_userRenamed(bot, oldnick, newnick):
    update_user(oldnick, "changing name to %s" % newnick, "renamed")    

def handle_action(bot, user, channel, data):
    update_user(user, "performing an action", data)
    
def update_user(user, action, msg):
    global users
    users[getnick.get(user).lower()] = {'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        'action': action,
                                        'msg': msg}