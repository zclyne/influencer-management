import csv
from collections.abc import Iterable
from io import StringIO
from typing import Any, Protocol

from app.domain.enums import ImportSourceType
from app.influencers.ingestion.normalization import (
    extract_emails,
    normalize_email,
    normalize_platform,
    normalize_profile_url,
    normalize_username,
    parse_int,
    parse_percentage_or_rate,
    parse_ranked_key_value,
)
from app.influencers.ingestion.schemas import (
    CanonicalInfluencerRow,
    ContactCandidate,
    ImportPreviewInput,
    SocialLinkCandidate,
)


class UnsupportedImportFileError(ValueError):
    pass


class InfluencerImportAdapter(Protocol):
    source_type: ImportSourceType

    def parse(self, input: ImportPreviewInput) -> list[CanonicalInfluencerRow]:
        ...


class ModashCsvImportAdapter:
    source_type = ImportSourceType.MODASH_CSV
    required_headers = {"Username", "Channel", "Account URL"}
    social_link_columns = {
        "Instagram": "instagram",
        "YouTube": "youtube",
        "TikTok": "tiktok",
        "Twitch": "twitch",
        "X": "x",
        "Facebook": "facebook",
        "Threads": "threads",
        "Snapchat": "snapchat",
        "Linktree": "linktree",
        "Pinterest": "pinterest",
        "Tumblr": "tumblr",
        "WeChat": "wechat",
    }

    def parse(self, input: ImportPreviewInput) -> list[CanonicalInfluencerRow]:
        try:
            decoded = input.content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise UnsupportedImportFileError("CSV must be UTF-8 encoded.") from exc
        reader = csv.DictReader(StringIO(decoded))
        headers = set(reader.fieldnames or [])
        missing = self.required_headers - headers
        if missing:
            raise UnsupportedImportFileError(
                f"Missing required Modash headers: {', '.join(sorted(missing))}"
            )
        return [
            self._row_to_canonical(row_number, row)
            for row_number, row in enumerate(reader, 2)
        ]

    def _row_to_canonical(
        self, row_number: int, row: dict[str, str]
    ) -> CanonicalInfluencerRow:
        warnings: list[str] = []
        errors: list[str] = []
        platform = normalize_platform(row.get("Channel"))
        username = row.get("Username") or None
        normalized_username = normalize_username(platform, username)
        profile_url = row.get("Account URL") or None
        normalized_profile_url = normalize_profile_url(profile_url)
        full_name = row.get("Fullname") or None
        display_name = full_name or username
        bio = row.get("Bio/Description") or None

        contacts = self._contacts(row, bio, warnings)
        social_links = self._social_links(row)
        metrics = self._metrics(row, errors)
        age_gender = self._age_gender(row, warnings)
        top_countries = self._ranked(row, "%Top", "_Cntr", 1, 3, warnings)
        top_cities = self._ranked(row, "%Top", "_City", 1, 5, warnings)
        top_interests = self._ranked(row, "%Top", "_Interest", 1, 8, warnings)

        if not display_name:
            errors.append("Missing display name.")
        if not platform:
            errors.append("Missing or invalid platform.")
        if not normalized_profile_url:
            errors.append("Missing or invalid profile URL.")

        return CanonicalInfluencerRow(
            source_type=self.source_type.value,
            source_row_number=row_number,
            raw_row_json=dict(row),
            display_name=display_name,
            full_name=full_name,
            gender=row.get("Gender") or None,
            country=row.get("Country") or None,
            city=row.get("City") or None,
            bio=bio,
            platform=platform,
            username=username,
            normalized_username=normalized_username,
            profile_url=profile_url,
            normalized_profile_url=normalized_profile_url,
            contacts=contacts,
            social_links=social_links,
            age_gender_json=age_gender,
            top_countries_json=top_countries,
            top_cities_json=top_cities,
            top_interests_json=top_interests,
            parse_errors=errors,
            warnings=warnings,
            **metrics,
        )

    def _metrics(self, row: dict[str, str], errors: list[str]) -> dict[str, Any]:
        mapping = {
            "follower_count": (("#Followers/Subscribers",), parse_int),
            "engagement_rate": (("%ER",), parse_percentage_or_rate),
            "follower_credibility": (
                ("%Follower Credibility", "Follower Credibility"),
                parse_percentage_or_rate,
            ),
            "notable_follower_rate": (
                ("%Notable Followers/Subscribers", "Notable Followers/Subscribers"),
                parse_percentage_or_rate,
            ),
            "avg_likes": (("Avg likes",), parse_int),
            "avg_views": (("Avg views",), parse_int),
            "avg_comments": (("Avg comments",), parse_int),
            "avg_reels_plays": (("Avg Reels plays",), parse_int),
            "total_likes": (("Total likes",), parse_int),
            "total_posts_or_videos": (("Total posts/videos",), parse_int),
            "total_views": (("Total views",), parse_int),
        }
        parsed: dict[str, Any] = {"raw_metrics_json": {}}
        for target, (sources, parser) in mapping.items():
            source, value = self._first_present(row, sources)
            try:
                parsed[target] = parser(value)
            except ValueError as exc:
                errors.append(str(exc))
                parsed[target] = None
            if value not in (None, ""):
                parsed["raw_metrics_json"][source] = value
        return parsed

    def _first_present(
        self, row: dict[str, str], sources: tuple[str, ...]
    ) -> tuple[str, str | None]:
        for source in sources:
            value = row.get(source)
            if value not in (None, ""):
                return source, value
        return sources[0], None

    def _contacts(
        self, row: dict[str, str], bio: str | None, warnings: list[str]
    ) -> list[ContactCandidate]:
        contacts: list[ContactCandidate] = []
        for index in range(1, 7):
            raw = row.get(f"Email_{index}")
            if not raw:
                continue
            email = normalize_email(raw)
            if email:
                contacts.append(ContactCandidate(email=email, source=f"Email_{index}"))
            else:
                warnings.append(f"Invalid email skipped from Email_{index}.")
        for email in extract_emails(bio):
            if email not in {contact.email for contact in contacts}:
                contacts.append(ContactCandidate(email=email, source="bio_extracted"))
        return contacts

    def _social_links(self, row: dict[str, str]) -> list[SocialLinkCandidate]:
        links: list[SocialLinkCandidate] = []
        for column, platform in self.social_link_columns.items():
            raw_url = row.get(column)
            normalized_url = normalize_profile_url(raw_url)
            if normalized_url:
                links.append(
                    SocialLinkCandidate(
                        platform=platform,
                        profile_url=normalized_url,
                        username=normalize_username(platform, normalized_url),
                    )
                )
        return links

    def _age_gender(self, row: dict[str, str], warnings: list[str]) -> dict[str, Any]:
        output: dict[str, Any] = {}
        for key in ("%13-17", "%18-24", "%25-34", "%35-44", "%Male", "%Female"):
            value = row.get(key)
            if value in (None, ""):
                continue
            try:
                output[key.removeprefix("%")] = parse_percentage_or_rate(value)
            except ValueError:
                warnings.append(f"Could not parse audience value {key}.")
                output[key.removeprefix("%")] = {"raw": value}
        return output

    def _ranked(
        self,
        row: dict[str, str],
        prefix: str,
        suffix: str,
        start: int,
        end: int,
        warnings: list[str],
    ) -> list[dict[str, Any]]:
        values: list[dict[str, Any]] = []
        for rank in range(start, end + 1):
            key = f"{prefix}{rank}{suffix}"
            parsed = parse_ranked_key_value(row.get(key))
            if parsed:
                parsed["rank"] = rank
                values.append(parsed)
            elif row.get(key):
                warnings.append(f"Could not parse ranked audience value {key}.")
        return values


def rows_to_preview_json(rows: Iterable[CanonicalInfluencerRow]) -> list[dict[str, Any]]:
    return [row.model_dump(mode="json") for row in rows]
