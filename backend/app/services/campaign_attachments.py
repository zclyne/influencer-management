from sqlalchemy.orm import Session

from app.db import models
from app.enums import StoredFileKind
from app.repositories.sqlalchemy import (
    CampaignAttachmentRepository,
    CampaignRepository,
    StoredFileRepository,
)
from app.schemas.campaign_attachments import (
    CampaignAttachmentListResponse,
    CampaignAttachmentResponse,
)
from app.schemas.files import StoredFileResponse
from app.services.campaigns import CampaignNotFound, CampaignServiceError
from app.storage.files import ManagedFileStorage


class CampaignAttachmentNotFound(CampaignServiceError):
    code = "not_found"
    status_code = 404


class ArchivedCampaignAttachmentMutation(CampaignServiceError):
    code = "archived_campaign"
    status_code = 422


class CampaignAttachmentService:
    def __init__(self, db: Session, storage: ManagedFileStorage | None = None) -> None:
        self.db = db
        self.campaigns = CampaignRepository(db)
        self.attachments = CampaignAttachmentRepository(db)
        self.files = StoredFileRepository(db)
        self.storage = storage or ManagedFileStorage()

    def list_for_campaign(self, campaign_id: str) -> CampaignAttachmentListResponse:
        self._require_campaign(campaign_id)
        return CampaignAttachmentListResponse(
            attachments=[
                self._response(attachment)
                for attachment in self.attachments.list_for_campaign(campaign_id)
            ]
        )

    def upload(
        self,
        campaign_id: str,
        *,
        original_name: str,
        content: bytes,
        mime_type: str | None,
    ) -> CampaignAttachmentResponse:
        self._require_mutable_campaign(campaign_id)
        file_id = models.uuid_str()
        try:
            safe_name = self.storage.safe_original_name(original_name)
            stored = self.storage.store_bytes(
                file_id=file_id,
                kind=StoredFileKind.CAMPAIGN_ATTACHMENT,
                original_name=safe_name,
                content=content,
                mime_type=mime_type,
            )
        except ValueError as exc:
            raise CampaignServiceError(
                str(exc),
                details={"original_name": original_name},
            ) from exc

        stored_file = self.files.create(
            id=file_id,
            kind=StoredFileKind.CAMPAIGN_ATTACHMENT.value,
            original_name=safe_name,
            storage_path=stored.relative_path,
            mime_type=stored.mime_type,
            size_bytes=stored.size_bytes,
            checksum=stored.checksum,
        )
        attachment = self.attachments.create(campaign_id=campaign_id, file_id=stored_file.id)
        self.db.commit()
        return self._response(attachment)

    def delete(self, campaign_id: str, attachment_id: str) -> None:
        self._require_mutable_campaign(campaign_id)
        attachment = self.attachments.get_for_campaign(campaign_id, attachment_id)
        if not attachment:
            raise CampaignAttachmentNotFound(
                "Campaign attachment not found.",
                details={"campaign_id": campaign_id, "attachment_id": attachment_id},
            )

        stored_file = attachment.file
        path = self.storage.resolve_relative(stored_file.storage_path)
        if path.exists():
            path.unlink()
        self.attachments.delete(attachment)
        self.files.delete(stored_file)
        self.db.commit()

    def _require_campaign(self, campaign_id: str) -> models.Campaign:
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            raise CampaignNotFound("Campaign not found.", details={"campaign_id": campaign_id})
        return campaign

    def _require_mutable_campaign(self, campaign_id: str) -> models.Campaign:
        campaign = self._require_campaign(campaign_id)
        if campaign.archived_at is not None:
            raise ArchivedCampaignAttachmentMutation(
                "Archived campaigns cannot be modified.",
                details={"campaign_id": campaign_id},
            )
        return campaign

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

    def _response(self, attachment: models.CampaignAttachment) -> CampaignAttachmentResponse:
        return CampaignAttachmentResponse(
            id=attachment.id,
            campaign_id=attachment.campaign_id,
            file=self._file_response(attachment.file),
            created_at=attachment.created_at,
            updated_at=attachment.updated_at,
        )
