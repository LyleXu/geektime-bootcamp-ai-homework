"""
Global error handlers for validation, timeout, and database errors.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import asyncio

from app.utils.timeout import QueryTimeoutError


async def validation_exception_handler(request: Request, exc: RequestValidationError | ValidationError):
    """Handle Pydantic validation errors."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Validation error",
            "details": exc.errors(),
        },
    )


async def timeout_exception_handler(request: Request, exc: QueryTimeoutError):
    """Handle query timeout errors."""
    return JSONResponse(
        status_code=status.HTTP_408_REQUEST_TIMEOUT,
        content={
            "error": "Query timeout",
            "message": str(exc),
            "timeoutSeconds": exc.timeout_seconds,
        },
    )


async def asyncio_timeout_handler(request: Request, exc: asyncio.TimeoutError):
    """Handle asyncio timeout errors."""
    return JSONResponse(
        status_code=status.HTTP_408_REQUEST_TIMEOUT,
        content={
            "error": "Request timeout",
            "message": "Operation exceeded maximum timeout",
        },
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    # Temporarily add traceback for debugging
    import traceback
    traceback_str = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    print(f"Error: {exc}")
    print(f"Traceback:\n{traceback_str}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "type": type(exc).__name__,
            "traceback": traceback_str.split('\n')[:10],  # First 10 lines
        },
    )


def register_error_handlers(app):
    """Register all error handlers with the FastAPI app."""
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(QueryTimeoutError, timeout_exception_handler)
    app.add_exception_handler(asyncio.TimeoutError, asyncio_timeout_handler)
    app.add_exception_handler(Exception, general_exception_handler)
