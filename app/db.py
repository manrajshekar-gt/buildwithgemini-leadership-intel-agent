"""Unified Database, Storage, and AI Client provider with GCP & Local Fallback.

Provides transparent fallback to SQLite and local disk storage when Google Cloud
credentials (ADC / Firestore / Cloud Storage) are not configured, enabling 100%
local development while supporting production GCP when credentials are provided.
"""

import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

from dotenv import load_dotenv
from google import genai

load_dotenv()

logger = logging.getLogger(__name__)

# Constants and Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-04-a0fc456f3f90")
COLLECTION_NAME = os.getenv("FIRESTORE_COLLECTION", "leadership_profiles")
CONFIG_COLLECTION = "system_configurations"
BUCKET_NAME = os.getenv("ASSET_BUCKET_NAME", "leadership-intel-assets-9698")
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "leadership_intel.db"

_firestore_client = None
_storage_client = None
_genai_client = None


# =====================================================================
# LOCAL FIRESTORE-COMPATIBLE ADAPTER (SQLite Backed)
# =====================================================================

class LocalDocumentSnapshot:
    """Emulates a Firestore DocumentSnapshot."""

    def __init__(self, doc_id: str, data: Optional[Dict[str, Any]]):
        self.id = doc_id
        self._data = data

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data) if self._data else {}


class LocalDocumentReference:
    """Emulates a Firestore DocumentReference."""

    def __init__(self, db: "LocalFirestoreClient", collection_name: str, doc_id: str):
        self.db = db
        self.collection_name = collection_name
        self.id = doc_id

    def get(self) -> LocalDocumentSnapshot:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT data FROM documents WHERE collection_name = ? AND doc_id = ?",
                (self.collection_name, self.id),
            )
            row = cursor.fetchone()
            if row:
                return LocalDocumentSnapshot(self.id, json.loads(row[0]))
            return LocalDocumentSnapshot(self.id, None)

    def set(self, data: Dict[str, Any], merge: bool = False) -> None:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            if merge:
                cursor.execute(
                    "SELECT data FROM documents WHERE collection_name = ? AND doc_id = ?",
                    (self.collection_name, self.id),
                )
                row = cursor.fetchone()
                if row:
                    existing = json.loads(row[0])
                    existing.update(data)
                    data = existing
            cursor.execute(
                """
                INSERT INTO documents (collection_name, doc_id, data)
                VALUES (?, ?, ?)
                ON CONFLICT(collection_name, doc_id) DO UPDATE SET data = excluded.data
                """,
                (self.collection_name, self.id, json.dumps(data)),
            )
            conn.commit()

    def delete(self) -> None:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM documents WHERE collection_name = ? AND doc_id = ?",
                (self.collection_name, self.id),
            )
            conn.commit()


class LocalCollectionReference:
    """Emulates a Firestore CollectionReference / Query."""

    def __init__(self, db: "LocalFirestoreClient", collection_name: str, filters: Optional[List[tuple]] = None):
        self.db = db
        self.collection_name = collection_name
        self.filters = filters or []

    def document(self, doc_id: str) -> LocalDocumentReference:
        return LocalDocumentReference(self.db, self.collection_name, doc_id)

    def where(self, field: str, op: str, value: Any) -> "LocalCollectionReference":
        new_filters = list(self.filters)
        new_filters.append((field, op, value))
        return LocalCollectionReference(self.db, self.collection_name, new_filters)

    def stream(self) -> Iterator[LocalDocumentSnapshot]:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT doc_id, data FROM documents WHERE collection_name = ?",
                (self.collection_name,),
            )
            for row in cursor.fetchall():
                doc_id, raw_data = row[0], json.loads(row[1])
                matches = True
                for field, op, val in self.filters:
                    field_val = raw_data.get(field)
                    if op in ("==", "=") and field_val != val:
                        matches = False
                        break
                if matches:
                    yield LocalDocumentSnapshot(doc_id, raw_data)


class LocalFirestoreClient:
    """SQLite-backed fallback for Firestore."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    collection_name TEXT NOT NULL,
                    doc_id TEXT NOT NULL,
                    data TEXT NOT NULL,
                    PRIMARY KEY (collection_name, doc_id)
                )
                """
            )
            conn.commit()
        self._seed_default_data()

    def _seed_default_data(self) -> None:
        # Check if leadership_profiles has any documents
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM documents WHERE collection_name = ?",
                (COLLECTION_NAME,),
            )
            count = cursor.fetchone()[0]
            if count == 0:
                try:
                    from seed_firestore import SEEDED_PROFILES
                    for p in SEEDED_PROFILES:
                        doc_id = p.get("id") or f"{p.get('company_name')}-{p.get('name')}"
                        cursor.execute(
                            "INSERT OR IGNORE INTO documents (collection_name, doc_id, data) VALUES (?, ?, ?)",
                            (COLLECTION_NAME, doc_id, json.dumps(p)),
                        )
                    conn.commit()
                    logger.info("Auto-seeded %d profiles into local database.", len(SEEDED_PROFILES))
                except Exception as e:
                    logger.warning("Could not auto-seed local database: %s", e)

    def collection(self, name: str) -> LocalCollectionReference:
        return LocalCollectionReference(self, name)


# =====================================================================
# LOCAL CLOUD STORAGE ADAPTER
# =====================================================================

class LocalBlob:
    """Emulates a Cloud Storage Blob."""

    def __init__(self, bucket: "LocalBucket", name: str):
        self.bucket = bucket
        self.name = name
        self.local_file_path = self.bucket.storage_dir / name

    def upload_from_string(self, data: Union[str, bytes], content_type: Optional[str] = None) -> None:
        self.local_file_path.parent.mkdir(parents=True, exist_ok=True)
        mode = "wb" if isinstance(data, bytes) else "w"
        with open(self.local_file_path, mode) as f:
            f.write(data)

    def download_as_bytes(self) -> bytes:
        with open(self.local_file_path, "rb") as f:
            return f.read()


class LocalBucket:
    """Emulates a Cloud Storage Bucket."""

    def __init__(self, name: str, storage_dir: Path):
        self.name = name
        self.storage_dir = storage_dir

    def blob(self, name: str) -> LocalBlob:
        return LocalBlob(self, name)


class LocalStorageClient:
    """Local disk fallback for Google Cloud Storage."""

    def __init__(self, base_dir: Path = DATA_DIR / "storage"):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def bucket(self, name: str) -> LocalBucket:
        bucket_dir = self.base_dir / name
        bucket_dir.mkdir(parents=True, exist_ok=True)
        return LocalBucket(name, bucket_dir)


# =====================================================================
# CLIENT FACTORIES
# =====================================================================

def get_db():
    """Returns a Firestore client or LocalFirestoreClient fallback."""
    global _firestore_client
    if _firestore_client is not None:
        return _firestore_client

    # Check if forced local
    force_local = os.getenv("USE_LOCAL_DB", "").lower() in ("true", "1")
    if not force_local:
        try:
            from google.cloud import firestore
            client = firestore.Client(project=PROJECT_ID)
            # Test connectivity
            _ = list(client.collection(COLLECTION_NAME).limit(1).stream())
            _firestore_client = client
            logger.info("Connected to Google Cloud Firestore (project=%s)", PROJECT_ID)
            return _firestore_client
        except Exception as e:
            logger.warning("Could not connect to Cloud Firestore (%s). Using local SQLite database.", e)

    _firestore_client = LocalFirestoreClient()
    return _firestore_client


def get_firestore_client():
    """Alias for get_db()."""
    return get_db()


def get_storage():
    """Returns a Cloud Storage client or LocalStorageClient fallback."""
    global _storage_client
    if _storage_client is not None:
        return _storage_client

    force_local = os.getenv("USE_LOCAL_STORAGE", "").lower() in ("true", "1")
    if not force_local:
        try:
            from google.cloud import storage
            client = storage.Client(project=PROJECT_ID)
            _storage_client = client
            logger.info("Connected to Google Cloud Storage (project=%s)", PROJECT_ID)
            return _storage_client
        except Exception as e:
            logger.warning("Could not connect to Cloud Storage (%s). Using local storage fallback.", e)

    _storage_client = LocalStorageClient()
    return _storage_client


def get_storage_client():
    """Alias for get_storage()."""
    return get_storage()


def get_genai():
    """Returns a Google GenAI Client configured for Vertex AI or Google AI Studio."""
    global _genai_client
    if _genai_client is not None:
        return _genai_client

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in ("true", "1")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

    if gemini_api_key and not use_vertex:
        _genai_client = genai.Client(api_key=gemini_api_key)
        logger.info("Initialized Google GenAI client via Gemini API Key")
        return _genai_client

    try:
        _genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location=location)
        logger.info("Initialized Google GenAI client via Vertex AI (project=%s, location=%s)", PROJECT_ID, location)
        return _genai_client
    except Exception as e:
        if gemini_api_key:
            _genai_client = genai.Client(api_key=gemini_api_key)
            logger.info("Fallback to Google AI Studio via GEMINI_API_KEY")
            return _genai_client
        logger.warning("GenAI client initialization warning: %s", e)
        # Return standard client so errors surface when called
        _genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location=location)
        return _genai_client


def get_genai_client():
    """Alias for get_genai()."""
    return get_genai()
