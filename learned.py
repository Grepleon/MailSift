import imaplib
import email.utils
from collections import Counter

import config


def connect():
    if not config.IMAP_PASSWORD:
        raise SystemExit("Задай переменную окружения GMAIL_APP_PASSWORD")
    imap = imaplib.IMAP4_SSL(config.IMAP_HOST, config.IMAP_PORT)
    imap.login(config.IMAP_USER, config.IMAP_PASSWORD)
    return imap


def top_senders(imap, folder=config.FOLDER, limit=config.LIMIT, top_n=config.TOP_N):
    status, _ = imap.select(f'"{folder}"', readonly=True)
    if status != "OK":
        raise SystemExit(f"Не удалось открыть папку {folder}. Список папок: {imap.list()[1]}")
    _, data = imap.search(None, "ALL")
    ids = data[0].split()[-limit:]
    cnt = Counter()
    for i in ids:
        _, d = imap.fetch(i, "(BODY.PEEK[HEADER.FIELDS (FROM)])")
        raw = d[0][1].decode("utf-8", "ignore")
        addr = email.utils.parseaddr(raw.split(":", 1)[-1])[1].lower()
        if not addr:
            continue
        key = addr.split("@")[-1] if config.GROUP_BY_DOMAIN else addr
        cnt[key] += 1
    return cnt.most_common(top_n)


if __name__ == "__main__":
    import config

    print(repr(config.IMAP_USER), len(config.IMAP_PASSWORD))

    p = config.IMAP_PASSWORD
    print(p[:1] + '... .... .... ...' + p[-1:], len(p))

    imap = connect()
    try:
        result = top_senders(imap)
    finally:
        imap.logout()


    with open(config.OUTPUT_FILE, "w", encoding="utf-8") as f:
        for sender, n in result:
            line = f"{n}\t{sender}"
            print(line)
            f.write(line + "\n")
