from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.enums import JobStatus, StoredFileKind
from app.services.files import FileService, ManagedFileMissing
from app.services.jobs import JobService
from app.storage.files import ManagedFileStorage


def test_job_service_success_and_failure(db_session: Session, api_client: TestClient) -> None:
    service = JobService(db_session)
    created = service.create_job("export")

    succeeded = service.run_sync(created.id, lambda: {"file_id": "file-1"})

    assert succeeded.status == JobStatus.SUCCEEDED
    assert succeeded.result_json == {"file_id": "file-1"}

    failed = service.create_job("email_sync")
    service.run_sync(failed.id, lambda: (_ for _ in ()).throw(RuntimeError("secret stack")))

    response = api_client.get(f"/api/v1/jobs/{failed.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == JobStatus.FAILED.value
    assert body["error_message"] == "secret stack"


def test_unknown_job_returns_404(api_client: TestClient) -> None:
    response = api_client.get("/api/v1/jobs/missing")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_file_service_stores_downloads_and_deletes_managed_file(
    db_session: Session,
    tmp_path: Path,
) -> None:
    service = FileService(db_session, storage=ManagedFileStorage(tmp_path))

    stored = service.register_bytes(
        kind=StoredFileKind.CAMPAIGN_EXPORT,
        original_name="../pipeline.csv",
        content="name\nCréateur\n".encode(),
        mime_type="text/csv",
    )

    assert stored.original_name == "pipeline.csv"
    assert stored.size_bytes == len("name\nCréateur\n".encode())
    assert stored.exists is True
    path = service.resolve_download_path(stored.id)
    assert path.read_text() == "name\nCréateur\n"

    service.delete_file(stored.id)
    assert not path.exists()


def test_file_service_reports_missing_managed_file(
    db_session: Session,
    tmp_path: Path,
) -> None:
    service = FileService(db_session, storage=ManagedFileStorage(tmp_path))
    stored = service.register_bytes(
        kind=StoredFileKind.RECEIPT,
        original_name="receipt.txt",
        content=b"paid",
    )
    service.resolve_download_path(stored.id).unlink()

    refreshed = service.get_file(stored.id)
    assert refreshed.exists is False

    try:
        service.resolve_download_path(stored.id)
    except ManagedFileMissing as exc:
        assert exc.code == "managed_file_missing"
    else:
        raise AssertionError("Expected missing managed file error.")
