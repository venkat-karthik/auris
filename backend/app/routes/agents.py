"""
Auris - Agent CRUD routes
Refactored to use CRUD helpers for DRY and consistency
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_org, get_current_user
from app.models.agent import Agent
from app.models.organization import Organization
from app.models.user import User
from app.utils.crud import (
    get_agent_or_404,
    list_agents_paginated,
    safe_add_and_commit,
    safe_update_and_commit,
)

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentResponse(BaseModel):
    id: int
    org_id: int
    name: str
    description: str | None
    graph: dict
    model_config_data: dict = Field(..., alias="model_config", validation_alias="model_config")
    context_variables: dict

    class Config:
        from_attributes = True
        populate_by_name = True


class AgentCreate(BaseModel):
    name: str
    description: str | None = None
    graph: dict = {}
    model_config_data: dict = {}
    context_variables: dict = {}


class AgentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    graph: dict | None = None
    model_config_data: dict | None = None
    context_variables: dict | None = None





@router.post("", response_model=AgentResponse, status_code=201)
async def create_agent(
    body: AgentCreate,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new agent for the organization.
    
    Request body example:
    ```json
    {
        "name": "Support Agent",
        "description": "Handles customer support calls",
        "graph": {},
        "model_config_data": {},
        "context_variables": {}
    }
    ```
    
    Response: Agent object with auto-generated ID (201 Created)
    """
    agent = Agent(
        org_id=org.id,
        created_by=user.id,
        name=body.name,
        description=body.description,
        graph=body.graph,
        model_config=body.model_config_data,
        context_variables=body.context_variables,
    )
    return await safe_add_and_commit(db, agent, "create_agent")


@router.get("", response_model=list[AgentResponse])
async def list_agents(
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """
    List all active agents for the organization.
    
    Results are paginated with limit and offset.
    
    Example response:
    ```json
    [
        {
            "id": 1,
            "org_id": 123,
            "name": "Support Agent",
            "description": "Customer support voice agent",
            "graph": {},
            "model_config": {},
            "context_variables": {}
        }
    ]
    ```
    """
    agents = await list_agents_paginated(org.id, db, limit=limit, offset=offset)
    return agents


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific agent by ID.
    
    Returns 404 if agent not found.
    Response includes X-Request-ID header for tracing.
    """
    return await get_agent_or_404(agent_id, org.id, db, eager_load=True)


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    body: AgentUpdate,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing agent."""
    agent = await get_agent_or_404(agent_id, org.id, db, eager_load=False)

    # Update only provided fields
    if body.name is not None:
        agent.name = body.name
    if body.description is not None:
        agent.description = body.description
    if body.graph is not None:
        agent.graph = body.graph
    if body.model_config_data is not None:
        agent.model_config = body.model_config_data
    if body.context_variables is not None:
        agent.context_variables = body.context_variables

    return await safe_update_and_commit(db, agent, "update_agent")


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: int,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete an agent (sets is_active = False)."""
    agent = await get_agent_or_404(agent_id, org.id, db, eager_load=False)
    agent.is_active = False
    await safe_update_and_commit(db, agent, "delete_agent")


@router.get("/{agent_id}/studio")
async def get_studio_graph(
    agent_id: int,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Get visual studio workflow graph data for React Flow."""
    agent = await get_agent_or_404(agent_id, org.id, db, eager_load=False)
    return {"agent_id": agent.id, "graph": agent.graph or {}}


@router.post("/{agent_id}/studio")
async def save_studio_graph(
    agent_id: int,
    graph_data: dict,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Save visual studio workflow graph from React Flow."""
    agent = await get_agent_or_404(agent_id, org.id, db, eager_load=False)
    agent.graph = graph_data
    await safe_update_and_commit(db, agent, "save_studio_graph")
    return {"status": "success", "agent_id": agent.id, "graph": agent.graph}

