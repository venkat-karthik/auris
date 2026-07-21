"""
Auris - Common CRUD utilities to eliminate code duplication
Provides reusable functions for entity lookup, error handling, response building
"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import TypeVar, Generic, Type, Optional, Any
from loguru import logger

T = TypeVar('T')


class NotFoundError(HTTPException):
    """Custom exception for resource not found"""
    def __init__(self, resource_type: str, resource_id: Any = None):
        detail = f"{resource_type} not found"
        if resource_id:
            detail += f" (ID: {resource_id})"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class UnauthorizedError(HTTPException):
    """Custom exception for unauthorized access"""
    def __init__(self, detail: str = "Not authorized"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class ValidationError(HTTPException):
    """Custom exception for invalid request"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


# ========================================
# AGENT CRUD HELPERS
# ========================================

async def get_agent_or_404(
    agent_id: int,
    org_id: int,
    db: AsyncSession,
    eager_load: bool = True
) -> 'Agent':
    """
    Fetch agent by ID and organization.
    Raises HTTPException(404) if not found.
    
    Args:
        agent_id: Agent ID to fetch
        org_id: Organization ID for ownership check
        db: Database session
        eager_load: If True, eagerly load related data (call_runs, agents)
    
    Returns:
        Agent object
        
    Raises:
        NotFoundError(404) if agent not found
    """
    from app.models.agent import Agent
    
    query = select(Agent).where(
        Agent.id == agent_id,
        Agent.org_id == org_id,
        Agent.is_active == True
    )
    
    if eager_load:
        query = query.options(selectinload(Agent.org))
    
    result = await db.execute(query)
    agent = result.scalar_one_or_none()
    
    if not agent:
        logger.warning(f"Agent not found: ID={agent_id}, Org={org_id}")
        raise NotFoundError("Agent", agent_id)
    
    return agent


async def list_agents_paginated(
    org_id: int,
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0
) -> list['Agent']:
    """
    List all agents for organization with pagination.
    
    Args:
        org_id: Organization ID
        db: Database session
        limit: Number of results per page
        offset: Pagination offset
    
    Returns:
        List of Agent objects
    """
    from app.models.agent import Agent
    
    query = (
        select(Agent)
        .where(Agent.org_id == org_id, Agent.is_active == True)
        .order_by(Agent.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    
    result = await db.execute(query)
    return result.scalars().all()


# ========================================
# CALL RUN CRUD HELPERS
# ========================================

async def get_call_or_404(
    call_id: int,
    org_id: int,
    db: AsyncSession
) -> 'CallRun':
    """
    Fetch call run by ID and organization.
    
    Args:
        call_id: Call ID
        org_id: Organization ID
        db: Database session
    
    Returns:
        CallRun object
        
    Raises:
        NotFoundError(404) if not found
    """
    from app.models.call_run import CallRun
    
    query = select(CallRun).where(
        CallRun.id == call_id,
        CallRun.org_id == org_id
    )
    
    result = await db.execute(query)
    call = result.scalar_one_or_none()
    
    if not call:
        logger.warning(f"Call not found: ID={call_id}, Org={org_id}")
        raise NotFoundError("Call", call_id)
    
    return call


async def list_calls_paginated(
    org_id: int,
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
    agent_id: Optional[int] = None,
    status: Optional[str] = None,
    call_type: Optional[str] = None,
    disposition: Optional[str] = None,
    start_date: Optional[Any] = None,
    end_date: Optional[Any] = None
) -> list['CallRun']:
    """
    List calls with advanced filtering and pagination.
    
    Args:
        org_id: Organization ID
        db: Database session
        limit: Page size
        offset: Pagination offset
        agent_id: Filter by agent (optional)
        status: Filter by call status (optional)
        call_type: Filter by call type (optional)
        disposition: Filter by disposition (optional)
        start_date: Filter by created_at >= start_date (optional)
        end_date: Filter by created_at <= end_date (optional)
    
    Returns:
        List of CallRun objects
    """
    from app.models.call_run import CallRun
    
    query = select(CallRun).where(CallRun.org_id == org_id)
    
    # Apply filters
    if agent_id is not None:
        query = query.where(CallRun.agent_id == agent_id)
    if status is not None:
        query = query.where(CallRun.status == status)
    if call_type is not None:
        query = query.where(CallRun.call_type == call_type)
    if disposition is not None:
        query = query.where(CallRun.disposition == disposition)
    if start_date is not None:
        query = query.where(CallRun.created_at >= start_date)
    if end_date is not None:
        query = query.where(CallRun.created_at <= end_date)
    
    query = query.order_by(CallRun.created_at.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    return result.scalars().all()


# ========================================
# CAMPAIGN CRUD HELPERS
# ========================================

async def get_campaign_or_404(
    campaign_id: int,
    org_id: int,
    db: AsyncSession
) -> 'Campaign':
    """
    Fetch campaign by ID and organization.
    
    Args:
        campaign_id: Campaign ID
        org_id: Organization ID
        db: Database session
    
    Returns:
        Campaign object
        
    Raises:
        NotFoundError(404) if not found
    """
    from app.models.campaign import Campaign
    
    query = select(Campaign).where(
        Campaign.id == campaign_id,
        Campaign.org_id == org_id
    )
    
    result = await db.execute(query)
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        logger.warning(f"Campaign not found: ID={campaign_id}, Org={org_id}")
        raise NotFoundError("Campaign", campaign_id)
    
    return campaign


# ========================================
# ORGANIZATION CRUD HELPERS
# ========================================

async def get_org_or_404(
    org_id: int,
    db: AsyncSession
) -> 'Organization':
    """
    Fetch organization by ID.
    
    Args:
        org_id: Organization ID
        db: Database session
    
    Returns:
        Organization object
        
    Raises:
        NotFoundError(404) if not found
    """
    from app.models.organization import Organization
    
    query = select(Organization).where(Organization.id == org_id)
    result = await db.execute(query)
    org = result.scalar_one_or_none()
    
    if not org:
        logger.warning(f"Organization not found: ID={org_id}")
        raise NotFoundError("Organization", org_id)
    
    return org


# ========================================
# TRANSACTION HELPERS
# ========================================

async def safe_commit(db: AsyncSession, operation: str = "operation") -> bool:
    """
    Safely commit transaction with error handling.
    
    Args:
        db: Database session
        operation: Description of operation for logging
    
    Returns:
        True if successful, False if failed
    """
    try:
        await db.commit()
        logger.info(f"Successfully committed: {operation}")
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to commit {operation}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed. Please try again."
        )


async def safe_add_and_commit(
    db: AsyncSession,
    entity: Any,
    operation: str = "create"
) -> Any:
    """
    Safely add entity and commit transaction.
    
    Args:
        db: Database session
        entity: Entity to add
        operation: Description for logging
    
    Returns:
        Refreshed entity object
        
    Raises:
        HTTPException(500) on failure
    """
    try:
        db.add(entity)
        await db.commit()
        await db.refresh(entity)
        logger.info(f"Successfully {operation}: {entity.__class__.__name__} ID={entity.id}")
        return entity
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to {operation}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to {operation} resource"
        )


async def safe_update_and_commit(
    db: AsyncSession,
    entity: Any,
    operation: str = "update"
) -> Any:
    """
    Safely update entity and commit transaction.
    
    Args:
        db: Database session
        entity: Entity to update
        operation: Description for logging
    
    Returns:
        Refreshed entity object
    """
    return await safe_add_and_commit(db, entity, operation)


# ========================================
# VALIDATION HELPERS
# ========================================

def validate_positive(value: float, field_name: str) -> float:
    """Validate that a value is positive"""
    if value <= 0:
        raise ValidationError(f"{field_name} must be positive")
    return value


def validate_not_empty(value: str, field_name: str) -> str:
    """Validate that a string is not empty"""
    if not value or not value.strip():
        raise ValidationError(f"{field_name} cannot be empty")
    return value


def validate_file_size(
    file_size: int,
    max_size: int = 10 * 1024 * 1024,  # 10 MB default
    file_name: str = "File"
) -> bool:
    """Validate file size"""
    if file_size > max_size:
        raise ValidationError(
            f"{file_name} too large ({file_size} bytes, max {max_size} bytes)"
        )
    return True


def validate_content_type(
    content_type: str,
    allowed_types: list[str],
    file_name: str = "File"
) -> bool:
    """Validate content type"""
    if not any(content_type.startswith(t) for t in allowed_types):
        raise ValidationError(
            f"{file_name} has invalid type. Allowed: {', '.join(allowed_types)}"
        )
    return True
