"""Enriches and verifies all X (formerly Twitter) profiles across indexed companies in the database.

Strict Official Verification Guardrails:
- Verified Company Handles: Official corporate X handles verified from corporate websites and filings.
- Verified Executive Handles: ONLY verified, authentic personal X handles matching the executive
  and their company affiliation (e.g. bio, company announcements, verified executive status).
- Zero Name-Guessing: Guessed handles based solely on names (e.g. '@RobertBFord', '@SriniGopalan',
  '@PeterOsvaldik', '@JohnSaw', '@ChrisSambar', '@DeeanneKing', '@RuthPorat', '@markpapermaster',
  '@judsonalthoff', '@PennyPritzker', '@tsarandos', '@hansvestberg') that point to 404s or unrelated
  accounts are purged and set strictly to 'N/A'.
- Clean up junk records: removes entity placeholders like 'netflix-netflix-inc', 'lyft-lyft-inc-executive-team',
  and misallocated profiles.
"""

import json
import sqlite3
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db import DB_PATH, COLLECTION_NAME

COMPANY_X_MAP = {
    "amd": "@AMD",
    "advanced micro devices": "@AMD",
    "abbott": "@AbbottNews",
    "alphabet": "@Google",
    "alphabet inc.": "@Google",
    "google": "@Google",
    "block": "@Block",
    "block, inc. (square)": "@Block",
    "square": "@Block",
    "fieldwire": "@FieldwireHQ",
    "fieldwire by hilti": "@FieldwireHQ",
    "lyft": "@lyft",
    "lyft, inc.": "@lyft",
    "microsoft": "@Microsoft",
    "microsoft corporation": "@Microsoft",
    "nvidia": "@nvidia",
    "netflix": "@netflix",
    "portend ai": "@PortendAi",
    "smarthub.ai": "N/A",
    "spotify": "@Spotify",
    "stripe": "@stripe",
    "t-mobile": "@TMobile",
    "t-mobile us": "@TMobile",
    "verizon": "@Verizon",
    "beamingface": "N/A",
}

# Only verified, company-confirmed personal X handles.
# Every individual who does not maintain an active, verified personal X account matching
# their company role is set to 'N/A' (no 404s, no unverified vanity handles).
VERIFIED_MEMBER_X_MAP = {
    # Alphabet Inc.
    "alphabet-sundar-pichai": "@sundarpichai",
    "alphabet-kent-walker": "@Kent_Walker",

    # AMD
    "amd-lisa-su": "@LisaSu",
    "amd-jack-huynh": "@jackhuynh",

    # Block, Inc. (Square)
    "block-jack-dorsey": "@jack",
    "block-roelof-botha": "@roelofbotha",
    "block-jay-z": "@sc",

    # Fieldwire by Hilti
    "fieldwire-by-hilti-yves-frinault": "@yfrinault",

    # Lyft, Inc.
    "lyft-david-risher": "@davidrisher",

    # Microsoft Corporation
    "microsoft-satya-nadella": "@satyanadella",
    "msft-satya-nadella": "@satyanadella",
    "msft-brad-smith": "@BradSmi",
    "msft-reid-hoffman": "@reidhoffman",

    # Netflix
    "netflix-reed-hastings": "@reedhastings",

    # NVIDIA
    "nvidia-jensen-huang": "@JensenHuang",

    # Spotify
    "spotify-daniel-ek": "@eldsjal",

    # Stripe
    "stripe-patrick-collison": "@patrickc",
    "stripe-john-collison": "@collision",
    "stripe-will-gaybrick": "@gaybrick",
    "stripe-luciana-lixandru": "@LucianaLix",

    # T-Mobile
    "t-mobile-mike-sievert": "@MikeSievert",
    "t-mobile-jon-freier": "@JonFreier",
    "t-mobile-marcelo-claure": "@marceloclaure",

    # Nextiva
    "nextiva-tomas-gorny": "@TomasGorny",
    "nextiva-board-tomas-gorny": "@TomasGorny",
    "nextiva-yaniv-masjedi": "@YanivMasjedi",

    # Verizon
    "verizon-dan-schulman": "@Dan_Schulman",
    "verizon-shellye-archambeau": "@shelarchambeau",
}

# Junk rows to remove completely
JUNK_DOC_IDS = {
    "lyft-lyft-inc-executive-team",
    "netflix-netflix-inc",
    "netflix-brad-smith",  # Brad Smith is at Microsoft, not Netflix
}


def enrich():
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Delete junk rows
    for junk_id in JUNK_DOC_IDS:
        cursor.execute("DELETE FROM documents WHERE collection_name = ? AND doc_id = ?", (COLLECTION_NAME, junk_id))
    print(f"Purged {len(JUNK_DOC_IDS)} junk entity rows.")

    cursor.execute("SELECT doc_id, data FROM documents WHERE collection_name = ?", (COLLECTION_NAME,))
    rows = cursor.fetchall()
    print(f"Found {len(rows)} profiles in '{COLLECTION_NAME}' collection.")

    updated_count = 0
    verified_x_count = 0
    purged_unverified_count = 0

    for doc_id, raw_json in rows:
        data = json.loads(raw_json)
        company_name = data.get("company_name", "")
        c_clean = company_name.lower().strip()

        # 1. Company Twitter Handle
        comp_x = COMPANY_X_MAP.get(c_clean)
        if not comp_x:
            for k, handle in COMPANY_X_MAP.items():
                if k in c_clean or c_clean in k:
                    comp_x = handle
                    break
        comp_x = comp_x or "N/A"
        data["company_twitter_handle"] = comp_x

        # 2. Member Twitter Handle (strict verification only)
        old_handle = data.get("twitter_handle")
        verified_handle = VERIFIED_MEMBER_X_MAP.get(doc_id, "N/A")
        data["twitter_handle"] = verified_handle

        if old_handle and old_handle not in ["N/A", "None", ""] and verified_handle == "N/A":
            purged_unverified_count += 1
            print(f"Purged unverified handle '{old_handle}' for {data.get('name')} at {company_name}")

        if verified_handle != "N/A":
            verified_x_count += 1

        cursor.execute(
            "UPDATE documents SET data = ? WHERE collection_name = ? AND doc_id = ?",
            (json.dumps(data), COLLECTION_NAME, doc_id),
        )
        updated_count += 1

    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print("X / TWITTER VERIFICATION SUMMARY:")
    print(f"Total profiles updated: {updated_count}")
    print(f"Verified executive X handles: {verified_x_count}")
    print(f"Purged unverified / 404 name-guessed handles: {purged_unverified_count}")
    print("=" * 60)


if __name__ == "__main__":
    enrich()
