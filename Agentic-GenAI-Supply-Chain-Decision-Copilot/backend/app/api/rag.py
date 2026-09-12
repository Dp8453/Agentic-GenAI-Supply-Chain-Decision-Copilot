from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.rag.schemas import RAGQueryRequest, RAGQueryResponse
from app.rag.retriever import retrieve_relevant_chunks

router = APIRouter()


@router.post("/rag/query", response_model=RAGQueryResponse, summary="Query Vector Knowledge Base (RAG Search)")
async def rag_vector_search(
    request: RAGQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Performs vector similarity search over procurement policies and supplier contract chunks.
    Returns structured relevant chunks with source citations and similarity scores.
    """
    try:
        supplier_filter = request.filters.supplier if request.filters else None
        doc_type_filter = request.filters.document_type if request.filters else None

        res = retrieve_relevant_chunks(
            query=request.query,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
            supplier_filter=supplier_filter,
            doc_type_filter=doc_type_filter,
            db=db
        )
        return RAGQueryResponse(**res)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG query search failed: {str(e)}")
