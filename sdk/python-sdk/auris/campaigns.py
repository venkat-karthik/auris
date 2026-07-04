from typing import Optional, Dict, Any, List

class CampaignsModule:
    def __init__(self, client):
        self.client = client

    def create(
        self,
        name: str,
        agent_id: int,
        concurrency: int = 5,
        caller_id: Optional[str] = None,
        schedule_time: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new outbound dialer campaign."""
        data = {
            "name": name,
            "agent_id": agent_id,
            "concurrency": concurrency,
            "caller_id": caller_id,
            "schedule_time": schedule_time,
        }
        data = {k: v for k, v in data.items() if v is not None}
        return self.client.post("campaigns", json_data=data)

    def upload_contacts(self, campaign_id: int, contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Upload contacts to an existing campaign."""
        return self.client.post(f"campaigns/{campaign_id}/contacts/upload", json_data={"contacts": contacts})

    def start(self, campaign_id: int) -> Dict[str, Any]:
        """Start or resume a campaign."""
        return self.client.post(f"campaigns/{campaign_id}/start")

    def pause(self, campaign_id: int) -> Dict[str, Any]:
        """Pause an active campaign."""
        return self.client.post(f"campaigns/{campaign_id}/pause")

    def get_stats(self, campaign_id: int) -> Dict[str, Any]:
        """Get live statistics for a campaign."""
        return self.client.get(f"campaigns/{campaign_id}/stats")
