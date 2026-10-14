"""Unit tests for app.db local Firestore and Storage adapters."""

import pytest
from app.db import LocalFirestoreClient, LocalStorageClient


def test_local_firestore_crud(tmp_path):
    db_file = tmp_path / "test.db"
    client = LocalFirestoreClient(db_path=db_file)
    coll = client.collection("test_coll")

    # Set document
    doc_ref = coll.document("doc1")
    doc_ref.set({"name": "Test Company", "rating": 5})

    # Get document
    snap = doc_ref.get()
    assert snap.exists is True
    assert snap.to_dict()["name"] == "Test Company"
    assert snap.to_dict()["rating"] == 5

    # Merge update
    doc_ref.set({"rating": 4, "category": "Tech"}, merge=True)
    snap_merged = doc_ref.get()
    assert snap_merged.to_dict()["name"] == "Test Company"
    assert snap_merged.to_dict()["rating"] == 4
    assert snap_merged.to_dict()["category"] == "Tech"

    # Stream all
    docs = list(coll.stream())
    assert len(docs) == 1
    assert docs[0].id == "doc1"

    # Where filter
    matching = list(coll.where("category", "==", "Tech").stream())
    assert len(matching) == 1
    unmatched = list(coll.where("category", "==", "Finance").stream())
    assert len(unmatched) == 0

    # Delete
    doc_ref.delete()
    assert doc_ref.get().exists is False


def test_local_storage(tmp_path):
    storage = LocalStorageClient(base_dir=tmp_path / "storage")
    bucket = storage.bucket("test-bucket")
    blob = bucket.blob("folder/file.txt")

    blob.upload_from_string("hello world", content_type="text/plain")
    assert blob.download_as_bytes() == b"hello world"
