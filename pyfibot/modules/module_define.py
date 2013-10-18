# -*- coding: utf-8 -*-

from lxml import etree


url = "http://services.aonaware.com/DictService/DictService.asmx/Define?word=%s"

def command_define(bot, user, channel, args):
    if args:
        query = args
    else:
        return bot.say(channel, "No query!")
    
    tree = etree.parse(url % query)
    root = tree.getroot()
    
    definition = root[1][0][2].text
    
    if definition.find("1.") != 0:
        cleandef = definition[definition.find("1.")+3:definition.find('[1')]
    else:
        cleandef = definition[definition.find("]")+1:definition.find('[1')]
    
    return bot.say(channel, cleandef)