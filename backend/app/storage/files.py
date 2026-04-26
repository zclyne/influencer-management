import hashlib
import mimetypes
from dataclasses import dataclass
from pathlib import Path

from app.core.config import get_settings
from app.enums import StoredFileKind

KIND_DIRECTORIES = {
    StoredFileKind.IMPORT_SOURCE: "imports",
    StoredFileKind.CAMPAIGN_EXPORT: "exports",
    StoredFileKind.RECEIPT: "receipts",
    StoredFileKind.EMAIL_ATTACHMENT: "email_attachments",
    StoredFileKind.GENERATED_DOCUMENT: "generated",
}


@dataclass(frozen=True)
class StoredBytes:
    relative_path: str
    size_bytes: int
    checksum: str
    mime_type: str | None


class ManagedFileStorage:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = (base_dir or get_settings().local_storage_dir).resolve()

    def ensure_layout(self) -> None:
        for directory in (*KIND_DIRECTORIES.values(), "logs"):
            (self.base_dir / directory).mkdir(parents=True, exist_ok=True)

    def store_bytes(
        self,
        *,
        file_id: str,
        kind: StoredFileKind,
        original_name: str,
        content: bytes,
        mime_type: str | None = None,
    ) -> StoredBytes:
        self.ensure_layout()
        safe_name = self.safe_original_name(original_name)
        extension = Path(safe_name).suffix[:32]
        checksum = hashlib.sha256(content).hexdigest()
        relative_path = Path(KIND_DIRECTORIES[kind]) / f"{file_id}-{checksum[:16]}{extension}"
        absolute_path = self.resolve_relative(relative_path.as_posix())
        absolute_path.write_bytes(content)
        guessed_type = mime_type or mimetypes.guess_type(safe_name)[0]
        return StoredBytes(
            relative_path=relative_path.as_posix(),
            size_bytes=len(content),
            checksum=checksum,
            mime_type=guessed_type,
        )

    def resolve_relative(self, relative_path: str) -> Path:
        candidate = (self.base_dir / relative_path).resolve()
        if candidate != self.base_dir and self.base_dir not in candidate.parents:
            raise ValueError("Managed file path escapes the app data directory.")
        return candidate

    def safe_original_name(self, original_name: str) -> str:
        candidate = Path(original_name).name.strip()
        if not candidate or candidate in {".", ".."}:
            raise ValueError("File name is required.")
        return candidate
