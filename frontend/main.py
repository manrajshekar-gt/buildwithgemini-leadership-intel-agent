"""FastAPI Backend and Search Proxy for Leadership Intelligence Agent.

Serves the front-end web UI and provides:
1. /api/search - Instant query of Firestore; if no records exist, triggers automated
   real-time discovery (scraping, Gemini extraction, custom logo generation, and DB storage).
2. /api/companies - List of all companies available in the database.
3. /api/admin/all - Full list of all stored profiles across all companies.
4. /api/admin/export/csv - Download all stored profiles as CSV.
5. /api/admin/export/json - Download all stored profiles as JSON.
6. /api/admin/upload-batch - Upload a CSV of company names / domains and batch extract & store!
"""

import csv
import io
import json
import os
import re
from typing import List, Optional
from fastapi import FastAPI, File, Query, UploadFile
from fastapi.responses import Response, StreamingResponse
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


@app.get("/api/admin/all")
async def get_all_records():
    """Returns all records stored in Firestore."""
    db = get_db()
    docs = list(db.collection(COLLECTION_NAME).stream())
    records = []
    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        records.append(d)
    
    records.sort(key=lambda x: (x.get("company_name", "").lower(), x.get("group", ""), x.get("name", "")))
    return {
        "total_records": len(records),
        "records": records,
    }


@app.get("/api/admin/export/csv")
async def export_all_csv():
    """Streams all collected database records as a CSV download."""
    db = get_db()
    docs = list(db.collection(COLLECTION_NAME).stream())
    records = []
    for doc in docs:
        d = doc.to_dict()
        records.append(d)

    records.sort(key=lambda x: (x.get("company_name", "").lower(), x.get("group", ""), x.get("name", "")))

    output = io.StringIO()
    fieldnames = [
        "Company",
        "Name",
        "Title",
        "Group",
        "Email",
        "Logo URL",
        "Committee",
        "Independent",
        "Tenure (Years)",
        "Company URL",
        "Bio",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for r in records:
        writer.writerow({
            "Company": r.get("company_name", ""),
            "Name": r.get("name", ""),
            "Title": r.get("title", ""),
            "Group": r.get("group", ""),
            "Email": r.get("email") or "N/A",
            "Logo URL": r.get("logo_url") or "N/A",
            "Committee": r.get("committee") or "N/A",
            "Independent": "Yes" if r.get("is_independent") else "No",
            "Tenure (Years)": r.get("tenure_years") if r.get("tenure_years") is not None else "N/A",
            "Company URL": r.get("company_url") or "",
            "Bio": r.get("bio") or "",
        })

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=all-leadership-intel-data.csv"},
    )


@app.get("/api/admin/export/json")
async def export_all_json():
    """Streams all collected database records as a formatted JSON download."""
    db = get_db()
    docs = list(db.collection(COLLECTION_NAME).stream())
    records = []
    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        records.append(d)

    records.sort(key=lambda x: (x.get("company_name", "").lower(), x.get("name", "")))
    json_data = json.dumps(records, indent=2)
    return Response(
        content=json_data,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=all-leadership-intel-data.json"},
    )


@app.post("/api/admin/upload-batch")
async def upload_batch_csv(file: UploadFile = File(...)):
    """Receives an uploaded CSV file of companies/domains, parses items, checks if already extracted,

    and runs extraction, logo generation, and Firestore storage for any new ones.
    """
    contents = await file.read()
    try:
        text = contents.decode("utf-8")
    except UnicodeDecodeError:
        text = contents.decode("latin1", errors="ignore")

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return {"status": "error", "message": "Uploaded file is empty"}

    # Determine items from CSV rows
    raw_reader = csv.reader(lines)
    items_to_process = []
    for row in raw_reader:
        if not row:
            continue
        val = row[0].strip()
        # Skip header rows if present
        if val.lower() in ["company", "company_name", "domain", "url", "name", "website"]:
            continue
        if val and val not in items_to_process:
            items_to_process.append(val)

    if not items_to_process:
        return {"status": "error", "message": "No valid company names or domains found in CSV."}

    # Retrieve existing companies to avoid duplicate scraping
    db = get_db()
    existing_docs = list(db.collection(COLLECTION_NAME).stream())
    existing_companies = set()
    for d in existing_docs:
        c = d.to_dict().get("company_name", "")
        if c:
            existing_companies.add(c.lower())
        u = d.to_dict().get("company_url", "")
        if u:
            existing_companies.add(u.lower())

    results = []
    for item in items_to_process:
        item_lower = item.lower()
        # Check if already present
        already_exists = any(item_lower in ec or ec in item_lower for ec in existing_companies)
        if already_exists:
            results.append({
                "query": item,
                "status": "already_indexed",
                "message": f"'{item}' is already collected in Firestore.",
            })
            continue

        # Run extraction & storage
        try:
            res = discover_and_save_company(item)
            results.append({
                "query": item,
                "status": "success",
                "company_name": res.get("company_name"),
                "profiles_saved": res.get("total_results", 0),
                "logo_url": res.get("company_logo", ""),
            })
            if res.get("company_name"):
                existing_companies.add(res["company_name"].lower())
        except Exception as e:
            results.append({
                "query": item,
                "status": "failed",
                "error": str(e),
            })

    total_added = sum(r.get("profiles_saved", 0) for r in results if r.get("status") == "success")
    return {
        "status": "completed",
        "total_requested": len(items_to_process),
        "total_new_profiles_added": total_added,
        "details": results,
    }


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
