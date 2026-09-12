from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.llm.schemas import CopilotQueryRequest, CopilotResponse
from app.llm.service import LLMService

router = APIRouter()


@router.post("/copilot/query", response_model=CopilotResponse, summary="Query SupplyChain AI Copilot (Grounded LLM Layer)")
async def copilot_query(
    request: CopilotQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Transforms user natural-language questions into grounded structured copilot answers.
    Executes intent classification, context assembly (RAG evidence + deterministic risk & forecast metrics),
    LLM response generation, and strict citation validation.
    """
    try:
        service = LLMService(provider_name=request.provider_override)
        response = service.process_query(
            question=request.question,
            supplier_filter=request.supplier_filter,
            doc_type_filter=request.document_type_filter,
            top_k=request.top_k,
            provider_override=request.provider_override,
            db=db
        )
        return response
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Copilot query processing failed: {str(e)}")
