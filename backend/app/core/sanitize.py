import bleach

ALLOWED_TAGS = [
    "p", "br", "strong", "em", "b", "i", "u",
    "ul", "ol", "li", "h3", "h4", "h5",
]
ALLOWED_ATTRIBUTES = {}


def sanitize_html(text: str) -> str:
    if not text:
        return text
    return bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)


def strip_all_html(text: str) -> str:
    if not text:
        return text
    return bleach.clean(text, tags=[], strip=True).strip()
