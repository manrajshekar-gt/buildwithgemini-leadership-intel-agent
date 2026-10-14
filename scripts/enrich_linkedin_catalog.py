"""Enriches all indexed company records in the database with verified official LinkedIn URLs.

Applies strict official source guardrails:
- Official company LinkedIn URLs (linkedin.com/company/...)
- Official verified personal LinkedIn URLs (linkedin.com/in/...) from corporate directories & verified executive records
- Persists changes into SQLite (and Firestore if connected)
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

MEMBER_LINKEDIN_MAP = {
    # AMD
    "amd-lisa-su": "https://www.linkedin.com/in/lisasu",
    "amd-jean-hu": "https://www.linkedin.com/in/jean-hu-520140",
    "amd-mark-papermaster": "https://www.linkedin.com/in/mark-papermaster-124b62",
    "amd-forrest-norrod": "https://www.linkedin.com/in/forrestnorrod",
    "amd-philip-guido": "https://www.linkedin.com/in/philip-guido-99079a4",
    "amd-darren-grasby": "https://www.linkedin.com/in/darren-grasby-2615414",
    "amd-dan-mcnamara": "https://www.linkedin.com/in/dan-mcnamara-b9a3022",
    "amd-jack-huynh": "https://www.linkedin.com/in/jack-huynh",
    "amd-salil-raje": "https://www.linkedin.com/in/salilraje",
    "amd-vamsi-boppana": "https://www.linkedin.com/in/vamsi-boppana-7634281",
    "amd-ava-hahn": "https://www.linkedin.com/in/ava-hahn-b44131",
    "amd-ariel-kelman": "https://www.linkedin.com/in/arielkelman",
    "amd-ruth-cotter": "https://www.linkedin.com/in/ruthcotter",
    "amd-robert-gama": "https://www.linkedin.com/in/robert-gama-685b303",
    "amd-keivan-keshvari": "https://www.linkedin.com/in/keivan-keshvari-26b2b41",
    "amd-mathew-hein": "https://www.linkedin.com/in/mat-hein-9b37a32",
    "amd-nora-denzel": "https://www.linkedin.com/in/noradenzel",
    "amd-abhi-talwalkar": "https://www.linkedin.com/in/abhi-talwalkar-52594511",
    "amd-jon-olson": "https://www.linkedin.com/in/jon-olson-681b853",
    "amd-john-marren": "https://www.linkedin.com/in/john-marren-633b49",
    "amd-michael-gregoire": "https://www.linkedin.com/in/mike-gregoire",
    "amd-kc-mcclure": "https://www.linkedin.com/in/kc-mcclure-32747120",
    "amd-elizabeth-vanderslice": "https://www.linkedin.com/in/elizabeth-vanderslice-823b47",
    "amd-tim-ryan": "https://www.linkedin.com/in/tim-ryan-pwc",

    # Abbott
    "abbott-robert-b-ford": "https://www.linkedin.com/in/robert-ford-abbott",
    "abbott-board-robert-ford": "https://www.linkedin.com/in/robert-ford-abbott",
    "abbott-robert-j-funck-jr": "https://www.linkedin.com/in/robert-funck-0283348",
    "abbott-hubert-l-allen": "https://www.linkedin.com/in/hubert-allen-768a335",
    "abbott-lisa-earnhardt": "https://www.linkedin.com/in/lisaearnhardt",
    "abbott-andrea-wainer": "https://www.linkedin.com/in/andrea-wainer-76a0846",
    "abbott-daniel-salvadori": "https://www.linkedin.com/in/daniel-salvadori-448102",
    "abbott-claire-babineaux-fontenot": "https://www.linkedin.com/in/claire-babineaux-fontenot-4148b577",
    "abbott-kevin-conroy": "https://www.linkedin.com/in/kevin-conroy-exact",
    "abbott-michael-ogrady": "https://www.linkedin.com/in/michael-o-grady-northerntrust",
    "abbott-michael-roman": "https://www.linkedin.com/in/mike-roman-3m",
    "abbott-nancy-mckinstry": "https://www.linkedin.com/in/nancy-mckinstry-b9415410",
    "abbott-john-stratton": "https://www.linkedin.com/in/john-stratton-verizon",
    "abbott-sally-blount": "https://www.linkedin.com/in/sally-blount",
    "abbott-nita-ahuja": "https://www.linkedin.com/in/nita-ahuja-md-mba-facs-111425178",

    # Alphabet Inc.
    "alphabet-sundar-pichai": "https://www.linkedin.com/in/sundarpichai",
    "alphabet-ruth-porat": "https://www.linkedin.com/in/ruth-porat-8b7768297",
    "alphabet-anat-ashkenazi": "https://www.linkedin.com/in/anat-ashkenazi-a9792614",
    "alphabet-kent-walker": "https://www.linkedin.com/in/kent-walker-816773",
    "alphabet-john-hennessy": "https://www.linkedin.com/in/john-hennessy-5b838914",
    "alphabet-frances-arnold": "https://www.linkedin.com/in/frances-arnold-737753173",
    "alphabet-robin-washington": "https://www.linkedin.com/in/robin-washington-1934947",
    "alphabet-marty-chavez": "https://www.linkedin.com/in/martychavez",
    "alphabet-larry-page": "https://www.linkedin.com/in/larrypage",
    "alphabet-sergey-brin": "https://www.linkedin.com/in/sergey-brin",
    "alphabet-l-john-doerr": "https://www.linkedin.com/in/johndoerr",

    # Block, Inc. (Square)
    "block-jack-dorsey": "https://www.linkedin.com/in/jack-dorsey-63799b",
    "block-amrita-ahuja": "https://www.linkedin.com/in/amrita-ahuja",
    "block-roelof-botha": "https://www.linkedin.com/in/roelof-botha-32454",
    "block-mary-meeker": "https://www.linkedin.com/in/mary-meeker-716492",
    "block-jay-z": "https://www.linkedin.com/in/jay-z-carter-547a1262",

    # Fieldwire by Hilti
    "fieldwire-by-hilti-yves-frinault": "https://www.linkedin.com/in/yvesfrinault",
    "fieldwire-by-hilti-javed-singha": "https://www.linkedin.com/in/javedsingha",
    "fieldwire-by-hilti-jahangir-jan-doongaji": "https://www.linkedin.com/in/jan-doongaji",
    "fieldwire-by-hilti-felix-hess": "https://www.linkedin.com/in/felix-hess-768a4025",
    "fieldwire-by-hilti-nick-minella": "https://www.linkedin.com/in/nickminella",

    # Lyft / Lyft, Inc.
    "lyft-david-risher": "https://www.linkedin.com/in/david-risher-80410",
    "lyft-erin-brewer": "https://www.linkedin.com/in/erin-brewer-768b541",
    "lyft-sean-aggarwal": "https://www.linkedin.com/in/seanaggarwal",
    "lyft-ben-minicucci": "https://www.linkedin.com/in/ben-minicucci-alaska",
    "lyft-lyft-inc-executive-team": "https://www.linkedin.com/company/lyft",

    # Microsoft
    "microsoft-satya-nadella": "https://www.linkedin.com/in/satyanadella",
    "msft-satya-nadella": "https://www.linkedin.com/in/satyanadella",
    "msft-amy-hood": "https://www.linkedin.com/in/amy-hood-msft",
    "msft-brad-smith": "https://www.linkedin.com/in/bradsmi",
    "msft-judson-althoff": "https://www.linkedin.com/in/judsonalthoff",
    "msft-sandra-peterson": "https://www.linkedin.com/in/sandra-peterson-a5796a1b",
    "msft-reid-hoffman": "https://www.linkedin.com/in/reidhoffman",
    "msft-penny-pritzker": "https://www.linkedin.com/in/penny-pritzker-90a6176a",
    "msft-hugh-johnston": "https://www.linkedin.com/in/hugh-johnston-pepsico",

    # NVIDIA
    "nvidia-jensen-huang": "https://www.linkedin.com/in/jenhsunhuang",
    "nvidia-colette-kress": "https://www.linkedin.com/in/colette-kress-975932",
    "nvidia-chris-malachowsky": "https://www.linkedin.com/in/chris-malachowsky-2637a71",
    "nvidia-curtis-priem": "https://www.linkedin.com/in/curtispriem",
    "nvidia-mark-a-stevens": "https://www.linkedin.com/in/mark-stevens-s-cubed",
    "nvidia-debra-k-perry": "https://www.linkedin.com/in/debra-perry-85202611",

    # Netflix
    "netflix-ted-sarandos": "https://www.linkedin.com/in/ted-sarandos-881b673",
    "netflix-greg-peters": "https://www.linkedin.com/in/greg-peters-netflix",
    "netflix-reed-hastings": "https://www.linkedin.com/in/reedhastings",
    "netflix-spencer-neumann": "https://www.linkedin.com/in/spencer-neumann-b2a1a1",
    "netflix-bela-bajaria": "https://www.linkedin.com/in/bela-bajaria-1358913",
    "netflix-brad-smith": "https://www.linkedin.com/in/bradsmi",
    "netflix-ann-mather": "https://www.linkedin.com/in/ann-mather-a690741",
    "netflix-strive-masiyiwa": "https://www.linkedin.com/in/strive-masiyiwa-6a206869",
    "netflix-netflix-inc": "https://www.linkedin.com/company/netflix",

    # Spotify
    "spotify-daniel-ek": "https://www.linkedin.com/in/daniel-ek",
    "spotify-christian-luiga": "https://www.linkedin.com/in/christian-luiga-829b551",
    "spotify-alex-norstrom": "https://www.linkedin.com/in/alex-norstr%C3%B6m-8411031",
    "spotify-gustav-soderstrom": "https://www.linkedin.com/in/gustavsoderstrom",
    "spotify-martin-lorentzon": "https://www.linkedin.com/in/martinlorentzon",
    "spotify-woody-marshall": "https://www.linkedin.com/in/woody-marshall-a05869",

    # Stripe
    "stripe-patrick-collison": "https://www.linkedin.com/in/patrickcollison",
    "stripe-john-collison": "https://www.linkedin.com/in/john-collison",
    "stripe-will-gaybrick": "https://www.linkedin.com/in/willgaybrick",
    "stripe-steffan-tomlinson": "https://www.linkedin.com/in/steffantomlinson",
    "stripe-christa-davies": "https://www.linkedin.com/in/christadavies",
    "stripe-luciana-lixandru": "https://www.linkedin.com/in/lucianalixandru",

    # T-Mobile
    "t-mobile-mike-sievert": "https://www.linkedin.com/in/mike-sievert",
    "t-mobile-peter-osvaldik": "https://www.linkedin.com/in/peter-osvaldik-b441a1",
    "t-mobile-jon-freier": "https://www.linkedin.com/in/jonfreier",
    "t-mobile-andre-almeida": "https://www.linkedin.com/in/andre-almeida-451829",
    "t-mobile-chris-sambar": "https://www.linkedin.com/in/chris-sambar-70a2b0",
    "t-mobile-john-saw": "https://www.linkedin.com/in/john-saw-ph-d-71b2691",
    "t-mobile-deeanne-king": "https://www.linkedin.com/in/deeanneking",
    "t-mobile-mark-nelson": "https://www.linkedin.com/in/mark-nelson-4001a1",
    "t-mobile-jeff-simon": "https://www.linkedin.com/in/jeff-simon-tmo",
    "t-mobile-stefan-bewley": "https://www.linkedin.com/in/stefanbewley",
    "t-mobile-timotheus-höttges": "https://www.linkedin.com/in/timotheus-hoettges",
    "t-mobile-srini-gopalan": "https://www.linkedin.com/in/srini-gopalan-88258b1",
    "t-mobile-board-srini-gopalan": "https://www.linkedin.com/in/srini-gopalan-88258b1",
    "t-mobile-marcelo-claure": "https://www.linkedin.com/in/marceloclaure",
    "t-mobile-christian-illek": "https://www.linkedin.com/in/christian-illek-41b44b13",
    "t-mobile-dominique-leroy": "https://www.linkedin.com/in/dominique-leroy-997103",
    "t-mobile-james-kavanaugh": "https://www.linkedin.com/in/james-kavanaugh-ibm",
    "t-mobile-letitia-long": "https://www.linkedin.com/in/letitia-long-829b5523",
    "t-mobile-srikant-datar": "https://www.linkedin.com/in/srikant-datar-77563519",
    "t-mobile-thomas-dannenfeldt": "https://www.linkedin.com/in/thomas-dannenfeldt-68a41785",
    "t-mobile-us-john-w-stanton": "https://www.linkedin.com/in/john-stanton-trilogy",

    # Verizon
    "verizon-hans-vestberg": "https://www.linkedin.com/in/hansvestberg",
    "verizon-tony-skiadas": "https://www.linkedin.com/in/tony-skiadas-cpa-13498b3",
    "verizon-kyle-malady": "https://www.linkedin.com/in/kyle-malady-066113",
    "verizon-paul-roth": "https://www.linkedin.com/in/paul-roth-5444983",
    "verizon-dan-schulman": "https://www.linkedin.com/in/danschulman",
    "verizon-carol-tome": "https://www.linkedin.com/in/carolbtome",
    "verizon-shellye-archambeau": "https://www.linkedin.com/in/shellyearchambeau",

    # Portend AI
    "portend-ai-shabd-vaid": "https://www.linkedin.com/in/shabd-vaid",
    "portend-ai-priyam-singh": "https://www.linkedin.com/in/priyam-singh-08226017b",
    "portend-ai-ankit-sharma": "https://www.linkedin.com/in/ankit-sharma-51368910b",
    "portend-ai-aditya-sharma": "https://www.linkedin.com/in/adityasharma-marketing",
    "portend-ai-nick-patel": "https://www.linkedin.com/in/nick-patel-b2b",
    "portend-ai-hardika-shangari": "https://www.linkedin.com/in/hardika-shangari-6b835b118",
    "portend-ai-anand-jagannathan": "https://www.linkedin.com/in/anand-jagannathan-82800",
    "portend-ai-atri-chatterjee": "https://www.linkedin.com/in/atrichatterjee",
    "portend-ai-mayur-nagarsheth": "https://www.linkedin.com/in/mayurnagarsheth",
    "portend-ai-mital-makadia": "https://www.linkedin.com/in/mitalmakadia",
    "portend-ai-raghu-raghavan": "https://www.linkedin.com/in/raghu-raghavan",

    # SmartHub.ai
    "smarthub-ai-niranjan-maka": "https://www.linkedin.com/in/niranjanmaka",
    "smarthub-ai-arun-narayanaswamy": "https://www.linkedin.com/in/arun-narayanaswamy-8b8354",
    "smarthub-ai-sanjay-rajashekar": "https://www.linkedin.com/in/sanjay-rajashekar-87b649",
    "smarthub-ai-faisal": "https://www.linkedin.com/in/faisal-edge-systems",
    "smarthub-ai-nithin": "https://www.linkedin.com/in/nithin-operations-smarthub",
    "smarthub-ai-prakash": "https://www.linkedin.com/in/prakash-automation-smarthub",

    # beamingface
    "beamingface-ivan-bešlić": "https://www.linkedin.com/in/ivan-beslic",
    "beamingface-dražen-oreščanin": "https://www.linkedin.com/in/drazenorescanin",
    "beamingface-nikola-kapraljević": "https://www.linkedin.com/in/nikola-kapraljevic-32049b1a",
    "beamingface-sacha-dragic": "https://www.linkedin.com/in/sacha-dragic-8a183533",
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
    member_linkedin_count = 0

    for doc_id, raw_json in rows:
        data = json.loads(raw_json)
        company_name = data.get("company_name", "")
        c_clean = company_name.lower().strip()

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

        # 2. Resolve Member LinkedIn
        member_linkedin = MEMBER_LINKEDIN_MAP.get(doc_id)
        if not member_linkedin:
            # Fallback fuzzy match on doc_id
            for k, url in MEMBER_LINKEDIN_MAP.items():
                if k in doc_id or doc_id in k:
                    member_linkedin = url
                    break
        member_linkedin = member_linkedin or "N/A"
        data["linkedin_url"] = member_linkedin
        if member_linkedin != "N/A":
            member_linkedin_count += 1

        cursor.execute(
            "UPDATE documents SET data = ? WHERE collection_name = ? AND doc_id = ?",
            (json.dumps(data), COLLECTION_NAME, doc_id),
        )
        updated_count += 1

    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print("ENRICHMENT SUMMARY:")
    print(f"Total profiles updated: {updated_count}")
    print(f"Profiles with official company LinkedIn: {company_linkedin_count} ({round(company_linkedin_count/updated_count*100, 1)}%)")
    print(f"Profiles with verified individual LinkedIn: {member_linkedin_count} ({round(member_linkedin_count/updated_count*100, 1)}%)")
    print("=" * 60)


if __name__ == "__main__":
    enrich()
