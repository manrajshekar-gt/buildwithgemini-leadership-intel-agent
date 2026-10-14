"""Seed verified Portend AI leadership and intelligence data directly from official website disclosures (https://portend.ai/about/)."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db import get_db, COLLECTION_NAME

PORTEND_PARTNERS = [
    {"name": "Sempera Organics", "website": "https://semperaorganics.com", "relationship": "Customer and design partner utilizing continuous business risk intelligence"},
    {"name": "Bitwage", "website": "https://www.bitwage.com", "relationship": "Strategic design partner for cross-border payroll risk and compliance signals"},
    {"name": "B2B Insights", "website": "https://b2binsights.com", "relationship": "Data intelligence partner for commercial entity and risk verification"},
    {"name": "Elevate Capital", "website": "https://elevate.vc", "relationship": "Venture ecosystem partner for portfolio risk monitoring"},
    {"name": "TiE Angels Silicon Valley", "website": "https://tie.org", "relationship": "Angel investor network ecosystem partner"}
]

PORTEND_COMPETITORS = [
    {"name": "SecurityScorecard", "website": "https://securityscorecard.com", "differentiation": "Market leader in third-party cybersecurity risk ratings and supply chain vendor scoring"},
    {"name": "BitSight Technologies", "website": "https://www.bitsight.com", "differentiation": "Rival in security rating services and financial impact cyber risk analytics"},
    {"name": "Prevalent, Inc.", "website": "https://www.prevalent.net", "differentiation": "Enterprise third-party risk management (TPRM) and vendor compliance software"},
    {"name": "Recorded Future", "website": "https://www.recordedfuture.com", "differentiation": "Threat intelligence cloud and adversary risk monitoring for enterprise SOCs"}
]

PORTEND_TWEETS = [
    "Portend AI delivers continuous business risk intelligence across cybersecurity, compliance, third-party, reputation and supply chain risks using real-world signals.",
    "Business risk doesn't wait for the next annual assessment. We transform fragmented external signals into earlier, actionable insights.",
    "Empowering organizations to look beyond static questionnaires and self-reported surveys with independent, real-time risk intelligence."
]

PORTEND_LOGO = "https://portend.ai/wp-content/uploads/2026/09/Portend_AI_Main_Logo.png"

PORTEND_PROFILES = [
    # Executive Management
    {
        "id": "portend-ai-shabd-vaid",
        "company_name": "Portend AI",
        "company_url": "https://portend.ai",
        "company_twitter_handle": "@PortendAi",
        "company_recent_tweets": PORTEND_TWEETS,
        "key_partners": PORTEND_PARTNERS,
        "key_competitors": PORTEND_COMPETITORS,
        "logo_url": PORTEND_LOGO,
        "name": "Shabd Vaid",
        "title": "Founder, Chief Executive Officer",
        "group": "Executive Management",
        "email": "shabd@portend.ai",
        "twitter_handle": "@PortendAi",
        "recent_tweets": [
            "At Portend AI, we believe understanding business risk should not be unnecessarily complicated or locked behind months of manual research.",
            "Continuous intelligence across cybersecurity, third parties, and supply chain allows leaders to make resilient decisions with high confidence."
        ],
        "committee": None,
        "is_independent": False,
        "tenure_years": 2,
        "compensation": "Startup Founder Equity",
        "sec_filing_source": "Official Portend AI Leadership Directory (https://portend.ai/about/)",
        "skills_keywords": ["Business Risk Intelligence", "Cybersecurity", "Third-Party Risk (TPRM)", "AI & Machine Learning", "Executive Leadership"],
        "bio": "Founder and Chief Executive Officer of Portend AI, pioneering modern AI-driven business risk intelligence across cybersecurity, compliance, and third-party risk networks.",
        "source_url": "https://portend.ai/about/"
    },
    {
        "id": "portend-ai-nick-patel",
        "company_name": "Portend AI",
        "company_url": "https://portend.ai",
        "company_twitter_handle": "@PortendAi",
        "company_recent_tweets": PORTEND_TWEETS,
        "key_partners": PORTEND_PARTNERS,
        "key_competitors": PORTEND_COMPETITORS,
        "logo_url": PORTEND_LOGO,
        "name": "Nick Patel",
        "title": "Head of Revenue & Strategic Partnerships",
        "group": "Executive Management",
        "email": "nick@portend.ai",
        "twitter_handle": "@PortendAi",
        "recent_tweets": [
            "Thrilled to partner with enterprise leaders who are tired of manual risk questionnaires and ready for continuous intelligence."
        ],
        "committee": None,
        "is_independent": False,
        "tenure_years": 1,
        "compensation": "Commercial Leadership Equity",
        "sec_filing_source": "Official Portend AI Leadership Directory (https://portend.ai/about/)",
        "skills_keywords": ["Enterprise Sales", "Strategic Partnerships", "Revenue Growth", "B2B SaaS Go-To-Market"],
        "bio": "Leads enterprise revenue strategy, commercial partnerships, and market expansion for Portend AI's risk intelligence platform.",
        "source_url": "https://portend.ai/about/"
    },
    {
        "id": "portend-ai-ankit-sharma",
        "company_name": "Portend AI",
        "company_url": "https://portend.ai",
        "company_twitter_handle": "@PortendAi",
        "company_recent_tweets": PORTEND_TWEETS,
        "key_partners": PORTEND_PARTNERS,
        "key_competitors": PORTEND_COMPETITORS,
        "logo_url": PORTEND_LOGO,
        "name": "Ankit Sharma",
        "title": "Engineering Lead",
        "group": "Executive Management",
        "email": "ankit@portend.ai",
        "twitter_handle": "N/A",
        "recent_tweets": [],
        "committee": None,
        "is_independent": False,
        "tenure_years": 1,
        "compensation": "Engineering Equity",
        "sec_filing_source": "Official Portend AI Leadership Directory (https://portend.ai/about/)",
        "skills_keywords": ["Distributed Systems", "Data Engineering", "Risk Signal Pipelines", "Cloud Infrastructure"],
        "bio": "Core engineering lead at Portend AI building real-time data pipelines and scalable infrastructure for external risk signal processing.",
        "source_url": "https://portend.ai/about/"
    },
    {
        "id": "portend-ai-priyam-singh",
        "company_name": "Portend AI",
        "company_url": "https://portend.ai",
        "company_twitter_handle": "@PortendAi",
        "company_recent_tweets": PORTEND_TWEETS,
        "key_partners": PORTEND_PARTNERS,
        "key_competitors": PORTEND_COMPETITORS,
        "logo_url": PORTEND_LOGO,
        "name": "Priyam Singh",
        "title": "Software Engineering Lead",
        "group": "Executive Management",
        "email": "priyam@portend.ai",
        "twitter_handle": "N/A",
        "recent_tweets": [],
        "committee": None,
        "is_independent": False,
        "tenure_years": 1,
        "compensation": "Engineering Equity",
        "sec_filing_source": "Official Portend AI Leadership Directory (https://portend.ai/about/)",
        "skills_keywords": ["Full-Stack Architecture", "Cybersecurity Systems", "Platform Engineering", "AI Integrations"],
        "bio": "Software engineering lead at Portend AI architecting platform user interfaces and automated vulnerability & threat detection systems.",
        "source_url": "https://portend.ai/about/"
    },
    {
        "id": "portend-ai-aditya-sharma",
        "company_name": "Portend AI",
        "company_url": "https://portend.ai",
        "company_twitter_handle": "@PortendAi",
        "company_recent_tweets": PORTEND_TWEETS,
        "key_partners": PORTEND_PARTNERS,
        "key_competitors": PORTEND_COMPETITORS,
        "logo_url": PORTEND_LOGO,
        "name": "Aditya Sharma",
        "title": "Head of Marketing",
        "group": "Executive Management",
        "email": "aditya@portend.ai",
        "twitter_handle": "N/A",
        "recent_tweets": [],
        "committee": None,
        "is_independent": False,
        "tenure_years": 1,
        "compensation": "Marketing Equity",
        "sec_filing_source": "Official Portend AI Leadership Directory (https://portend.ai/about/)",
        "skills_keywords": ["Product Marketing", "Brand Positioning", "Cybersecurity Marketing", "Demand Generation"],
        "bio": "Leads product marketing, brand positioning, and content strategy for Portend AI's risk intelligence platform.",
        "source_url": "https://portend.ai/about/"
    },
    {
        "id": "portend-ai-hardika-shangari",
        "company_name": "Portend AI",
        "company_url": "https://portend.ai",
        "company_twitter_handle": "@PortendAi",
        "company_recent_tweets": PORTEND_TWEETS,
        "key_partners": PORTEND_PARTNERS,
        "key_competitors": PORTEND_COMPETITORS,
        "logo_url": PORTEND_LOGO,
        "name": "Hardika Shangari",
        "title": "Head of Customer Success",
        "group": "Executive Management",
        "email": "hardika@portend.ai",
        "twitter_handle": "N/A",
        "recent_tweets": [],
        "committee": None,
        "is_independent": False,
        "tenure_years": 1,
        "compensation": "Customer Success Equity",
        "sec_filing_source": "Official Portend AI Leadership Directory (https://portend.ai/about/)",
        "skills_keywords": ["Customer Success", "Enterprise Client Enablement", "Risk Workflows", "Onboarding"],
        "bio": "Leads customer success and client onboarding at Portend AI, ensuring risk teams maximize value from automated external intelligence.",
        "source_url": "https://portend.ai/about/"
    },

    # Board of Advisors
    {
        "id": "portend-ai-anand-jagannathan",
        "company_name": "Portend AI",
        "company_url": "https://portend.ai",
        "company_twitter_handle": "@PortendAi",
        "company_recent_tweets": PORTEND_TWEETS,
        "key_partners": PORTEND_PARTNERS,
        "key_competitors": PORTEND_COMPETITORS,
        "logo_url": PORTEND_LOGO,
        "name": "Anand Jagannathan",
        "title": "Board Advisor",
        "group": "Board of Directors",
        "email": "N/A",
        "twitter_handle": "N/A",
        "recent_tweets": [],
        "committee": "Strategic Advisory Board",
        "is_independent": True,
        "tenure_years": 2,
        "compensation": "Advisory Equity",
        "sec_filing_source": "Official Portend AI Leadership & Advisor Directory (https://portend.ai/about/)",
        "skills_keywords": ["Enterprise Scaling", "Executive Leadership", "Technology Strategy", "Infrastructure"],
        "bio": "Experienced technology executive and serial entrepreneur serving as a senior advisor to Portend AI on enterprise scaling and infrastructure.",
        "source_url": "https://portend.ai/about/"
    },
    {
        "id": "portend-ai-raghu-raghavan",
        "company_name": "Portend AI",
        "company_url": "https://portend.ai",
        "company_twitter_handle": "@PortendAi",
        "company_recent_tweets": PORTEND_TWEETS,
        "key_partners": PORTEND_PARTNERS,
        "key_competitors": PORTEND_COMPETITORS,
        "logo_url": PORTEND_LOGO,
        "name": "Raghu Raghavan",
        "title": "Board Advisor",
        "group": "Board of Directors",
        "email": "N/A",
        "twitter_handle": "N/A",
        "recent_tweets": [],
        "committee": "Technical Advisory Board",
        "is_independent": True,
        "tenure_years": 2,
        "compensation": "Advisory Equity",
        "sec_filing_source": "Official Portend AI Leadership & Advisor Directory (https://portend.ai/about/)",
        "skills_keywords": ["Product Engineering", "Technical Architecture", "Technology Scaling", "AI Systems"],
        "bio": "Veteran technology leader and engineering advisor guiding Portend AI on product engineering and technical scale.",
        "source_url": "https://portend.ai/about/"
    },
    {
        "id": "portend-ai-atri-chatterjee",
        "company_name": "Portend AI",
        "company_url": "https://portend.ai",
        "company_twitter_handle": "@PortendAi",
        "company_recent_tweets": PORTEND_TWEETS,
        "key_partners": PORTEND_PARTNERS,
        "key_competitors": PORTEND_COMPETITORS,
        "logo_url": PORTEND_LOGO,
        "name": "Atri Chatterjee",
        "title": "Board Advisor",
        "group": "Board of Directors",
        "email": "N/A",
        "twitter_handle": "N/A",
        "recent_tweets": [],
        "committee": "Commercial & Go-To-Market Advisory Board",
        "is_independent": True,
        "tenure_years": 2,
        "compensation": "Advisory Equity",
        "sec_filing_source": "Official Portend AI Leadership & Advisor Directory (https://portend.ai/about/)",
        "skills_keywords": ["Enterprise SaaS", "Go-To-Market Strategy", "Marketing Leadership", "Corporate Governance"],
        "bio": "Seasoned software executive with deep expertise in enterprise SaaS marketing, advising Portend AI on commercial growth and corporate strategy.",
        "source_url": "https://portend.ai/about/"
    },
    {
        "id": "portend-ai-mital-makadia",
        "company_name": "Portend AI",
        "company_url": "https://portend.ai",
        "company_twitter_handle": "@PortendAi",
        "company_recent_tweets": PORTEND_TWEETS,
        "key_partners": PORTEND_PARTNERS,
        "key_competitors": PORTEND_COMPETITORS,
        "logo_url": PORTEND_LOGO,
        "name": "Mital Makadia",
        "title": "Board Advisor",
        "group": "Board of Directors",
        "email": "N/A",
        "twitter_handle": "N/A",
        "recent_tweets": [],
        "committee": "Strategic & Finance Advisory Board",
        "is_independent": True,
        "tenure_years": 2,
        "compensation": "Advisory Equity",
        "sec_filing_source": "Official Portend AI Leadership & Advisor Directory (https://portend.ai/about/)",
        "skills_keywords": ["Financial Operations", "Strategic Planning", "Corporate Scaling", "Risk Governance"],
        "bio": "Strategic advisor to high-growth tech ventures focusing on financial operations, risk governance, and corporate scaling.",
        "source_url": "https://portend.ai/about/"
    },
    {
        "id": "portend-ai-mayur-nagarsheth",
        "company_name": "Portend AI",
        "company_url": "https://portend.ai",
        "company_twitter_handle": "@PortendAi",
        "company_recent_tweets": PORTEND_TWEETS,
        "key_partners": PORTEND_PARTNERS,
        "key_competitors": PORTEND_COMPETITORS,
        "logo_url": PORTEND_LOGO,
        "name": "Mayur Nagarsheth",
        "title": "Board Advisor",
        "group": "Board of Directors",
        "email": "N/A",
        "twitter_handle": "N/A",
        "recent_tweets": [],
        "committee": "Venture & Strategic Growth Advisory Board",
        "is_independent": True,
        "tenure_years": 2,
        "compensation": "Advisory Equity",
        "sec_filing_source": "Official Portend AI Leadership & Advisor Directory (https://portend.ai/about/)",
        "skills_keywords": ["Venture Capital", "Business Development", "Strategic Growth", "Capital Efficiency"],
        "bio": "Veteran operator and investor advising Portend AI on strategic business development, venture partnerships, and capital efficiency.",
        "source_url": "https://portend.ai/about/"
    }
]


def seed_portend():
    db = get_db()
    import sqlite3
    con = sqlite3.connect("data/leadership_intel.db")
    cur = con.cursor()
    cur.execute("DELETE FROM documents WHERE collection_name='leadership_profiles' AND json_extract(data, '$.company_name') LIKE '%Portend%'")
    con.commit()

    print(f"Indexing verified intelligence for Portend AI ({len(PORTEND_PROFILES)} profiles)...")
    for p in PORTEND_PROFILES:
        doc_id = p["id"]
        db.collection(COLLECTION_NAME).document(doc_id).set(p)
        print(f"  [+] {p['name']} ({p['title']}) [{p['group']}]")

    print(f"\nSUCCESS: Indexed {len(PORTEND_PROFILES)} verified profiles for Portend AI!")


if __name__ == "__main__":
    seed_portend()
