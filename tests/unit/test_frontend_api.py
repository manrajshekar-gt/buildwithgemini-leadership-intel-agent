"""Unit tests for frontend FastAPI search, admin, and metrics endpoints."""

import sys
from pathlib import Path
import pytest
from starlette.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "frontend"))

import main


@pytest.fixture
def client():
    return TestClient(main.app)


def test_static_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Leadership & Board Intelligence Portal" in response.text


def test_api_search_cached(client):
    response = client.get("/api/search?q=Alphabet")
    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "Alphabet Inc."
    assert data["total_results"] >= 2
    assert len(data["executives"]) >= 1


def test_api_admin_schedule(client):
    response = client.get("/api/admin/schedule")
    assert response.status_code == 200
    data = response.json()
    assert "frequency" in data
    assert "enabled" in data


def test_api_admin_metrics(client):
    response = client.get("/api/admin/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "catalog" in data
    assert data["catalog"]["total_profiles"] >= 2
