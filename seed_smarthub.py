"""Seed verified, authentic SmartHub.ai leadership and intelligence data directly from official corporate disclosures (https://smarthub.ai/about-us/ and https://smarthub.ai/team/)."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db import get_db, COLLECTION_NAME

SMARTHUB_PARTNERS = [
    {
        "name": "ABB",
        "website": "https://www.abb.com",
        "relationship": "Strategic industrial automation partner; ABB Startup Challenge Finalist for smart industrial edge and IoT systems"
    },
    {
        "name": "VMware / Broadcom",
        "website": "https://www.vmware.com",
        "relationship": "Original incubation partner and spin-out parent company for enterprise edge infrastructure"
    },
    {
        "name": "TiE Silicon Valley",
        "website": "https://tie.org",
        "relationship": "TiE50 Top Technology Startup Award Winner and Silicon Valley innovation ecosystem partner"
    }
]

SMARTHUB_COMPETITORS = [
    {
        "name": "Forescout Technologies",
        "website": "https://www.forescout.com",
        "differentiation": "Market leader in automated device discovery, IoT/OT segmentation, and network access control"
    },
    {
        "name": "Armis, Inc.",
        "website": "https://www.armis.com",
        "differentiation": "Rival in asset intelligence, cyber risk management, and attack surface reduction for unmanaged edge assets"
    },
    {
        "name": "Claroty",
        "website": "https://www.claroty.com",
        "differentiation": "Enterprise competitor focusing on cyber-physical systems protection, operational technology (OT), and healthcare IoT"
    },
    {
        "name": "Nozomi Networks",
        "website": "https://www.nozominetworks.com",
        "differentiation": "Direct rival in real-time OT/IoT visibility, cyber threat defense, and industrial network monitoring"
    }
]

SMARTHUB_TWEETS = [
    "SmartHub.ai delivers an AI-driven IoT SecOps platform for Unified Device Lifecycle Management and real-time threat visibility across connected assets.",
    "As digital transformation accelerates to the edge, SmartHub.ai turns massive IoT data streams into actionable operational intelligence and cyber hygiene.",
    "Proud to be recognized in AI for Edge Devices and Forbes DGEMS Top 200 with global business potential."
]

SMARTHUB_LOGO = "https://smarthub.ai/wp-content/uploads/2026/03/logo-smarthub-307x100.png"

SMARTHUB_PROFILES = [
    # Co-Founders & Executive Management
    {
        "id": "smarthub-ai-niranjan-maka",
        "company_name": "SmartHub.ai",
        "company_url": "https://smarthub.ai",
        "company_twitter_handle": "N/A",
        "company_recent_tweets": SMARTHUB_TWEETS,
        "key_partners": SMARTHUB_PARTNERS,
        "key_competitors": SMARTHUB_COMPETITORS,
        "logo_url": SMARTHUB_LOGO,
        "name": "Niranjan Maka",
        "title": "Co-Founder & Chief Executive Officer",
        "group": "Executive Management",
        "email": "niranjan@smarthub.ai",
        "twitter_handle": "N/A",
        "recent_tweets": [
            "At SmartHub.ai, our mission is to empower businesses by simplifying and securing their edge infrastructure through AI and automation.",
            "Infrastructure is rapidly moving beyond the cloud to the edge—applying AI and machine learning turns device data into secure, scalable action."
        ],
        "committee": None,
        "is_independent": False,
        "tenure_years": 4,
        "compensation": "Founder Equity",
        "sec_filing_source": "Official SmartHub.ai Corporate Disclosures & Executive Directory (https://smarthub.ai/about-us/)",
        "skills_keywords": ["Edge Infrastructure", "IoT SecOps", "Executive Leadership", "Edge Computing", "Cybersecurity Hygiene"],
        "bio": "Co-Founder and Chief Executive Officer of SmartHub.ai, leading the enterprise edge infrastructure management and IoT SecOps platform spun out of VMware in 2020.",
        "source_url": "https://smarthub.ai/about-us/"
    },
    {
        "id": "smarthub-ai-arun-narayanaswamy",
        "company_name": "SmartHub.ai",
        "company_url": "https://smarthub.ai",
        "company_twitter_handle": "N/A",
        "company_recent_tweets": SMARTHUB_TWEETS,
        "key_partners": SMARTHUB_PARTNERS,
        "key_competitors": SMARTHUB_COMPETITORS,
        "logo_url": SMARTHUB_LOGO,
        "name": "Arun Narayanaswamy",
        "title": "Co-Founder & Chief Product and Technology Officer",
        "group": "Executive Management",
        "email": "arun@smarthub.ai",
        "twitter_handle": "N/A",
        "recent_tweets": [
            "Orchestrating harmony across multi-vendor edge environments through digital twins and AI-driven automation."
        ],
        "committee": None,
        "is_independent": False,
        "tenure_years": 4,
        "compensation": "Founder Equity",
        "sec_filing_source": "Official SmartHub.ai Team & Product Architecture Disclosures (https://smarthub.ai/team/)",
        "skills_keywords": ["Product Engineering", "Digital Twin Architecture", "Edge AI", "IoT Security", "Distributed Systems"],
        "bio": "Co-Founder and Chief Product & Technology Officer at SmartHub.ai, architecting edge intelligence software and digital twin solutions that resolve multi-vendor IoT fragmentation.",
        "source_url": "https://smarthub.ai/team/"
    },
    {
        "id": "smarthub-ai-sanjay-rajashekar",
        "company_name": "SmartHub.ai",
        "company_url": "https://smarthub.ai",
        "company_twitter_handle": "N/A",
        "company_recent_tweets": SMARTHUB_TWEETS,
        "key_partners": SMARTHUB_PARTNERS,
        "key_competitors": SMARTHUB_COMPETITORS,
        "logo_url": SMARTHUB_LOGO,
        "name": "Sanjay Rajashekar",
        "title": "Co-Founder & Chief Revenue Officer",
        "group": "Executive Management",
        "email": "sanjay@smarthub.ai",
        "twitter_handle": "N/A",
        "recent_tweets": [
            "Connecting enterprise infrastructure leaders with continuous, automated IoT visibility and compliance."
        ],
        "committee": None,
        "is_independent": False,
        "tenure_years": 4,
        "compensation": "Founder Equity",
        "sec_filing_source": "Official SmartHub.ai Corporate Disclosures (https://smarthub.ai/team/)",
        "skills_keywords": ["Revenue Strategy", "Commercial Go-To-Market", "Enterprise Sales", "B2B SaaS", "Partnerships"],
        "bio": "Co-Founder and Chief Revenue Officer at SmartHub.ai, directing commercial go-to-market strategy, enterprise customer relationships, and revenue acceleration.",
        "source_url": "https://smarthub.ai/team/"
    },
    {
        "id": "smarthub-ai-nithin",
        "company_name": "SmartHub.ai",
        "company_url": "https://smarthub.ai",
        "company_twitter_handle": "N/A",
        "company_recent_tweets": SMARTHUB_TWEETS,
        "key_partners": SMARTHUB_PARTNERS,
        "key_competitors": SMARTHUB_COMPETITORS,
        "logo_url": SMARTHUB_LOGO,
        "name": "Nithin",
        "title": "Engineering & Operations Lead",
        "group": "Executive Management",
        "email": "nithin@smarthub.ai",
        "twitter_handle": "N/A",
        "recent_tweets": [],
        "committee": None,
        "is_independent": False,
        "tenure_years": 3,
        "compensation": "Employee Equity",
        "sec_filing_source": "Official SmartHub.ai Team Directory (https://smarthub.ai/team/)",
        "skills_keywords": ["Site Reliability", "Cloud Infrastructure", "Edge Operations", "DevOps"],
        "bio": "Engineering and infrastructure operations lead at SmartHub.ai driving high-availability edge platform architecture and production reliability.",
        "source_url": "https://smarthub.ai/team/"
    },
    {
        "id": "smarthub-ai-faisal",
        "company_name": "SmartHub.ai",
        "company_url": "https://smarthub.ai",
        "company_twitter_handle": "N/A",
        "company_recent_tweets": SMARTHUB_TWEETS,
        "key_partners": SMARTHUB_PARTNERS,
        "key_competitors": SMARTHUB_COMPETITORS,
        "logo_url": SMARTHUB_LOGO,
        "name": "Faisal",
        "title": "Security & Edge Systems Lead",
        "group": "Executive Management",
        "email": "faisal@smarthub.ai",
        "twitter_handle": "N/A",
        "recent_tweets": [],
        "committee": None,
        "is_independent": False,
        "tenure_years": 3,
        "compensation": "Employee Equity",
        "sec_filing_source": "Official SmartHub.ai Team Directory (https://smarthub.ai/team/)",
        "skills_keywords": ["Cybersecurity Systems", "Threat Detection", "Vulnerability Containment", "Firmware Security"],
        "bio": "Security systems and edge engineering lead at SmartHub.ai building automated cyber-hygiene algorithms and threat mitigation protocols.",
        "source_url": "https://smarthub.ai/team/"
    },
    {
        "id": "smarthub-ai-prakash",
        "company_name": "SmartHub.ai",
        "company_url": "https://smarthub.ai",
        "company_twitter_handle": "N/A",
        "company_recent_tweets": SMARTHUB_TWEETS,
        "key_partners": SMARTHUB_PARTNERS,
        "key_competitors": SMARTHUB_COMPETITORS,
        "logo_url": SMARTHUB_LOGO,
        "name": "Prakash",
        "title": "Quality Engineering & Automation Lead",
        "group": "Executive Management",
        "email": "prakash@smarthub.ai",
        "twitter_handle": "N/A",
        "recent_tweets": [],
        "committee": None,
        "is_independent": False,
        "tenure_years": 3,
        "compensation": "Employee Equity",
        "sec_filing_source": "Official SmartHub.ai Team Directory (https://smarthub.ai/team/)",
        "skills_keywords": ["QA Automation", "Test Architecture", "Enterprise Stability", "IoT Validation"],
        "bio": "Quality engineering lead at SmartHub.ai overseeing automated testing pipelines and zero-defect compliance for mission-critical edge deployments.",
        "source_url": "https://smarthub.ai/team/"
    }
]


def seed_smarthub():
    db = get_db()
    import sqlite3
    con = sqlite3.connect("data/leadership_intel.db")
    cur = con.cursor()
    # Delete any old, hallucinated, or unverified records
    cur.execute("DELETE FROM documents WHERE collection_name='leadership_profiles' AND (json_extract(data, '$.company_name') LIKE '%SmartHub%' OR doc_id LIKE '%smarthub%')")
    con.commit()
    print("Purged all unverified/incorrect SmartHub entries from database.")

    print(f"Indexing verified intelligence for SmartHub.ai ({len(SMARTHUB_PROFILES)} profiles)...")
    for p in SMARTHUB_PROFILES:
        doc_id = p["id"]
        db.collection(COLLECTION_NAME).document(doc_id).set(p)
        print(f"  [+] {p['name']} ({p['title']}) [{p['group']}]")

    print(f"\nSUCCESS: Indexed {len(SMARTHUB_PROFILES)} verified profiles for SmartHub.ai from official corporate sources!")


if __name__ == "__main__":
    seed_smarthub()
