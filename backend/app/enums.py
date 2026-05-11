from enum import StrEnum


class CampaignStatus(StrEnum):
    PLANNING = "PLANNING"
    ACTIVE = "ACTIVE"
    EVALUATING = "EVALUATING"
    CLOSED = "CLOSED"


class DealStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    LOST = "LOST"


class DeliverableStatus(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    POSTED = "POSTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class CompensationItemType(StrEnum):
    CASH_STIPEND = "CASH_STIPEND"
    PRODUCT_GIFT = "PRODUCT_GIFT"
    SAMPLE_PRODUCT = "SAMPLE_PRODUCT"
    FLIGHT_REIMBURSEMENT = "FLIGHT_REIMBURSEMENT"
    HOTEL_REIMBURSEMENT = "HOTEL_REIMBURSEMENT"
    LOCAL_TRANSPORT_REIMBURSEMENT = "LOCAL_TRANSPORT_REIMBURSEMENT"
    MEAL_OR_PER_DIEM = "MEAL_OR_PER_DIEM"
    OTHER = "OTHER"


class CompensationItemStatus(StrEnum):
    PLANNED = "PLANNED"
    PROMISED = "PROMISED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ContactRole(StrEnum):
    CREATOR = "creator"
    MANAGER = "manager"
    AGENCY = "agency"
    ASSISTANT = "assistant"
    BUSINESS = "business"
    UNKNOWN = "unknown"


class TemplateType(StrEnum):
    OUTREACH_EMAIL = "OUTREACH_EMAIL"
    CONTRACT = "CONTRACT"
    REPORT = "REPORT"
    BRIEF = "BRIEF"
    OTHER = "OTHER"


class ImportSourceType(StrEnum):
    MODASH_CSV = "modash_csv"
    MANUAL = "manual"


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StoredFileKind(StrEnum):
    IMPORT_SOURCE = "import_source"
    CAMPAIGN_EXPORT = "campaign_export"
    RECEIPT = "receipt"
    EMAIL_ATTACHMENT = "email_attachment"
    GENERATED_DOCUMENT = "generated_document"
