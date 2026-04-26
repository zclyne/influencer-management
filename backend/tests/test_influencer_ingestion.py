from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import (
    Deal,
    ImportSession,
    Influencer,
    InfluencerAudienceSnapshot,
    InfluencerContact,
    InfluencerPlatform,
)
from app.enums import DealStatus, ImportSourceType
from app.influencers.ingestion.adapters import ModashCsvImportAdapter, UnsupportedImportFileError
from app.repositories.sqlalchemy import (
    CampaignRepository,
    DealRepository,
    InfluencerContactRepository,
    InfluencerPlatformRepository,
)
from app.schemas.influencer_ingestion import (
    ImportPreviewInput,
    IngestionConfirmRequest,
    IngestionConfirmRow,
)
from app.services.influencer_ingestion import InfluencerIngestionService

MODASH_EXPORT_FIXTURE = Path(__file__).with_name("modash-export.csv")


def _preview_input(content: bytes, file_name: str = "modash.csv") -> ImportPreviewInput:
    return ImportPreviewInput(
        source_type=ImportSourceType.MODASH_CSV,
        file_name=file_name,
        content=content,
    )


def _confirm_request(
    rows: list,
    file_name: str = "modash.csv",
    target_campaign_id: str | None = None,
) -> IngestionConfirmRequest:
    return IngestionConfirmRequest(
        source_type=ImportSourceType.MODASH_CSV,
        rows=[IngestionConfirmRow(row=row, action="create") for row in rows],
        file_name=file_name,
        target_campaign_id=target_campaign_id,
    )


def test_modash_adapter_maps_fields_and_preserves_raw_status() -> None:
    csv = (
        "Username,Channel,Account URL,Fullname,#Followers/Subscribers,%ER,"
        "Email_1,Status,Note,Labels\n"
        "creator,Instagram,https://instagram.com/creator?utm_source=x,Creator Name,"
        "12.5K,3%,A@EXAMPLE.COM,Lead,Keep,VIP\n"
    )
    row = ModashCsvImportAdapter().parse(_preview_input(csv.encode()))[0]
    assert row.display_name == "Creator Name"
    assert row.platform == "instagram"
    assert row.follower_count == 12500
    assert str(row.engagement_rate) == "0.03"
    assert row.contacts[0].email == "a@example.com"
    assert row.raw_row_json["Status"] == "Lead"
    assert not hasattr(row, "deal_status")


def test_modash_adapter_rejects_missing_required_headers() -> None:
    csv = "Username,Channel\ncreator,Instagram\n"
    try:
        ModashCsvImportAdapter().parse(_preview_input(csv.encode()))
    except UnsupportedImportFileError as exc:
        assert "Account URL" in str(exc)
    else:
        raise AssertionError("Expected unsupported file error")


def test_ingestion_confirm_creates_records_without_deal_status_mapping(
    db_session: Session,
) -> None:
    csv = (
        "Username,Channel,Account URL,Fullname,#Followers/Subscribers,%ER,"
        "Email_1,Status,Note,Labels\n"
        "creator,Instagram,https://instagram.com/creator,Creator Name,1000,0.03,"
        "a@example.com,Approved,Note,VIP\n"
    )
    service = InfluencerIngestionService(db_session)
    preview = service.preview_import(_preview_input(csv.encode()))
    result = service.confirm_import(_confirm_request([preview.rows[0].row]))
    assert result.imported_count == 1
    assert result.skipped_count == 0
    assert result.rows[0].status == "created"


def test_modash_preview_api_returns_canonical_rows(api_client: TestClient) -> None:
    csv = (
        "Username,Channel,Account URL,Fullname,#Followers/Subscribers,%ER,"
        "Email_1,Status,Note,Labels\n"
        "creator,Instagram,https://instagram.com/creator,Creator Name,1000,0.03,"
        "a@example.com,Approved,Note,VIP\n"
    )
    response = api_client.post(
        "/api/v1/influencers/imports/modash/preview",
        files={"file": ("modash.csv", csv, "text/csv")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source_type"] == "modash_csv"
    assert body["row_count"] == 1
    assert body["rows"][0]["status"] == "new"
    assert body["rows"][0]["row"]["display_name"] == "Creator Name"


def test_modash_preview_api_rejects_missing_required_header(
    api_client: TestClient,
) -> None:
    response = api_client.post(
        "/api/v1/influencers/imports/modash/preview",
        files={"file": ("bad.csv", "Username,Channel\ncreator,Instagram\n", "text/csv")},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "unsupported_import_file"
    assert "Account URL" in body["message"]


def test_modash_confirm_api_creates_session_and_session_lookup(
    api_client: TestClient,
) -> None:
    csv = (
        "Username,Channel,Account URL,Fullname,#Followers/Subscribers,%ER,"
        "Email_1,Status,Note,Labels\n"
        "creator,Instagram,https://instagram.com/creator,Creator Name,1000,0.03,"
        "a@example.com,Approved,Note,VIP\n"
    )
    preview_response = api_client.post(
        "/api/v1/influencers/imports/modash/preview",
        files={"file": ("modash.csv", csv, "text/csv")},
    )
    row = preview_response.json()["rows"][0]["row"]

    confirm_response = api_client.post(
        "/api/v1/influencers/imports/confirm",
        json={
            "source_type": "modash_csv",
            "rows": [{"row": row, "action": "create"}],
            "file_name": "modash.csv",
        },
    )

    assert confirm_response.status_code == 200
    confirm_body = confirm_response.json()
    assert confirm_body["imported_count"] == 1
    assert confirm_body["skipped_count"] == 0
    assert confirm_body["row_count"] == 1
    assert confirm_body["rows"][0]["status"] == "created"

    session_response = api_client.get(
        f"/api/v1/influencers/imports/sessions/{confirm_body['import_session_id']}"
    )
    assert session_response.status_code == 200
    session_body = session_response.json()
    assert session_body["id"] == confirm_body["import_session_id"]
    assert session_body["source_type"] == "modash_csv"
    assert session_body["file_name"] == "modash.csv"
    assert session_body["imported_count"] == 1


def test_get_unknown_import_session_returns_404(api_client: TestClient) -> None:
    response = api_client.get("/api/v1/influencers/imports/sessions/missing-session")

    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "not_found"
    assert body["details"] == {"import_session_id": "missing-session"}


def test_modash_confirm_conflicts_on_existing_campaign_deal(
    db_session: Session,
) -> None:
    csv = (
        "Username,Channel,Account URL,Fullname,#Followers/Subscribers,%ER,"
        "Email_1,Status,Note,Labels\n"
        "creator,Instagram,https://instagram.com/creator,Creator Name,1000,0.03,"
        "a@example.com,Approved,Note,VIP\n"
    )
    campaign = CampaignRepository(db_session).create(name="Launch")
    service = InfluencerIngestionService(db_session)

    first_preview = service.preview_import(_preview_input(csv.encode()))
    first_result = service.confirm_import(
        _confirm_request(
            [first_preview.rows[0].row],
            target_campaign_id=campaign.id,
        )
    )
    assert first_result.imported_count == 1
    assert first_result.created_deals == 1

    second_preview = service.preview_import(_preview_input(csv.encode()))
    second_result = service.confirm_import(
        _confirm_request(
            [second_preview.rows[0].row],
            target_campaign_id=campaign.id,
        )
    )

    assert second_result.imported_count == 0
    assert second_result.conflict_count == 1
    assert second_result.created_deals == 0
    deal = DealRepository(db_session).get_by_campaign_influencer(
        campaign.id, second_preview.rows[0].dedup.influencer_id
    )
    assert deal is not None
    assert deal.status == DealStatus.DRAFT.value


def test_real_modash_export_preview_and_import_populates_influencer_graph(
    db_session: Session,
) -> None:
    content = MODASH_EXPORT_FIXTURE.read_bytes()
    service = InfluencerIngestionService(db_session)

    preview = service.preview_import(_preview_input(content, file_name="modash-export.csv"))

    assert preview.row_count == 179
    assert {row.status for row in preview.rows} == {"new"}
    assert not any(row.row.parse_errors for row in preview.rows)
    assert not any(row.row.warnings for row in preview.rows)
    assert sum(len(row.row.contacts) for row in preview.rows) == 258
    assert sum(len(row.row.social_links) for row in preview.rows) == 530
    assert sum(bool(row.row.age_gender_json) for row in preview.rows) == 179
    assert sum(bool(row.row.top_countries_json) for row in preview.rows) == 179
    assert sum(bool(row.row.top_cities_json) for row in preview.rows) == 104
    assert sum(bool(row.row.top_interests_json) for row in preview.rows) == 102

    first_row = preview.rows[0].row
    assert first_row.display_name == "Carter Smith"
    assert first_row.normalized_profile_url == "https://instagram.com/carterpcs_"
    assert first_row.follower_count == 816983
    assert str(first_row.engagement_rate) == "0.024483"
    assert str(first_row.follower_credibility) == "0.818719"
    assert str(first_row.notable_follower_rate) == "0.049925"
    assert first_row.contacts[0].email == "carterpcs@rakugomedia.com"
    assert first_row.raw_row_json["Status"] == "NotStarted"
    assert first_row.raw_row_json["Note"] == ""
    assert first_row.raw_row_json["Labels"] == ""

    result = service.confirm_import(
        _confirm_request(
            [row.row for row in preview.rows],
            file_name="modash-export.csv",
        )
    )

    assert result.row_count == 179
    assert result.imported_count == 179
    assert result.skipped_count == 0
    assert result.conflict_count == 0
    assert result.created_deals == 0
    assert {row.status for row in result.rows} == {"created", "merged"}

    assert db_session.scalar(select(func.count()).select_from(Influencer)) == 174
    assert db_session.scalar(select(func.count()).select_from(InfluencerPlatform)) == 577
    assert db_session.scalar(select(func.count()).select_from(InfluencerContact)) == 249
    assert db_session.scalar(select(func.count()).select_from(InfluencerAudienceSnapshot)) == 179
    assert db_session.scalar(select(func.count()).select_from(ImportSession)) == 1
    assert db_session.scalar(select(func.count()).select_from(Deal)) == 0

    primary_platform = InfluencerPlatformRepository(
        db_session
    ).find_by_normalized_profile_url("https://instagram.com/carterpcs_")
    assert primary_platform is not None
    assert primary_platform.username == "@carterpcs_"
    assert primary_platform.normalized_username == "carterpcs_"
    assert primary_platform.follower_count == 816983
    assert str(primary_platform.engagement_rate) == "0.024483"
    assert str(primary_platform.follower_credibility) == "0.818719"
    assert str(primary_platform.notable_follower_rate) == "0.049925"
    assert primary_platform.raw_metrics_json["%Follower Credibility"] == "0.818719"

    influencer = db_session.get(Influencer, primary_platform.influencer_id)
    assert influencer is not None
    assert influencer.display_name == "Carter Smith"
    assert influencer.full_name == "Carter Smith"
    assert influencer.gender == "MALE"
    assert "making tech less of a snooze fest" in (influencer.bio or "")
    assert not hasattr(influencer, "status")
    assert not hasattr(influencer, "labels")

    contacts = InfluencerContactRepository(db_session).find_by_email(
        "carterpcs@rakugomedia.com"
    )
    assert len(contacts) == 1
    assert contacts[0].influencer_id == influencer.id
    assert contacts[0].source == "Email_1"

    snapshot = db_session.scalar(
        select(InfluencerAudienceSnapshot).where(
            InfluencerAudienceSnapshot.influencer_platform_id == primary_platform.id
        )
    )
    assert snapshot is not None
    assert snapshot.age_gender_json["Male"] == 0.922059
    assert snapshot.top_countries_json[0] == {
        "label": "United States",
        "value": 0.570561,
        "raw": "United States=0.570561",
        "rank": 1,
    }

    import_session = service.get_session(result.import_session_id)
    assert import_session.file_name == "modash-export.csv"
    assert import_session.row_count == 179
    assert import_session.imported_count == 179


def test_real_modash_export_import_with_campaign_creates_unique_deals(
    db_session: Session,
) -> None:
    content = MODASH_EXPORT_FIXTURE.read_bytes()
    campaign = CampaignRepository(db_session).create(name="Spring Launch")
    service = InfluencerIngestionService(db_session)
    preview = service.preview_import(_preview_input(content, file_name="modash-export.csv"))

    result = service.confirm_import(
        _confirm_request(
            [row.row for row in preview.rows],
            file_name="modash-export.csv",
            target_campaign_id=campaign.id,
        )
    )

    assert result.row_count == 179
    assert result.imported_count == 179
    assert result.skipped_count == 0
    assert result.conflict_count == 0
    assert result.created_deals == 174
    assert db_session.scalar(select(func.count()).select_from(Influencer)) == 174
    assert db_session.scalar(select(func.count()).select_from(Deal)) == 174

    duplicate_result = service.confirm_import(
        _confirm_request(
            [row.row for row in preview.rows],
            file_name="modash-export.csv",
            target_campaign_id=campaign.id,
        )
    )

    assert duplicate_result.imported_count == 0
    assert duplicate_result.conflict_count == 179
    assert duplicate_result.created_deals == 0
    assert db_session.scalar(select(func.count()).select_from(Influencer)) == 174
    assert db_session.scalar(select(func.count()).select_from(Deal)) == 174
