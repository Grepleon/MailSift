from weed_out.base import WeedOut
import config

class BlackAndWhiteList:
    def __init__(self):
        self.blacklist_words = []
        self.whitelist_words = []
        self.blacklist_emails = []
        self.whitelist_emails = []


