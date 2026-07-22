"""
Auris - Global Exception Handler
Centralized error handling middleware for consistent API responses
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError, OperationalError
from loguru import logger
import traceback
import uuid


class GlobalExceptionHandler:
    """Centralized exception handling for all routes"""
    
    @staticmethod
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTPException"""
        from app.services.structured_logging import log_api_error
        
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        endpoint = f"{request.method} {request.url.path}"
        
        logger.warning(
            f"HTTPException [ID: {request_id}]: "
            f"Status={exc.status_code}, Detail={exc.detail}"
        )
        
        log_api_error(
            error_code=f"HTTP_{exc.status_code}",
            error_message=exc.detail,
            endpoint=endpoint,
            status_code=exc.status_code,
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "request_id": request_id,
                "error_type": "http_exception"
            }
        )
    
    @staticmethod
    async def database_integrity_error(request: Request, exc: IntegrityError):
        """Handle database integrity violations (unique constraint, etc.)"""
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        logger.error(
            f"Database Integrity Error [ID: {request_id}]: {exc.orig}",
            exc_info=True
        )
        
        # Check for specific constraint violations
        error_str = str(exc.orig).lower()
        if "unique constraint" in error_str:
            detail = "Resource already exists"
        elif "foreign key constraint" in error_str:
            detail = "Invalid reference to related resource"
        elif "not null constraint" in error_str:
            detail = "Missing required field"
        else:
            detail = "Database constraint violation"
        
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": detail,
                "request_id": request_id,
                "error_type": "database_integrity_error"
            }
        )
    
    @staticmethod
    async def database_operational_error(request: Request, exc: OperationalError):
        """Handle database operational errors (connection issues, etc.)"""
        from app.services.structured_logging import StructuredLogger, CriticalPath, LogLevel
        
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        logger.error(
            f"Database Operational Error [ID: {request_id}]: {exc.orig}",
            exc_info=True
        )
        
        StructuredLogger.log_database_error(
            operation="query_execution",
            table="unknown",
            error_message=str(exc.orig),
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "detail": "Database connection error. Please try again later.",
                "request_id": request_id,
                "error_type": "database_operational_error"
            }
        )
    
    @staticmethod
    async def generic_exception_handler(request: Request, exc: Exception):
        """Handle generic unhandled exceptions"""
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        # Log full traceback for debugging
        logger.error(
            f"Unhandled Exception [ID: {request_id}]: {type(exc).__name__}\n"
            f"{traceback.format_exc()}",
            exc_info=True
        )
        
        # Environment-specific response
        from app.core.config import DEBUG
        
        if DEBUG:
            # Development: include more details
            error_detail = f"{type(exc).__name__}: {str(exc)}"
        else:
            # Production: generic message
            error_detail = "An unexpected error occurred"
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": error_detail,
                "request_id": request_id,
                "error_type": "internal_server_error"
            }
        )


def register_exception_handlers(app):
    """
    Register all exception handlers to FastAPI app
    
    Usage:
        register_exception_handlers(app)
    """
    app.add_exception_handler(
        HTTPException,
        GlobalExceptionHandler.http_exception_handler
    )
    
    app.add_exception_handler(
        IntegrityError,
        GlobalExceptionHandler.database_integrity_error
    )
    
    app.add_exception_handler(
        OperationalError,
        GlobalExceptionHandler.database_operational_error
    )
    
    app.add_exception_handler(
        Exception,
        GlobalExceptionHandler.generic_exception_handler
    )
    
    logger.info("Registered global exception handlers")
