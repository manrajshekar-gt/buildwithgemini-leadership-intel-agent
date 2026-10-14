"""Unit tests for batch extract / upload, duplicate detection, and UI confirmation."""

import io
import sys
from pathlib import Path
from unittest.mock import patch
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


def test_batch_upload_existing_companies_ignored_and_confirmed(client):
    """Uploading companies already in DB should confirm success, skip them, and show 0 new."""
    csv_bytes = b"Intel\nMeta\nAnthropic\n"
    resp = client.post(
        "/api/admin/upload-batch",
        files={"file": ("test_companies.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["total_requested"] == 3
    assert data["total_new_companies"] == 0
    assert data["total_skipped_companies"] == 3
    assert data["total_new_profiles_added"] == 0
    assert len(data["newly_added"]) == 0
    assert len(data["already_indexed"]) == 3

    indexed_names = {c["company_name"] for c in data["already_indexed"]}
    assert "Intel" in indexed_names
    assert "Meta" in indexed_names
    assert "Anthropic" in indexed_names

    # Confirmation message explains that all were already in catalog
    assert "already indexed" in data["message"].lower()


def test_batch_upload_picks_up_new_and_ignores_existing(client):
    """Batch upload should pick up only new companies and ignore existing ones."""
    mock_company = {
        "company_name": "TestNewCorp",
        "company_logo": "https://example.com/logo.png",
        "total_results": 5,
        "executives": [{"name": "Jane Doe", "title": "CEO", "group": "Executive Management"}],
        "board_of_directors": [],
    }

    with patch("main.discover_and_save_company", return_value=mock_company) as mock_discover:
        csv_bytes = b"Intel\nTestNewCorp\nMeta\n"
        resp = client.post(
            "/api/admin/upload-batch",
            files={"file": ("mixed.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["total_new_companies"] == 1
        assert data["total_skipped_companies"] == 2
        assert data["total_new_profiles_added"] == 5

        # Check newly added list explicitly indicates the new company
        newly_added_names = [c["company_name"] for c in data["newly_added"]]
        assert "TestNewCorp" in newly_added_names

        # Check existing list explicitly contains Intel and Meta
        skipped_names = [c["company_name"] for c in data["already_indexed"]]
        assert "Intel" in skipped_names
        assert "Meta" in skipped_names

        # Ensure discover_and_save_company was called ONLY for the new company
        mock_discover.assert_called_once_with("TestNewCorp")


def test_batch_upload_direct_paste_form_data(client):
    """Batch endpoint should accept raw_text form data for direct pasting."""
    resp = client.post(
        "/api/admin/upload-batch",
        data={"raw_text": "Intel\nMeta\nAnthropic"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["total_skipped_companies"] == 3
    assert data["total_new_companies"] == 0


def test_admin_ui_batch_elements():
    """Verify admin.html contains batch confirmation, dropzone, and paste elements."""
    admin_path = ROOT_DIR / "frontend" / "static" / "admin.html"
    content = admin_path.read_text(encoding="utf-8")

    # Dropzone and file input
    assert 'id="batch-dropzone"' in content
    assert 'id="csv-file-input"' in content
    assert "drag-active" in content

    # Direct paste box
    assert 'id="btn-toggle-paste"' in content
    assert 'id="batch-paste-box"' in content
    assert 'id="batch-paste-text"' in content

    # Result renderer and handlers
    assert "function renderBatchResult(" in content
    assert "function handleBatchUploadFile(" in content
    assert "function submitBatchPaste(" in content
    assert "Batch Extraction Successful" in content
    assert "Already in System" in content
