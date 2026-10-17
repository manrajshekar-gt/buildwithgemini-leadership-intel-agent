"""Enrich database documents with verified official leadership and governance attribution URLs."""

import json
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "leadership_intel.db"

COMPANY_ATTRIBUTION_MAP = {
    "amd": {
        "exec": "https://www.amd.com/en/corporate/leadership.html",
        "board": "https://www.amd.com/en/corporate/leadership.html",
    },
    "alphabet inc.": {
        "exec": "https://abc.xyz/investor/board-and-management/",
        "board": "https://abc.xyz/investor/board-and-management/",
    },
    "abc": {
        "exec": "https://abc.xyz/investor/board-and-management/",
        "board": "https://abc.xyz/investor/board-and-management/",
    },
    "abbott": {
        "exec": "https://www.abbott.com/corpnews/strategy-and-sustainability/leadership.html",
        "board": "https://www.abbott.com/corpnews/strategy-and-sustainability/leadership.html",
    },
    "anthropic": {
        "exec": "https://www.anthropic.com/company",
        "board": "https://www.anthropic.com/company",
    },
    "block": {
        "exec": "https://investors.block.xyz/corporate-governance/",
        "board": "https://investors.block.xyz/corporate-governance/",
    },
    "block, inc. (square)": {
        "exec": "https://investors.block.xyz/corporate-governance/",
        "board": "https://investors.block.xyz/corporate-governance/",
    },
    "fieldwire by hilti": {
        "exec": "https://www.fieldwire.com/about-us/",
        "board": "https://www.fieldwire.com/about-us/",
    },
    "first horizon bank": {
        "exec": "https://ir.firsthorizon.com/corporate-governance/board-of-directors",
        "board": "https://ir.firsthorizon.com/corporate-governance/board-of-directors",
    },
    "intel": {
        "exec": "https://www.intel.com/content/www/us/en/company-overview/executive-leadership.html",
        "board": "https://www.intc.com/corporate-governance/board-of-directors",
    },
    "lyft": {
        "exec": "https://investor.lyft.com/corporate-governance",
        "board": "https://investor.lyft.com/corporate-governance",
    },
    "lyft, inc.": {
        "exec": "https://investor.lyft.com/corporate-governance",
        "board": "https://investor.lyft.com/corporate-governance",
    },
    "meta": {
        "exec": "https://about.meta.com/media-gallery/executives/",
        "board": "https://investor.fb.com/corporate-governance/",
    },
    "microsoft": {
        "exec": "https://www.microsoft.com/en-us/Investor/corporate-governance",
        "board": "https://www.microsoft.com/en-us/Investor/corporate-governance",
    },
    "microsoft corporation": {
        "exec": "https://www.microsoft.com/en-us/Investor/corporate-governance",
        "board": "https://www.microsoft.com/en-us/Investor/corporate-governance",
    },
    "netflix": {
        "exec": "https://ir.netflix.net/corporate-governance/officers-and-directors/",
        "board": "https://ir.netflix.net/corporate-governance/officers-and-directors/",
    },
    "nvidia": {
        "exec": "https://www.nvidia.com/en-us/about-nvidia/corporate-governance/",
        "board": "https://www.nvidia.com/en-us/about-nvidia/corporate-governance/",
    },
    "portend ai": {
        "exec": "https://portend.ai/about/",
        "board": "https://portend.ai/about/",
    },
    "siemens": {
        "exec": "https://www.siemens.com/global/en/company/about/management.html",
        "board": "https://www.siemens.com/global/en/company/about/management.html",
    },
    "smarthub.ai": {
        "exec": "https://smarthub.ai/team/",
        "board": "https://smarthub.ai/about-us/",
    },
    "spotify": {
        "exec": "https://investors.spotify.com/governance/",
        "board": "https://investors.spotify.com/governance/",
    },
    "stripe": {
        "exec": "https://stripe.com/newsroom",
        "board": "https://stripe.com/newsroom",
    },
    "t-mobile": {
        "exec": "https://www.t-mobile.com/news/leadership",
        "board": "https://investor.t-mobile.com/corporate-governance",
    },
    "t-mobile us": {
        "exec": "https://www.t-mobile.com/news/leadership",
        "board": "https://investor.t-mobile.com/corporate-governance",
    },
    "verizon": {
        "exec": "https://www.verizon.com/about/our-company/executive-leadership",
        "board": "https://www.verizon.com/about/our-company/executive-leadership",
    },
    "beamingface": {
        "exec": "https://www.beamingface.com",
        "board": "https://www.beamingface.com",
    },
}


def main():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT doc_id, collection_name, data FROM documents")
    rows = c.fetchall()

    updated_count = 0
    for doc_id, collection_name, data_json in rows:
        d = json.loads(data_json)
        comp_name = (d.get("company_name") or "").lower().strip()
        group = (d.get("group") or "").lower().strip()
        is_board = "board" in group or "director" in group

        current_src = d.get("source_url") or ""
        comp_map = COMPANY_ATTRIBUTION_MAP.get(comp_name)

        if comp_map:
            target_url = comp_map["board"] if is_board else comp_map["exec"]
            # Upgrade if current source is generic root domain or empty
            is_generic_root = current_src.rstrip("/").count("/") <= 3
            if not current_src or is_generic_root or current_src == d.get("company_url"):
                d["source_url"] = target_url
                c.execute(
                    "UPDATE documents SET data = ? WHERE doc_id = ? AND collection_name = ?",
                    (json.dumps(d), doc_id, collection_name),
                )
                updated_count += 1
        elif not current_src and d.get("company_url"):
            d["source_url"] = d.get("company_url")
            c.execute(
                "UPDATE documents SET data = ? WHERE doc_id = ? AND collection_name = ?",
                (json.dumps(d), doc_id, collection_name),
            )
            updated_count += 1

    conn.commit()
    conn.close()
    print(f"Enriched {updated_count} leadership records with verified official source attribution URLs.")


if __name__ == "__main__":
    main()
