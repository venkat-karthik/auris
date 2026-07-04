from typing import Optional, Dict, Any, List

class PhoneNumbersModule:
    def __init__(self, client):
        self.client = client

    def list(self) -> List[Dict[str, Any]]:
        """List all provisioned phone numbers."""
        return self.client.get("phone-numbers")

    def attach(self, number_id: int, agent_id: int) -> Dict[str, Any]:
        """Attach a phone number to an agent."""
        return self.client.put(f"phone-numbers/{number_id}", json_data={"agent_id": agent_id})

    def detach(self, number_id: int) -> Dict[str, Any]:
        """Detach a phone number from its assigned agent."""
        return self.client.put(f"phone-numbers/{number_id}", json_data={"agent_id": None})
