import os
from dotenv import load_dotenv

load_dotenv()

path_to_data = os.getenv("PATH_TO_DATA")

def _bool(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "yes", "on")


# --- доступ к ящику ---
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
IMAP_USER = os.getenv("IMAP_USER", "")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", "").replace(" ", "")

# --- что анализируем ---
FOLDER = os.getenv("FOLDER", "INBOX")
LIMIT = int(os.getenv("LIMIT", "5000"))
TOP_N = int(os.getenv("TOP_N", "100"))
GROUP_BY_DOMAIN = _bool(os.getenv("GROUP_BY_DOMAIN", "true"))

# --- результат ---
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "senders.txt")