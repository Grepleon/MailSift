from mail.email import Email

class BaseSender(Email):
    def send(self, text: dict[str: str]):
        pass