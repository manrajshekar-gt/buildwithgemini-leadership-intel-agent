"""Unit tests for LinkedIn profiles support across agent tools, API endpoints, and database models."""

import csv
import io
import json
import sys
from pathlib import Path
import pytest
from starlette.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "frontend"))

import main
from app.agent import save_leadership_profile, export_governance_report_csv, get_leadership_profiles
from app.db import LocalFirestoreClient, COLLECTION_NAME


@pytest.fixture
def client():
    return TestClient(main.app)


def test_agent_save_and_retrieve_linkedin(tmp_path, monkeypatch):
    test_db = tmp_path / "test_linkedin.db"
    mock_client = LocalFirestoreClient(db_path=test_db)
    monkeypatch.setattr("app.agent.get_firestore_client", lambda: mock_client)

    res = save_leadership_profile(
        name="Dr. Lisa Su",
        company_name="AMD",
        title="Chair and CEO",
        group="Executive Management",
        email="lisa.su@amd.com",
        linkedin_url="https://www.linkedin.com/in/lisasu",
        company_linkedin_url="https://www.linkedin.com/company/amd",
    )
    assert res["status"] == "success"
    profile = res["profile"]
    assert profile["linkedin_url"] == "https://www.linkedin.com/in/lisasu"
    assert profile["company_linkedin_url"] == "https://www.linkedin.com/company/amd"


def test_agent_export_csv_includes_linkedin(tmp_path, monkeypatch):
    test_db = tmp_path / "test_export.db"
    mock_client = LocalFirestoreClient(db_path=test_db)
    monkeypatch.setattr("app.agent.get_firestore_client", lambda: mock_client)

    # Save a profile
    save_leadership_profile(
        name="Alice Founder",
        company_name="Acme Corp",
        title="CEO",
        group="Executive Management",
        email="alice@acmecorp.com",
        linkedin_url="https://www.linkedin.com/in/alice-founder",
        company_linkedin_url="https://www.linkedin.com/company/acmecorp",
    )

    # Export report
    res = export_governance_report_csv("Acme Corp")
    assert res["status"] == "success"
    assert res["profiles_exported"] == 1


def test_api_search_returns_linkedin(client):
    response = client.get("/api/search?q=AMD")
    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "AMD"
    assert data["company_linkedin_url"] == "https://www.linkedin.com/company/amd"
    assert len(data["executives"]) > 0
    first_exec = data["executives"][0]
    assert "linkedin_url" in first_exec
    assert first_exec["linkedin_url"].startswith("https://www.linkedin.com/in/")


def test_api_admin_metrics_linkedin_coverage(client):
    response = client.get("/api/admin/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "coverage" in data
    assert "linkedin_coverage_pct" in data["coverage"]
    assert "linkedin_count" in data["coverage"]
    assert data["coverage"]["linkedin_coverage_pct"] > 0
    assert data["coverage"]["linkedin_count"] > 0


def test_api_admin_export_csv_has_linkedin_headers(client):
    response = client.get("/api/admin/export/csv")
    assert response.status_code == 200
    csv_text = response.text
    reader = csv.reader(io.StringIO(csv_text))
    header = next(reader)
    assert "Company LinkedIn" in header
    assert "LinkedIn Profile" in header


def test_unlisted_linkedin_profile_handling(tmp_path, monkeypatch):
    test_db = tmp_path / "test_unlisted.db"
    mock_client = LocalFirestoreClient(db_path=test_db)
    monkeypatch.setattr("app.agent.get_firestore_client", lambda: mock_client)

    res = save_leadership_profile(
        name="John Collison",
        company_name="Stripe",
        title="President & Co-Founder",
        group="Executive Management",
        email="N/A",
        linkedin_url="N/A",
        company_linkedin_url="https://www.linkedin.com/company/stripe",
    )
    assert res["status"] == "success"
    profile = res["profile"]
    assert profile["linkedin_url"] == "N/A"
    assert profile["company_linkedin_url"] == "https://www.linkedin.com/company/stripe"


def test_frontend_html_contains_not_found_indicator():
    index_html_path = ROOT_DIR / "frontend" / "static" / "index.html"
    content = index_html_path.read_text(encoding="utf-8")
    assert "LinkedIn profile not found" in content
    assert "company-linkedin-badge-unlisted" in content
    assert "LinkedIn not listed" in content

    admin_html_path = ROOT_DIR / "frontend" / "static" / "admin.html"
    admin_content = admin_html_path.read_text(encoding="utf-8")
    assert "Not Found" in admin_content


def test_purged_unverified_vanity_profiles(client):
    # Stripe: John & Patrick Collison must NOT have false vanity URLs
    resp = client.get("/api/search?q=Stripe")
    assert resp.status_code == 200
    stripe_members = {m["name"]: m["linkedin_url"] for m in resp.json()["executives"] + resp.json()["board_of_directors"]}
    assert stripe_members.get("John Collison") == "N/A"
    assert stripe_members.get("Patrick Collison") == "N/A"
    assert stripe_members.get("Steffan Tomlinson") == "https://www.linkedin.com/in/steffantomlinson"

    # AMD: Lisa Su must be N/A, while Jean Hu is verified
    resp = client.get("/api/search?q=AMD")
    assert resp.status_code == 200
    amd_members = {m["name"]: m["linkedin_url"] for m in resp.json()["executives"] + resp.json()["board_of_directors"]}
    assert amd_members.get("Lisa Su") == "N/A"
    assert amd_members.get("Jean Hu") == "https://www.linkedin.com/in/jean-hu-520140"

    # Alphabet: Sundar Pichai must be N/A, while Ruth Porat is verified
    resp = client.get("/api/search?q=Alphabet")
    assert resp.status_code == 200
    goog_members = {m["name"]: m["linkedin_url"] for m in resp.json()["executives"] + resp.json()["board_of_directors"]}
    assert goog_members.get("Sundar Pichai") == "N/A"
    assert goog_members.get("Ruth Porat") == "https://www.linkedin.com/in/ruth-porat-8b7768297"

    # Fieldwire: Felix Hess must be N/A (was unrelated UX designer)
    resp = client.get("/api/search?q=Fieldwire")
    assert resp.status_code == 200
    fw_members = {m["name"]: m["linkedin_url"] for m in resp.json()["executives"] + resp.json()["board_of_directors"]}
    assert fw_members.get("Felix Hess") == "N/A"
    assert fw_members.get("Yves Frinault") == "https://www.linkedin.com/in/yvesfrinault"


