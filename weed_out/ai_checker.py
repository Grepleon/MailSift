from fnmatch import fnmatchcase
from email.utils import parseaddr
import config, saves


def _match(addr: str, patterns: list) -> bool:
    return any(fnmatchcase(addr, p.lower()) for p in patterns)


class BlackAndWhiteList:
    def __init__(self):
        self.data = saves.Saves(config.path_to_data)
        ai_data = self.data.loaded_data["ai"]
        self.spam_words = [w.lower() for w in ai_data["spam-words"]]
        self.send_words = [w.lower() for w in ai_data["send-words"]]
        self.spam_count = int(ai_data["spam-count"])
        self.send_count = int(ai_data["send-count"])
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

        for word in words:
            if word in self.send_words:
                self.send += words[word] * 10 * self.send_words[word] / self.send_count

    def to_send(self) -> bool:
        print("Баллов за \"отправлять\":", self.send)
        print("Баллов за \"мусор\":", self.trash)
        return self.send > self.trash