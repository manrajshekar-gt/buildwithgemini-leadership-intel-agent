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
                "company_twitter_handle": d.get("company_twitter_handle") or "N/A",
                "key_partners": d.get("key_partners") or [],
                "key_competitors": d.get("key_competitors") or [],
            }
        elif comp:
            if not companies[comp]["logo_url"] and d.get("logo_url"):
                companies[comp]["logo_url"] = d.get("logo_url")
            if companies[comp]["company_twitter_handle"] == "N/A" and d.get("company_twitter_handle"):
                companies[comp]["company_twitter_handle"] = d.get("company_twitter_handle")
            if not companies[comp]["key_partners"] and d.get("key_partners"):
                companies[comp]["key_partners"] = d.get("key_partners")
            if not companies[comp]["key_competitors"] and d.get("key_competitors"):
                companies[comp]["key_competitors"] = d.get("key_competitors")
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
        "Company URL",
        "Company Twitter",
        "Key Partners",
        "Key Competitors",
        "Name",
        "Title",
        "Group",
        "Email",
        "Individual Twitter",
        "Recent Tweets",
        "Logo URL",
        "Committee",
        "Independent",
        "Tenure (Years)",
        "Bio",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for r in records:
        tweets_list = r.get("recent_tweets") or []
        tweets_str = " | ".join(tweets_list) if isinstance(tweets_list, list) else str(tweets_list)

        partners_list = r.get("key_partners") or []
        partners_str = " | ".join(f"{p.get('name')} ({p.get('website')})" for p in partners_list if isinstance(p, dict)) if partners_list else "N/A"

        competitors_list = r.get("key_competitors") or []
        competitors_str = " | ".join(f"{c.get('name')} ({c.get('website')})" for c in competitors_list if isinstance(c, dict)) if competitors_list else "N/A"

        writer.writerow({
            "Company": r.get("company_name", ""),
            "Company URL": r.get("company_url") or "",
            "Company Twitter": r.get("company_twitter_handle") or "N/A",
            "Key Partners": partners_str,
            "Key Competitors": competitors_str,
            "Name": r.get("name", ""),
            "Title": r.get("title", ""),
            "Group": r.get("group", ""),
            "Email": r.get("email") or "N/A",
            "Individual Twitter": r.get("twitter_handle") or "N/A",
            "Recent Tweets": tweets_str or "N/A",
            "Logo URL": r.get("logo_url") or "N/A",
            "Committee": r.get("committee") or "N/A",
            "Independent": "Yes" if r.get("is_independent") else "No",
            "Tenure (Years)": r.get("tenure_years") if r.get("tenure_years") is not None else "N/A",
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

    lines = [line.strip() for line in text.splitlines() if line.strip() and all(32 <= ord(c) <= 126 for c in line)]
    if not lines:
        return {"status": "error", "message": "Uploaded file is empty"}

    raw_reader = csv.reader(lines)
    items_to_process = []
    for row in raw_reader:
        if not row:
            continue
        val = row[0].strip()
        if val.lower() in ["company", "company_name", "domain", "url", "name", "website"]:
            continue
        if val and val not in items_to_process:
            items_to_process.append(val)

    if not items_to_process:
        return {"status": "error", "message": "No valid company names or domains found in CSV."}

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
        already_exists = any(item_lower in ec or ec in item_lower for ec in existing_companies)
        if already_exists:
            results.append({
                "query": item,
                "status": "already_indexed",
                "message": f"'{item}' is already collected in Firestore.",
            })
            continue

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
    company_twitter_found = ""
    company_recent_tweets_found = []
    key_partners_found = []
    key_competitors_found = []

    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        c_name = d.get("company_name", "")
        c_url = d.get("company_url", "")
        p_name = d.get("name", "")
        p_title = d.get("title", "")
        p_email = d.get("email", "")
        p_twitter = d.get("twitter_handle", "")

        matches_company = query_str in c_name.lower() or query_str in c_url.lower()
        matches_person = (
            query_str in p_name.lower() or 
            query_str in p_title.lower() or 
            query_str in p_email.lower() or
            query_str in p_twitter.lower()
        )

        if matches_company or matches_person:
            if not company_name_found and c_name:
                company_name_found = c_name
            if not company_logo_found and d.get("logo_url"):
                company_logo_found = d.get("logo_url")
            if not company_url_found and c_url:
                company_url_found = c_url
            if not company_twitter_found and d.get("company_twitter_handle"):
                company_twitter_found = d.get("company_twitter_handle")
            if not company_recent_tweets_found and d.get("company_recent_tweets"):
                company_recent_tweets_found = d.get("company_recent_tweets")
            if not key_partners_found and d.get("key_partners"):
                key_partners_found = d.get("key_partners")
            if not key_competitors_found and d.get("key_competitors"):
                key_competitors_found = d.get("key_competitors")

            group = d.get("group", "Executive Management")
            if "board" in group.lower():
                board_members.append(d)
            else:
                executives.append(d)

    total_results = len(executives) + len(board_members)

    if total_results == 0:
        print(f"Zero results for '{q}' in Firestore. Launching auto-discovery & logo generation pipeline...")
        discovered = discover_and_save_company(q)
        return discovered

    return {
        "query": q,
        "company_name": company_name_found or q,
        "company_logo": company_logo_found,
        "company_url": company_url_found,
        "company_twitter_handle": company_twitter_found or "N/A",
        "company_recent_tweets": company_recent_tweets_found or [],
        "key_partners": key_partners_found or [],
        "key_competitors": key_competitors_found or [],
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
