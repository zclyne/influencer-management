from pathlib import Path

from sqlalchemy.orm import Session

from app.db import models
from app.db.models import uuid_str
from app.domain.enums import StoredFileKind
from app.files.schemas import StoredFileResponse
from app.repositories.sqlalchemy import StoredFileRepository
from app.storage.files import ManagedFileStorage


class FileServiceError(Exception):
    code = "file_error"
    status_code = 422

    def __init__(self, message: str, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class StoredFileNotFound(FileServiceError):
    code = "not_found"
    status_code = 404


class ManagedFileMissing(FileServiceError):
    code = "managed_file_missing"
    status_code = 404


class FileService:
    def __init__(self, db: Session, storage: ManagedFileStorage | None = None) -> None:
        self.db = db
        self.files = StoredFileRepository(db)
        self.storage = storage or ManagedFileStorage()

    def register_bytes(
        self,
        *,
        kind: StoredFileKind,
        original_name: str,
        content: bytes,
        mime_type: str | None = None,
    ) -> StoredFileResponse:
        file_id = uuid_str()
        try:
            safe_name = self.storage.safe_original_name(original_name)
            stored = self.storage.store_bytes(
                file_id=file_id,
                kind=kind,
                original_name=safe_name,
                content=content,
                mime_type=mime_type,
            )
        except ValueError as exc:
            raise FileServiceError(str(exc), details={"original_name": original_name}) from exc
        row = self.files.create(
            id=file_id,
            kind=kind.value,
            original_name=safe_name,
            storage_path=stored.relative_path,
            mime_type=stored.mime_type,
            size_bytes=stored.size_bytes,
            checksum=stored.checksum,
        )
        self.db.commit()
        return self._response(row)

    def get_file(self, file_id: str) -> StoredFileResponse:
        return self._response(self._require_file(file_id))

    def resolve_download_path(self, file_id: str) -> Path:
        row = self._require_file(file_id)
        path = self.storage.resolve_relative(row.storage_path)
        if not path.exists():
            raise ManagedFileMissing(
                "Managed file is missing from local storage.",
                details={"file_id": file_id},
            )
        return path

    def delete_file(self, file_id: str) -> None:
        row = self._require_file(file_id)
        path = self.storage.resolve_relative(row.storage_path)
        if path.exists():
            path.unlink()
        self.files.delete(row)
        self.db.commit()

    def _require_file(self, file_id: str) -> models.StoredFile:
        row = self.files.get(file_id)
        if not row:
            raise StoredFileNotFound("File not found.", details={"file_id": file_id})
        return row

    def _response(self, row: models.StoredFile) -> StoredFileResponse:
        path = self.storage.resolve_relative(row.storage_path)
        return StoredFileResponse(
            id=row.id,
            kind=StoredFileKind(row.kind),
            original_name=row.original_name,
            mime_type=row.mime_type,
            size_bytes=row.size_bytes,
            checksum=row.checksum,
            exists=path.exists(),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
