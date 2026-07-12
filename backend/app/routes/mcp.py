"""
Auris - Model Context Protocol (MCP) Server Routes
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_org, get_current_user
from app.models.agent import Agent
from app.models.call_run import CallRun
from app.models.campaign import Campaign
from app.models.organization import Organization
from app.models.user import User

router = APIRouter(prefix="/mcp", tags=["mcp"])


class MCPManifestResponse(BaseModel):
    name: str = "Auris Voice AI MCP Server"
    version: str = "1.0.0"
    description: str = "Model Context Protocol server for the Auris Enterprise Voice AI Platform."
    capabilities: Dict[str, Any] = {
        "tools": {"listChanged": True},
        "resources": {"subscribe": False, "listChanged": True},
    }
    tools: List[Dict[str, Any]]
    resources: List[Dict[str, Any]]


class MCPInvokeRequest(BaseModel):
    tool_name: str | None = None
    name: str | None = None
    arguments: Dict[str, Any] = {}


@router.get("")
@router.get("/tools")
async def get_mcp_manifest():
    """Get the Model Context Protocol server manifest and available tools/resources."""
    tools = [
        {
            "name": "dispatch_call",
            "description": "Dispatch an outbound phone call to a virtual voice agent.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {"type": "integer", "description": "ID of the virtual agent"},
                    "to_number": {"type": "string", "description": "Destination phone number in E.164 format"},
                    "call_context": {"type": "object", "description": "Key-value context dictionary injected into agent prompt"},
                },
                "required": ["agent_id", "to_number"],
            },
        },
        {
            "name": "create_agent",
            "description": "Create a new virtual conversational voice agent.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "system_prompt": {"type": "string"},
                    "welcome_message": {"type": "string"},
                },
                "required": ["name", "system_prompt"],
            },
        },
        {
            "name": "start_campaign",
            "description": "Start or resume an outbound dialer campaign.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "campaign_id": {"type": "integer"},
                },
                "required": ["campaign_id"],
            },
        },
        {
            "name": "get_balance",
            "description": "Get current Razorpay billing credit balance.",
            "inputSchema": {"type": "object", "properties": {}},
        },
    ]

    resources = [
        {"uri": "agents://all", "name": "All Virtual Agents", "description": "List of all active virtual agents"},
        {"uri": "calls://recent", "name": "Recent Calls", "description": "List of recent call runs"},
        {"uri": "campaigns://active", "name": "Active Campaigns", "description": "List of active outbound dialer campaigns"},
    ]

    return MCPManifestResponse(tools=tools, resources=resources)


@router.post("/tools/call")
@router.post("/invoke")
async def call_mcp_tool(
    body: MCPInvokeRequest,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Execute an MCP tool call against the Auris platform."""
    args = body.arguments or {}
    tool_name = body.tool_name or body.name
    if not tool_name:
        raise HTTPException(status_code=400, detail="tool_name or name is required")


    if tool_name == "get_balance":
        return {
            "status": "success",
            "tool": tool_name,
            "result": {"balance_credits": org.balance_credits, "currency": "USD"},
        }

    elif tool_name == "create_agent":
        name = args.get("name")
        system_prompt = args.get("system_prompt")
        welcome_message = args.get("welcome_message", "Hello! How can I help you?")
        if not name or not system_prompt:
            raise HTTPException(status_code=400, detail="name and system_prompt are required for create_agent")

        agent = Agent(
            org_id=org.id,
            created_by=user.id,
            name=name,
            description=system_prompt[:200],
            graph={},
            model_config={"system_prompt": system_prompt, "welcome_message": welcome_message},
            context_variables={},
        )
        db.add(agent)
        await db.commit()
        await db.refresh(agent)
        return {
            "status": "success",
            "tool": tool_name,
            "result": {"agent_id": agent.id, "name": agent.name, "created_at": str(agent.created_at)},
        }

    elif tool_name == "dispatch_call":
        agent_id = args.get("agent_id")
        to_number = args.get("to_number")
        call_context = args.get("call_context", {})
        if not agent_id or not to_number:
            raise HTTPException(status_code=400, detail="agent_id and to_number are required for dispatch_call")

        # Verify agent exists
        res = await db.execute(select(Agent).where(Agent.id == agent_id, Agent.org_id == org.id))
        agent = res.scalar_one_or_none()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        call_run = CallRun(
            org_id=org.id,
            agent_id=agent.id,
            caller_number=to_number,
            transport="telnyx",
            call_type="outbound",
            status="initiated",
            initial_context=call_context,
        )
        db.add(call_run)
        await db.commit()
        await db.refresh(call_run)
        return {
            "status": "success",
            "tool": tool_name,
            "result": {"call_id": call_run.id, "agent_id": agent.id, "to_number": to_number, "status": call_run.status},
        }

    elif tool_name == "start_campaign":
        campaign_id = args.get("campaign_id")
        if not campaign_id:
            raise HTTPException(status_code=400, detail="campaign_id is required for start_campaign")

        res = await db.execute(select(Campaign).where(Campaign.id == campaign_id, Campaign.org_id == org.id))
        campaign = res.scalar_one_or_none()
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        campaign.status = "running"
        await db.commit()
        return {
            "status": "success",
            "tool": tool_name,
            "result": {"campaign_id": campaign.id, "status": campaign.status},
        }

    else:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")


@router.get("/resources")
async def list_mcp_resources(
    uri: Optional[str] = None,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Fetch data for an MCP resource."""
    if uri == "agents://all" or not uri:
        res = await db.execute(select(Agent).where(Agent.org_id == org.id, Agent.is_active == True))
        agents = res.scalars().all()
        return {"uri": "agents://all", "data": [{"id": a.id, "name": a.name} for a in agents]}

    elif uri == "calls://recent":
        res = await db.execute(select(CallRun).where(CallRun.org_id == org.id).order_by(CallRun.created_at.desc()).limit(20))
        calls = res.scalars().all()
        return {"uri": "calls://recent", "data": [{"id": c.id, "status": c.status, "direction": c.call_type} for c in calls]}

    elif uri == "campaigns://active":
        res = await db.execute(select(Campaign).where(Campaign.org_id == org.id, Campaign.status == "running"))
        campaigns = res.scalars().all()
        return {"uri": "campaigns://active", "data": [{"id": c.id, "name": c.name, "status": c.status} for c in campaigns]}

    else:
        raise HTTPException(status_code=404, detail=f"Resource URI '{uri}' not supported")
