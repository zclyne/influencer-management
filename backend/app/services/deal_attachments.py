from sqlalchemy.orm import Session

from app.db import models
from app.enums import StoredFileKind
from app.repositories.sqlalchemy import (
    DealAttachmentRepository,
    DealRepository,
    StoredFileRepository,
)
from app.schemas.deal_attachments import DealAttachmentListResponse, DealAttachmentResponse
from app.schemas.files import StoredFileResponse
from app.services.deals import DealNotFound, DealServiceError
from app.storage.files import ManagedFileStorage


class DealAttachmentNotFound(DealServiceError):
    code = "not_found"
    status_code = 404


class ArchivedDealAttachmentMutation(DealServiceError):
    code = "archived_deal"
    status_code = 422


class DealAttachmentService:
    def __init__(self, db: Session, storage: ManagedFileStorage | None = None) -> None:
        self.db = db
        self.deals = DealRepository(db)
        self.attachments = DealAttachmentRepository(db)
        self.files = StoredFileRepository(db)
        self.storage = storage or ManagedFileStorage()

    def list_for_deal(self, deal_id: str) -> DealAttachmentListResponse:
        self._require_deal(deal_id)
        return DealAttachmentListResponse(
            attachments=[
                self._response(attachment)
                for attachment in self.attachments.list_for_deal(deal_id)
            ]
        )

    def upload(
        self,
        deal_id: str,
        *,
        original_name: str,
        content: bytes,
        mime_type: str | None,
    ) -> DealAttachmentResponse:
        self._require_mutable_deal(deal_id)
        file_id = models.uuid_str()
        try:
            safe_name = self.storage.safe_original_name(original_name)
            stored = self.storage.store_bytes(
                file_id=file_id,
                kind=StoredFileKind.DEAL_ATTACHMENT,
                original_name=safe_name,
                content=content,
                mime_type=mime_type,
            )
        except ValueError as exc:
            raise DealServiceError(
                str(exc),
                details={"original_name": original_name},
            ) from exc

        stored_file = self.files.create(
            id=file_id,
            kind=StoredFileKind.DEAL_ATTACHMENT.value,
            original_name=safe_name,
            storage_path=stored.relative_path,
            mime_type=stored.mime_type,
            size_bytes=stored.size_bytes,
            checksum=stored.checksum,
        )
        attachment = self.attachments.create(deal_id=deal_id, file_id=stored_file.id)
        self.db.commit()
        return self._response(attachment)

    def delete(self, deal_id: str, attachment_id: str) -> None:
        self._require_mutable_deal(deal_id)
        attachment = self.attachments.get_for_deal(deal_id, attachment_id)
        if not attachment:
            raise DealAttachmentNotFound(
                "Deal attachment not found.",
                details={"deal_id": deal_id, "attachment_id": attachment_id},
            )

        stored_file = attachment.file
        path = self.storage.resolve_relative(stored_file.storage_path)
        if path.exists():
            path.unlink()
        self.attachments.delete(attachment)
        self.files.delete(stored_file)
        self.db.commit()

    def _require_deal(self, deal_id: str) -> models.Deal:
        deal = self.deals.get(deal_id)
        if not deal:
            raise DealNotFound("Deal not found.", details={"deal_id": deal_id})
        return deal

    def _require_mutable_deal(self, deal_id: str) -> models.Deal:
        deal = self._require_deal(deal_id)
        if deal.archived_at is not None:
            raise ArchivedDealAttachmentMutation(
                "Archived deals cannot be modified.",
                details={"deal_id": deal_id},
            )
        return deal

    def _file_response(self, stored_file: models.StoredFile) -> StoredFileResponse:
        path = self.storage.resolve_relative(stored_file.storage_path)
        return StoredFileResponse(
            id=stored_file.id,
            kind=StoredFileKind(stored_file.kind),
            original_name=stored_file.original_name,
            mime_type=stored_file.mime_type,
            size_bytes=stored_file.size_bytes,
            checksum=stored_file.checksum,
            exists=path.exists(),
            created_at=stored_file.created_at,
            updated_at=stored_file.updated_at,
        )

    def _response(self, attachment: models.DealAttachment) -> DealAttachmentResponse:
        return DealAttachmentResponse(
            id=attachment.id,
            deal_id=attachment.deal_id,
            file=self._file_response(attachment.file),
            created_at=attachment.created_at,
            updated_at=attachment.updated_at,
        )
