import email
import email.utils
import random
from email.header import decode_header
from pathlib import Path

import weed_out.ai_checker as ai

DEFAULT_PATTERN = "*.com"
TEST_FRACTION = 0.1
SEED = 42

def load_hf_enron():
    """Enron-Spam с Hugging Face (~33 тыс. писем). pip install datasets"""
    from datasets import load_dataset

    ds = load_dataset("SetFit/enron_spam", split="train")
    samples = []

    for row in ds:
        subject = row.get("subject") or ""
        body = row.get("message") or row.get("text") or ""
        text = f"Subject: {subject}\n\n{body}"
        is_ham = row["label_text"] == "ham"
        samples.append((text, is_ham))

    return samples


def load_csv(path, text_col="text", label_col="label", spam_value="spam"):
    """Любой CSV с колонками текст/метка (удобно для Kaggle-наборов)."""
    import csv

    samples = []

    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        for row in csv.DictReader(f):
            is_ham = str(row[label_col]).strip().lower() != spam_value
            samples.append((row[text_col], is_ham))

    return samples


def decode_text(value):
    if not value:
        return ""

    result = ""

    for part, encoding in decode_header(value):
        if isinstance(part, bytes):
            result += part.decode(encoding or "utf-8", errors="replace")
        else:
            result += part

    return result


def eml_to_text(raw):
    msg = email.message_from_bytes(raw)

    sender = email.utils.parseaddr(msg.get("From", ""))[1]
    subject = decode_text(msg.get("Subject", ""))

    parts = []
    for part in msg.walk():
        if part.get_content_type() != "text/plain":
            continue
        if part.get_content_disposition() == "attachment":
            continue

        payload = part.get_payload(decode=True)
        if payload:
            charset = part.get_content_charset() or "utf-8"
            try:
                parts.append(payload.decode(charset, errors="replace"))
            except LookupError:
                parts.append(payload.decode("utf-8", errors="replace"))

    body = "\n".join(parts)
    return f"From: {sender}\nSubject: {subject}\n\n{body}"


def load_eml_folders(spam_dir, ham_dir):
    """Папки с сырыми письмами: SpamAssassin, TREC и т.п."""
    samples = []

    for folder, is_ham in ((spam_dir, False), (ham_dir, True)):
        for path in Path(folder).rglob("*"):
            if path.is_file():
                try:
                    samples.append((eml_to_text(path.read_bytes()), is_ham))
                except Exception as e:
                    print(f"Пропуск {path}: {e}")

    return samples

def train(samples):
    random.Random(SEED).shuffle(samples)

    split = int(len(samples) * (1 - TEST_FRACTION))
    train_set, test_set = samples[:split], samples[split:]

    checker = ai.AIChecker()
    spam_count = ham_count = 0

    for i, (text, is_ham) in enumerate(train_set, 1):
        checker.set_text(text, DEFAULT_PATTERN)
        checker.process_text()
        checker.learn(is_ham)

        if is_ham:
            ham_count += 1
        else:
            spam_count += 1

        if i % 1000 == 0:
            print(f"Обработано {i}/{len(train_set)}")

    print("\nОбучение завершено:")
    print(f"Спам: {spam_count}")
    print(f"Отправлять: {ham_count}")
    print(f"Отложено для проверки: {len(test_set)}")

    return checker, test_set


if __name__ == "__main__":
    samples = []

    samples += load_hf_enron()
    # samples += load_csv("spam.csv", text_col="text", label_col="label")
    # samples += load_eml_folders("data/spam", "data/ham")

    checker, test_set = train(samples)