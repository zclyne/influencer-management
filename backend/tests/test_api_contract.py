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


def test_unmatched_routes_use_shared_error_shape(api_client: TestClient) -> None:
    response = api_client.get("/api/v1/not-a-real-route")

    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "not_found"
    assert body["message"] == "Not Found"
    assert body["request_id"] is None
    assert body["details"] == {"path": "/api/v1/not-a-real-route"}


def test_empty_list_endpoints_return_empty_arrays(api_client: TestClient) -> None:
    campaigns_response = api_client.get("/api/v1/campaigns")
    brands_response = api_client.get("/api/v1/brands")
    influencers_response = api_client.get("/api/v1/influencers")
    campaign_response = api_client.post("/api/v1/campaigns", json={"name": "Empty Campaign"})
    campaign_id = campaign_response.json()["id"]
    deals_response = api_client.get(f"/api/v1/campaigns/{campaign_id}/deals")

    assert campaigns_response.status_code == 200
    assert campaigns_response.json()["campaigns"] == []
    assert brands_response.status_code == 200
    assert brands_response.json()["brands"] == []
    assert influencers_response.status_code == 200
    assert influencers_response.json()["influencers"] == []
    assert deals_response.status_code == 200
    assert deals_response.json()["deals"] == []


def test_openapi_contains_versioned_paths_and_response_models() -> None:
    schema = app.openapi()

    assert "/api/v1/brands" in schema["paths"]
    assert "/api/v1/influencers" in schema["paths"]
    assert "/api/v1/influencers/manual" in schema["paths"]
    manual_post = schema["paths"]["/api/v1/influencers/manual"]["post"]
    response_schema = manual_post["responses"]["201"]["content"]["application/json"]["schema"]
    assert response_schema["$ref"].endswith("/ManualInfluencerResponse")
