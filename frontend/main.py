"""FastAPI Backend and Search Proxy for Leadership Intelligence Agent.

Serves the front-end web UI and provides:
1. /api/search - Instant query of Firestore; if no records exist, triggers automated
   real-time discovery (scraping, Gemini extraction, custom logo generation, and DB storage).
2. /api/companies - List of all companies available in the database.
"""

import os
from typing import Optional
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import firestore

from discovery_service import discover_and_save_company

app = FastAPI(title="Leadership Intelligence Portal")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ID = "qwiklabs-gcp-04-a0fc456f3f90"
COLLECTION_NAME = "leadership_profiles"

_db = None


def get_db():
    global _db
    if _db is None:
        _db = firestore.Client(project=PROJECT_ID)
    return _db


@app.get("/api/companies")
async def list_companies():
    """Returns a list of distinct companies currently stored in the database."""
    db = get_db()
    docs = db.collection(COLLECTION_NAME).stream()
    companies = {}
    for doc in docs:
        d = doc.to_dict()
        comp = d.get("company_name")
        if comp and comp not in companies:
            companies[comp] = {
                "name": comp,
                "logo_url": d.get("logo_url") or "",
                "company_url": d.get("company_url") or "",
            }
        elif comp and not companies[comp]["logo_url"] and d.get("logo_url"):
            companies[comp]["logo_url"] = d.get("logo_url")
    return list(companies.values())


@app.get("/api/search")
async def search_leadership(q: str = Query(..., min_length=1)):
    """Search for leadership profiles. If not found in DB, triggers auto-discovery and logo gen."""
    db = get_db()
    query_str = q.strip().lower()
    docs = list(db.collection(COLLECTION_NAME).stream())

    executives = []
    board_members = []
    company_name_found = ""
    company_logo_found = ""
    company_url_found = ""

    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        c_name = d.get("company_name", "")
        c_url = d.get("company_url", "")
        p_name = d.get("name", "")
        p_title = d.get("title", "")
        p_email = d.get("email", "")

        matches_company = query_str in c_name.lower() or query_str in c_url.lower()
        matches_person = query_str in p_name.lower() or query_str in p_title.lower() or query_str in p_email.lower()

        if matches_company or matches_person:
            if not company_name_found and c_name:
                company_name_found = c_name
            if not company_logo_found and d.get("logo_url"):
                company_logo_found = d.get("logo_url")
            if not company_url_found and c_url:
                company_url_found = c_url

            group = d.get("group", "Executive Management")
            if "board" in group.lower():
                board_members.append(d)
            else:
                executives.append(d)

    total_results = len(executives) + len(board_members)

    # IF NO DATA IN DATABASE: Automatically run discovery pipeline!
    if total_results == 0:
        print(f"Zero results for '{q}' in Firestore. Launching auto-discovery & logo generation pipeline...")
        discovered = discover_and_save_company(q)
        return discovered

    return {
        "query": q,
        "company_name": company_name_found or q,
        "company_logo": company_logo_found,
        "company_url": company_url_found,
        "total_results": total_results,
        "executives": executives,
        "board_of_directors": board_members,
        "auto_discovered": False,
    }


STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8085, reload=True)
