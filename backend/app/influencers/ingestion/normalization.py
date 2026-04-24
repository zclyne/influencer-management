import re
from decimal import Decimal, InvalidOperation
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
}
EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")


def normalize_email(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip().removeprefix("mailto:").strip().lower()
    return cleaned if EMAIL_RE.fullmatch(cleaned) else None


def extract_emails(value: str | None) -> list[str]:
    if not value:
        return []
    emails = []
    for match in EMAIL_RE.findall(value):
        normalized = normalize_email(match)
        if normalized and normalized not in emails:
            emails.append(normalized)
    return emails


def normalize_platform(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower()
    aliases = {
        "ig": "instagram",
        "instagram": "instagram",
        "youtube": "youtube",
        "yt": "youtube",
        "tiktok": "tiktok",
        "tik tok": "tiktok",
        "twitter": "x",
        "x": "x",
    }
    return aliases.get(normalized, normalized.replace(" ", "_"))


def normalize_profile_url(value: str | None) -> str | None:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    if not raw.startswith(("http://", "https://")):
        raw = f"https://{raw}"
    parsed = urlparse(raw)
    host = parsed.netloc.lower().removeprefix("www.").removeprefix("m.")
    query = urlencode(
        [(key, val) for key, val in parse_qsl(parsed.query) if key not in TRACKING_PARAMS]
    )
    path = parsed.path.rstrip("/")
    return urlunparse(("https", host, path, "", query, ""))


def normalize_username(platform: str | None, value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip()
    if cleaned.startswith(("http://", "https://")):
        parsed = urlparse(cleaned)
        parts = [part for part in parsed.path.split("/") if part]
        if parts:
            cleaned = parts[-1]
    cleaned = cleaned.removeprefix("@").strip().lower()
    if platform == "youtube" and cleaned.startswith("channel/"):
        cleaned = cleaned.removeprefix("channel/")
    return cleaned or None


def parse_int(value: str | int | float | None) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    multipliers = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}
    suffix = text[-1].lower()
    try:
        if suffix in multipliers:
            return int(Decimal(text[:-1]) * multipliers[suffix])
        return int(Decimal(text))
    except (InvalidOperation, ValueError):
        raise ValueError(f"Invalid integer value: {value}") from None


def parse_decimal(value: str | int | float | Decimal | None) -> Decimal | None:
    if value in (None, ""):
        return None
    if isinstance(value, Decimal):
        return value
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        raise ValueError(f"Invalid decimal value: {value}") from None


def parse_percentage_or_rate(value: str | int | float | Decimal | None) -> Decimal | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    is_percent = text.endswith("%")
    if is_percent:
        text = text[:-1]
    parsed = parse_decimal(text)
    if parsed is None:
        return None
    if is_percent or parsed > 1:
        return parsed / Decimal("100")
    return parsed


def parse_ranked_key_value(value: str | None) -> dict[str, object] | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    if "=" not in text:
        return {"label": text, "value": None, "raw": text}
    label, raw_value = text.split("=", 1)
    try:
        parsed_value = parse_percentage_or_rate(raw_value)
    except ValueError:
        parsed_value = None
    return {"label": label.strip(), "value": parsed_value, "raw": text}
