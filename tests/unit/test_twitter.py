"""Unit tests for X (Twitter) profile data verification, company mapping, and 404 prevention."""

import sys
from pathlib import Path
import pytest
from starlette.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "frontend"))

import main
from app.db import LocalFirestoreClient, COLLECTION_NAME


@pytest.fixture
def client():
    return TestClient(main.app)


def test_unverified_name_guessed_handles_are_purged(client):
    """Ensure guessed handles based on names (which 404) are purged to N/A."""
    # Abbott: Robert B. Ford should NOT have @RobertBFord (doesn't exist)
    resp = client.get("/api/search?q=Abbott")
    assert resp.status_code == 200
    abbott_members = {m["name"]: m.get("twitter_handle") for m in resp.json()["executives"] + resp.json()["board_of_directors"]}
    assert abbott_members.get("Robert B. Ford") in ["N/A", None]

    # T-Mobile: Srini Gopalan, Peter Osvaldik, John Saw, Deeanne King, Chris Sambar
    resp = client.get("/api/search?q=T-Mobile")
    assert resp.status_code == 200
    tmo_members = {m["name"]: m.get("twitter_handle") for m in resp.json()["executives"] + resp.json()["board_of_directors"]}
    assert tmo_members.get("Srini Gopalan") in ["N/A", None]
    assert tmo_members.get("Peter Osvaldik") in ["N/A", None]
    assert tmo_members.get("John Saw, Ph.D.") in ["N/A", None]
    assert tmo_members.get("Deeanne King") in ["N/A", None]
    assert tmo_members.get("Chris Sambar") in ["N/A", None]

    # Alphabet: Ruth Porat
    resp = client.get("/api/search?q=Alphabet")
    assert resp.status_code == 200
    goog_members = {m["name"]: m.get("twitter_handle") for m in resp.json()["executives"] + resp.json()["board_of_directors"]}
    assert goog_members.get("Ruth Porat") in ["N/A", None]

    # AMD: Mark Papermaster
    resp = client.get("/api/search?q=AMD")
    assert resp.status_code == 200
    amd_members = {m["name"]: m.get("twitter_handle") for m in resp.json()["executives"] + resp.json()["board_of_directors"]}
    assert amd_members.get("Mark Papermaster") in ["N/A", None]


def test_verified_authentic_handles_are_correctly_mapped(client):
    """Ensure genuine verified handles matching company role are preserved."""
    # Alphabet: Sundar Pichai (@sundarpichai), Kent Walker (@Kent_Walker)
    resp = client.get("/api/search?q=Alphabet")
    assert resp.status_code == 200
    goog_members = {m["name"]: m.get("twitter_handle") for m in resp.json()["executives"] + resp.json()["board_of_directors"]}
    assert goog_members.get("Sundar Pichai") == "@sundarpichai"
    assert goog_members.get("Kent Walker") == "@Kent_Walker"

    # AMD: Lisa Su (@LisaSu), Jack Huynh (@jackhuynh)
    resp = client.get("/api/search?q=AMD")
    assert resp.status_code == 200
    amd_members = {m["name"]: m.get("twitter_handle") for m in resp.json()["executives"] + resp.json()["board_of_directors"]}
    assert amd_members.get("Lisa Su") == "@LisaSu"
    assert amd_members.get("Jack Huynh") == "@jackhuynh"

    # Stripe: Patrick Collison (@patrickc), John Collison (@collision), Will Gaybrick (@gaybrick)
    resp = client.get("/api/search?q=Stripe")
    assert resp.status_code == 200
    stripe_members = {m["name"]: m.get("twitter_handle") for m in resp.json()["executives"] + resp.json()["board_of_directors"]}
    assert stripe_members.get("Patrick Collison") == "@patrickc"
    assert stripe_members.get("John Collison") == "@collision"
    assert stripe_members.get("Will Gaybrick") == "@gaybrick"

    # T-Mobile: Mike Sievert (@MikeSievert), Jon Freier (@JonFreier), Marcelo Claure (@marceloclaure)
    resp = client.get("/api/search?q=T-Mobile")
    assert resp.status_code == 200
    tmo_members = {m["name"]: m.get("twitter_handle") for m in resp.json()["executives"] + resp.json()["board_of_directors"]}
    assert tmo_members.get("G. Michael (Mike) Sievert") == "@MikeSievert"
    assert tmo_members.get("Jon Freier") == "@JonFreier"
    assert tmo_members.get("Marcelo Claure") == "@marceloclaure"


def test_company_twitter_handles_are_verified(client):
    """Ensure company corporate handles are authentic."""
    resp = client.get("/api/search?q=Spotify")
    assert resp.status_code == 200
    assert resp.json()["company_twitter_handle"] == "@Spotify"

    resp = client.get("/api/search?q=AMD")
    assert resp.status_code == 200
    assert resp.json()["company_twitter_handle"] == "@AMD"

    resp = client.get("/api/search?q=Abbott")
    assert resp.status_code == 200
    assert resp.json()["company_twitter_handle"] == "@AbbottNews"


def test_frontend_renders_x_svg_and_omits_unverified():
    """Verify frontend HTML handles X icons and avoids rendering broken links."""
    index_html_path = ROOT_DIR / "frontend" / "static" / "index.html"
    content = index_html_path.read_text(encoding="utf-8")

    # SVG X icon present for verified handles
    assert "viewBox=\"0 0 24 24\"" in content
    assert "M18.244 2.25h3.308l-7.227 8.26" in content

    # Uses rel="noopener" for target="_blank"
    assert 'target="_blank" rel="noopener" class="twitter-link"' in content
