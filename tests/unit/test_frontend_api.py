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


def test_admin_sidebar_panels():
    admin_path = ROOT_DIR / "frontend" / "static" / "admin.html"
    content = admin_path.read_text(encoding="utf-8")
    
    # Left sidebar panel present
    assert "admin-sidebar" in content
    assert "sidebar-nav" in content
    
    # All 4 tabs present in navigation
    assert 'data-tab="analytics"' in content
    assert 'data-tab="settings"' in content
    assert 'data-tab="integrations"' in content
    assert 'data-tab="bulk"' in content

    # All 4 corresponding tab content panels present
    assert 'id="tab-analytics"' in content
    assert 'id="tab-settings"' in content
    assert 'id="tab-integrations"' in content
    assert 'id="tab-bulk"' in content

    # Tab switching logic
    assert "function switchTab(tabId)" in content


def test_admin_bulk_operations_table_and_pagination():
    admin_path = ROOT_DIR / "frontend" / "static" / "admin.html"
    content = admin_path.read_text(encoding="utf-8")

    # Table and banner must reside inside tab-bulk
    tab_bulk_start = content.find('id="tab-bulk"')
    assert tab_bulk_start != -1

    tab_bulk_content = content[tab_bulk_start:]

    assert "All Collected Leadership Intelligence" in tab_bulk_content
    assert 'id="table-body"' in tab_bulk_content
    assert 'id="pagination-bar"' in tab_bulk_content
    assert 'id="btn-prev-page"' in tab_bulk_content
    assert 'id="btn-next-page"' in tab_bulk_content
    assert 'id="pagination-pages"' in tab_bulk_content

    # Verify table has been removed from tab-analytics
    tab_analytics_start = content.find('id="tab-analytics"')
    tab_settings_start = content.find('id="tab-settings"')
    tab_analytics_content = content[tab_analytics_start:tab_settings_start]
    assert "All Collected Leadership Intelligence" not in tab_analytics_content
    assert 'id="table-body"' not in tab_analytics_content

    # Pagination logic in JS (25 rows at a time)
    assert "const pageSize = 25;" in content
    assert "function renderTablePage()" in content
    assert "function updatePaginationControls(" in content
    assert "function changePage(" in content
    assert "function goToPage(" in content

