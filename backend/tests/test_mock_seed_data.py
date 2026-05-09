import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import models
from app.dev.seed_mock_data import apply_sql

BACKEND_ROOT = Path(__file__).resolve().parents[1]
MOCK_SQL_PATH = BACKEND_ROOT / "dev" / "mock_data.sql"
PRIMARY_CAMPAIGN_ID = "22222222-2222-2222-2222-222222222221"
ARCHIVED_CAMPAIGN_ID = "22222222-2222-2222-2222-222222222225"
MULTI_PLATFORM_INFLUENCER_ID = "44444444-4444-4444-4444-444444444441"
ACTIVE_DEAL_ID = "99999999-9999-9999-9999-999999999991"


def _driver_connection(db_session: Session) -> sqlite3.Connection:
    raw_connection = db_session.connection().connection
    driver_connection = getattr(raw_connection, "driver_connection", None)
    if driver_connection is not None:
        return driver_connection
    return raw_connection.connection


def _seed_session(db_session: Session) -> None:
    _driver_connection(db_session).executescript(MOCK_SQL_PATH.read_text(encoding="utf-8"))
    db_session.expire_all()


def test_mock_sql_seed_is_idempotent(db_session: Session) -> None:
    _seed_session(db_session)
    first_counts = {
        "campaigns": db_session.scalar(select(func.count()).select_from(models.Campaign)),
        "influencers": db_session.scalar(select(func.count()).select_from(models.Influencer)),
        "deals": db_session.scalar(select(func.count()).select_from(models.Deal)),
        "templates": db_session.scalar(select(func.count()).select_from(models.Template)),
    }

    _seed_session(db_session)
    second_counts = {
        "campaigns": db_session.scalar(select(func.count()).select_from(models.Campaign)),
        "influencers": db_session.scalar(select(func.count()).select_from(models.Influencer)),
        "deals": db_session.scalar(select(func.count()).select_from(models.Deal)),
        "templates": db_session.scalar(select(func.count()).select_from(models.Template)),
    }

    assert first_counts == second_counts
    assert second_counts == {
        "campaigns": 5,
        "influencers": 8,
        "deals": 9,
        "templates": 4,
    }


def test_seeded_campaign_and_influencer_api_smoke(
    api_client: TestClient,
    db_session: Session,
) -> None:
    _seed_session(db_session)

    campaigns_response = api_client.get("/api/v1/campaigns")
    assert campaigns_response.status_code == 200
    campaigns = campaigns_response.json()["campaigns"]
    assert [campaign["id"] for campaign in campaigns] == [
        PRIMARY_CAMPAIGN_ID,
        "22222222-2222-2222-2222-222222222222",
        "22222222-2222-2222-2222-222222222223",
        "22222222-2222-2222-2222-222222222224",
    ]
    assert campaigns[0]["brands"][0]["brand"]["name"] == "Northstar Beauty"
    assert campaigns[0]["tags"] == ["beauty", "skincare", "launch"]

    archived_response = api_client.get("/api/v1/campaigns", params={"include_archived": True})
    assert archived_response.status_code == 200
    archived_ids = {campaign["id"] for campaign in archived_response.json()["campaigns"]}
    assert ARCHIVED_CAMPAIGN_ID in archived_ids

    influencers_response = api_client.get("/api/v1/influencers")
    assert influencers_response.status_code == 200
    influencers = influencers_response.json()["influencers"]
    maya = next(item for item in influencers if item["id"] == MULTI_PLATFORM_INFLUENCER_ID)
    assert maya["primary_platform"]["platform"] == "tiktok"
    assert maya["follower_count"] == 380000
    assert maya["tags"] == ["beauty", "skincare", "macro"]

    influencer_detail_response = api_client.get(
        f"/api/v1/influencers/{MULTI_PLATFORM_INFLUENCER_ID}"
    )
    assert influencer_detail_response.status_code == 200
    influencer_detail = influencer_detail_response.json()
    assert len(influencer_detail["platforms"]) == 2
    assert influencer_detail["contacts"][0]["email"] == "maya@example.com"


def test_seeded_deal_graph_and_export_api_smoke(
    api_client: TestClient,
    db_session: Session,
) -> None:
    _seed_session(db_session)

    deals_response = api_client.get(f"/api/v1/campaigns/{PRIMARY_CAMPAIGN_ID}/deals")
    assert deals_response.status_code == 200
    deals = deals_response.json()["deals"]
    statuses = {deal["status"] for deal in deals}
    assert {"ACTIVE", "NEGOTIATING", "OUTREACHED"}.issubset(statuses)
    active_deal = next(deal for deal in deals if deal["id"] == ACTIVE_DEAL_ID)
    assert active_deal["deliverables"]["total_count"] == 2
    assert active_deal["compensation"]["cash_totals"]["USD"] == "8500.00"

    deliverables_response = api_client.get(f"/api/v1/deals/{ACTIVE_DEAL_ID}/deliverables")
    assert deliverables_response.status_code == 200
    assert len(deliverables_response.json()["deliverables"]) == 2

    compensation_response = api_client.get(f"/api/v1/deals/{ACTIVE_DEAL_ID}/compensation-items")
    assert compensation_response.status_code == 200
    assert len(compensation_response.json()["compensation_items"]) == 2

    export_response = api_client.get(f"/api/v1/campaigns/{PRIMARY_CAMPAIGN_ID}/export.csv")
    assert export_response.status_code == 200
    assert "Maya Chen" in export_response.text
    assert "Northstar Beauty" in export_response.text


def test_seed_runner_command_applies_sql_to_file_database(tmp_path: Path) -> None:
    database_path = tmp_path / "seed-runner.db"
    env = {
        **os.environ,
        "PYTHONPATH": str(BACKEND_ROOT),
    }
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.dev.seed_mock_data",
            "--database-url",
            f"sqlite:///{database_path}",
        ],
        cwd=BACKEND_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Seeded mock data into" in result.stdout
    assert "campaigns: 5" in result.stdout

    counts = apply_sql(f"sqlite:///{database_path}", MOCK_SQL_PATH)
    assert counts["campaigns"] == 5
    assert counts["deals"] == 9
