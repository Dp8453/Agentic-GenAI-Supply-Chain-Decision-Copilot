import os
import sys
from sqlalchemy import text

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database.connection import engine, SessionLocal
from app.database.base import Base
from app.database.models import DocumentChunk
from app.rag.loaders import load_knowledge_base_documents
from app.rag.cleaner import clean_text
from app.rag.chunker import chunk_document
from app.rag.embeddings import embed_documents

KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "knowledge_base")


def run_ingestion_pipeline() -> Dict[str, int]:
    print("--- Starting RAG Ingestion Pipeline ---")

    # 1. Load documents
    docs = load_knowledge_base_documents(KNOWLEDGE_BASE_DIR)
    print(f"Discovered {len(docs)} knowledge base documents.")

    all_chunks = []
    for doc in docs:
        cleaned_content = clean_text(doc["content"])
        doc["content"] = cleaned_content
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)

    print(f"Generated {len(all_chunks)} document chunks.")

    # 2. Generate 384-dim Embeddings in batch
    texts = [c["content"] for c in all_chunks]
    embeddings = embed_documents(texts)
    print(f"Generated {len(embeddings)} 384-dimensional dense vector embeddings.")

    # 3. Connect to DB and enable pgvector
    db = SessionLocal()

    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()

        Base.metadata.create_all(bind=engine)

        # Idempotent replacement: delete existing chunks before re-inserting
        db.query(DocumentChunk).delete()
        db.commit()

        # Insert chunks
        inserted_count = 0
        for chunk_data, vec in zip(all_chunks, embeddings):
            chunk_row = DocumentChunk(
                document_name=chunk_data["document_name"],
                document_type=chunk_data["document_type"],
                chunk_index=chunk_data["chunk_index"],
                content=chunk_data["content"],
                doc_metadata=chunk_data["metadata"],
                embedding=vec
            )
            db.add(chunk_row)
            inserted_count += 1

        db.commit()
        print(f"[SUCCESS] RAG Ingestion Complete! Inserted {inserted_count} document chunks into PostgreSQL pgvector table.")
        return {"documents": len(docs), "chunks": len(all_chunks), "inserted": inserted_count}

    except Exception as e:
        db.rollback()
        print(f"[FAIL] RAG Ingestion Failed with Error: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    run_ingestion_pipeline()
