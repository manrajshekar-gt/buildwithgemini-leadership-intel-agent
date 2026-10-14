"""Seed script for Firestore with sample leadership and governance data."""

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db import get_db, COLLECTION_NAME, PROJECT_ID

SEEDED_PROFILES = [
    {
        "id": "alphabet-sundar-pichai",
        "company_name": "Alphabet Inc.",
        "company_url": "https://abc.xyz",
        "company_linkedin_url": "https://www.linkedin.com/company/google",
        "name": "Sundar Pichai",
        "title": "Chief Executive Officer",
        "group": "Executive Management",
        "email": "sundar@google.com",
        "linkedin_url": "https://www.linkedin.com/in/sundarpichai",
        "bio": "Sundar Pichai is the CEO of Alphabet and Google.",
        "committee": None,
        "is_independent": False,
        "tenure_years": 10,
        "source_url": "https://abc.xyz/investor/board-and-management/",
    },
    {
        "id": "alphabet-ruth-porat",
        "company_name": "Alphabet Inc.",
        "company_url": "https://abc.xyz",
        "company_linkedin_url": "https://www.linkedin.com/company/google",
        "name": "Ruth Porat",
        "title": "President & Chief Investment Officer",
        "group": "Executive Management",
        "email": "ruth@google.com",
        "linkedin_url": "https://www.linkedin.com/in/ruth-porat-8b7768297",
        "bio": "Ruth Porat oversees Alphabet's other bets and investment portfolio.",
        "committee": None,
        "is_independent": False,
        "tenure_years": 9,
        "source_url": "https://abc.xyz/investor/board-and-management/",
    },
    {
        "id": "alphabet-john-hennessy",
        "company_name": "Alphabet Inc.",
        "company_url": "https://abc.xyz",
        "company_linkedin_url": "https://www.linkedin.com/company/google",
        "name": "John L. Hennessy",
        "title": "Chairman of the Board of Directors",
        "group": "Board of Directors",
        "email": "hennessy@stanford.edu",
        "linkedin_url": "https://www.linkedin.com/in/john-hennessy-5b838914",
        "bio": "John L. Hennessy has served as the Chairman of the Board since 2018.",
        "committee": "Nominating and Corporate Governance",
        "is_independent": True,
        "tenure_years": 19,
        "source_url": "https://abc.xyz/investor/board-and-management/",
    },
    {
        "id": "alphabet-l-john-doerr",
        "company_name": "Alphabet Inc.",
        "company_url": "https://abc.xyz",
        "company_linkedin_url": "https://www.linkedin.com/company/google",
        "name": "L. John Doerr",
        "title": "Director",
        "group": "Board of Directors",
        "email": "jdoerr@kpcb.com",
        "linkedin_url": "https://www.linkedin.com/in/johndoerr",
        "bio": "General Partner of Kleiner Perkins, served on Alphabet Board since 1999.",
        "committee": "Audit Committee",
        "is_independent": True,
        "tenure_years": 25,
        "source_url": "https://abc.xyz/investor/board-and-management/",
    },
    {
        "id": "microsoft-satya-nadella",
        "company_name": "Microsoft Corporation",
        "company_url": "https://microsoft.com",
        "company_linkedin_url": "https://www.linkedin.com/company/microsoft",
        "name": "Satya Nadella",
        "title": "Chairman and Chief Executive Officer",
        "group": "Executive Management",
        "email": "satya.nadella@microsoft.com",
        "linkedin_url": "https://www.linkedin.com/in/satyanadella",
        "bio": "Satya Nadella is Chairman and CEO of Microsoft.",
        "committee": None,
        "is_independent": False,
        "tenure_years": 10,
        "source_url": "https://www.microsoft.com/en-us/investor/leadership",
    },
    {
        "id": "microsoft-sandra-peterson",
        "company_name": "Microsoft Corporation",
        "company_url": "https://microsoft.com",
        "company_linkedin_url": "https://www.linkedin.com/company/microsoft",
        "name": "Sandra E. Peterson",
        "title": "Lead Independent Director",
        "group": "Board of Directors",
        "email": "speterson@cdr-inc.com",
        "linkedin_url": "https://www.linkedin.com/in/sandra-peterson-a5796a1b",
        "bio": "Operating Partner at Clayton, Dubilier & Rice, Lead Independent Director.",
        "committee": "Governance and Nominating Committee",
        "is_independent": True,
        "tenure_years": 9,
        "source_url": "https://www.microsoft.com/en-us/investor/leadership",
    },
]


def seed():
    print(f"Connecting to database for project / local store (project={PROJECT_ID})...")
    db = get_db()
    collection_ref = db.collection(COLLECTION_NAME)

    for item in SEEDED_PROFILES:
        doc_id = item["id"]
        doc_ref = collection_ref.document(doc_id)
        doc_ref.set(item)
        print(f"Seeded: {item['name']} <{item.get('email')}> ({item['group']}) at {item['company_name']}")

    print("Firestore seeding completed successfully!")


if __name__ == "__main__":
    seed()
