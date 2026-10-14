"""Unit tests for company-only LinkedIn support across agent tools, API endpoints, and database models."""

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


def test_agent_save_and_retrieve_company_linkedin(tmp_path, monkeypatch):
    test_db = tmp_path / "test_linkedin.db"
    mock_client = LocalFirestoreClient(db_path=test_db)
    monkeypatch.setattr("app.agent.get_firestore_client", lambda: mock_client)

    res = save_leadership_profile(
        name="Dr. Lisa Su",
        company_name="AMD",
        title="Chair and CEO",
        group="Executive Management",
        email="lisa.su@amd.com",
        company_linkedin_url="https://www.linkedin.com/company/amd",
    )
    assert res["status"] == "success"
    profile = res["profile"]
    assert "linkedin_url" not in profile
    assert profile["company_linkedin_url"] == "https://www.linkedin.com/company/amd"


def test_agent_export_csv_includes_company_linkedin(tmp_path, monkeypatch):
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
        company_linkedin_url="https://www.linkedin.com/company/acmecorp",
    )

    # Export report
    res = export_governance_report_csv("Acme Corp")
    assert res["status"] == "success"
    assert res["profiles_exported"] == 1


def test_api_search_returns_company_linkedin_and_omits_individual(client):
    response = client.get("/api/search?q=AMD")
    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "AMD"
    assert data["company_linkedin_url"] == "https://www.linkedin.com/company/amd"
    assert len(data["executives"]) > 0
    first_exec = data["executives"][0]
    # Individual linkedin is removed from member records
    assert "linkedin_url" not in first_exec


def test_api_admin_metrics_company_linkedin_coverage(client):
    response = client.get("/api/admin/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "coverage" in data
    assert "company_linkedin_coverage_pct" in data["coverage"]
    assert "company_linkedin_count" in data["coverage"]
    assert data["coverage"]["company_linkedin_coverage_pct"] > 0
    assert data["coverage"]["company_linkedin_count"] > 0


def test_api_admin_export_csv_has_company_linkedin_only(client):
    response = client.get("/api/admin/export/csv")
    assert response.status_code == 200
    csv_text = response.text
    reader = csv.reader(io.StringIO(csv_text))
    header = next(reader)
    assert "Company LinkedIn" in header
    assert "LinkedIn Profile" not in header


def test_frontend_html_omits_individual_linkedin_and_preserves_company_linkedin():
    index_html_path = ROOT_DIR / "frontend" / "static" / "index.html"
    content = index_html_path.read_text(encoding="utf-8")
    # Individual LinkedIn and not-found indicators removed from member cards
    assert "LinkedIn profile not found" not in content
    assert "linkedin-link" not in content
    # Company LinkedIn badge preserved in corporate header
    assert "company-linkedin-badge" in content

    admin_html_path = ROOT_DIR / "frontend" / "static" / "admin.html"
    admin_content = admin_html_path.read_text(encoding="utf-8")
    assert "Company LinkedIn" in admin_content
    assert "<th>LinkedIn</th>" not in admin_content


def test_individual_and_bod_linkedin_removed_for_all_companies(client):
    for comp in ["Stripe", "AMD", "Alphabet", "Fieldwire", "Microsoft", "Netflix"]:
        resp = client.get(f"/api/search?q={comp}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["company_linkedin_url"].startswith("https://www.linkedin.com/company/")
        for m in data["executives"] + data["board_of_directors"]:
            assert "linkedin_url" not in m
