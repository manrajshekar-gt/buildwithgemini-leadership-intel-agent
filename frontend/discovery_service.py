"""Automated Discovery and Research Pipeline for New Companies.

When a search misses in Firestore:
1. Gathers intelligence from the company website and Wikipedia/search fallbacks.
2. Extracts key Executives and Board of Directors using Gemini.
3. Generates a custom company logo and uploads to Cloud Storage.
4. Persists the new profiles and logo into Firestore.
"""

import json
import os
import re
import urllib.parse
from typing import Any, Dict, List, Optional
from google import genai
from google.cloud import firestore, storage
import httpx
from bs4 import BeautifulSoup

PROJECT_ID = "qwiklabs-gcp-04-a0fc456f3f90"
COLLECTION_NAME = "leadership_profiles"
BUCKET_NAME = "leadership-intel-assets-9698"

# Set vertexai configuration in environment
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"

_genai_client = None
_db = None
_storage = None


def get_genai():
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client()
    return _genai_client


def get_db():
    global _db
    if _db is None:
        _db = firestore.Client(project=PROJECT_ID)
    return _db


def get_storage():
    global _storage
    if _storage is None:
        _storage = storage.Client(project=PROJECT_ID)
    return _storage


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text).strip("-")


def discover_and_save_company(query: str) -> Dict[str, Any]:
    """Orchestrates automated discovery, logo generation, and DB storage for an unindexed company."""
    # Determine probable URL or company name
    is_url = "http://" in query or "https://" in query or ".com" in query or ".io" in query or ".ai" in query or ".org" in query
    company_name = query
    website_url = query if is_url else f"https://www.{_slugify(query)}.com"
    if not website_url.startswith("http"):
        website_url = "https://" + website_url

    # 1. Fetch text from the target site if reachable
    scraped_text = ""
    discovered_emails = []
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        with httpx.Client(timeout=8.0, follow_redirects=True, headers=headers) as client:
            resp = client.get(website_url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                if soup.title and soup.title.string:
                    t = soup.title.string.strip()
                    if "|" in t:
                        company_name = t.split("|")[0].strip()
                    elif "-" in t:
                        company_name = t.split("-")[0].strip()
                    else:
                        company_name = t[:40].strip()
                for tag in soup(["script", "style", "svg", "noscript"]):
                    tag.decompose()
                scraped_text = soup.get_text(separator="\n", strip=True)[:4000]
                discovered_emails = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b", scraped_text)
    except Exception:
        pass

    # 2. Query Wikipedia for company background
    wiki_context = ""
    try:
        search_term = urllib.parse.quote(company_name)
        api_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={search_term}&format=json"
        req = urllib.request.Request(api_url, headers={"User-Agent": "LeadershipIntelAgent/1.0"})
        with urllib.request.urlopen(req, timeout=6) as response:
            wdata = json.loads(response.read().decode())
            items = wdata.get("query", {}).get("search", [])
            if items:
                wiki_title = items[0]["title"]
                ext_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1&titles={urllib.parse.quote(wiki_title)}&format=json"
                ext_req = urllib.request.Request(ext_url, headers={"User-Agent": "LeadershipIntelAgent/1.0"})
                with urllib.request.urlopen(ext_req, timeout=6) as ext_resp:
                    ext_data = json.loads(ext_resp.read().decode())
                    for pid, pdata in ext_data.get("query", {}).get("pages", {}).items():
                        wiki_context = pdata.get("extract", "")[:3000]
    except Exception:
        pass

    # 3. Use Gemini to extract leadership and board members
    ai_client = get_genai()
    prompt = f"""
You are an executive research agent. Research or extract the current management team (C-Suite/Executives) and Board of Directors for:
Company: '{company_name}'
Website: '{website_url}'

Context from website:
{scraped_text[:2000]}

Context from Wikipedia/Public records:
{wiki_context[:2000]}

Discovered emails on site: {list(set(discovered_emails))[:6]}

Return a JSON array of 4 to 8 members representing both 'Executive Management' and 'Board of Directors'.
Each object in the array MUST contain:
- name: string (Full Name)
- title: string (Role or Office, e.g. 'Chief Executive Officer', 'Independent Director')
- group: string (either 'Executive Management' or 'Board of Directors')
- email: string (guessed or public corporate email, e.g. first@domain or name@company.com, or N/A)
- committee: string or null (e.g. 'Audit Committee', 'Nominating & Governance')
- is_independent: boolean (true for independent board members)
- tenure_years: integer or null
- bio: string (1-2 sentence background summary)

Respond with ONLY the JSON array inside a ```json ``` block.
"""

    resp = ai_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    raw_text = resp.text or ""
    # Extract JSON array
    json_match = re.search(r"\[\s*\{.*\}\s*\]", raw_text, re.DOTALL)
    members_data = []
    if json_match:
        try:
            members_data = json.loads(json_match.group(0))
        except Exception:
            pass

    # 4. Generate custom company logo and upload to Cloud Storage
    logo_url = ""
    try:
        logo_client = genai.Client(vertexai=True, project=PROJECT_ID, location="us-central1")
        logo_prompt = (
            f"A vibrant, playful, and fun modern company logo for '{company_name}'. "
            f"Clever and cheerful startup branding, charismatic mascot or iconic colorful emblem, "
            f"bold friendly typography silhouette, vivid complementary colors, creative and energetic, "
            f"delightful vector aesthetic, perfectly centered on a crisp clean white background."
        )
        logo_resp = logo_client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=logo_prompt,
        )
        image_bytes = None
        for part in logo_resp.candidates[0].content.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
                break

        if image_bytes:
            filename = f"logos/{_slugify(company_name)}-logo.png"
            storage_client = get_storage()
            bucket = storage_client.bucket(BUCKET_NAME)
            blob = bucket.blob(filename)
            blob.upload_from_string(image_bytes, content_type="image/png")
            logo_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
    except Exception as e:
        print(f"Logo generation error for {company_name}: {e}")

    # 5. Persist profiles into Firestore
    db = get_db()
    executives = []
    board_of_directors = []

    for m in members_data:
        doc_id = f"{_slugify(company_name)}-{_slugify(m.get('name', 'member'))}"
        record = {
            "id": doc_id,
            "company_name": company_name,
            "company_url": website_url,
            "name": m.get("name", "Unknown"),
            "title": m.get("title", "Leadership"),
            "group": m.get("group", "Executive Management"),
            "email": m.get("email") or "N/A",
            "logo_url": logo_url,
            "committee": m.get("committee"),
            "is_independent": bool(m.get("is_independent", False)),
            "tenure_years": m.get("tenure_years"),
            "bio": m.get("bio", ""),
            "source_url": website_url,
        }
        db.collection(COLLECTION_NAME).document(doc_id).set(record)

        if "board" in record["group"].lower():
            board_of_directors.append(record)
        else:
            executives.append(record)

    return {
        "query": query,
        "company_name": company_name,
        "company_logo": logo_url,
        "company_url": website_url,
        "total_results": len(executives) + len(board_of_directors),
        "executives": executives,
        "board_of_directors": board_of_directors,
        "auto_discovered": True,
    }
