"""Tests for guardian routing stub."""
from fastapi.testclient import TestClient
from app.main import app

def test_guardian_post():
    client = TestClient(app)
    payload = {"text": "Hello", "route_hint": "loan"}
    resp = client.post("/guardian", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "todo"
    assert data["route"] == "loan"

