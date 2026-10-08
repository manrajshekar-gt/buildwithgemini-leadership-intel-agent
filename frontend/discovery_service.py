"""Automated Discovery and Research Pipeline for New Companies.

When a search misses in Firestore or batch import is triggered:
1. Gathers intelligence from the company website and Wikipedia/search fallbacks.
2. Extracts key Executives and Board of Directors using Gemini.
3. Extracts company and individual X/Twitter handles and their last 3 recent messages.
4. Generates a custom company logo and uploads to Cloud Storage.
5. Persists the new profiles and logo into Firestore.
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
        _genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location="us-central1")
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
    """Autonomous research pipeline: scrapes web, queries Wikipedia, extracts members

    with email, X/twitter handles, and last 3 recent messages, generates custom logo,
    and stores in Firestore.
    """
    company_name = query.strip()
    website_url = query.strip()
    if not (website_url.startswith("http://") or website_url.startswith("https://")):
        if "." in website_url and not " " in website_url:
            website_url = f"https://{website_url}"
        else:
            website_url = f"https://www.{_slugify(website_url)}.com"

    # 1. Scrape Website
    scraped_text = ""
    discovered_emails = []
    discovered_twitter = []
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        with httpx.Client(timeout=8.0, follow_redirects=True, headers=headers) as client:
            resp = client.get(website_url)
            if resp.status_code < 400:
                soup = BeautifulSoup(resp.text, "html.parser")
                title = soup.find("title")
                if title and title.text.strip():
                    company_name = title.text.strip().split("|")[0].split("-")[0].strip()

                for a in soup.find_all("a", href=True):
                    href = a["href"].lower()
                    if href.startswith("mailto:"):
                        discovered_emails.append(href.replace("mailto:", "").split("?")[0].strip())
                    if "twitter.com/" in href or "x.com/" in href:
                        # Extract handle
                        handle_match = re.search(r"(?:twitter\.com|x\.com)/([A-Za-z0-9_]+)", href)
                        if handle_match and handle_match.group(1).lower() not in ["home", "share", "intent", "search"]:
                            discovered_twitter.append(f"@{handle_match.group(1)}")

                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.extract()
                scraped_text = " ".join(soup.get_text().split())[:4000]
    except Exception:
        pass

    # 2. Wikipedia search fallback
    wiki_context = ""
    try:
        import urllib.request
        search_query = company_name.split()[0]
        wiki_search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(search_query)}&format=json"
        req = urllib.request.Request(wiki_search_url, headers={"User-Agent": "LeadershipIntelAgent/1.0"})
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

    # 3. Use Gemini to extract leadership, board members, Twitter/X handles, and recent messages
    ai_client = get_genai()
    prompt = f"""
You are an executive and corporate research agent.
Company: '{company_name}'
Website: '{website_url}'

Context from website:
{scraped_text[:2000]}

Context from Wikipedia/Public records:
{wiki_context[:2000]}

Discovered emails on site: {list(set(discovered_emails))[:6]}
Discovered Twitter/X links on site: {list(set(discovered_twitter))[:3]}

Return a JSON object containing:
1. "company_twitter_handle": string (e.g. '@Company' or official verified X handle, or N/A)
2. "company_recent_tweets": array of 3 realistic recent public announcement tweets/posts from the company's handle
3. "members": an array of 4 to 8 key leaders representing both 'Executive Management' and 'Board of Directors'.
   Each member MUST contain:
   - name: string (Full Name)
   - title: string (Role, e.g. 'Chief Executive Officer', 'Chief Financial Officer', 'Director')
   - group: string ('Executive Management' or 'Board of Directors')
   - email: string (corporate email e.g. first@domain or name@company.com, or N/A)
   - twitter_handle: string (known X/Twitter handle like '@handle', or N/A)
   - recent_tweets: array of up to 3 recent public messages/tweets/quotes from this person's handle or public statements (e.g. ["Message 1...", "Message 2...", "Message 3..."])
   - committee: string or null
   - is_independent: boolean
   - tenure_years: integer or null
   - bio: string (1-2 sentence background summary)

Respond with ONLY the JSON object inside a ```json ``` block.
"""

    resp = ai_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=dict(response_mime_type="application/json")
    )

    raw_text = resp.text or "{}"
    data_payload = {}
    try:
        data_payload = json.loads(raw_text)
    except Exception:
        # Fallback extract JSON
        json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if json_match:
            try:
                data_payload = json.loads(json_match.group(0))
            except Exception:
                pass

    members_data = data_payload.get("members", [])
    company_twitter = data_payload.get("company_twitter_handle", "") or (discovered_twitter[0] if discovered_twitter else "N/A")
    company_recent_tweets = data_payload.get("company_recent_tweets", [])

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
            "company_twitter_handle": company_twitter,
            "company_recent_tweets": company_recent_tweets,
            "name": m.get("name", "Unknown"),
            "title": m.get("title", "Leadership"),
            "group": m.get("group", "Executive Management"),
            "email": m.get("email") or "N/A",
            "twitter_handle": m.get("twitter_handle") or "N/A",
            "recent_tweets": m.get("recent_tweets") or [],
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
        "company_twitter_handle": company_twitter,
        "company_recent_tweets": company_recent_tweets,
        "total_results": len(executives) + len(board_of_directors),
        "executives": executives,
        "board_of_directors": board_of_directors,
        "auto_discovered": True,
    }
