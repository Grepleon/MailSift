from fnmatch import fnmatchcase
from email.utils import parseaddr
import config, saves


def _match(addr: str, patterns: list) -> bool:
    return any(fnmatchcase(addr, p.lower()) for p in patterns)


class BlackAndWhiteList:
    def __init__(self):
        data = saves.Saves(config.path_to_data).loaded_data
        self.blacklist_words = [w.lower() for w in data["blacklist-words"]]
        self.whitelist_words = [w.lower() for w in data["whitelist-words"]]
        self.blacklist_emails = [e.lower() for e in data["blacklist-emails"]]
        self.whitelist_emails = [e.lower() for e in data["whitelist-emails"]]
        self.text = ""
        self.sender = ""
        self.send = 0
        self.trash = 0

    def set_text(self, text: str, sender) -> None:
        self.text = (text
            .replace(".", "")
            .replace(",", "")
            .replace("!", "")
            .replace("?", "")
            .replace(":", "")
            .replace("-", "")
            .replace("—", "")
            .replace("(", "")
            .replace(")", "")
            .lower()
        )
        self.sender = parseaddr(sender or "")[1].lower()
        self.send = 0
        self.trash = 0

    def _count(self, patterns: list, words: dict) -> int:
        total = 0
        padded = f" {self.text} "
        for p in patterns:
            if " " in p:
                total += padded.count(f" {p} ")
            elif "*" in p:
                total += sum(n for w, n in words.items() if fnmatchcase(w, p))
            else:
                total += words.get(p, 0)
        return total

    def process_text(self) -> None:
        words = {}
        for word in self.text.split():
            words[word] = words.get(word, 0) + 1

        self.trash += self._count(self.blacklist_words, words)
        self.send += self._count(self.whitelist_words, words)

        if _match(self.sender, self.whitelist_emails):
            self.send += 5

        if _match(self.sender, self.blacklist_emails):
            self.trash += 5

    def to_send(self) -> bool:
        print("Баллов за \"отправлять\":", self.send)
        print("Баллов за \"мусор\":", self.trash)
        return self.send > self.trash