import pytest
import os
from fastapi.testclient import TestClient

from app.main import app
from app.rag.loaders import load_knowledge_base_documents
from app.rag.cleaner import clean_text
from app.rag.chunker import chunk_document
from app.rag.embeddings import embed_text, embed_documents
from app.rag.retriever import retrieve_relevant_chunks

client = TestClient(app)
# Correct path to root knowledge_base directory
KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "knowledge_base")


def test_document_loaders():
    docs = load_knowledge_base_documents(KNOWLEDGE_BASE_DIR)
    assert len(docs) >= 12
    for doc in docs:
        assert "document_name" in doc
        assert "document_type" in doc
        assert "content" in doc
        assert len(doc["content"]) > 0
        assert "metadata" in doc


def test_text_cleaner():
    raw_text = "   This is   a test   with \r\n multiple newlines \n\n\n and spaces.   "
    cleaned = clean_text(raw_text)
    assert "\r" not in cleaned
    assert "\n\n\n" not in cleaned
    assert "multiple newlines" in cleaned


def test_section_aware_chunker():
    sample_doc = {
        "document_name": "test_contract.md",
        "document_type": "contract",
        "content": "## Section 1\nThis is paragraph one under section one.\n\n## Section 2\nThis is paragraph two under section two.",
        "metadata": {"supplier": "TestCorp"}
    }
    chunks = chunk_document(sample_doc)
    assert len(chunks) == 2
    assert chunks[0]["document_name"] == "test_contract.md"
    assert chunks[0]["chunk_index"] == 1
    assert "Section 1" in chunks[0]["content"]
    assert chunks[1]["chunk_index"] == 2
    assert "Section 2" in chunks[1]["content"]


def test_embeddings_generation():
    text = "Supplier lead time penalty rate is 1.5% per week."
    vec = embed_text(text)
    assert isinstance(vec, list)
    assert len(vec) == 384
    assert all(isinstance(val, float) for val in vec)

    batch_vecs = embed_documents([text, "Safety stock policy"])
    assert len(batch_vecs) == 2
    assert len(batch_vecs[0]) == 384


def test_retriever_query():
    query = "What is the penalty for delivery delay in supplier contracts?"
    res = retrieve_relevant_chunks(query=query, top_k=3, similarity_threshold=0.01)
    assert res["query"] == query
    assert res["top_k"] == 3
    assert len(res["results"]) > 0
    top_result = res["results"][0]
    assert "document_name" in top_result
    assert "content" in top_result
    assert "similarity" in top_result


def test_hit_at_k_evaluation():
    # Test recall: querying about GlobalTech penalty should retrieve GlobalTech contract document chunks
    query = "GlobalTech Components penalty fee delivery delay"
    res = retrieve_relevant_chunks(query=query, top_k=5, similarity_threshold=0.01)
    retrieved_docs = [r["document_name"] for r in res["results"]]
    assert any("globaltech" in doc.lower() for doc in retrieved_docs)



def test_rag_api_endpoint():
    # Test valid RAG query POST request
    payload = {
        "query": "What is the minimum order quantity for Global Electronics?",
        "top_k": 3,
        "similarity_threshold": 0.01,
        "filters": {
            "supplier": "Global Electronics Corp"
        }
    }
    response = client.post("/api/v1/rag/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == payload["query"]
    assert data["top_k"] == 3
    assert "results" in data
    assert isinstance(data["results"], list)

    # Test validation error on empty query
    bad_payload = {
        "query": "",
        "top_k": 3
    }
    bad_response = client.post("/api/v1/rag/query", json=bad_payload)
    assert bad_response.status_code == 422  # Pydantic field validation error

