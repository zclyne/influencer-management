from sqlalchemy.orm import Session

from app.db import models
from app.repositories.sqlalchemy import TemplateRepository
from app.schemas.templates import (
    TemplateCreateRequest,
    TemplateListResponse,
    TemplateResponse,
    TemplateUpdateRequest,
)


class TemplateServiceError(Exception):
    code = "template_error"
    status_code = 422

    def __init__(self, message: str, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class TemplateNotFound(TemplateServiceError):
    code = "not_found"
    status_code = 404


class TemplateService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.templates = TemplateRepository(db)

    def list_templates(self, *, include_archived: bool = False) -> TemplateListResponse:
        return TemplateListResponse(
            templates=[
                self._template_response(template)
                for template in self.templates.list(include_archived=include_archived)
            ]
        )

    def create_template(self, payload: TemplateCreateRequest) -> TemplateResponse:
        template = self.templates.create(**payload.model_dump())
        self.db.commit()
        return self._template_response(template)

    def get_template(self, template_id: str) -> TemplateResponse:
        return self._template_response(self._require_template(template_id))

    def update_template(
        self, template_id: str, payload: TemplateUpdateRequest
    ) -> TemplateResponse:
        template = self._require_template(template_id)
        values = payload.model_dump(exclude_unset=True)
        if values:
            template = self.templates.update(template, **values)
            self.db.commit()
        return self._template_response(template)

    def archive_template(self, template_id: str) -> None:
        template = self._require_template(template_id)
        self.templates.archive(template)
        self.db.commit()

    def _require_template(self, template_id: str) -> models.Template:
        template = self.templates.get(template_id)
        if not template:
            raise TemplateNotFound("Template not found.", details={"template_id": template_id})
        return template

    def _template_response(self, template: models.Template) -> TemplateResponse:
        return TemplateResponse(
            id=template.id,
            type=template.type,
            name=template.name,
            subject_template=template.subject_template,
            body_template=template.body_template,
            description=template.description,
            is_archived=template.is_archived,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )
