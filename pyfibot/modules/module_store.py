import json, os, sys, logging

log = logging.getLogger('store')
data = {}

def init(bot):
    global data

    with open(os.path.join(sys.path[0], 'modules', 'module_store_conf.json')) as datafile:
        data = json.load(datafile)

def command_store(bot, user, channel, args):
    """.store [key] [value] - Store arbitrary text under a given key for later reference (key is one word)"""
    global data

    input = str(args).split()
    if len(input) < 2:
        log.info("Failed to store data with args: %s" % args)
        bot.say(channel, "Could not store data; must provide both key and string data.")
    else:
        newkey = input[0]
        for key in data.keys():
            if newkey.lower() == key.lower():
                return bot.say(channel, "Could not store data; that key is already in use.")
        data[newkey] = args[args.find(' ')+1:]
        bot.say(channel, "Data succesfully added for key: %s" % newkey)
        with open(os.path.join(sys.path[0], 'modules', 'module_store_conf.json'),'w') as datafile:
            json.dump(data, datafile, indent=2)


def command_get(bot, user, channel, args):
    """.get [key] - Retrieve previously stored text (key is one word)"""
    global data

    if len(args) < 1:
        return bot.say(channel, "Could not get data; must provide a string key.")

    if args.lower() == 'list':
        return bot.say(channel, "Stored keys: %s" % ['%s' % str(k) for k in data.keys()])

    for key in data.keys():
        if args.lower() == key.lower():
            return bot.say(channel, "%s: %s" % (key, data[key]))

    bot.say(channel, "Couldn't find any data stored for key: %s" % args)
