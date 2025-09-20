from fastapi.testclient import TestClient
from main import app


def test_chart_adjust_placeholder_contract():
    client = TestClient(app)
    payload = {"foo": "bar"}
    resp = client.post("/v1/charts/adjust", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "message" in data
    assert data.get("request") == payload

