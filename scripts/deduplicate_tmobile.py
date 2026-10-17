"""Deduplicate T-Mobile records and unify company catalog entries."""

import json
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "leadership_intel.db"

def run():
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 1. Fetch John W. Stanton from t-mobile-us and save under t-mobile-john-w-stanton
    c.execute('SELECT data FROM documents WHERE collection_name="leadership_profiles" AND doc_id="t-mobile-us-john-w-stanton"')
    row = c.fetchone()
    if row:
        d = json.loads(row[0])
        d["id"] = "t-mobile-john-w-stanton"
        d["company_name"] = "T-Mobile"
        d["company_url"] = "https://www.t-mobile.com"
        d["source_url"] = "https://investor.t-mobile.com/corporate-governance"
        c.execute("""
            INSERT INTO documents (collection_name, doc_id, data)
            VALUES (?, ?, ?)
            ON CONFLICT(collection_name, doc_id) DO UPDATE SET data=excluded.data
        """, ("leadership_profiles", "t-mobile-john-w-stanton", json.dumps(d)))
        print("  [+] Migrated John W. Stanton to t-mobile-john-w-stanton")

    # 2. Update Srini Gopalan to President, Chief Executive Officer & Director
    c.execute('SELECT data FROM documents WHERE collection_name="leadership_profiles" AND doc_id="t-mobile-srini-gopalan"')
    row = c.fetchone()
    if row:
        d = json.loads(row[0])
        d["title"] = "President, Chief Executive Officer & Director"
        d["group"] = "Executive Management"
        c.execute("""
            UPDATE documents SET data=? WHERE collection_name="leadership_profiles" AND doc_id="t-mobile-srini-gopalan"
        """, (json.dumps(d),))
        print("  [+] Updated Srini Gopalan title to President, Chief Executive Officer & Director")

    # 3. Ensure G. Michael (Mike) Sievert has Vice-Chair title and verified handle @MikeSievert
    c.execute('SELECT data FROM documents WHERE collection_name="leadership_profiles" AND doc_id="t-mobile-mike-sievert"')
    row = c.fetchone()
    if row:
        d = json.loads(row[0])
        d["name"] = "G. Michael (Mike) Sievert"
        d["title"] = "Vice-Chair of the Board of Directors"
        d["group"] = "Board of Directors"
        d["twitter_handle"] = "@MikeSievert"
        c.execute("""
            UPDATE documents SET data=? WHERE collection_name="leadership_profiles" AND doc_id="t-mobile-mike-sievert"
        """, (json.dumps(d),))
        print("  [+] Confirmed Mike Sievert as Vice-Chair of the Board with handle @MikeSievert")

    # 4. Delete redundant duplicate doc_ids
    docs_to_delete = [
        "t-mobile-us-g-michael-sievert",
        "t-mobile-us-mike-sievert",
        "t-mobile-us-peter-osvaldik",
        "t-mobile-us-timotheus-höttges",
        "t-mobile-us-john-w-stanton",
        "t-mobile-board-srini-gopalan",
        # Abbott redundant duplicates
        "abbott-board-robert-ford",
        "abbott-lisa-earnhardt",
        "abbott-michael-ogrady",
        "abbott-sally-blount",
    ]

    deleted_count = 0
    for doc_id in docs_to_delete:
        c.execute('DELETE FROM documents WHERE collection_name="leadership_profiles" AND doc_id=?', (doc_id,))
        if c.rowcount > 0:
            deleted_count += 1
            print(f"  [-] Deleted duplicate doc: {doc_id}")

    conn.commit()
    conn.close()
    print(f"\nDeduplication complete! Purged {deleted_count} duplicate documents.")

if __name__ == "__main__":
    run()
