from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.sql.schemas import SQLQueryRequest, SQLResponse
from app.sql.service import SQLService

router = APIRouter()


@router.post("/sql/query", response_model=SQLResponse, summary="Execute Natural-Language Read-Only SQL Query")
async def sql_query_endpoint(
    request: SQLQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Converts natural-language supply-chain questions into validated read-only PostgreSQL queries.
    Validates queries against safety policies (SELECT/WITH only, single-statement, table allowlisting),
    executes queries with limits & statement timeouts, and returns grounded explanations.
    """
    try:
        service = SQLService(provider_name=request.provider_override)
        response = service.execute_natural_language_query(
            question=request.question,
            db=db,
            limit_override=request.limit_override,
            provider_override=request.provider_override
        )
        return response
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NL-to-SQL execution failed: {str(e)}")
