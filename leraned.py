from collections import Counter
import email.utils

def top_senders(imap, folder="INBOX", limit=5000):
    imap.select(f'"{folder}"', readonly=True)
    _, data = imap.search(None, "ALL")
    ids = data[0].split()[-limit:]
    cnt = Counter()
    for i in ids:
        _, d = imap.fetch(i, "(BODY.PEEK[HEADER.FIELDS (FROM)])")
        raw = d[0][1].decode("utf-8", "ignore")
        addr = email.utils.parseaddr(raw.split(":", 1)[-1])[1].lower()
        cnt[addr.split("@")[-1]] += 1
    return cnt.most_common(100)

for domain, n in top_senders(imap):
    print(n, domain)