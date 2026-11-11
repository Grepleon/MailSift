import imaplib
import email
import email.utils
from collections import Counter
from email.header import decode_header

import config
import weed_out.ai_checker as ai


SPAM_DOMAINS = {
    "tm.openai.com",
    "email.claude.com"
}


def connect():
    if not config.IMAP_PASSWORD:
        raise SystemExit("Задай переменную окружения GMAIL_APP_PASSWORD")

    imap = imaplib.IMAP4_SSL(config.IMAP_HOST, config.IMAP_PORT)
    imap.login(config.IMAP_USER, config.IMAP_PASSWORD)
    return imap


def get_sender_domain(msg):
    """Получает домен отправителя."""
    addr = email.utils.parseaddr(msg.get("From", ""))[1].lower()

    if not addr or "@" not in addr:
        return ""

    return addr.rsplit("@", 1)[1]


def is_spam_domain(domain):
    """Проверяет домен с учётом поддоменов."""
    return any(
        domain == spam_domain or domain.endswith("." + spam_domain)
        for spam_domain in SPAM_DOMAINS
    )


def decode_text(value):
    """Декодирует заголовки письма."""
    if not value:
        return ""

    result = ""

    for part, encoding in decode_header(value):
        if isinstance(part, bytes):
            result += part.decode(encoding or "utf-8", errors="replace")
        else:
            result += part

    return result


def get_email_text(msg):
    """Извлекает текст письма."""
    result = []

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
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
            result.append(payload.decode(charset, errors="replace"))

    return "\n".join(result)


def classify_emails(imap, folder="INBOX", limit=100):
    status, _ = imap.select(f'"{folder}"')

    if status != "OK":
        raise SystemExit(f"Не удалось открыть папку {folder}")

    status, data = imap.search(None, "ALL")

    if status != "OK":
        raise SystemExit("Ошибка получения списка писем")

    ids = data[0].split()[-limit:]

    checker = ai.AIChecker()

    spam_count = 0
    send_count = 0

    for mail_id in ids:
        status, data = imap.fetch(mail_id, "(BODY.PEEK[])")

        if status != "OK" or not data or not isinstance(data[0], tuple):
            continue

        raw = data[0][1]

        msg = email.message_from_bytes(raw)

        sender = email.utils.parseaddr(msg.get("From", ""))[1]
        domain = get_sender_domain(msg)

        subject = decode_text(msg.get("Subject", ""))
        body = get_email_text(msg)

        text = f"""
        From: {sender}
        Subject: {subject}

        {body}
        """

        # Сначала проверяем известные домены
        if is_spam_domain(domain):
            checker.set_text(text, "*.com")
            checker.process_text()

            checker.learn(False)

            spam_count += 1
            print(f"[SPAM] {sender}")

        else:
            checker.set_text(text, "*.com")
            checker.process_text()

            checker.learn(True)

            send_count += 1
            print(f"[SEND] {sender}")

    print("\nРезультаты:")
    print(f"Спам: {spam_count}")
    print(f"Отправлять: {send_count}")


if __name__ == "__main__":
    imap = connect()

    try:
        classify_emails(imap, config.FOLDER, config.LIMIT)
    finally:
        imap.logout()
