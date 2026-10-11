import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_index_endpoint():
    response = client.get("/")
    assert response.status_code == 200


def test_config_endpoint():
    response = client.get("/config")
    assert response.status_code == 200
    data = response.json()
    assert "photo_enabled" in data


def test_recommend_endpoint_units():
    payload = {
        "state": "MH",
        "units_kwh": 350.0,
        "billing_days": 30,
        "has_roof": "yes",
        "lang": "en",
    }
    response = client.post("/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["system_kw"] > 0
    assert data["bill_before"] > 0
    assert data["bill_after"] >= 0
    assert data["subsidy"] > 0
    assert data["savings_monthly"] > 0
    assert len(data["explanation"]) > 0
    assert len(data["checklist"]) > 0


def test_recommend_endpoint_amount_only():
    payload = {
        "state": "UP",
        "units_kwh": 0.0,
        "amount_payable": 2200.0,
        "billing_days": 30,
        "has_roof": "yes",
    }
    response = client.post("/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["system_kw"] > 0
    assert data["bill_before"] > 0


def test_recommend_validation_missing_input():
    payload = {
        "state": "DL",
        "units_kwh": 0.0,
    }
    response = client.post("/recommend", json=payload)
    assert response.status_code == 422  # Pydantic validation error


def test_recommend_default_roof():
    payload = {
        "state": "DL",
        "units_kwh": 250.0,
    }
    response = client.post("/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["system_kw"] > 0.0
    assert data["subsidy"] > 0.0
    assert data["bill_after"] < data["bill_before"]
