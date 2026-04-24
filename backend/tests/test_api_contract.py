from fastapi.testclient import TestClient

from app.main import app


def test_validation_errors_use_shared_shape(api_client: TestClient) -> None:
    response = api_client.post("/api/v1/campaigns", json={"name": "   "})

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
    assert body["message"] == "Request validation failed."
    assert body["request_id"] is None
    assert body["details"]["path"] == "/api/v1/campaigns"


def test_openapi_contains_versioned_paths_and_response_models() -> None:
    schema = app.openapi()

    assert "/api/v1/brands" in schema["paths"]
    assert "/api/v1/influencers" in schema["paths"]
    assert "/api/v1/influencers/manual" in schema["paths"]
    manual_post = schema["paths"]["/api/v1/influencers/manual"]["post"]
    response_schema = manual_post["responses"]["201"]["content"]["application/json"]["schema"]
    assert response_schema["$ref"].endswith("/ManualInfluencerResponse")
