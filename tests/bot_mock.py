import requests

from pyfibot import botcore


class BotMock(botcore.CoreCommands):
    config = {}

    def get_url(self, url, nocache=False):
        return self.factory.getUrl(url, nocache)
        
    def getUrl(self, url, nocache=False):
        print("Getting url %s" % url)
        return requests.get(url)

    def say(self, channel, message, length=None):
        return("%s|%s" % (channel, message))

## Mock other functions too

