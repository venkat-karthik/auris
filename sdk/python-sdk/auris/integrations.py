from typing import Optional, Dict, Any, List

class IntegrationsModule:
    def __init__(self, client):
        self.client = client

    def list(self) -> List[Dict[str, Any]]:
        """List all available integrations."""
        return self.client.get("integrations")

    def toggle(self, integration_id: int, is_active: bool, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Enable or disable an integration."""
        data = {
            "integration_id": integration_id,
            "is_active": is_active,
            "config_json": config or {},
        }
        return self.client.post("integrations/toggle", json_data=data)
