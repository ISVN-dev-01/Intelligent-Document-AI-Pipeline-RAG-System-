import re


def clean_text(text: str) -> str:
    """Keep paragraph boundaries and factual punctuation while normalizing whitespace."""
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[^\S\n]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()
