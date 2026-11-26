# mail/email_sender.py
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

from mail.base_sender import BaseSender


class EmailSender(BaseSender):
    def __init__(
        self,
        email,
        password,
        imap="imap.gmail.com",
        port=993,
        smtp="smtp.gmail.com",
        smtp_port=465,
    ):
        super().__init__(email, password, imap, port)
        self.smtp = smtp
        self.smtp_port = smtp_port

    def _open_smtp(self):
        """Открывает SMTP-соединение (SSL на 465, STARTTLS на остальных)."""
        context = ssl.create_default_context()

        if self.smtp_port == 465:
            server = smtplib.SMTP_SSL(self.smtp, self.smtp_port, context=context, timeout=30)
        else:
            server = smtplib.SMTP(self.smtp, self.smtp_port, timeout=30)
            server.starttls(context=context)

        server.login(self.email, self.password)
        return server

    def build_message(self, text: dict[str, str]) -> EmailMessage:
        """
        Собирает письмо из словаря.

        Ключи: to (обязательно), subject, body, html, cc, bcc, reply_to.
        Несколько адресатов — через запятую.
        """
        if not text.get("to"):
            raise ValueError("Не указан получатель ('to')")

        msg = EmailMessage()
        msg["From"] = self.email
        msg["To"] = text["to"]
        msg["Subject"] = text.get("subject", "")
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid(domain=self.email.rsplit("@", 1)[-1])

        if text.get("cc"):
            msg["Cc"] = text["cc"]
        if text.get("reply_to"):
            msg["Reply-To"] = text["reply_to"]

        msg.set_content(text.get("body", ""))

        if text.get("html"):
            msg.add_alternative(text["html"], subtype="html")

        return msg

    def send(self, text: dict[str, str]):
        """Отправляет письмо. bcc не попадает в заголовки, только в конверт."""
        msg = self.build_message(text)

        recipients = []
        for key in ("to", "cc", "bcc"):
            if text.get(key):
                recipients += [a.strip() for a in text[key].split(",") if a.strip()]

        with self._open_smtp() as server:
            server.send_message(msg, from_addr=self.email, to_addrs=recipients)