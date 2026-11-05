from fnmatch import fnmatchcase
from email.utils import parseaddr
import config, saves
from weed_out.base import WeedOut

def _match(addr: str, patterns: list) -> bool:
    return any(fnmatchcase(addr, p.lower()) for p in patterns)


class AIChecker(WeedOut):
    def __init__(self):
        self.data = saves.Saves(config.path_to_data)
        ai_data = self.data.loaded_data["ai"]
        self.spam_words = ai_data["spam-words"]
        self.send_words = ai_data["send-words"]
        self.spam_count = int(ai_data["spam-count"])
        self.send_count = int(ai_data["send-count"])
        self.text = ""
        self.sender = ""
        self.send = 0
        self.spam = 0
        self.res = None

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
            .replace("]", "")
            .replace("[", "")
            .replace("<", "")
            .replace(">", "")
            .lower()
        )
        self.sender = parseaddr(sender or "")[1].lower()
        self.send = 0
        self.spam = 0

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
            if word in self.spam_words:
                self.spam += words[word] * 10 * self.spam_words[word] / self.spam_count

    def to_send(self) -> bool:
        print("Баллов за \"отправлять\":", self.send)
        print("Баллов за \"мусор\":", self.spam)
        self.res = self.send > self.spam
        return self.res

    def learn(self, true_answer):
        if true_answer:
            for word in self.text.split():
                self.send_words[word] = self.send_words.get(word, 0) + 1
            self.send_count += len(self.text.split())
        else:
            for word in self.text.split():
                self.spam_words[word] = self.spam_words.get(word, 0) + 1
            self.spam_count += len(self.text.split())
        new_data = self.data.loaded_data
        new_data["ai"]["spam-words"] = self.spam_words
        new_data["ai"]["send-words"] = self.send_words
        new_data["ai"]["spam-count"] = self.spam_count
        new_data["ai"]["send-count"] = self.send_count
        self.data.save_file(new_data)
