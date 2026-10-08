"""Seed script for Firestore with sample leadership and governance data."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-a0fc456f3f90"
COLLECTION_NAME = "leadership_profiles"

SEEDED_PROFILES = [
    {
        "id": "alphabet-sundar-pichai",
        "company_name": "Alphabet Inc.",
        "company_url": "https://abc.xyz",
        "name": "Sundar Pichai",
        "title": "Chief Executive Officer",
        "group": "Executive Management",
        "email": "sundar@google.com",
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
        "name": "Ruth Porat",
        "title": "President & Chief Investment Officer",
        "group": "Executive Management",
        "email": "ruth@google.com",
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
        "name": "John L. Hennessy",
        "title": "Chairman of the Board of Directors",
        "group": "Board of Directors",
        "email": "hennessy@stanford.edu",
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
        "name": "L. John Doerr",
        "title": "Director",
        "group": "Board of Directors",
        "email": "jdoerr@kpcb.com",
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
        "name": "Satya Nadella",
        "title": "Chairman and Chief Executive Officer",
        "group": "Executive Management",
        "email": "satya.nadella@microsoft.com",
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
        "name": "Sandra E. Peterson",
        "title": "Lead Independent Director",
        "group": "Board of Directors",
        "email": "speterson@cdr-inc.com",
        "bio": "Operating Partner at Clayton, Dubilier & Rice, Lead Independent Director.",
        "committee": "Governance and Nominating Committee",
        "is_independent": True,
        "tenure_years": 9,
        "source_url": "https://www.microsoft.com/en-us/investor/leadership",
    },
]


def seed():
    print(f"Connecting to Firestore for project: {PROJECT_ID}")
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection(COLLECTION_NAME)

    for item in SEEDED_PROFILES:
        doc_id = item["id"]
        doc_ref = collection_ref.document(doc_id)
        doc_ref.set(item)
        print(f"Seeded: {item['name']} <{item.get('email')}> ({item['group']}) at {item['company_name']}")

    print("Firestore seeding completed successfully!")


if __name__ == "__main__":
    seed()
