# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import csv
import io
import json
import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup
from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google import genai
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.cloud import firestore, storage
from google.genai import types
import httpx

from .a2ui_utils import a2ui_callback

MODEL = "gemini-3.8-flash"
IMAGE_MODEL = "gemini-2.5-flash-image"
PROJECT_ID = "qwiklabs-gcp-04-a0fc456f3f90"
COLLECTION_NAME = "leadership_profiles"
BUCKET_NAME = "leadership-intel-assets-9698"

_firestore_client: Optional[firestore.Client] = None
_storage_client: Optional[storage.Client] = None
_genai_client: Optional[genai.Client] = None


def get_firestore_client() -> firestore.Client:
    """Returns a singleton Firestore client with hardcoded project ID."""
    global _firestore_client
    if _firestore_client is None:
        _firestore_client = firestore.Client(project=PROJECT_ID)
    return _firestore_client


def get_storage_client() -> storage.Client:
    """Returns a singleton Cloud Storage client with hardcoded project ID."""
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client(project=PROJECT_ID)
    return _storage_client


def get_genai_client() -> genai.Client:
    """Returns a singleton GenAI client configured with Vertex AI and hardcoded project ID."""
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location="us-central1")
    return _genai_client


def _slugify(text: str) -> str:
    """Generate a clean slug for document IDs and filenames."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text).strip("-")


def generate_company_logo(
    company_name: str,
    business_description: Optional[str] = None,
    style_preference: Optional[str] = None,
) -> Dict[str, Any]:
    """Generates a professional custom company logo based on the business type and uploads it to Cloud Storage.

    Args:
        company_name: The name of the company or customer business (e.g. 'CloudScale Technologies', 'Solaris Health').
        business_description: A description of what the business does, industry, products, or core value proposition.
        style_preference: Optional style cue (e.g. 'minimalist modern', 'geometric tech', 'elegant luxury', 'playful organic').

    Returns:
        A dictionary containing the logo generation status, company name, Cloud Storage public image URL, and description.
    """
    desc = business_description or f"A fun, innovative modern business called {company_name}"
    style = style_preference or "playful, fun, and vibrant modern logo, charismatic mascot or creative emblem, vivid colors, friendly aesthetic, clean white background"

    prompt = (
        f"A vibrant, playful, and fun company logo for '{company_name}'. Business domain: {desc}. "
        f"Design style: {style}. Creative and clever mascot or emblem, vivid joyful colors, vector art, isolated on a solid white background."
    )

    try:
        client = get_genai_client()
        response = client.models.generate_content(
            model=IMAGE_MODEL,
            contents=prompt,
        )

        image_bytes = None
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
                break

        if not image_bytes:
            return {
                "status": "error",
                "message": "Image model did not return image data in the response.",
                "logo_url": None,
            }

        # Upload generated logo to public GCS bucket
        filename = f"logos/{_slugify(company_name)}-logo.png"
        storage_client = get_storage_client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type="image/png")

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

        return {
            "status": "success",
            "company_name": company_name,
            "logo_url": public_url,
            "business_description": desc,
            "message": f"Successfully generated and published new logo for {company_name} at {public_url}",
        }
    except Exception as e:
        return {
            "status": "error",
            "company_name": company_name,
            "message": f"Failed to generate logo for {company_name}: {e}",
            "logo_url": None,
        }


def get_leadership_profiles(
    company_name: Optional[str] = None,
    group: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve leadership and board profiles from the Firestore database.

    Args:
        company_name: Optional company name to filter profiles (e.g. 'Alphabet' or 'Microsoft').
        group: Optional leadership group to filter by, e.g. 'Executive Management' or 'Board of Directors'.

    Returns:
        A list of leadership profile records matching the query, including email and logo URL.
    """
    db = get_firestore_client()
    coll_ref = db.collection(COLLECTION_NAME)

    docs = coll_ref.stream()
    results = []

    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id

        if company_name:
            rec_company = data.get("company_name", "").lower()
            rec_url = data.get("company_url", "").lower()
            q = company_name.lower()
            if q not in rec_company and q not in rec_url:
                continue

        if group:
            rec_group = data.get("group", "").lower()
            if group.lower() not in rec_group:
                continue

        results.append(data)

    return results


def save_leadership_profile(
    name: str,
    company_name: str,
    title: str,
    group: str,
    email: Optional[str] = None,
    logo_url: Optional[str] = None,
    company_url: Optional[str] = None,
    bio: Optional[str] = None,
    committee: Optional[str] = None,
    is_independent: bool = False,
    tenure_years: Optional[int] = None,
    source_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Save or update an executive or board member profile in Firestore.

    Args:
        name: Full name of the executive or board director.
        company_name: Name of the company/corporation.
        title: Title/role (e.g., 'Chief Executive Officer', 'Lead Independent Director').
        group: Either 'Executive Management' or 'Board of Directors'.
        email: Contact or professional email address (e.g. 'name@company.com').
        logo_url: Public URL to the company's generated or official logo image.
        company_url: Official website URL for the company.
        bio: Brief professional background or summary.
        committee: Board committee membership (e.g., 'Audit Committee', 'Compensation Committee').
        is_independent: Whether the board member is an independent outside director.
        tenure_years: Number of years served with the company or board.
        source_url: Source page URL where this profile was retrieved.

    Returns:
        A dictionary confirming the saved profile and its Firestore document ID.
    """
    db = get_firestore_client()
    doc_id = f"{_slugify(company_name)}-{_slugify(name)}"
    doc_ref = db.collection(COLLECTION_NAME).document(doc_id)

    profile_data = {
        "id": doc_id,
        "name": name,
        "company_name": company_name,
        "title": title,
        "group": group,
        "email": email or "",
        "logo_url": logo_url or "",
        "company_url": company_url or "",
        "bio": bio or "",
        "committee": committee,
        "is_independent": is_independent,
        "tenure_years": tenure_years,
        "source_url": source_url or "",
    }

    doc_ref.set(profile_data)
    return {
        "status": "success",
        "message": f"Saved profile for {name} ({group}) with email '{email or 'N/A'}' and logo '{logo_url or 'N/A'}' at {company_name}",
        "profile": profile_data,
    }


def fetch_leadership_page_text(url: str) -> Dict[str, Any]:
    """Fetches the webpage text at the given URL, discovering emails and leadership links.

    Strips scripts, navigation noise, and styles, returning clean page text alongside
    any discovered email addresses (mailto: links or text patterns) and candidate subpages.

    Args:
        url: The website URL to inspect (e.g. 'https://openai.com' or 'https://stripe.com/about').

    Returns:
        A dictionary containing the parsed main text, page title, detected emails, and candidate leadership sublinks.
    """
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }

    try:
        with httpx.Client(timeout=12.0, follow_redirects=True, headers=headers) as client:
            resp = client.get(url)
            resp.raise_for_status()
            html = resp.text
            final_url = str(resp.url)
    except Exception as e:
        return {
            "status": "error",
            "url": url,
            "message": f"Failed to fetch {url}: {e}",
            "text": "",
            "discovered_emails": [],
            "candidate_sublinks": [],
        }

    soup = BeautifulSoup(html, "html.parser")

    discovered_emails = set()
    for mailto in soup.find_all("a", href=re.compile(r"^mailto:", re.IGNORECASE)):
        raw_email = mailto["href"].replace("mailto:", "").split("?")[0].strip()
        if "@" in raw_email:
            discovered_emails.add(raw_email)

    for tag in soup(["script", "style", "svg", "noscript", "iframe"]):
        tag.decompose()

    page_title = soup.title.string.strip() if soup.title and soup.title.string else ""

    candidate_sublinks = []
    leadership_keywords = ["leader", "team", "board", "about", "governance", "executive", "officer", "investor", "contact"]

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        link_text = a.get_text(strip=True).lower()
        full_url = urllib.parse.urljoin(final_url, href)

        if any(kw in link_text or kw in href.lower() for kw in leadership_keywords):
            if full_url.startswith("http") and full_url not in candidate_sublinks and full_url != final_url:
                candidate_sublinks.append(full_url)
                if len(candidate_sublinks) >= 8:
                    break

    text_content = soup.get_text(separator="\n", strip=True)

    body_emails = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b", text_content)
    for be in body_emails:
        if not re.search(r"\.(png|jpg|jpeg|webp|svg|gif|css|js)$", be, re.I):
            discovered_emails.add(be)

    truncated_text = text_content[:8000]

    return {
        "status": "success",
        "url": final_url,
        "page_title": page_title,
        "text": truncated_text,
        "discovered_emails": sorted(list(discovered_emails)),
        "candidate_sublinks": candidate_sublinks,
    }


def search_company_governance(company_name: str, query_type: str = "all") -> Dict[str, Any]:
    """Searches corporate governance, executive team, board info, and emails using Wikipedia and web fallbacks.

    Useful when the primary company website has minimal leadership detail or uses dynamic JavaScript widgets.

    Args:
        company_name: The name of the company (e.g. 'Databricks', 'Stripe', 'CrowdStrike').
        query_type: Focus area: 'executives', 'board', 'email', or 'all'.

    Returns:
        Structured search snippets, Wikipedia summaries, leadership sections, and contact emails.
    """
    search_queries = []
    if query_type in ("executives", "all"):
        search_queries.append(f"{company_name} executive leadership management team")
    if query_type in ("board", "all"):
        search_queries.append(f"{company_name} board of directors governance")
    if query_type in ("email", "all"):
        search_queries.append(f"{company_name} corporate leadership contact email press investor relations")

    wiki_results = []
    discovered_emails = set()

    try:
        search_term = urllib.parse.quote(company_name)
        api_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={search_term}&format=json"
        req = urllib.request.Request(api_url, headers={"User-Agent": "LeadershipIntelAgent/1.0"})
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode())
            search_items = data.get("query", {}).get("search", [])

            if search_items:
                page_title = search_items[0]["title"]
                extract_url = (
                    f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1&titles={urllib.parse.quote(page_title)}&format=json"
                )
                ext_req = urllib.request.Request(extract_url, headers={"User-Agent": "LeadershipIntelAgent/1.0"})
                with urllib.request.urlopen(ext_req, timeout=8) as ext_resp:
                    ext_data = json.loads(ext_resp.read().decode())
                    pages = ext_data.get("query", {}).get("pages", {})
                    for pid, pdata in pages.items():
                        extract_text = pdata.get("extract", "")
                        wiki_results.append({
                            "title": pdata.get("title"),
                            "summary": extract_text[:2500],
                            "url": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(pdata.get('title', ''))}",
                        })
                        for em in re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b", extract_text):
                            discovered_emails.add(em)
    except Exception as e:
        wiki_results.append({"error": f"Wikipedia lookup error: {e}"})

    ddg_info = {}
    try:
        ddg_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(company_name)}&format=json&no_html=1&skip_disambig=1"
        with httpx.Client(timeout=6.0) as client:
            res = client.get(ddg_url)
            if res.status_code == 200:
                ddg_data = res.json()
                abstract_text = ddg_data.get("AbstractText", "")
                ddg_info = {
                    "heading": ddg_data.get("Heading", ""),
                    "abstract": abstract_text,
                    "source": ddg_data.get("AbstractSource", ""),
                    "url": ddg_data.get("AbstractURL", ""),
                }
                for em in re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b", abstract_text):
                    discovered_emails.add(em)
    except Exception:
        pass

    return {
        "status": "success",
        "company_name": company_name,
        "wikipedia_articles": wiki_results,
        "quick_facts": ddg_info,
        "discovered_emails": sorted(list(discovered_emails)),
        "suggested_queries": search_queries,
    }


def export_governance_report_csv(company_name: str) -> Dict[str, Any]:
    """Generates a CSV report of the management team and board of directors (including emails and logo URLs) and uploads it to Cloud Storage.

    Args:
        company_name: The company name to generate the CSV report for.

    Returns:
        A dictionary containing the report summary, total count, and public download URL.
    """
    profiles = get_leadership_profiles(company_name=company_name)
    if not profiles:
        return {
            "status": "warning",
            "message": f"No stored profiles found for '{company_name}'. Try saving profiles first or fetching the company website.",
            "csv_url": None,
        }

    output = io.StringIO()
    fieldnames = [
        "Company",
        "Name",
        "Title",
        "Group",
        "Email",
        "Logo URL",
        "Committee",
        "Independent Director",
        "Tenure (Years)",
        "Source URL",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for p in sorted(profiles, key=lambda x: (x.get("group", ""), x.get("name", ""))):
        writer.writerow({
            "Company": p.get("company_name", company_name),
            "Name": p.get("name", ""),
            "Title": p.get("title", ""),
            "Group": p.get("group", ""),
            "Email": p.get("email") or "N/A",
            "Logo URL": p.get("logo_url") or "N/A",
            "Committee": p.get("committee") or "N/A",
            "Independent Director": "Yes" if p.get("is_independent") else "No",
            "Tenure (Years)": p.get("tenure_years") if p.get("tenure_years") is not None else "N/A",
            "Source URL": p.get("source_url") or p.get("company_url") or "",
        })

    csv_data = output.getvalue().encode("utf-8")

    filename = f"reports/{_slugify(company_name)}-leadership-report.csv"
    storage_client = get_storage_client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(csv_data, content_type="text/csv")

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

    return {
        "status": "success",
        "company_name": company_name,
        "profiles_exported": len(profiles),
        "filename": filename,
        "csv_url": public_url,
        "message": f"Successfully exported {len(profiles)} leadership profiles (with email addresses & logo URLs) for {company_name} to {public_url}",
    }


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are the Executive & Board Leadership Intelligence Agent. "
        "Your role is to help users research, organize, and inspect company management teams and boards of directors. "
        "For each company or customer, you can generate a custom brand logo using `generate_company_logo` based on what the business does. "
        "For each member, always discover and capture their email address and associate the company's logo URL. "
        "When given a website URL, use `fetch_leadership_page_text` to read the site and find leadership pages and contact emails. "
        "If you need additional or fallback information, use `search_company_governance`. "
        "Store discovered executive and director records (including email and logo_url) using `save_leadership_profile`. "
        "Retrieve stored profiles using `get_leadership_profiles`. "
        "To provide a downloadable spreadsheet, use `export_governance_report_csv` to upload a CSV with emails and logo URLs to Cloud Storage. "
        "Always categorize leaders into their respective groups: 'Executive Management' or 'Board of Directors'."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        generate_company_logo,
        fetch_leadership_page_text,
        search_company_governance,
        export_governance_report_csv,
        get_leadership_profiles,
        save_leadership_profile,
    ],
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
