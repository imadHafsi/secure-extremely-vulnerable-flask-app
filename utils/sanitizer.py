import bleach

# Allow only basic formatting tags
ALLOWED_TAGS = [
    "b", "strong",
    "i", "em",
    "u",
    "p", "br",
    "ul", "ol", "li",
]


def sanitize_note_text(raw: str) -> str:
    return bleach.clean(
        raw or "",
        tags=ALLOWED_TAGS,
        strip=True,
    )
