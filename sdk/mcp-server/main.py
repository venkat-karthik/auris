import os
import logging
from typing import Dict, Any, List, Optional
from fastmcp import FastMCP
from auris import AurisClient

logger = logging.getLogger(__name__)

mcp = FastMCP(name="Auris Voice AI MCP Server")


def get_client() -> AurisClient:
    api_key = os.getenv("AURIS_API_KEY", "mock_key")
    base_url = os.getenv("AURIS_BASE_URL", "http://localhost:8000/api/v1")
    return AurisClient(api_key=api_key, base_url=base_url)


@mcp.tool(description="Dispatch an outbound phone call to an Auris voice agent.")
def dispatch_a_call(agent_id: int, to_number: str, call_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Dispatch an outbound call to a destination phone number.
    
    Args:
        agent_id: The numeric ID of the virtual agent.
        to_number: Destination phone number in E.164 format.
        call_context: Optional key-value dictionary injected into agent prompt.
    """
    client = get_client()
    return client.calls.dispatch(agent_id=agent_id, to_number=to_number, call_context=call_context or {})


@mcp.tool(description="Create a new virtual conversational voice agent in Auris.")
def create_assistant(name: str, system_prompt: str, welcome_message: Optional[str] = "Hello! How can I help you?") -> Dict[str, Any]:
    """
    Create a new voice AI agent.
    
    Args:
        name: Name of the virtual agent.
        system_prompt: Core system instructions and behavior rules.
        welcome_message: Initial greeting spoken by the agent when the call starts.
    """
    client = get_client()
    return client.agents.create(name=name, system_prompt=system_prompt, welcome_message=welcome_message)


@mcp.tool(description="Start an outbound dialer campaign in Auris.")
def start_campaign(campaign_id: int) -> Dict[str, Any]:
    """
    Start or resume an outbound dialer campaign.
    
    Args:
        campaign_id: The numeric ID of the campaign.
    """
    client = get_client()
    return client.campaigns.start(campaign_id=campaign_id)


@mcp.tool(description="Check current Razorpay credit balance for the Auris organization.")
def get_balance() -> Dict[str, Any]:
    """Check billing credit balance."""
    client = get_client()
    return client.billing.get_balance()


@mcp.resource("agents://all")
def get_all_assistants() -> List[Dict[str, Any]]:
    """List all active virtual voice agents."""
    client = get_client()
    return client.agents.list()


@mcp.resource("calls://recent")
def get_recent_calls() -> List[Dict[str, Any]]:
    """List recent call runs."""
    client = get_client()
    return client.calls.list()


def create_app():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    create_app()
