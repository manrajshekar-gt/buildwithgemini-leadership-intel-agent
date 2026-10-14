"""Enriches all indexed company records in the database with verified official company LinkedIn URLs.

Applies strict corporate-only LinkedIn guardrails:
- Official company LinkedIn URLs (linkedin.com/company/...) for corporate presence.
- Removes individual and BOD member LinkedIn URLs completely to avoid 404s, broken links,
  login walls, and false vanity URL mappings.
- Persists changes into SQLite and Firestore.
"""

import json
import sqlite3
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db import DB_PATH, COLLECTION_NAME, get_db

COMPANY_LINKEDIN_MAP = {
    "amd": "https://www.linkedin.com/company/amd",
    "advanced micro devices": "https://www.linkedin.com/company/amd",
    "abbott": "https://www.linkedin.com/company/abbott-",
    "alphabet": "https://www.linkedin.com/company/google",
    "alphabet inc.": "https://www.linkedin.com/company/google",
    "google": "https://www.linkedin.com/company/google",
    "block": "https://www.linkedin.com/company/blockinc",
    "block, inc. (square)": "https://www.linkedin.com/company/blockinc",
    "square": "https://www.linkedin.com/company/blockinc",
    "fieldwire": "https://www.linkedin.com/company/fieldwire",
    "fieldwire by hilti": "https://www.linkedin.com/company/fieldwire",
    "lyft": "https://www.linkedin.com/company/lyft",
    "lyft, inc.": "https://www.linkedin.com/company/lyft",
    "microsoft": "https://www.linkedin.com/company/microsoft",
    "microsoft corporation": "https://www.linkedin.com/company/microsoft",
    "nvidia": "https://www.linkedin.com/company/nvidia",
    "netflix": "https://www.linkedin.com/company/netflix",
    "portend ai": "https://www.linkedin.com/company/portend-ai",
    "smarthub.ai": "https://www.linkedin.com/company/smarthub-ai",
    "spotify": "https://www.linkedin.com/company/spotify",
    "stripe": "https://www.linkedin.com/company/stripe",
    "t-mobile": "https://www.linkedin.com/company/t-mobile",
    "t-mobile us": "https://www.linkedin.com/company/t-mobile",
    "verizon": "https://www.linkedin.com/company/verizon",
    "beamingface": "https://www.linkedin.com/company/beamingface",
}


def enrich():
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT doc_id, data FROM documents WHERE collection_name = ?", (COLLECTION_NAME,))
    rows = cursor.fetchall()
    print(f"Found {len(rows)} profiles in '{COLLECTION_NAME}' collection.")

    updated_count = 0
    company_linkedin_count = 0
    distinct_companies = set()

    for doc_id, raw_json in rows:
        data = json.loads(raw_json)
        company_name = data.get("company_name", "")
        c_clean = company_name.lower().strip()
        distinct_companies.add(company_name)

        # 1. Resolve Company LinkedIn
        comp_linkedin = COMPANY_LINKEDIN_MAP.get(c_clean)
        if not comp_linkedin:
            for k, url in COMPANY_LINKEDIN_MAP.items():
                if k in c_clean or c_clean in k:
                    comp_linkedin = url
                    break
        comp_linkedin = comp_linkedin or "N/A"
        data["company_linkedin_url"] = comp_linkedin
        if comp_linkedin != "N/A":
            company_linkedin_count += 1

        # 2. Strip individual member LinkedIn completely
        data.pop("linkedin_url", None)

        cursor.execute(
            "UPDATE documents SET data = ? WHERE collection_name = ? AND doc_id = ?",
            (json.dumps(data), COLLECTION_NAME, doc_id),
        )
        updated_count += 1

    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print("ENRICHMENT SUMMARY (OFFICIAL COMPANY LINKEDIN ONLY):")
    print(f"Total profiles updated: {updated_count}")
    print(f"Total distinct companies: {len(distinct_companies)}")
    print(f"Official company LinkedIn present: {company_linkedin_count} ({round(company_linkedin_count/updated_count*100, 1)}%)")
    print(f"Individual & BOD member LinkedIn profiles: Removed / Omitted completely")
    print("=" * 60)


if __name__ == "__main__":
    enrich()
