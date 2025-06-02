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
    assert len(results["documents"]) > 0


def test_delete_documents(vector_db):
    documents = ["Document 1", "Document 2"]
    document_ids = ["test_delete_1", "test_delete_2"]
    vector_db.add_documents(documents, ids=document_ids)

    # 문서 추가 확인
    assert vector_db.get_collection_count() == 2

    # 문서 삭제
    result = vector_db.delete_documents(document_ids)
    assert result is True
    assert vector_db.get_collection_count() == 0

def test_update_document(vector_db):
    documents = ["Document 1"]
    ids = ["test_doc_1"]
    vector_db.add_documents(documents, ids=ids)

    # 저장된 문서 확인
    results = vector_db.collection.get(ids=["test_doc_1"])
    assert len(results["ids"]) > 0

    document_id = results["ids"][0]
    result = vector_db.update_document(document_id, "Updated Document 1")
    assert result is True

    # 업데이트된 문서 확인
    updated_results = vector_db.collection.get(ids=[document_id])
    assert updated_results["documents"][0] == "Updated Document 1"
