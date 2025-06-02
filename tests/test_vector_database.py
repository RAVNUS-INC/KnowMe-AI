import pytest
from src.database.vector_database import ChromaVectorDB

@pytest.fixture
def vector_db():
    db = ChromaVectorDB()
    yield db
    db.delete_collection()

def test_add_documents(vector_db):
    documents = ["Document 1", "Document 2"]
    result = vector_db.add_documents(documents)
    assert result is True
    assert vector_db.get_collection_count() == 2

def test_similarity_search(vector_db):
    documents = ["Document 1", "Document 2"]
    vector_db.add_documents(documents)
    results = vector_db.similarity_search("Document 1")
    assert len(results['documents']) > 0

def test_delete_documents(vector_db):
    documents = ["Document 1", "Document 2"]
    vector_db.add_documents(documents)
    document_ids = [str(i) for i in range(2)]
    result = vector_db.delete_documents(document_ids)
    assert result is True
    assert vector_db.get_collection_count() == 0

def test_update_document(vector_db):
    documents = ["Document 1"]
    vector_db.add_documents(documents)
    document_id = vector_db.collection.get_ids()[0]
    result = vector_db.update_document(document_id, "Updated Document 1")
    assert result is True
    updated_doc = vector_db.collection.get_documents()[0]
    assert updated_doc == "Updated Document 1"