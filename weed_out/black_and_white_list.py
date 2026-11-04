from weed_out.base import WeedOut
import config, saves

class BlackAndWhiteList:
    def __init__(self):
        self.blacklist_words = saves.Saves(config.path_to_data).loaded_data["blacklist-words"]
        self.whitelist_words = saves.Saves(config.path_to_data).loaded_data["whitelist-words"]
        self.blacklist_emails = saves.Saves(config.path_to_data).loaded_data["blacklist-emails"]
        self.whitelist_emails = saves.Saves(config.path_to_data).loaded_data["whitelist-emails"]
        self.text = ""
        self.sender = None
        self.send = 0
        self.trash = 0

    def set_text(self, text:str, sender) -> None:
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
        self.sender = sender
        print(self.text)

    def process_text(self) -> None:
        words = {}
        for word in self.text.split():
            words[word] = words.get(word, 0) + 1

        for black_word in self.blacklist_words:
            self.trash += words.get(black_word, 0)

        for white_word in self.whitelist_words:
            self.send += words.get(white_word, 0)

        if self.sender in self.whitelist_emails:
            self.send += 5

        if self.sender in self.blacklist_emails:
            self.send -= 5

    def to_send(self) -> bool:
        print("Баллов за \"отправлять\":", self.send)
        print("Баллов за \"мусор\":", self.trash)
        return self.send > self.trash

if __name__ == "__main__":
    pass

