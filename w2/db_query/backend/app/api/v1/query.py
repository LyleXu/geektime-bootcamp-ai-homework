"""Query execution API endpoints."""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from app.models.query import QueryRequest, QueryResponse, ErrorResponse, NaturalQueryRequest, NaturalQueryResponse, ExportRequest
from app.services.query_service import QueryService
from app.services.llm_service import LLMService
from app.services.export_service import ExportService
from app.utils.timeout import QueryTimeoutError

router = APIRouter(prefix="/dbs", tags=["queries"])

query_service = QueryService()
llm_service = LLMService()
export_service = ExportService()


@router.post("/{name}/query", response_model=QueryResponse, responses={
    400: {"model": ErrorResponse, "description": "SQL validation error"},
    404: {"model": ErrorResponse, "description": "Database not found"},
    408: {"model": ErrorResponse, "description": "Query timeout"},
    500: {"model": ErrorResponse, "description": "Database or execution error"},
})
async def execute_query(name: str, request: QueryRequest):
    """Execute a SQL query against a database connection.
    
    The query will be validated to ensure it's a SELECT statement only,
    and will be executed with a timeout limit.
    """
    try:
        rows, row_count, execution_time_ms, columns = await query_service.execute_query(
            name, request.sql
        )
        
        return QueryResponse(
            rows=rows,
            row_count=row_count,
            execution_time_ms=execution_time_ms,
            columns=columns,
        )
        
    except ValueError as e:
        # SQL validation error or database not found
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )
    
    except QueryTimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=str(e),
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/{name}/query/natural", response_model=NaturalQueryResponse, responses={
    400: {"model": ErrorResponse, "description": "Invalid request or validation error"},
    404: {"model": ErrorResponse, "description": "Database not found"},
    500: {"model": ErrorResponse, "description": "LLM API or execution error"},
})
async def generate_sql_from_natural_language(name: str, request: NaturalQueryRequest):
    """Generate SQL query from natural language description.
    
    Uses LLM (GPT-4o) to convert natural language to SQL based on the database schema.
    The generated SQL is validated before being returned.
    """
    try:
        generated_sql, explanation, is_valid, validation_error = await llm_service.generate_sql_from_natural_language(
            name, request.natural_language
        )
        
        return NaturalQueryResponse(
            generated_sql=generated_sql,
            explanation=explanation,
            is_valid=is_valid,
            validation_error=validation_error,
        )
        
    except ValueError as e:
        # Database not found or no schema available
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )
    
    except Exception as e:
        # LLM API errors or other failures
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/export", responses={
    200: {"description": "Exported file content"},
    400: {"model": ErrorResponse, "description": "Invalid export request"},
    500: {"model": ErrorResponse, "description": "Export error"},
})
async def export_data(request: ExportRequest):
    """Export query results to CSV or JSON format.
    
    Returns the exported content as a downloadable file.
    """
    try:
        content_bytes, filename = export_service.export_data(
            data=request.data,
            format=request.format,
            filename=request.filename
        )
        
        # Set appropriate content type
        # CSV uses text/plain for better Excel compatibility
        if request.format == "csv":
            media_type = "text/csv"
        else:
            media_type = "application/json; charset=utf-8"
        
        return Response(
            content=content_bytes,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
