from saves import Saves
from mail.sender.email_sender import EmailSender
from mail.email import Email
from weed_out.ai_checker import AIChecker

file_save = Saves("data.json")
data = file_save.loaded_data
data_sender = data["sender"]

sender = EmailSender(
    data_sender["email"],
    data_sender["password"],
    data_sender["imap"],
    data_sender["port"]
)

for user in data["accounts"]:
    account_mail = Email(
        user["email"],
        user["password"],
        data_sender["imap"],
        data_sender["port"]
    )
    checker = AIChecker()
    for letter in account_mail.list_messages():
        checker.set_text(letter["body"], letter["from"])
        checker.process_text()
        if checker.to_send():
            letter["subject"] = "ОТПРАВЛЯТЬ от " + letter["from"]
        else:
            letter["subject"] = "БАН! от " + letter["from"]
        letter["to"] = data["recipient"]["email"]

        sender.send(letter)