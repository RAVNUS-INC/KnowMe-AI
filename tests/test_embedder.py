import pytest
from src.embedding.embedder import Embedder  # Adjust the import based on your actual class name

@pytest.fixture
def embedder():
    return Embedder()  # Initialize your embedder class here

def test_embedding_generation(embedder):
    texts = ["Hello, world!", "This is a test."]
    embeddings = embedder.generate_embeddings(texts)
    
    assert len(embeddings) == len(texts)
    assert all(isinstance(embedding, list) for embedding in embeddings)
    assert all(len(embedding) > 0 for embedding in embeddings)

def test_embedding_shape(embedder):
    texts = ["Test embedding shape."]
    embeddings = embedder.generate_embeddings(texts)
    
    assert len(embeddings) == 1
    assert len(embeddings[0]) == embedder.embedding_dimension  # Replace with actual dimension if needed

def test_invalid_input(embedder):
    with pytest.raises(ValueError):
        embedder.generate_embeddings(None)  # Adjust based on your error handling logic

    with pytest.raises(ValueError):
        embedder.generate_embeddings([])  # Adjust based on your error handling logic