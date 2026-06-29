"""
Auris - Agent CRUD routes
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field


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
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_org, get_current_user
from app.models.agent import Agent
from app.models.organization import Organization
from app.models.user import User

router = APIRouter(prefix="/agents", tags=["agents"])


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
    agent = Agent(
        org_id=org.id,
        created_by=user.id,
        name=body.name,
        description=body.description,
        graph=body.graph,
        model_config=body.model_config_data,
        context_variables=body.context_variables,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


@router.get("", response_model=list[AgentResponse])
async def list_agents(
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Agent).where(Agent.org_id == org.id, Agent.is_active == True)
    )
    return result.scalars().all()


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.org_id == org.id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    body: AgentUpdate,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.org_id == org.id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

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

    await db.commit()
    await db.refresh(agent)
    return agent


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: int,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.org_id == org.id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.is_active = False
    await db.commit()
