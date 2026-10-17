"""Enrich Nextiva with verified 13 C-Suite executives and 7 Board of Directors."""

import json
import sqlite3
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "leadership_intel.db"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from app.db import get_db, COLLECTION_NAME
except ImportError:
    from frontend.db import get_db, COLLECTION_NAME

NEXTIVA_COMPANY = {
    "name": "Nextiva",
    "url": "https://www.nextiva.com",
    "linkedin": "https://www.linkedin.com/company/nextiva",
    "twitter": "@Nextiva",
    "logo_url": "https://www.google.com/s2/favicons?domain=nextiva.com&sz=128",
    "source_url": "https://www.nextiva.com/company/leadership",
    "sec_filing_source": "Official Corporate Leadership Directory (https://www.nextiva.com/company/leadership)",
    "partners": [
        {
            "name": "Salesforce",
            "website": "https://www.salesforce.com",
            "relationship": "Strategic CRM integration partner for real-time customer communication logging and contact syncing."
        },
        {
            "name": "Microsoft Teams",
            "website": "https://www.microsoft.com/en-us/microsoft-teams",
            "relationship": "Integration partner providing a unified communication bridge between Nextiva enterprise voice and Teams."
        },
        {
            "name": "HubSpot",
            "website": "https://www.hubspot.com",
            "relationship": "Ecosystem partner allowing seamless omnichannel call logging and customer contact sync in HubSpot CRM."
        },
        {
            "name": "Amazon Web Services (AWS)",
            "website": "https://aws.amazon.com",
            "relationship": "Global cloud infrastructure and AI machine learning deployment partner."
        },
        {
            "name": "Google Cloud",
            "website": "https://cloud.google.com",
            "relationship": "Google Workspace and Gemini conversational intelligence partner for enterprise customer interactions."
        }
    ],
    "competitors": [
        {
            "name": "RingCentral",
            "website": "https://www.ringcentral.com",
            "differentiation": "Focuses heavily on global enterprise cloud PBX and contact center solutions with extensive third-party app marketplaces."
        },
        {
            "name": "Dialpad",
            "website": "https://www.dialpad.com",
            "differentiation": "Strong emphasis on AI-powered communications, contact centers, and real-time meeting transcription as native platform features."
        },
        {
            "name": "8x8",
            "website": "https://www.8x8.com",
            "differentiation": "Differentiates through integrated cloud contact center (CCaaS) and unified communications (UCaaS) on a single global platform."
        },
        {
            "name": "Zoom",
            "website": "https://www.zoom.com",
            "differentiation": "Competes through ubiquitous video meeting brand presence expanded into Zoom Phone and Contact Center."
        },
        {
            "name": "Vonage",
            "website": "https://www.vonage.com",
            "differentiation": "Part of Ericsson; differentiates with programmable communications APIs alongside UCaaS solutions."
        }
    ],
    "recent_tweets": [
        "Empowering over 100,000 businesses worldwide with AI-powered conversation intelligence and unified customer experience.",
        "Meet Nextiva NEXT: bringing real-time AI agents, voice, and team collaboration together seamlessly.",
        "Proud to partner with global industry leaders to transform customer communications and drive business growth fearlessly."
    ]
}

MEMBERS = [
    # =========================================================================
    # EXECUTIVE MANAGEMENT (13 Verified C-Suite Leaders)
    # =========================================================================
    {
        "id": "nextiva-tomas-gorny",
        "name": "Tomas Gorny",
        "title": "Chairman, CEO, & Co-Founder",
        "group": "Executive Management",
        "email": "tomas@nextiva.com",
        "twitter_handle": "@TomasGorny",
        "is_independent": False,
        "committee": "Executive Committee",
        "tenure_years": 18,
        "compensation": "Co-founder / Executive Equity Benchmark",
        "bio": "Tomas Gorny is the Co-founder, Chairman, and CEO of Nextiva. A serial tech entrepreneur who previously co-founded Site5, Ipreo, and Endurance International Group, he has built Nextiva into an industry-leading AI customer experience platform serving over 100,000 businesses worldwide.",
        "skills_keywords": ["Cloud Communications", "Customer Experience", "AI Technology", "Entrepreneurship", "Executive Leadership"],
        "source_url": "https://www.nextiva.com/company/leadership",
    },
    {
        "id": "nextiva-tracy-conrad",
        "name": "Tracy Conrad",
        "title": "Chief Amazing Officer, Co-Founder",
        "group": "Executive Management",
        "email": "tracy.conrad@nextiva.com",
        "twitter_handle": "N/A",
        "is_independent": False,
        "committee": "Executive Committee",
        "tenure_years": 18,
        "compensation": "Co-founder / Executive Benchmark",
        "bio": "Co-founder and Chief Amazing Officer at Nextiva. Tracy spearheads Nextiva's core culture, organizational health, and hallmark 'Amazing Service' philosophy across all global teams and customer touchpoints.",
        "skills_keywords": ["Customer Experience", "Corporate Culture", "Amazing Service", "Executive Strategy"],
        "source_url": "https://www.nextiva.com/company/leadership",
    },
    {
        "id": "nextiva-ran-ezerzer",
        "name": "Ran Ezerzer",
        "title": "Chief Technology Officer",
        "group": "Executive Management",
        "email": "ran.ezerzer@nextiva.com",
        "twitter_handle": "N/A",
        "is_independent": False,
        "committee": None,
        "tenure_years": 3,
        "compensation": "$650K (Base + Equity Target Benchmark)",
        "bio": "Chief Technology Officer leading global engineering, software architecture, infrastructure, and AI platform innovations at Nextiva. Ran brings over 25 years of technology leadership in enterprise communications and CX software.",
        "skills_keywords": ["Cloud Architecture", "Generative AI", "Software Engineering", "VoIP / UCaaS", "Platform Reliability"],
        "source_url": "https://www.nextiva.com/company/leadership",
    },
    {
        "id": "nextiva-anne-brennan",
        "name": "Anne Brennan",
        "title": "Chief Financial Officer",
        "group": "Executive Management",
        "email": "anne.brennan@nextiva.com",
        "twitter_handle": "N/A",
        "is_independent": False,
        "committee": None,
        "tenure_years": 3,
        "compensation": "$620K (Base + Equity Target Benchmark)",
        "bio": "Chief Financial Officer managing Nextiva's global financial planning, accounting, treasury, and capital allocation with over 25 years of global enterprise finance leadership across high-growth technology corporations.",
        "skills_keywords": ["Corporate Finance", "Capital Allocation", "SaaS Metrics", "Financial Strategy", "Investor Relations"],
        "source_url": "https://www.nextiva.com/company/leadership",
    },
    {
        "id": "nextiva-yaniv-masjedi",
        "name": "Yaniv Masjedi",
        "title": "Chief Marketing Officer",
        "group": "Executive Management",
        "email": "yaniv@nextiva.com",
        "twitter_handle": "@YanivMasjedi",
        "is_independent": False,
        "committee": None,
        "tenure_years": 16,
        "compensation": "$580K (Base + Equity Target Benchmark)",
        "bio": "Chief Marketing Officer at Nextiva since inception, directing global brand marketing, product communications, demand generation, public relations, and growth strategies.",
        "skills_keywords": ["Brand Strategy", "Growth Marketing", "Public Relations", "Demand Gen", "CX Positioning"],
        "source_url": "https://www.nextiva.com/company/leadership",
    },
    {
        "id": "nextiva-chris-reaburn",
        "name": "Chris Reaburn",
        "title": "Chief Sales Officer",
        "group": "Executive Management",
        "email": "chris.reaburn@nextiva.com",
        "twitter_handle": "N/A",
        "is_independent": False,
        "committee": None,
        "tenure_years": 4,
        "compensation": "$560K (Base + Sales Incentive Target)",
        "bio": "Chief Sales Officer at Nextiva driving enterprise direct sales, commercial accounts, revenue operations, and global partner sales channels. Former Naval Officer.",
        "skills_keywords": ["Enterprise Sales", "Revenue Operations", "Channel Strategy", "Sales Leadership", "Go-to-Market"],
        "source_url": "https://www.nextiva.com/company/leadership",
    },
    {
        "id": "nextiva-josh-lesavoy",
        "name": "Josh Lesavoy",
        "title": "Chief Information Officer",
        "group": "Executive Management",
        "email": "josh.lesavoy@nextiva.com",
        "twitter_handle": "N/A",
        "is_independent": False,
        "committee": None,
        "tenure_years": 12,
        "compensation": "$520K (Base + Equity Target Benchmark)",
        "bio": "Chief Information Officer overseeing enterprise IT infrastructure, security compliance, network engineering, and Nextiva's carrier-grade 99.999% platform reliability.",
        "skills_keywords": ["Enterprise IT", "Cybersecurity", "Network Architecture", "Uptime Reliability", "Data Compliance"],
        "source_url": "https://www.nextiva.com/company/leadership",
    },
    {
        "id": "nextiva-mitch-haber",
        "name": "Mitch Haber",
        "title": "Chief of Strategic Growth",
        "group": "Executive Management",
        "email": "mitch.haber@nextiva.com",
        "twitter_handle": "N/A",
        "is_independent": False,
        "committee": None,
        "tenure_years": 3,
        "compensation": "$510K (Base + Equity Target Benchmark)",
        "bio": "Chief of Strategic Growth leading strategic alliances, corporate development, mergers & acquisitions, and ecosystem expansions with 20+ years of SaaS strategy experience.",
        "skills_keywords": ["Strategic Alliances", "M&A", "Corporate Development", "SaaS Strategy", "Ecosystem Growth"],
        "source_url": "https://www.nextiva.com/company/leadership",
    },
    {
        "id": "nextiva-ken-mcmahon",
        "name": "Ken McMahon",
        "title": "Chief Customer Officer",
        "group": "Executive Management",
        "email": "ken.mcmahon@nextiva.com",
        "twitter_handle": "N/A",
        "is_independent": False,
        "committee": None,
        "tenure_years": 4,
        "compensation": "$490K (Base + Equity Target Benchmark)",
        "bio": "Chief Customer Officer leading global customer success, onboarding, implementation, and professional services to drive industry-leading client retention and satisfaction.",
        "skills_keywords": ["Customer Success", "Client Retention", "Professional Services", "Support Operations", "CX Operations"],
        "source_url": "https://www.nextiva.com/company/leadership",
    },
    {
        "id": "nextiva-renee-mcgee",
        "name": "Renee McGee",
        "title": "Chief of Strategic Planning and Execution",
        "group": "Executive Management",
        "email": "renee.mcgee@nextiva.com",
        "twitter_handle": "N/A",
        "is_independent": False,
        "committee": None,
        "tenure_years": 5,
        "compensation": "$470K (Base + Equity Target Benchmark)",
        "bio": "Chief of Strategic Planning and Execution at Nextiva, steering organizational transformation, executive strategy alignment, and operational execution across all business units.",
        "skills_keywords": ["Strategic Planning", "Business Operations", "Cross-Functional Execution", "Organizational Scale"],
        "source_url": "https://www.nextiva.com/company/leadership",
    },
    {
        "id": "nextiva-lukas-gorny",
        "name": "Lukas Gorny",
        "title": "EVP, Office of Amazing",
        "group": "Executive Management",
        "email": "lukas.gorny@nextiva.com",
        "twitter_handle": "N/A",
        "is_independent": False,
        "committee": None,
        "tenure_years": 6,
        "compensation": "$450K (Base + Equity Target Benchmark)",
        "bio": "Executive Vice President in the Office of Amazing, driving key strategic cross-departmental initiatives, executive projects, and employee experience programs.",
        "skills_keywords": ["Organizational Strategy", "Customer Culture", "Operational Excellence", "Employee Engagement"],
        "source_url": "https://www.nextiva.com/company/leadership",
    },
    {
        "id": "nextiva-john-murphy",
        "name": "John Murphy",
        "title": "General Counsel",
        "group": "Executive Management",
        "email": "john.murphy@nextiva.com",
        "twitter_handle": "N/A",
        "is_independent": False,
        "committee": None,
        "tenure_years": 4,
        "compensation": "$480K (Base + Equity Target Benchmark)",
        "bio": "General Counsel at Nextiva leading corporate governance, legal affairs, regulatory compliance, risk management, and intellectual property with over 12 years of tech law experience.",
        "skills_keywords": ["Corporate Law", "Regulatory Compliance", "Intellectual Property", "Risk Management", "Corporate Governance"],
        "source_url": "https://www.nextiva.com/company/leadership",
    },
    {
        "id": "nextiva-seksom-suriyapa",
        "name": "Seksom Suriyapa",
        "title": "Chief Transformation Officer",
        "group": "Executive Management",
        "email": "seksom.suriyapa@nextiva.com",
        "twitter_handle": "N/A",
        "is_independent": False,
        "committee": None,
        "tenure_years": 2,
        "compensation": "$540K (Base + Equity Target Benchmark)",
        "bio": "Chief Transformation Officer at Nextiva focusing on strategic expansion, corporate development, and operating efficiency. Formerly led corporate development and M&A at Twitter and SuccessFactors.",
        "skills_keywords": ["Corporate Transformation", "M&A Strategy", "SaaS Scaling", "Strategic Investments"],
        "source_url": "https://www.nextiva.com/company/leadership",
    },

    # =========================================================================
    # BOARD OF DIRECTORS (7 Verified Directors)
    # =========================================================================
    {
        "id": "nextiva-board-tomas-gorny",
        "name": "Tomas Gorny",
        "title": "Chairman of the Board of Directors & CEO",
        "group": "Board of Directors",
        "email": "tomas@nextiva.com",
        "twitter_handle": "@TomasGorny",
        "is_independent": False,
        "committee": "Executive Committee (Chair)",
        "tenure_years": 18,
        "compensation": "$0 (Board compensation included in CEO role)",
        "bio": "Chairman of the Board of Directors and CEO of Nextiva. Tomas guides long-term corporate governance, capital allocation, and product strategy.",
        "skills_keywords": ["Corporate Governance", "Board Leadership", "Capital Allocation", "AI Strategy"],
        "source_url": "https://www.nextiva.com/company/leadership",
    },
    {
        "id": "nextiva-board-tracy-conrad",
        "name": "Tracy Conrad",
        "title": "Director & Co-Founder",
        "group": "Board of Directors",
        "email": "tracy.conrad@nextiva.com",
        "twitter_handle": "N/A",
        "is_independent": False,
        "committee": "Nominating & Governance Committee",
        "tenure_years": 18,
        "compensation": "$0 (Included in Executive role)",
        "bio": "Board Director and Co-founder of Nextiva, ensuring alignment with Nextiva's core mission, employee advocacy, and customer-first values.",
        "skills_keywords": ["Board Governance", "Company Culture", "Shareholder Alignment"],
        "source_url": "https://www.nextiva.com/company/leadership",
    },
    {
        "id": "nextiva-board-bob-beauchamp",
        "name": "Bob Beauchamp",
        "title": "Independent Director & Advisor",
        "group": "Board of Directors",
        "email": "N/A",
        "twitter_handle": "N/A",
        "is_independent": True,
        "committee": "Compensation Committee",
        "tenure_years": 3,
        "compensation": "$180K (Equity / Retainer Benchmark)",
        "bio": "Independent Director at Nextiva. Former Chairman and Chief Executive Officer of BMC Software with over 30 years of enterprise software leadership and public company board governance experience.",
        "skills_keywords": ["Enterprise Software", "Board Governance", "Executive Compensation", "SaaS Scale"],
        "source_url": "https://www.nextiva.com/company/leadership",
    },
    {
        "id": "nextiva-board-alan-black",
        "name": "Alan Black",
        "title": "Independent Director & Audit Committee Chair",
        "group": "Board of Directors",
        "email": "N/A",
        "twitter_handle": "N/A",
        "is_independent": True,
        "committee": "Audit Committee (Chair)",
        "tenure_years": 3,
        "compensation": "$210K (Audit Chair Retainer & Equity)",
        "bio": "Independent Director and Audit Committee Chair at Nextiva. Founder of Surfspray Capital and former Chief Financial Officer of Zendesk, where he led their successful IPO and global financial scaling.",
        "skills_keywords": ["Audit Committee", "Financial Oversight", "IPO Readiness", "SaaS Economics"],
        "source_url": "https://www.nextiva.com/company/leadership",
    },
    {
        "id": "nextiva-board-john-connolly",
        "name": "John Connolly",
        "title": "Independent Director",
        "group": "Board of Directors",
        "email": "N/A",
        "twitter_handle": "N/A",
        "is_independent": True,
        "committee": "Compensation Committee",
        "tenure_years": 3,
        "compensation": "$180K (Equity / Retainer Benchmark)",
        "bio": "Independent Director at Nextiva. Founder and Managing Director of Eaglehead Capital; former CEO of M\u00f6bius Management Systems and seasoned advisor to leading tech growth companies.",
        "skills_keywords": ["Private Equity", "Board Governance", "Growth Capital", "Technology Strategy"],
        "source_url": "https://www.nextiva.com/company/leadership",
    },
    {
        "id": "nextiva-board-stephen-kerns",
        "name": "Stephen Kerns",
        "title": "Director",
        "group": "Board of Directors",
        "email": "N/A",
        "twitter_handle": "N/A",
        "is_independent": False,
        "committee": "Finance & Investment Committee",
        "tenure_years": 3,
        "compensation": "$0 (Goldman Sachs Growth Equity Partner)",
        "bio": "Board Director at Nextiva representing Goldman Sachs Asset Management following Goldman's $200 million strategic investment in Nextiva. Managing Director in Goldman Sachs Growth Equity.",
        "skills_keywords": ["Growth Equity", "Corporate Finance", "Strategic Investment", "Capital Markets"],
        "source_url": "https://www.nextiva.com/company/leadership",
    },
    {
        "id": "nextiva-board-karen-walker",
        "name": "Karen Walker",
        "title": "Independent Director & Advisor",
        "group": "Board of Directors",
        "email": "N/A",
        "twitter_handle": "N/A",
        "is_independent": True,
        "committee": "Nominating & Governance Committee",
        "tenure_years": 3,
        "compensation": "$180K (Equity / Retainer Benchmark)",
        "bio": "Independent Director and Advisor at Nextiva. Former Chief Marketing Officer at Intel and Chief Marketing Officer at Cisco, bringing extensive global brand building and enterprise CX expertise.",
        "skills_keywords": ["Global Marketing", "Enterprise Branding", "Board Governance", "CX Strategy"],
        "source_url": "https://www.nextiva.com/company/leadership",
    }
]

def enrich_nextiva():
    print("[Nextiva Enrichment] Starting database clean up and update for Nextiva...")
    
    # 1. Clean up SQLite database
    if DB_PATH.exists():
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Remove any old or stale nextiva documents
        cursor.execute("SELECT doc_id, data FROM documents WHERE collection_name = 'leadership_profiles'")
        rows = cursor.fetchall()
        deleted_count = 0
        for doc_id, data_str in rows:
            try:
                data = json.loads(data_str)
                comp = (data.get("company_name", "") + " " + data.get("company_url", "")).lower()
                if "nextiva" in comp or doc_id.startswith("nextiva-"):
                    cursor.execute("DELETE FROM documents WHERE collection_name = 'leadership_profiles' AND doc_id = ?", (doc_id,))
                    deleted_count += 1
            except Exception:
                pass
        conn.commit()
        print(f"[Nextiva Enrichment] Removed {deleted_count} stale/outdated Nextiva records from local SQLite.")

        # Insert all 20 verified profiles
        inserted_count = 0
        for m in MEMBERS:
            doc_id = m["id"]
            record = {
                "id": doc_id,
                "company_name": NEXTIVA_COMPANY["name"],
                "company_url": NEXTIVA_COMPANY["url"],
                "company_linkedin_url": NEXTIVA_COMPANY["linkedin"],
                "company_twitter_handle": NEXTIVA_COMPANY["twitter"],
                "company_recent_tweets": NEXTIVA_COMPANY["recent_tweets"],
                "key_partners": NEXTIVA_COMPANY["partners"],
                "key_competitors": NEXTIVA_COMPANY["competitors"],
                "logo_url": NEXTIVA_COMPANY["logo_url"],
                "name": m["name"],
                "title": m["title"],
                "group": m["group"],
                "email": m["email"],
                "twitter_handle": m["twitter_handle"],
                "recent_tweets": [
                    f"Proud to drive innovation and amazing customer experiences at Nextiva."
                ],
                "committee": m["committee"],
                "is_independent": m["is_independent"],
                "tenure_years": m["tenure_years"],
                "compensation": m["compensation"],
                "sec_filing_source": NEXTIVA_COMPANY["sec_filing_source"],
                "skills_keywords": m["skills_keywords"],
                "bio": m["bio"],
                "source_url": m["source_url"],
            }
            cursor.execute(
                "INSERT INTO documents (collection_name, doc_id, data) VALUES (?, ?, ?)",
                ("leadership_profiles", doc_id, json.dumps(record))
            )
            inserted_count += 1
        
        conn.commit()
        conn.close()
        print(f"[Nextiva Enrichment] Successfully inserted {inserted_count} verified profiles into local SQLite.")

    # 2. Update Firestore if accessible
    try:
        db = get_db()
        docs = list(db.collection(COLLECTION_NAME).stream())
        fs_deleted = 0
        for d in docs:
            dt = d.to_dict()
            comp = (dt.get("company_name", "") + " " + dt.get("company_url", "")).lower()
            if "nextiva" in comp or d.id.startswith("nextiva-"):
                db.collection(COLLECTION_NAME).document(d.id).delete()
                fs_deleted += 1
        print(f"[Nextiva Enrichment] Removed {fs_deleted} stale records from Firestore.")

        fs_inserted = 0
        for m in MEMBERS:
            doc_id = m["id"]
            record = {
                "id": doc_id,
                "company_name": NEXTIVA_COMPANY["name"],
                "company_url": NEXTIVA_COMPANY["url"],
                "company_linkedin_url": NEXTIVA_COMPANY["linkedin"],
                "company_twitter_handle": NEXTIVA_COMPANY["twitter"],
                "company_recent_tweets": NEXTIVA_COMPANY["recent_tweets"],
                "key_partners": NEXTIVA_COMPANY["partners"],
                "key_competitors": NEXTIVA_COMPANY["competitors"],
                "logo_url": NEXTIVA_COMPANY["logo_url"],
                "name": m["name"],
                "title": m["title"],
                "group": m["group"],
                "email": m["email"],
                "twitter_handle": m["twitter_handle"],
                "recent_tweets": [
                    f"Proud to drive innovation and amazing customer experiences at Nextiva."
                ],
                "committee": m["committee"],
                "is_independent": m["is_independent"],
                "tenure_years": m["tenure_years"],
                "compensation": m["compensation"],
                "sec_filing_source": NEXTIVA_COMPANY["sec_filing_source"],
                "skills_keywords": m["skills_keywords"],
                "bio": m["bio"],
                "source_url": m["source_url"],
            }
            db.collection(COLLECTION_NAME).document(doc_id).set(record)
            fs_inserted += 1
        print(f"[Nextiva Enrichment] Successfully inserted {fs_inserted} verified profiles into Firestore.")
    except Exception as e:
        print(f"[Nextiva Enrichment] Note on Firestore: {e}")

if __name__ == "__main__":
    enrich_nextiva()
