import os
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.rag.embeddings import embed_text, embed_documents
from app.rag.loaders import load_knowledge_base_documents
from app.rag.cleaner import clean_text
from app.rag.chunker import chunk_document

KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "knowledge_base")


def retrieve_relevant_chunks(
    query: str,
    top_k: int = 5,
    similarity_threshold: float = 0.35,
    supplier_filter: Optional[str] = None,
    doc_type_filter: Optional[str] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Performs vector similarity search over document_chunks using 384-dim dense query embeddings.
    Uses pgvector cosine distance (<=>) with graceful numpy fallback if DB session is unseeded/offline.
    """
    if not query or not query.strip():
        raise ValueError("Query string cannot be empty.")

    if top_k <= 0 or top_k > 20:
        raise ValueError("top_k must be between 1 and 20.")

    query_vec = embed_text(query)
    results = []

    # Attempt PostgreSQL pgvector retrieval
    if db is not None:
        try:
            from app.database.models import DocumentChunk
            query_expr = db.query(
                DocumentChunk,
                (1 - DocumentChunk.embedding.cosine_distance(query_vec)).label("similarity")
            )

            if doc_type_filter:
                query_expr = query_expr.filter(DocumentChunk.document_type == doc_type_filter)

            raw_results = query_expr.order_by(text("similarity DESC")).limit(top_k * 2).all()

            for chunk, sim in raw_results:
                sim_val = float(sim)
                if sim_val >= similarity_threshold:
                    meta = chunk.doc_metadata or {}
                    if supplier_filter and meta.get("supplier", "").lower() != supplier_filter.lower():
                        continue

                    results.append({
                        "chunk_id": chunk.id,
                        "document_name": chunk.document_name,
                        "document_type": chunk.document_type,
                        "chunk_index": chunk.chunk_index,
                        "content": chunk.content,
                        "similarity": round(sim_val, 4),
                        "metadata": meta
                    })

                    if len(results) >= top_k:
                        break
        except Exception:
            results = []

    # Fallback to local numpy cosine similarity search over knowledge_base if DB returned no results
    if not results and os.path.exists(KNOWLEDGE_BASE_DIR):
        docs = load_knowledge_base_documents(KNOWLEDGE_BASE_DIR)
        all_chunks = []
        for doc in docs:
            cleaned = clean_text(doc["content"])
            doc["content"] = cleaned
            all_chunks.extend(chunk_document(doc))

        if all_chunks:
            texts = [c["content"] for c in all_chunks]
            chunk_vecs = np.array(embed_documents(texts))
            q_vec = np.array(query_vec)

            # Cosine similarity = dot(A, B) / (norm(A) * norm(B))
            sims = np.dot(chunk_vecs, q_vec)

            scored_chunks = []
            for idx, (chunk, sim_val) in enumerate(zip(all_chunks, sims)):
                sim_float = float(sim_val)
                meta = chunk.get("metadata", {})

                if doc_type_filter and chunk["document_type"] != doc_type_filter:
                    continue
                if supplier_filter and meta.get("supplier", "").lower() != supplier_filter.lower():
                    continue

                if sim_float >= similarity_threshold:
                    scored_chunks.append({
                        "chunk_id": idx + 1,
                        "document_name": chunk["document_name"],
                        "document_type": chunk["document_type"],
                        "chunk_index": chunk["chunk_index"],
                        "content": chunk["content"],
                        "similarity": round(sim_float, 4),
                        "metadata": meta
                    })

            scored_chunks.sort(key=lambda x: x["similarity"], reverse=True)
            results = scored_chunks[:top_k]

    return {
        "query": query,
        "top_k": top_k,
        "total_retrieved": len(results),
        "results": results
    }
