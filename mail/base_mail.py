class BaseMail:
    def __init__(self, email, password, imap, port):
        self.email = email
        self.password = password
        self.imap = imap
        self.port = port

    def list_messages(self) -> str:
        pass