import random
import re

import weed_out.ai_checker as ai

DEFAULT_PATTERN = "*.com"
TEST_FRACTION = 0.1
SEED = 42

MAX_PER_CLASS = 20000
MAX_CHARS = 3000

TEXT_COL = None
LABEL_COL = None
SPAM_VALUES = None


def load_hf_ru(name="ruSpamModels/russian-spam-detection", split="train"):
    """Русский датасет спама с Hugging Face. pip install datasets"""
    from datasets import load_dataset

    ds = load_dataset(name, split=split)
    print("Колонки:", ds.column_names)
    print("Пример:", ds[0])

    text_col = TEXT_COL or next(
        (c for c in ("text", "message", "body", "content", "sms") if c in ds.column_names),
        ds.column_names[0],
    )
    label_col = LABEL_COL or next(
        (c for c in ("label", "labels", "is_spam", "spam", "target", "class", "label_text")
         if c in ds.column_names),
        None,
    )
    if label_col is None:
        raise SystemExit("Не нашёл колонку с меткой, задай LABEL_COL вручную")

    labels = set(str(x).strip().lower() for x in ds[label_col][:10000])
    print("Значения меток:", labels)

    spam_values = SPAM_VALUES or {"1", "spam", "true", "спам"}
    spam_values = {str(v).lower() for v in spam_values}
    if not (labels & spam_values):
        raise SystemExit(f"Среди меток {labels} нет спама, задай SPAM_VALUES вручную")

    spam, ham = [], []
    for i in random.Random(SEED).sample(range(len(ds)), len(ds)):
        row = ds[i]
        text = str(row[text_col] or "")
        if not text.strip():
            continue
        is_spam = str(row[label_col]).strip().lower() in spam_values
        bucket = spam if is_spam else ham
        if len(bucket) < MAX_PER_CLASS:
            bucket.append((text[:MAX_CHARS], not is_spam))
        if len(spam) >= MAX_PER_CLASS and len(ham) >= MAX_PER_CLASS:
            break

    print(f"Взято: спам {len(spam)}, ham {len(ham)}")
    return spam + ham


def load_my_emails(path="my_emails.txt"):
    """
    Свои письма для дообучения. Формат файла: письма разделены строкой
    '=====', первая строка каждого письма 'HAM' или 'SPAM'.
    """
    samples = []
    with open(path, encoding="utf-8") as f:
        for block in re.split(r"^=====\s*$", f.read(), flags=re.M):
            block = block.strip()
            if not block:
                continue
            head, _, text = block.partition("\n")
            samples.append((text[:MAX_CHARS], head.strip().upper() == "HAM"))
    return samples


def train(samples, own_samples=()):
    random.Random(SEED).shuffle(samples)

    split = int(len(samples) * (1 - TEST_FRACTION))
    train_set, test_set = samples[:split], samples[split:]

    train_set = train_set + list(own_samples) * 3

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
    samples = load_hf_ru()

    own = []
    try:
        own = load_my_emails("my_emails.txt")
        print(f"Своих писем: {len(own)}")
    except FileNotFoundError:
        print("my_emails.txt не найден, обучаю только на датасете")

    checker, test_set = train(samples, own)