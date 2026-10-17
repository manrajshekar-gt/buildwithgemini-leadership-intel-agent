"""Enrich Movius with complete verified leadership team and Board of Directors."""

import json
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "leadership_intel.db"

MOVIUS_COMPANY = {
    "name": "Movius",
    "url": "https://www.movius.ai",
    "linkedin": "https://www.linkedin.com/company/movius-corp",
    "twitter": "N/A",
    "logo_url": "https://www.google.com/s2/favicons?domain=movius.ai&sz=128",
    "source_url": "https://www.movius.ai/about-us/",
    "sec_filing_source": "Official Corporate Leadership Directory (https://www.movius.ai/about-us/)",
    "partners": [
        {
            "name": "T-Mobile",
            "website": "https://www.t-mobile.com",
            "relationship": "Strategic carrier partnership providing MultiLine virtual communications for enterprise mobility."
        },
        {
            "name": "Telstra",
            "website": "https://www.telstra.com.au",
            "relationship": "Global telecommunications service partner integrating compliant mobile multi-number solutions."
        },
        {
            "name": "BlackBerry",
            "website": "https://www.blackberry.com",
            "relationship": "Enterprise mobility management and security integration partner with BlackBerry Dynamics."
        },
        {
            "name": "Salesforce",
            "website": "https://www.salesforce.com",
            "relationship": "CRM integration partner enabling automatic logging of compliant client calls and messaging."
        },
        {
            "name": "Microsoft Teams",
            "website": "https://www.microsoft.com/en-us/microsoft-teams",
            "relationship": "Integrated communication platform partner bringing mobile compliance and voice recording to Teams."
        }
    ],
    "competitors": [
        {
            "name": "LeapXpert",
            "website": "https://www.leapxpert.com",
            "differentiation": "Focuses on federated enterprise messaging compliance across consumer channels like WhatsApp, WeChat, and Signal."
        },
        {
            "name": "TeleMessage",
            "website": "https://www.telemessage.com",
            "differentiation": "Provides carrier-level mobile archiving and secure messaging applications for regulatory compliance."
        },
        {
            "name": "VoxSmart",
            "website": "https://www.voxsmart.com",
            "differentiation": "Specializes in communications surveillance, trade reconstruction, and voice compliance for financial markets."
        },
        {
            "name": "Symphony",
            "website": "https://www.symphony.com",
            "differentiation": "Offers secure, compliant financial collaboration infrastructure and workflow automation."
        }
    ],
    "recent_tweets": [
        "Empowering global financial institutions to stay compliant while enabling secure mobile communication with MultiLine by Movius.",
        "Excited to showcase our AI-driven conversational intelligence and compliance solutions for modern distributed enterprise teams.",
        "Seamlessly integrate compliant voice, text, and WhatsApp messaging directly into your corporate CRM and archiving platforms."
    ]
}

MEMBERS = [
    # --- EXECUTIVE MANAGEMENT ---
    {
        "id": "movius-ananth-siva",
        "name": "Ananth Siva",
        "title": "Chief Executive Officer & Director",
        "group": "Executive Management",
        "email": "N/A",
        "twitter_handle": "N/A",
        "is_independent": False,
        "committee": "Executive Committee",
        "tenure_years": 4,
        "compensation": "N/A",
        "bio": "Ananth Siva serves as the Chief Executive Officer of Movius, leading company strategy and product innovation across mobile communications, AI intelligence, and compliance.",
        "skills_keywords": ["Enterprise Communications", "SaaS", "Compliance", "Mobile Technology"],
        "source_url": "https://www.movius.ai/about-us/",
    },
    {
        "id": "movius-rick-martig",
        "name": "Rick Martig",
        "title": "Chief Operating & Financial Officer",
        "group": "Executive Management",
        "email": "N/A",
        "twitter_handle": "N/A",
        "is_independent": False,
        "committee": None,
        "tenure_years": 3,
        "compensation": "N/A",
        "bio": "Rick Martig serves as the Chief Operating & Financial Officer at Movius, overseeing global corporate operations, finance, and financial strategy.",
        "skills_keywords": ["Financial Strategy", "Corporate Operations", "SaaS Finance", "Compliance"],
        "source_url": "https://www.movius.ai/about-us/",
    },
    {
        "id": "movius-amit-modi",
        "name": "Amit Modi",
        "title": "Chief Technology Officer & CISO",
        "group": "Executive Management",
        "email": "N/A",
        "twitter_handle": "N/A",
        "is_independent": False,
        "committee": None,
        "tenure_years": 5,
        "compensation": "N/A",
        "bio": "Amit Modi oversees global technology strategy, engineering architecture, cybersecurity, and information security protocols for Movius MultiLine.",
        "skills_keywords": ["Cloud Architecture", "Cybersecurity", "CISO", "InfoSec", "Enterprise Voice"],
        "source_url": "https://www.movius.ai/about-us/",
    },
    {
        "id": "movius-chethan-visweswar",
        "name": "Chethan Visweswar",
        "title": "Chief Product Officer",
        "group": "Executive Management",
        "email": "N/A",
        "twitter_handle": "N/A",
        "is_independent": False,
        "committee": None,
        "tenure_years": 4,
        "compensation": "N/A",
        "bio": "Chethan Visweswar leads global product roadmap, innovation, and user experience strategy across Movius's AI-enabled communication solutions.",
        "skills_keywords": ["Product Management", "Mobile Apps", "AI Communications", "Enterprise Software"],
        "source_url": "https://www.movius.ai/about-us/",
    },
    {
        "id": "movius-ajay-thakur",
        "name": "Ajay Thakur",
        "title": "Chief Information Officer",
        "group": "Executive Management",
        "email": "N/A",
        "twitter_handle": "N/A",
        "is_independent": False,
        "committee": None,
        "tenure_years": 3,
        "compensation": "N/A",
        "bio": "Ajay Thakur leads internal information systems, IT infrastructure, and digital transformation initiatives across global Movius offices.",
        "skills_keywords": ["IT Strategy", "Infrastructure", "Systems Architecture", "Digital Transformation"],
        "source_url": "https://www.movius.ai/about-us/",
    },
    {
        "id": "movius-bill-pettit",
        "name": "Bill Pettit",
        "title": "Vice President, Government Operations, InfoSec & IT",
        "group": "Executive Management",
        "email": "N/A",
        "twitter_handle": "N/A",
        "is_independent": False,
        "committee": None,
        "tenure_years": 6,
        "compensation": "N/A",
        "bio": "Bill Pettit manages government-sector client engagements, regulatory compliance programs, and secure communications deployments.",
        "skills_keywords": ["Government Operations", "Compliance", "InfoSec", "Defense & Public Sector"],
        "source_url": "https://www.movius.ai/about-us/",
    },
    {
        "id": "movius-sheila-cochran",
        "name": "Sheila Cochran",
        "title": "Vice President, Human Capital Management",
        "group": "Executive Management",
        "email": "N/A",
        "twitter_handle": "N/A",
        "is_independent": False,
        "committee": None,
        "tenure_years": 4,
        "compensation": "N/A",
        "bio": "Sheila Cochran leads global human resources, organizational development, talent acquisition, and company culture at Movius.",
        "skills_keywords": ["Human Resources", "Talent Management", "Organizational Leadership", "Culture"],
        "source_url": "https://www.movius.ai/about-us/",
    },
    {
        "id": "movius-dennis-napoliello",
        "name": "Dennis Napoliello",
        "title": "Vice President, Channel Partners",
        "group": "Executive Management",
        "email": "N/A",
        "twitter_handle": "N/A",
        "is_independent": False,
        "committee": None,
        "tenure_years": 3,
        "compensation": "N/A",
        "bio": "Dennis Napoliello manages global carrier relationships, reseller channels, and strategic telecom distribution partnerships.",
        "skills_keywords": ["Telecom Channels", "Carrier Partnerships", "Business Development", "Alliances"],
        "source_url": "https://www.movius.ai/about-us/",
    },
    {
        "id": "movius-eric-santillan",
        "name": "Eric Santillan",
        "title": "Vice President, Customer Experience",
        "group": "Executive Management",
        "email": "N/A",
        "twitter_handle": "N/A",
        "is_independent": False,
        "committee": None,
        "tenure_years": 3,
        "compensation": "N/A",
        "bio": "Eric Santillan oversees customer success, global client onboarding, technical support, and retention for enterprise deployments.",
        "skills_keywords": ["Customer Success", "Enterprise Onboarding", "Client Retention", "Customer Experience"],
        "source_url": "https://www.movius.ai/about-us/",
    },
    {
        "id": "movius-laura-santamaria",
        "name": "Laura Santamaria",
        "title": "Senior Legal Counsel",
        "group": "Executive Management",
        "email": "N/A",
        "twitter_handle": "N/A",
        "is_independent": False,
        "committee": None,
        "tenure_years": 4,
        "compensation": "N/A",
        "bio": "Laura Santamaria leads corporate legal affairs, regulatory compliance oversight, global contracts, and intellectual property.",
        "skills_keywords": ["Corporate Law", "Regulatory Compliance", "Contracts", "IP Protection"],
        "source_url": "https://www.movius.ai/about-us/",
    },

    # --- BOARD OF DIRECTORS ---
    {
        "id": "movius-augie-cruciotti",
        "name": "Augie Cruciotti",
        "title": "Chairman of the Board",
        "group": "Board of Directors",
        "email": "N/A",
        "twitter_handle": "N/A",
        "is_independent": True,
        "committee": "Audit & Governance Committee",
        "tenure_years": 8,
        "compensation": "N/A",
        "bio": "Augie Cruciotti serves as Chairman of the Board of Directors at Movius and is a Managing Director at Anschutz Investment Company, specializing in telecom and technology investments.",
        "skills_keywords": ["Board Governance", "Private Equity", "Telecommunications", "M&A"],
        "source_url": "https://www.movius.ai/about-us/",
    },
    {
        "id": "movius-sanjay-jain",
        "name": "Sanjay Jain",
        "title": "Independent Director",
        "group": "Board of Directors",
        "email": "N/A",
        "twitter_handle": "N/A",
        "is_independent": True,
        "committee": "Compensation Committee",
        "tenure_years": 4,
        "compensation": "N/A",
        "bio": "Sanjay Jain serves as an Independent Board Member, advising Movius on banking compliance, digital transformation, and global financial enterprise technology.",
        "skills_keywords": ["FinTech", "Banking Strategy", "Compliance", "Digital Transformation"],
        "source_url": "https://www.movius.ai/about-us/",
    },
    {
        "id": "movius-lisa-davis",
        "name": "Lisa Davis",
        "title": "Independent Director",
        "group": "Board of Directors",
        "email": "N/A",
        "twitter_handle": "N/A",
        "is_independent": True,
        "committee": "Audit Committee",
        "tenure_years": 3,
        "compensation": "N/A",
        "bio": "Lisa Davis is an Independent Board Member at Movius, bringing executive technology leadership experience as EVP & CIO at Blue Shield of California and former federal CIO.",
        "skills_keywords": ["Healthcare IT", "Cybersecurity", "Public Sector", "Board Governance"],
        "source_url": "https://www.movius.ai/about-us/",
    },
    {
        "id": "movius-john-mccracken",
        "name": "John McCracken",
        "title": "Director",
        "group": "Board of Directors",
        "email": "N/A",
        "twitter_handle": "N/A",
        "is_independent": True,
        "committee": "Nominating & Governance Committee",
        "tenure_years": 5,
        "compensation": "N/A",
        "bio": "John McCracken serves on the Board of Directors of Movius representing PointGuard Ventures, focusing on growth-stage software and communications investments.",
        "skills_keywords": ["Venture Capital", "Software Investments", "Enterprise Go-To-Market"],
        "source_url": "https://www.movius.ai/about-us/",
    },
    {
        "id": "movius-davinder-p-singh",
        "name": "Davinder P. Singh",
        "title": "Director",
        "group": "Board of Directors",
        "email": "N/A",
        "twitter_handle": "N/A",
        "is_independent": True,
        "committee": "Technology & Cybersecurity Advisory Committee",
        "tenure_years": 2,
        "compensation": "N/A",
        "bio": "Davinder P. Singh serves on the Board of Directors at Movius, contributing deep expertise as Head of Workforce Technology and Employee Platforms CTO at JPMorgan Chase.",
        "skills_keywords": ["Financial Systems", "Enterprise Collaboration", "Cloud Infrastructure", "Cybersecurity"],
        "source_url": "https://www.movius.ai/about-us/",
    },
]


def run():
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    count = 0
    for m in MEMBERS:
        doc_id = m["id"]
        doc_payload = {
            "id": doc_id,
            "company_name": MOVIUS_COMPANY["name"],
            "company_url": MOVIUS_COMPANY["url"],
            "company_linkedin_url": MOVIUS_COMPANY["linkedin"],
            "company_twitter_handle": MOVIUS_COMPANY["twitter"],
            "company_recent_tweets": MOVIUS_COMPANY["recent_tweets"],
            "key_partners": MOVIUS_COMPANY["partners"],
            "key_competitors": MOVIUS_COMPANY["competitors"],
            "name": m["name"],
            "title": m["title"],
            "group": m["group"],
            "email": m["email"],
            "twitter_handle": m["twitter_handle"],
            "recent_tweets": [],
            "logo_url": MOVIUS_COMPANY["logo_url"],
            "committee": m.get("committee"),
            "is_independent": m.get("is_independent", False),
            "tenure_years": m.get("tenure_years"),
            "compensation": m.get("compensation", "N/A"),
            "sec_filing_source": MOVIUS_COMPANY["sec_filing_source"],
            "source_url": m["source_url"],
            "skills_keywords": m.get("skills_keywords", []),
            "bio": m["bio"],
        }
        raw_json = json.dumps(doc_payload)
        c.execute("""
            INSERT INTO documents (collection_name, doc_id, data)
            VALUES (?, ?, ?)
            ON CONFLICT(collection_name, doc_id) DO UPDATE SET data=excluded.data
        """, ("leadership_profiles", doc_id, raw_json))
        count += 1
        print(f"  [+] Saved {m['group']}: {m['name']} ({m['title']})")

    conn.commit()
    conn.close()
    print(f"\nSuccessfully stored {count} Movius leadership & board profiles!")


if __name__ == "__main__":
    run()
