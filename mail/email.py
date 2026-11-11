from mail.base_mail import BaseMail
import imaplib
import email
import email.utils
from email.header import decode_header


class Email(BaseMail):
    def __init__(self, email, password, imap="imap.gmail.com", port=993):
        super().__init__(email, password, imap, port)
        self.connection = None

    def connect(self):
        """Подключение к IMAP."""
        self.connection = imaplib.IMAP4_SSL(self.imap, self.port)
        self.connection.login(self.email, self.password)
        return self

    def disconnect(self):
        """Отключение от IMAP."""
        if self.connection:
            try:
                self.connection.logout()
            finally:
                self.connection = None

    def decode(self, value):
        """Декодирование заголовков."""
        if not value:
            return ""

        result = ""

        for part, encoding in decode_header(value):
            if isinstance(part, bytes):
                result += part.decode(
                    encoding or "utf-8",
                    errors="replace"
                )
            else:
                result += part

        return result

    def get_body(self, msg):
        """Получение текста письма."""
        result = []

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() != "text/plain":
                    continue

                if part.get_content_disposition() == "attachment":
                    continue

                payload = part.get_payload(decode=True)

                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    result.append(
                        payload.decode(charset, errors="replace")
                    )
        else:
            payload = msg.get_payload(decode=True)

            if payload:
                charset = msg.get_content_charset() or "utf-8"
                result.append(
                    payload.decode(charset, errors="replace")
                )

        return "\n".join(result)

    def list_messages(self, folder="INBOX", limit=100):
        """
        Получение писем.

        Возвращает список словарей с информацией о письмах.
        """
        if not self.connection:
            self.connect()

        status, _ = self.connection.select(f'"{folder}"', readonly=True)

        if status != "OK":
            raise RuntimeError(f"Не удалось открыть папку {folder}")

        status, data = self.connection.search(None, "ALL")

        if status != "OK":
            raise RuntimeError("Не удалось получить список писем")

        ids = data[0].split()[-limit:]
        messages = []

        for mail_id in ids:
            status, data = self.connection.fetch(
                mail_id,
                "(BODY.PEEK[])"
            )

            if status != "OK" or not data or not isinstance(data[0], tuple):
                continue

            msg = email.message_from_bytes(data[0][1])

            sender = email.utils.parseaddr(
                msg.get("From", "")
            )[1]

            messages.append({
                "id": mail_id.decode(),
                "from": sender,
                "domain": sender.rsplit("@", 1)[-1].lower()
                    if "@" in sender else "",
                "subject": self.decode(msg.get("Subject", "")),
                "date": msg.get("Date", ""),
                "body": self.get_body(msg)
            })

        return messages

    def list_massages(self, folder="INBOX", limit=100):
        """Совместимость со старым названием метода."""
        return self.list_messages(folder, limit)

    def __enter__(self):
        return self.connect()

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()
