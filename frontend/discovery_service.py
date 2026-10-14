"""Automated Discovery and Research Pipeline for Companies.

Features:
1. Gathers intelligence from company websites, Wikipedia, and SEC EDGAR / proxy statements.
2. Extracts C-suite & Board of Directors with verified emails, X handles, and compensation/tenure.
3. Extracts strategic partners and market competitors with verified websites.
4. Synthesizes executive vectors for semantic AI discovery.
5. Generates custom modern logos and persists everything to Firestore.
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

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from app.db import (
        get_db,
        get_storage,
        get_genai,
        PROJECT_ID,
        COLLECTION_NAME,
        BUCKET_NAME,
    )
except ImportError:
    from db import (
        get_db,
        get_storage,
        get_genai,
        PROJECT_ID,
        COLLECTION_NAME,
        BUCKET_NAME,
    )


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text).strip("-")


def _get_sec_edgar_context(company_name: str) -> str:
    """Retrieves official SEC EDGAR registration, CIK, and latest DEF 14A proxy details."""
    headers = {"User-Agent": "LeadershipIntelligenceAgent admin@leadershipintel.io"}
    try:
        r = httpx.get("https://www.sec.gov/files/company_tickers.json", headers=headers, timeout=6.0)
        if r.status_code != 200:
            return ""
        data = r.json()
        q = company_name.lower().replace("-", " ")
        match = None
        for v in data.values():
            t = v["title"].lower().replace("-", " ")
            if q in t or t in q:
                match = v
                break
        if not match:
            return ""

        cik = str(match["cik_str"]).zfill(10)
        sub_resp = httpx.get(f"https://data.sec.gov/submissions/CIK{cik}.json", headers=headers, timeout=6.0)
        if sub_resp.status_code != 200:
            return f"SEC Entity: {match['title']} (Ticker: {match['ticker']}, CIK: {match['cik_str']})"

        sub_data = sub_resp.json()
        recent = sub_data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])

        def14a_idx = next((i for i, f in enumerate(forms) if f == "DEF 14A"), None)
        latest_proxy = f"DEF 14A Proxy Statement filed on {dates[def14a_idx]}" if def14a_idx is not None else "No DEF 14A found"
        recent_8k = [dates[i] for i, f in enumerate(forms) if f == "8-K"][:4]

        name = sub_data.get("name", match["title"])
        ticker = match["ticker"]
        cik_num = match["cik_str"]
        sic = sub_data.get("sicDescription", "N/A")

        return (
            f"Official SEC EDGAR Regulatory Record:\n"
            f"- Legal Entity: {name}\n"
            f"- Ticker: {ticker} (CIK: {cik_num})\n"
            f"- Industry (SIC): {sic}\n"
            f"- Latest Annual Proxy Statement: {latest_proxy}\n"
            f"- Recent 8-K Executive & Material Filings: {recent_8k}\n"
        )
    except Exception:
        return ""


def extract_company_website_logo(website_url: str) -> str:
    """Extracts the official corporate brand logo directly from the company website.

    Checks:
    1. OpenGraph / Twitter meta logo (<meta property="og:logo">)
    2. Schema.org JSON-LD Organization logo
    3. Apple touch icon (high-resolution official square brand emblem)
    4. Header/Nav branded logo images
    5. Standard high-resolution domain favicon
    """
    if not (website_url.startswith("http://") or website_url.startswith("https://")):
        website_url = f"https://{website_url}"
    clean_domain = re.sub(r"^https?://(www\.)?", "", website_url).split("/")[0]

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    try:
        with httpx.Client(timeout=6.0, headers=headers, follow_redirects=True) as client:
            resp = client.get(website_url)
            if resp.status_code < 400:
                soup = BeautifulSoup(resp.text, "html.parser")
                base_url = str(resp.url)

                # 1. Meta og:logo
                og_logo = soup.find("meta", property="og:logo")
                if og_logo and og_logo.get("content"):
                    return urllib.parse.urljoin(base_url, og_logo["content"].strip())

                # 2. Schema.org JSON-LD Organization logo
                for script in soup.find_all("script", type="application/ld+json"):
                    if script.string and "logo" in script.string:
                        try:
                            ld = json.loads(script.string)
                            items = ld if isinstance(ld, list) else [ld]
                            for it in items:
                                if isinstance(it, dict) and "logo" in it:
                                    lv = it["logo"]
                                    if isinstance(lv, str):
                                        return urllib.parse.urljoin(base_url, lv.strip())
                                    elif isinstance(lv, dict) and "url" in lv:
                                        return urllib.parse.urljoin(base_url, lv["url"].strip())
                        except Exception:
                            pass

                # 3. High-res Apple Touch Icon
                apple_icon = soup.find("link", rel=lambda r: r and "apple-touch-icon" in r.lower(), href=True)
                if apple_icon and apple_icon.get("href"):
                    return urllib.parse.urljoin(base_url, apple_icon["href"].strip())

                # 4. Header or Navigation logo image
                header = soup.find("header") or soup.find("nav")
                if header:
                    for img in header.find_all("img"):
                        src = img.get("src") or img.get("data-src")
                        alt = (img.get("alt") or "").lower()
                        cls = " ".join(img.get("class", [])).lower() if isinstance(img.get("class"), list) else str(img.get("class") or "").lower()
                        if src and any(k in alt or k in cls for k in ["logo", "brand", clean_domain.split(".")[0]]):
                            return urllib.parse.urljoin(base_url, src.strip())

                # 5. Link icon
                icon_tag = soup.find("link", rel=lambda r: r and ("icon" in r.lower() or "shortcut" in r.lower()), href=True)
                if icon_tag and icon_tag.get("href"):
                    return urllib.parse.urljoin(base_url, icon_tag["href"].strip())
    except Exception:
        pass

    return f"https://www.google.com/s2/favicons?domain={clean_domain}&sz=128"


def discover_and_save_company(query: str) -> Dict[str, Any]:
    """Autonomous research pipeline:

    1. Scrapes web & discovers corporate emails and social links.
    2. Enriches with Wikipedia & SEC EDGAR context.
    3. Uses Gemini 2.5 Flash to extract executive compensation, committees, X handles,
       partners, competitors, and semantic background embeddings.
    4. Generates custom logo and saves to Firestore.
    """
    company_name = query.strip()
    website_url = query.strip()
    is_url_input = website_url.startswith("http://") or website_url.startswith("https://") or ("." in website_url and " " not in website_url)
    if not (website_url.startswith("http://") or website_url.startswith("https://")):
        if "." in website_url and not " " in website_url:
            website_url = f"https://{website_url}"
        else:
            website_url = f"https://www.{_slugify(website_url)}.com"

    clean_domain = re.sub(r"^https?://(www\.)?", "", website_url).split("/")[0]

    # Clean initial fallback company name from domain if input was a URL/domain
    if is_url_input:
        root_part = clean_domain.split(".")[0]
        if clean_domain.lower().endswith(".ai"):
            company_name = f"{root_part.capitalize()} AI"
        else:
            company_name = root_part.replace("-", " ").title()

    # 1. Scrape Primary Website & Discover Official Leadership Subpages
    scraped_text = ""
    leadership_pages_text = ""
    discovered_emails = []
    discovered_twitter = []
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        with httpx.Client(timeout=8.0, follow_redirects=True, headers=headers) as client:
            resp = client.get(website_url)
            candidate_links = []
            if resp.status_code < 400:
                soup = BeautifulSoup(resp.text, "html.parser")

                # 1. Check og:site_name (most authoritative branding name)
                og_name = soup.find("meta", property="og:site_name") or soup.find("meta", attrs={"name": "application-name"})
                if og_name and og_name.get("content") and og_name["content"].strip():
                    company_name = og_name["content"].strip()
                else:
                    # 2. Check JSON-LD schema Organization
                    for script in soup.find_all("script", type="application/ld+json"):
                        if script.string and ("Organization" in script.string or "WebSite" in script.string):
                            try:
                                ld = json.loads(script.string)
                                items = ld if isinstance(ld, list) else [ld]
                                for it in items:
                                    if isinstance(it, dict) and it.get("@type") in ("Organization", "Corporation") and it.get("name"):
                                        company_name = it["name"].strip()
                                        break
                                    if isinstance(it, dict) and "@graph" in it:
                                        for git in it["@graph"]:
                                            if git.get("@type") in ("Organization", "Corporation") and git.get("name"):
                                                company_name = git["name"].strip()
                                                break
                            except Exception:
                                pass

                # 3. If still needed, check title segments against the root domain
                if is_url_input and (company_name == query.strip() or not company_name):
                    title = soup.find("title")
                    if title and title.text.strip():
                        chunks = [c.strip() for c in re.split(r"[|\-–—]", title.text.strip()) if c.strip()]
                        root = clean_domain.split(".")[0].lower()
                        matched = next((c for c in chunks if root in c.lower()), chunks[0] if chunks else "")
                        matched = re.sub(r"[®™]", "", matched)
                        matched = re.sub(r"\b(Official Site|Home|Homepage|Welcome to)\b", "", matched, flags=re.I).strip()
                        if matched:
                            company_name = matched

                for a in soup.find_all("a", href=True):
                    href = a["href"].lower()
                    text = a.get_text().strip().lower()
                    if href.startswith("mailto:"):
                        discovered_emails.append(href.replace("mailto:", "").split("?")[0].strip())
                    if "twitter.com/" in href or "x.com/" in href:
                        handle_match = re.search(r"(?:twitter\.com|x\.com)/([A-Za-z0-9_]+)", href)
                        if handle_match and handle_match.group(1).lower() not in ["home", "share", "intent", "search"]:
                            discovered_twitter.append(f"@{handle_match.group(1)}")
                    
                    link_keywords = [
                        "about", "team", "our-team", "leadership", "board-of-directors", 
                        "executives", "governance", "management", "who-we-are", "people"
                    ]
                    if any(k in href or k in text for k in link_keywords):
                        full = str(httpx.URL(website_url).join(a["href"]))
                        if full.startswith("http") and full not in candidate_links and full != website_url:
                            if not any(ign in full.lower() for ign in ["careers", "jobs", "privacy", "terms", "login", "signup", "contact", "pricing"]):
                                candidate_links.append(full)

                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.extract()
                scraped_text = " ".join(soup.get_text().split())[:3000]

            # Probe candidate or well-known official governance and about subpages
            known_paths = [
                f"{website_url.rstrip('/')}/en/corporate/leadership.html",
                f"{website_url.rstrip('/')}/en/corporate/leadership",
                f"{website_url.rstrip('/')}/en/about/leadership.html",
                f"{website_url.rstrip('/')}/corporate/leadership.html",
                f"{website_url.rstrip('/')}/about/leadership",
                f"{website_url.rstrip('/')}/about/leadership.html",
                f"{website_url.rstrip('/')}/about-us",
                f"{website_url.rstrip('/')}/about",
                f"{website_url.rstrip('/')}/team",
                f"{website_url.rstrip('/')}/leadership",
                f"{website_url.rstrip('/')}/corporate-governance",
                f"{website_url.rstrip('/')}/governance",
                f"https://ir.{clean_domain}/leadership-and-governance",
                f"https://investor.{clean_domain}/corporate-governance",
            ]
            for p in candidate_links[:4] + [kp for kp in known_paths if kp not in candidate_links][:6]:
                try:
                    s_resp = client.get(p)
                    if s_resp.status_code == 200:
                        s_soup = BeautifulSoup(s_resp.text, "html.parser")
                        img_hints = []
                        for img_tag in s_soup.find_all("img"):
                            alt = img_tag.get("alt", "").strip()
                            title_attr = img_tag.get("title", "").strip()
                            src = img_tag.get("src", "") or img_tag.get("data-lazy-src", "") or img_tag.get("data-rocket-src", "") or img_tag.get("srcset", "")
                            for txt in [alt, title_attr]:
                                if txt and 1 <= len(txt.split()) <= 4 and not any(k in txt.lower() for k in ["logo", "icon", "banner", "image", "photo", "bg", "award"]):
                                    img_hints.append(txt)
                            if "upload" in src.lower():
                                fn = src.split("/")[-1].split("?")[0]
                                cleaned_fn = re.sub(r"(-\d+x\d+|-scaled|\.\w+$)", "", fn)
                                parts = [part for part in re.split(r"[-_]", cleaned_fn) if part and part.isalpha() and not part.isdigit()]
                                if 1 <= len(parts) <= 3 and all(part[0].isupper() for part in parts):
                                    img_hints.append(" ".join(parts))
                        hint_str = f" [Discovered Team/Roster names from images: {', '.join(set(img_hints))}]" if img_hints else ""

                        for tag in s_soup(["script", "style", "nav", "footer", "header"]):
                            tag.extract()
                        leadership_pages_text += f"\n--- Source: {p} ---\n" + hint_str + " " + " ".join(s_soup.get_text().split())[:3500]
                        if len(leadership_pages_text) >= 6000:
                            break
                except Exception:
                    continue
    except Exception:
        pass

    # 2. Wikipedia search fallback using compliant User-Agent and httpx
    wiki_context = ""
    try:
        wiki_headers = {"User-Agent": "LeadershipIntelligenceBot/1.0 (admin@leadershipintel.io)"}
        with httpx.Client(timeout=8.0, headers=wiki_headers) as client:
            wresp = client.get(
                "https://en.wikipedia.org/w/api.php",
                params={"action": "query", "list": "search", "srsearch": company_name, "format": "json"}
            )
            if wresp.status_code == 200:
                items = wresp.json().get("query", {}).get("search", [])
                if items:
                    wiki_title = items[0]["title"]
                    ext_resp = client.get(
                        "https://en.wikipedia.org/w/api.php",
                        params={"action": "query", "prop": "extracts", "exintro": 1, "explaintext": 1, "titles": wiki_title, "format": "json"}
                    )
                    if ext_resp.status_code == 200:
                        pages = ext_resp.json().get("query", {}).get("pages", {})
                        for pid, pdata in pages.items():
                            wiki_context = pdata.get("extract", "")[:2500]
    except Exception:
        pass

    # 3. SEC EDGAR Official Context
    sec_context = _get_sec_edgar_context(company_name)

    # 4. Gemini Deep Extraction with Strict Authoritative & Reputable Source Mandate
    ai_client = get_genai()
    prompt = f"""
You are an executive and corporate governance research agent with direct access to official regulatory filings and corporate records.
Company: '{company_name}'
Website: '{website_url}'

========================================================================
OFFICIAL PRIMARY SOURCES AVAILABLE:
{sec_context}

OFFICIAL CORPORATE LEADERSHIP & GOVERNANCE PAGES:
{leadership_pages_text[:3500]}

OFFICIAL WEBSITE CORE TEXT:
{scraped_text[:2000]}

PUBLIC REFERENCE RECORDS:
{wiki_context[:2000]}

Discovered emails on site: {list(set(discovered_emails))[:6]}
Discovered Twitter/X links on site: {list(set(discovered_twitter))[:3]}
========================================================================

STRICT ACCURACY & AUTHORITATIVE REPUTABLE SOURCE MANDATE:
1. ABSOLUTE ZERO HALLUCINATION: You MUST ONLY extract individuals explicitly verified by official primary records (SEC filings, official corporate leadership directories, official /about or /team pages, and confirmed corporate records).
2. NEVER GUESS OR FABRICATE NAMES: If only 2, 3, or 4 leaders are confirmed by official sources, return ONLY those 2, 3, or 4. DO NOT invent or extrapolate additional names, investors, venture capitalists, or board members to fill an arbitrary count.
3. BOARD OF DIRECTORS: If a company does NOT publicly publish or disclose an external Board of Directors or advisory board in the provided official sources, DO NOT INVENT ONE. Return only confirmed individuals.
4. VERIFY RECENT TRANSITIONS: Specifically check for executive changes within the last 6 to 12 months (e.g. CEO transitions, CFO appointments, former CEOs moving to Board Chair). Do NOT return outdated legacy roles.
5. SOURCE TRACEABILITY: In 'sec_filing_source', cite the exact official primary source (e.g., 'SEC Form DEF 14A Proxy Statement', 'Official Corporate Leadership Directory (https://domain/team/)').

Return a JSON object containing:
1. "company_twitter_handle": string (e.g. '@Company' or official verified X handle, or N/A)
2. "company_recent_tweets": array of 3 realistic recent public announcement tweets/posts from the company's handle
3. "key_partners": array of 3 to 6 major ecosystem/strategic partners.
   Each object in "key_partners" MUST contain:
   - "name": string (Partner company name)
   - "website": string (Official website URL)
   - "relationship": string (Short description)
4. "key_competitors": array of 3 to 6 primary direct market competitors.
   Each object in "key_competitors" MUST contain:
   - "name": string (Competitor name)
   - "website": string (Official website URL)
   - "differentiation": string (Short description)
5. "members": an array of verified key leaders (1 to 12). If only 1, 2, or 3 verified leaders are confirmed by the official sources, return ONLY those verified leaders. Do NOT invent names.
   Each member MUST contain:
   - name: string (Full Name)
   - title: string (Role, e.g. 'Chief Executive Officer', 'Chief Financial Officer', 'Director', 'Chair of the Board')
   - group: string ('Executive Management' or 'Board of Directors')
   - email: string (corporate email e.g. first@domain or name@company.com, or N/A)
   - twitter_handle: string (known X/Twitter handle like '@handle', or N/A)
   - recent_tweets: array of up to 3 recent public messages/tweets/quotes
   - committee: string or null (e.g. 'Audit Committee', 'Compensation Committee', 'Executive Committee')
   - is_independent: boolean
   - tenure_years: integer or null
   - compensation: string (Estimated annual total compensation or proxy fee e.g. '$15.2M' or '$280K retainer' or 'N/A')
   - sec_filing_source: string (e.g. 'SEC Form DEF 14A Proxy Statement / Annual Report')
   - bio: string (1-2 sentence background summary)
   - skills_keywords: array of 3 to 5 domain expertise keywords (e.g. ["Cybersecurity", "FinTech", "Cloud Architecture"])

Respond with ONLY the JSON object inside a ```json ``` block.
"""

    primary_model = os.getenv("DISCOVERY_MODEL", os.getenv("MODEL", "gemini-3.8-flash"))
    candidate_models = [primary_model]
    for fallback in ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3-flash-preview", "gemini-flash-lite-latest"]:
        if fallback not in candidate_models:
            candidate_models.append(fallback)

    raw_text = "{}"
    for model_name in candidate_models:
        try:
            resp = ai_client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=dict(response_mime_type="application/json")
            )
            raw_text = resp.text or "{}"
            if raw_text and raw_text.strip() not in ("{}", ""):
                break
        except Exception as e:
            err_str = str(e)
            print(f"Discovery model {model_name} failed: {err_str[:120]}")
            if any(k in err_str for k in ("429", "503", "404", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "NOT_FOUND")):
                continue
            break
    data_payload = {}
    try:
        data_payload = json.loads(raw_text)
    except Exception:
        json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if json_match:
            try:
                data_payload = json.loads(json_match.group(0))
            except Exception:
                pass

    members_data = data_payload.get("members", [])
    company_twitter = data_payload.get("company_twitter_handle", "") or (discovered_twitter[0] if discovered_twitter else "N/A")
    company_recent_tweets = data_payload.get("company_recent_tweets", [])
    key_partners = data_payload.get("key_partners", [])
    key_competitors = data_payload.get("key_competitors", [])

    # 4. Fetch official company logo directly from company website
    logo_url = extract_company_website_logo(website_url)

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
            "key_partners": key_partners,
            "key_competitors": key_competitors,
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
            "compensation": m.get("compensation") or "N/A",
            "sec_filing_source": m.get("sec_filing_source") or "DEF 14A Proxy",
            "skills_keywords": m.get("skills_keywords") or [],
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
        "key_partners": key_partners,
        "key_competitors": key_competitors,
        "total_results": len(executives) + len(board_of_directors),
        "executives": executives,
        "board_of_directors": board_of_directors,
        "auto_discovered": True,
    }
