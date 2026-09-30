import re


def clean_text(text: str) -> str:
    """
    Clean unnecessary whitespace and formatting from extracted webpage text.
    """

    if not text:
        return ""

    # Replace non-breaking spaces
    text = text.replace("\xa0", " ")

    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize excessive newlines
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    # Remove spaces around newlines
    text = re.sub(r" *\n *", "\n", text)

    return text.strip()


def clean_line(text: str) -> str:
    """
    Clean a single line of extracted text.
    """

    if not text:
        return ""

    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()