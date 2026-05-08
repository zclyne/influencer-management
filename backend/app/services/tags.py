import re

MAX_TAGS = 20
MAX_TAG_LENGTH = 32
TAG_PATTERN = re.compile(r"^[\w\s\-/.&]+$", re.UNICODE)
ALLOWED_TAG_CHARACTERS = "letters, numbers, spaces, -, _, /, ., &"


class TagValidationError(ValueError):
    def __init__(self, message: str, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


def clean_tags(
    tags: list[str] | None,
    *,
    entity_name: str = "Item",
    max_tags: int = MAX_TAGS,
    max_length: int = MAX_TAG_LENGTH,
) -> list[str]:
    if not tags:
        return []

    cleaned: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        clean_tag = clean_tag_value(tag, entity_name=entity_name, max_length=max_length)
        key = clean_tag.casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(clean_tag)
        if len(cleaned) > max_tags:
            raise TagValidationError(
                f"{entity_name} can have at most {max_tags} tags.",
                details={"max_tags": max_tags},
            )
    return cleaned


def clean_tag_value(
    tag: str,
    *,
    entity_name: str = "Item",
    max_length: int = MAX_TAG_LENGTH,
) -> str:
    cleaned = " ".join(tag.strip().split())
    if not cleaned:
        raise TagValidationError(f"{entity_name} tag cannot be blank.")
    if len(cleaned) > max_length:
        raise TagValidationError(
            f"{entity_name} tag is too long.",
            details={"tag": cleaned, "max_length": max_length},
        )
    if not TAG_PATTERN.fullmatch(cleaned):
        raise TagValidationError(
            f"{entity_name} tag contains unsupported characters.",
            details={"tag": cleaned, "allowed_characters": ALLOWED_TAG_CHARACTERS},
        )
    return cleaned
