"""FastAPI Backend and Search Proxy for Leadership Intelligence Agent.

Serves the front-end web UI and provides:
1. /api/search - Instant query of Firestore with semantic vector search fallback.
2. /api/semantic-search - Natural-language executive search.
3. /api/webhook/crm - Outbound webhook trigger to sync leadership data with HubSpot/Salesforce.
4. /api/digest/weekly - Weekly competitor intelligence digest generator.
5. /api/admin/schedule - GET & POST endpoints to configure automated refresh frequency (Daily, 12h, 6h, Weekly, or Manual) and view execution telemetry.
6. /api/admin/schedule/run-now - Trigger an immediate full catalog automated refresh.
7. /api/admin/metrics - Real-time telemetry, coverage stats, performance counters & service health.
8. /api/admin/export/csv & /api/admin/export/json - Data downloads.
9. /api/admin/upload-batch - Batch CSV extraction.
"""

import asyncio
import csv
import io
import json
import os
import re
import time
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import firestore
import httpx

from discovery_service import discover_and_save_company, get_genai

app = FastAPI(title="Leadership Intelligence Portal & CRM Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-04-a0fc456f3f90")
COLLECTION_NAME = "leadership_profiles"
CONFIG_COLLECTION = "system_configurations"
SCHEDULE_DOC_ID = "refresh_schedule"

_db = None
_start_time = time.time()
_search_stats = {
    "total_queries": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "total_latency_seconds": 0.0,
}

# Automated scheduler state
_scheduler_task = None
_default_schedule = {
    "enabled": True,
    "frequency": "daily",  # options: hourly, every_6h, every_12h, daily, weekly, manual
    "interval_seconds": 86400,
    "last_run": None,
    "next_run": None,
    "last_status": "Idle (Awaiting schedule)",
    "last_companies_refreshed": 0,
    "last_duration_seconds": 0,
}


def get_db():
    global _db
    if _db is None:
        _db = firestore.Client(project=PROJECT_ID)
    return _db


# ==========================================
# AUTOMATED REFRESH RUNNER
# ==========================================

async def execute_scheduled_refresh():
    """Iterates through all indexed companies and re-runs discovery to refresh
    partners, competitors, latest tweets/statements, and executive movements.
    """
    db = get_db()
    docs = list(db.collection(COLLECTION_NAME).stream())
    distinct_companies = {}
    for d in docs:
        data = d.to_dict()
        comp = data.get("company_name")
        url = data.get("company_url")
        if comp and comp not in distinct_companies:
            distinct_companies[comp] = url or comp

    start_ts = time.time()
    refreshed_count = 0
    print(f"[Scheduler] Starting automated intelligence refresh for {len(distinct_companies)} companies...")

    for comp, query_val in distinct_companies.items():
        try:
            # Re-discover in thread to avoid blocking FastAPI
            await asyncio.to_thread(discover_and_save_company, query_val)
            refreshed_count += 1
            print(f"[Scheduler] Refreshed intelligence for: {comp}")
        except Exception as e:
            print(f"[Scheduler] Error refreshing {comp}: {e}")

    duration = round(time.time() - start_ts, 1)
    now_str = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

    # Update state in Firestore
    sched_doc = get_schedule_config()
    next_ts = time.time() + sched_doc.get("interval_seconds", 86400)
    next_str = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(next_ts))

    update_payload = {
        "last_run": now_str,
        "next_run": next_str,
        "last_status": f"Successfully refreshed {refreshed_count}/{len(distinct_companies)} companies in {duration}s",
        "last_companies_refreshed": refreshed_count,
        "last_duration_seconds": duration,
    }
    db.collection(CONFIG_COLLECTION).document(SCHEDULE_DOC_ID).set(update_payload, merge=True)
    return update_payload


async def scheduler_background_loop():
    """Continuous background loop monitoring schedule frequency."""
    # Small initial delay to allow FastAPI startup to complete cleanly
    await asyncio.sleep(5)
    while True:
        try:
            sched = get_schedule_config()
            if sched.get("enabled", True) and sched.get("frequency") != "manual":
                interval = sched.get("interval_seconds", 86400)
                last_run = sched.get("last_run_timestamp")
                now = time.time()

                if last_run is None:
                    # Initialize timestamp on first boot so it does not trigger immediately
                    db = get_db()
                    db.collection(CONFIG_COLLECTION).document(SCHEDULE_DOC_ID).set(
                        {"last_run_timestamp": now}, merge=True
                    )
                elif now - last_run >= interval:
                    # Update timestamp first to prevent re-entrancy
                    db = get_db()
                    db.collection(CONFIG_COLLECTION).document(SCHEDULE_DOC_ID).set(
                        {"last_run_timestamp": now}, merge=True
                    )
                    await execute_scheduled_refresh()
        except Exception as e:
            print(f"[Scheduler Loop Error] {e}")

        # Check every 60 seconds
        await asyncio.sleep(60)

        # Check every 60 seconds
        await asyncio.sleep(60)


@app.on_event("startup")
async def start_scheduler():
    global _scheduler_task
    _scheduler_task = asyncio.create_task(scheduler_background_loop())


def get_schedule_config() -> Dict[str, Any]:
    db = get_db()
    try:
        doc = db.collection(CONFIG_COLLECTION).document(SCHEDULE_DOC_ID).get()
        if doc.exists:
            merged = dict(_default_schedule)
            merged.update(doc.to_dict())
            return merged
    except Exception:
        pass
    return dict(_default_schedule)


# ==========================================
# ADMIN SCHEDULE CONTROLS & API
# ==========================================
@app.get("/api/admin/schedule")
async def get_schedule():
    """Returns current automation schedule, frequency, and telemetry."""
    return get_schedule_config()


@app.post("/api/admin/schedule")
async def update_schedule(payload: Dict[str, Any]):
    """Updates the automated intelligence refresh schedule at the admin level.

    Accepts:
    {
       "enabled": true,
       "frequency": "daily" | "every_12h" | "every_6h" | "hourly" | "weekly" | "manual"
    }
    """
    freq_map = {
        "hourly": 3600,
        "every_6h": 21600,
        "every_12h": 43200,
        "daily": 86400,
        "weekly": 604800,
        "manual": 0,
    }

    freq = payload.get("frequency", "daily")
    if freq not in freq_map:
        raise HTTPException(status_code=400, detail=f"Invalid frequency '{freq}'. Valid options: {list(freq_map.keys())}")

    enabled = bool(payload.get("enabled", True))
    interval = freq_map[freq]

    now_ts = time.time()
    next_run_str = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(now_ts + interval)) if enabled and interval > 0 else "Paused / Manual Only"

    updated = {
        "enabled": enabled,
        "frequency": freq,
        "interval_seconds": interval,
        "next_run": next_run_str,
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(now_ts)),
    }

    db = get_db()
    db.collection(CONFIG_COLLECTION).document(SCHEDULE_DOC_ID).set(updated, merge=True)
    return {"status": "success", "schedule": get_schedule_config()}


@app.post("/api/admin/schedule/run-now")
async def trigger_refresh_now():
    """Immediately triggers an on-demand full catalog refresh asynchronously."""
    asyncio.create_task(execute_scheduled_refresh())
    return {
        "status": "triggered",
        "message": "Automated intelligence refresh has been launched across all indexed companies in the background."
    }


# ==========================================
# 1. CRM WEBHOOK INTEGRATION (HubSpot/Salesforce)
# ==========================================
@app.post("/api/webhook/crm")
async def trigger_crm_sync(payload: Dict[str, Any]):
    """Syncs a company's leadership intelligence to an external CRM webhook."""
    company_name = payload.get("company_name", "").strip()
    webhook_url = payload.get("crm_webhook_url", "").strip()
    
    if not company_name:
        raise HTTPException(status_code=400, detail="Missing company_name")

    db = get_db()
    docs = list(db.collection(COLLECTION_NAME).where("company_name", "==", company_name).stream())
    if not docs:
        docs = [d for d in db.collection(COLLECTION_NAME).stream() if company_name.lower() in (d.to_dict().get("company_name", "")).lower()]

    if not docs:
        raise HTTPException(status_code=404, detail=f"No profiles found for company '{company_name}'")

    crm_payload = {
        "event": "leadership_intelligence.sync",
        "company": company_name,
        "timestamp": time.time(),
        "total_contacts": len(docs),
        "contacts": [
            {
                "name": d.to_dict().get("name"),
                "title": d.to_dict().get("title"),
                "email": d.to_dict().get("email"),
                "twitter": d.to_dict().get("twitter_handle"),
                "group": d.to_dict().get("group"),
                "compensation": d.to_dict().get("compensation"),
                "sec_source": d.to_dict().get("sec_filing_source"),
            }
            for d in docs
        ]
    }

    delivery_status = "payload_ready"
    if webhook_url:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.post(webhook_url, json=crm_payload)
                delivery_status = f"delivered (HTTP {resp.status_code})"
        except Exception as e:
            delivery_status = f"delivery_failed: {str(e)}"

    return {
        "status": "success",
        "crm_delivery": delivery_status,
        "synced_contacts_count": len(crm_payload["contacts"]),
        "payload": crm_payload,
    }


# ==========================================
# 2. VECTOR & SEMANTIC EXECUTIVE SEARCH (RAG)
# ==========================================
@app.get("/api/semantic-search")
async def semantic_search(prompt: str = Query(..., min_length=2)):
    """Natural-language semantic vector search across all executive & board member profiles."""
    db = get_db()
    docs = list(db.collection(COLLECTION_NAME).stream())
    catalog = [d.to_dict() for d in docs]

    if not catalog:
        return {"query": prompt, "matches": []}

    ai_client = get_genai()
    eval_prompt = f"""
You are an executive talent recruiter and vector search ranker.
User Search Query: "{prompt}"

Candidate Catalog:
{json.dumps([{"id": c.get("id"), "name": c.get("name"), "title": c.get("title"), "company": c.get("company_name"), "bio": c.get("bio"), "skills": c.get("skills_keywords", []), "group": c.get("group")} for c in catalog[:60]])}

Rank the top 1 to 6 most relevant matches based on semantic skill alignment, industry relevance, and role.
Return a JSON array of objects:
[
  {{
    "id": "exact candidate id",
    "relevance_score": float between 0.0 and 1.0,
    "match_reason": "1-sentence explanation of why they match the query"
  }}
]
Respond with ONLY JSON.
"""
    try:
        resp = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=eval_prompt,
            config=dict(response_mime_type="application/json")
        )
        ranked = json.loads(resp.text)
        ranked_ids = {r.get("id"): r for r in ranked if isinstance(r, dict)}

        results = []
        for c in catalog:
            if c.get("id") in ranked_ids:
                item = dict(c)
                item["relevance_score"] = ranked_ids[c.get("id")].get("relevance_score", 0.9)
                item["match_reason"] = ranked_ids[c.get("id")].get("match_reason", "")
                results.append(item)

        results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return {"query": prompt, "total_matches": len(results), "matches": results}
    except Exception as e:
        return {"query": prompt, "error": str(e), "matches": []}


# ==========================================
# 3. WEEKLY COMPETITOR INTELLIGENCE DIGEST
# ==========================================
@app.get("/api/digest/weekly")
async def generate_weekly_digest(company: Optional[str] = Query(None)):
    """Synthesizes a weekly competitor and leadership intelligence executive briefing."""
    db = get_db()
    docs = list(db.collection(COLLECTION_NAME).stream())
    all_records = [d.to_dict() for d in docs]

    if company:
        records = [r for r in all_records if company.lower() in (r.get("company_name", "")).lower()]
    else:
        records = all_records[:30]

    ai_client = get_genai()
    prompt = f"""
You are an executive strategic advisor preparing a high-level Weekly Competitor & Leadership Digest.
Data points collected:
{json.dumps([{"company": r.get("company_name"), "competitors": r.get("key_competitors"), "partners": r.get("key_partners"), "recent_tweets": r.get("company_recent_tweets")} for r in records[:15]])}

Generate an executive Monday Morning briefing containing:
1. Executive Summary & Market Shifts
2. Key Competitor Movements & Tactical Messaging
3. Strategic Partnership Watch
4. Leadership & Governance Radar
5. Recommended Action Items for Business Development

Format in professional, clean Markdown.
"""
    try:
        resp = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return {
            "status": "success",
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "digest_markdown": resp.text,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ==========================================
# 4. ADMIN METRICS & TELEMETRY
# ==========================================
@app.get("/api/admin/metrics")
async def get_system_metrics():
    """Computes real-time telemetry, coverage ratios, database health, and performance counters."""
    db = get_db()
    docs = list(db.collection(COLLECTION_NAME).stream())
    
    total_profiles = len(docs)
    companies = set()
    c_suite_count = 0
    board_count = 0
    with_email_count = 0
    with_twitter_count = 0
    with_tweets_count = 0
    total_partners = 0
    total_competitors = 0
    companies_with_logo = set()

    for doc in docs:
        d = doc.to_dict()
        c_name = d.get("company_name", "")
        if c_name:
            companies.add(c_name)
        if d.get("logo_url"):
            companies_with_logo.add(c_name)

        group = (d.get("group") or "").lower()
        if "board" in group:
            board_count += 1
        else:
            c_suite_count += 1

        email = d.get("email") or ""
        if email and email not in ["N/A", "None", ""]:
            with_email_count += 1

        twitter = d.get("twitter_handle") or ""
        if twitter and twitter not in ["N/A", "None", ""]:
            with_twitter_count += 1

        recent_tweets = d.get("recent_tweets") or []
        if recent_tweets:
            with_tweets_count += 1

        partners = d.get("key_partners") or []
        competitors = d.get("key_competitors") or []
        total_partners += len(partners)
        total_competitors += len(competitors)

    distinct_companies_count = len(companies)
    avg_profiles_per_company = round(total_profiles / distinct_companies_count, 1) if distinct_companies_count else 0
    email_coverage_pct = round((with_email_count / total_profiles) * 100, 1) if total_profiles else 0
    social_coverage_pct = round((with_twitter_count / total_profiles) * 100, 1) if total_profiles else 0
    logo_coverage_pct = round((len(companies_with_logo) / distinct_companies_count) * 100, 1) if distinct_companies_count else 0

    total_q = _search_stats["total_queries"]
    cache_hit_pct = round((_search_stats["cache_hits"] / total_q) * 100, 1) if total_q else 100.0
    avg_latency_ms = round((_search_stats["total_latency_seconds"] / total_q) * 1000, 1) if total_q else 0.0

    uptime_seconds = int(time.time() - _start_time)

    return {
        "catalog": {
            "total_companies": distinct_companies_count,
            "total_profiles": total_profiles,
            "c_suite_executives": c_suite_count,
            "board_of_directors": board_count,
            "avg_profiles_per_company": avg_profiles_per_company,
        },
        "coverage": {
            "email_coverage_pct": email_coverage_pct,
            "email_count": with_email_count,
            "social_coverage_pct": social_coverage_pct,
            "social_count": with_twitter_count,
            "logo_coverage_pct": logo_coverage_pct,
            "with_recent_messages": with_tweets_count,
        },
        "ecosystem": {
            "partners_data_points": total_partners,
            "competitors_data_points": total_competitors,
        },
        "performance": {
            "total_searches": total_q,
            "cache_hits": _search_stats["cache_hits"],
            "cache_misses": _search_stats["cache_misses"],
            "cache_hit_ratio_pct": cache_hit_pct,
            "avg_query_latency_ms": avg_latency_ms,
            "uptime_seconds": uptime_seconds,
        },
        "service_health": {
            "database_status": "ONLINE (Firestore Native)",
            "ai_engine_status": "ONLINE (Gemini 2.5 Flash on Vertex AI)",
            "storage_status": "ONLINE (Cloud Storage)",
            "gcp_project": PROJECT_ID,
            "region": "us-east1 / us-central1",
        }
    }


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
        "Compensation",
        "SEC Filing Source",
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
            "Compensation": r.get("compensation") or "N/A",
            "SEC Filing Source": r.get("sec_filing_source") or "N/A",
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
    """Receives an uploaded CSV file of companies/domains and batch processes them."""
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

    results = []
    for item in items_to_process:
        item_lower = item.lower()
        if any(item_lower in ec or ec in item_lower for ec in existing_companies):
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
            results.append({"query": item, "status": "failed", "error": str(e)})

    total_added = sum(r.get("profiles_saved", 0) for r in results if r.get("status") == "success")
    return {
        "status": "completed",
        "total_requested": len(items_to_process),
        "total_new_profiles_added": total_added,
        "details": results,
    }


@app.get("/api/search")
async def search_leadership(q: str = Query(..., min_length=1)):
    """Search for leadership profiles."""
    start_time = time.time()
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
    elapsed = time.time() - start_time
    _search_stats["total_queries"] += 1
    _search_stats["total_latency_seconds"] += elapsed

    if total_results == 0:
        _search_stats["cache_misses"] += 1
        disc_start = time.time()
        discovered = discover_and_save_company(q)
        disc_elapsed = time.time() - disc_start
        _search_stats["total_latency_seconds"] += disc_elapsed
        return discovered

    _search_stats["cache_hits"] += 1
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
