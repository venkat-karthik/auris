"""
Auris - Structured Logging Service
Centralized logging for critical paths with request context.
"""
import json
import time
from typing import Any, Optional, Dict
from loguru import logger
from enum import Enum


class LogLevel(str, Enum):
    """Log severity levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class CriticalPath(str, Enum):
    """Key business logic paths to log."""
    CALL_CREATION = "call_creation"
    CALL_COMPLETION = "call_completion"
    CAMPAIGN_START = "campaign_start"
    CAMPAIGN_EXECUTION = "campaign_execution"
    AGENT_INFERENCE = "agent_inference"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    PAYMENT_PROCESSING = "payment_processing"
    API_ERROR = "api_error"
    DATABASE_ERROR = "database_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"


class StructuredLogger:
    """Centralized structured logging."""
    
    @staticmethod
    def log_critical_path(
        path: CriticalPath,
        level: LogLevel = LogLevel.INFO,
        **context: Any
    ) -> None:
        """
        Log a critical business path.
        
        Args:
            path: Critical path identifier
            level: Log level
            **context: Additional context data to log
        """
        log_data = {
            "path": path.value,
            "level": level.value,
            "timestamp": time.time(),
            **context
        }
        
        message = f"[{path.value.upper()}] {context.get('message', '')}"
        
        if level == LogLevel.DEBUG:
            logger.debug(message, extra={"data": log_data})
        elif level == LogLevel.INFO:
            logger.info(message, extra={"data": log_data})
        elif level == LogLevel.SUCCESS:
            logger.info(f"✅ {message}", extra={"data": log_data})
        elif level == LogLevel.WARNING:
            logger.warning(f"⚠️  {message}", extra={"data": log_data})
        elif level == LogLevel.ERROR:
            logger.error(f"❌ {message}", extra={"data": log_data})
        elif level == LogLevel.CRITICAL:
            logger.critical(f"🔴 {message}", extra={"data": log_data})
    
    @staticmethod
    def log_call_created(
        call_id: int,
        org_id: int,
        agent_id: int,
        call_type: str,
        **extra: Any
    ) -> None:
        """Log successful call creation."""
        StructuredLogger.log_critical_path(
            CriticalPath.CALL_CREATION,
            LogLevel.SUCCESS,
            message=f"Call created: {call_id}",
            call_id=call_id,
            org_id=org_id,
            agent_id=agent_id,
            call_type=call_type,
            **extra
        )
    
    @staticmethod
    def log_call_completed(
        call_id: int,
        duration_seconds: float,
        status: str,
        **extra: Any
    ) -> None:
        """Log successful call completion."""
        StructuredLogger.log_critical_path(
            CriticalPath.CALL_COMPLETION,
            LogLevel.SUCCESS,
            message=f"Call completed: {call_id}",
            call_id=call_id,
            duration_seconds=duration_seconds,
            status=status,
            **extra
        )
    
    @staticmethod
    def log_campaign_started(
        campaign_id: int,
        org_id: int,
        contact_count: int,
        **extra: Any
    ) -> None:
        """Log campaign start."""
        StructuredLogger.log_critical_path(
            CriticalPath.CAMPAIGN_START,
            LogLevel.SUCCESS,
            message=f"Campaign started: {campaign_id}",
            campaign_id=campaign_id,
            org_id=org_id,
            contact_count=contact_count,
            **extra
        )
    
    @staticmethod
    def log_agent_inference(
        agent_id: int,
        call_id: int,
        inference_time_ms: float,
        model_used: str,
        **extra: Any
    ) -> None:
        """Log agent inference execution."""
        StructuredLogger.log_critical_path(
            CriticalPath.AGENT_INFERENCE,
            LogLevel.DEBUG,
            message=f"Agent inference: {agent_id}",
            agent_id=agent_id,
            call_id=call_id,
            inference_time_ms=inference_time_ms,
            model_used=model_used,
            **extra
        )
    
    @staticmethod
    def log_knowledge_retrieval(
        agent_id: int,
        org_id: int,
        query_terms: str,
        results_count: int,
        retrieval_time_ms: float,
        **extra: Any
    ) -> None:
        """Log knowledge base retrieval."""
        StructuredLogger.log_critical_path(
            CriticalPath.KNOWLEDGE_RETRIEVAL,
            LogLevel.DEBUG,
            message=f"Knowledge retrieved: {results_count} results",
            agent_id=agent_id,
            org_id=org_id,
            query_terms=query_terms,
            results_count=results_count,
            retrieval_time_ms=retrieval_time_ms,
            **extra
        )
    
    @staticmethod
    def log_auth_success(
        user_id: int,
        org_id: int,
        method: str = "api_key",
        **extra: Any
    ) -> None:
        """Log successful authentication."""
        StructuredLogger.log_critical_path(
            CriticalPath.AUTH_SUCCESS,
            LogLevel.INFO,
            message=f"Authentication successful",
            user_id=user_id,
            org_id=org_id,
            method=method,
            **extra
        )
    
    @staticmethod
    def log_auth_failure(
        reason: str,
        method: str = "api_key",
        ip_address: Optional[str] = None,
        **extra: Any
    ) -> None:
        """Log authentication failure (security event)."""
        StructuredLogger.log_critical_path(
            CriticalPath.AUTH_FAILURE,
            LogLevel.WARNING,
            message=f"Authentication failed: {reason}",
            reason=reason,
            method=method,
            ip_address=ip_address,
            **extra
        )
    
    @staticmethod
    def log_payment_processing(
        org_id: int,
        amount: float,
        currency: str,
        provider: str,
        status: str,
        **extra: Any
    ) -> None:
        """Log payment processing."""
        level = LogLevel.SUCCESS if status == "success" else LogLevel.ERROR
        StructuredLogger.log_critical_path(
            CriticalPath.PAYMENT_PROCESSING,
            level,
            message=f"Payment {status}: ${amount} {currency}",
            org_id=org_id,
            amount=amount,
            currency=currency,
            provider=provider,
            status=status,
            **extra
        )
    
    @staticmethod
    def log_api_error(
        error_code: str,
        error_message: str,
        endpoint: str,
        status_code: int,
        **extra: Any
    ) -> None:
        """Log API error."""
        StructuredLogger.log_critical_path(
            CriticalPath.API_ERROR,
            LogLevel.ERROR,
            message=f"API error: {error_code}",
            error_code=error_code,
            error_message=error_message,
            endpoint=endpoint,
            status_code=status_code,
            **extra
        )
    
    @staticmethod
    def log_database_error(
        operation: str,
        table: str,
        error_message: str,
        **extra: Any
    ) -> None:
        """Log database error."""
        StructuredLogger.log_critical_path(
            CriticalPath.DATABASE_ERROR,
            LogLevel.ERROR,
            message=f"Database error during {operation}",
            operation=operation,
            table=table,
            error_message=error_message,
            **extra
        )
    
    @staticmethod
    def log_external_service_error(
        service_name: str,
        error_message: str,
        retry_attempt: int = 0,
        **extra: Any
    ) -> None:
        """Log external service error."""
        StructuredLogger.log_critical_path(
            CriticalPath.EXTERNAL_SERVICE_ERROR,
            LogLevel.WARNING,
            message=f"External service error: {service_name}",
            service_name=service_name,
            error_message=error_message,
            retry_attempt=retry_attempt,
            **extra
        )


# Convenience functions for quick access
def log_call_created(call_id: int, org_id: int, agent_id: int, call_type: str, **extra):
    """Log successful call creation."""
    StructuredLogger.log_call_created(call_id, org_id, agent_id, call_type, **extra)


def log_call_completed(call_id: int, duration_seconds: float, status: str, **extra):
    """Log successful call completion."""
    StructuredLogger.log_call_completed(call_id, duration_seconds, status, **extra)


def log_campaign_started(campaign_id: int, org_id: int, contact_count: int, **extra):
    """Log campaign start."""
    StructuredLogger.log_campaign_started(campaign_id, org_id, contact_count, **extra)


def log_auth_failure(reason: str, method: str = "api_key", ip_address: Optional[str] = None, **extra):
    """Log authentication failure."""
    StructuredLogger.log_auth_failure(reason, method, ip_address, **extra)


def log_api_error(error_code: str, error_message: str, endpoint: str, status_code: int, **extra):
    """Log API error."""
    StructuredLogger.log_api_error(error_code, error_message, endpoint, status_code, **extra)
