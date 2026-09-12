import re


def clean_text(raw_text: str) -> str:
    """
    Cleans raw document text by normalizing line breaks and extra whitespace
    while strictly preserving markdown headings, lists, and numerical threshold rules.
    """
    if not raw_text:
        return ""

    # Normalize Windows line endings to \n
    text = raw_text.replace("\r\n", "\n")

    # Replace 3 or more consecutive newlines with 2 newlines (preserve paragraph gaps)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Trim trailing whitespace on each line
    lines = [line.rstrip() for line in text.split("\n")]
    cleaned = "\n".join(lines).strip()

    return cleaned
