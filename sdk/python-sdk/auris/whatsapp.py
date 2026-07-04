from typing import Optional, Dict, Any, List

class WhatsappModule:
    def __init__(self, client):
        self.client = client

    def list(self) -> List[Dict[str, Any]]:
        """List all registered WhatsApp Business numbers."""
        return self.client.get("whatsapp")

    def register(self, phone_number: str, waba_id: str, phone_number_id: str, verify_token: str) -> Dict[str, Any]:
        """Register a new WhatsApp Business number."""
        data = {
            "phone_number": phone_number,
            "waba_id": waba_id,
            "phone_number_id": phone_number_id,
            "verify_token": verify_token,
        }
        return self.client.post("whatsapp", json_data=data)

    def bind(self, number_id: int, agent_id: int) -> Dict[str, Any]:
        """Bind a WhatsApp number to a virtual voice/chat agent."""
        return self.client.put(f"whatsapp/{number_id}/bind", json_data={"agent_id": agent_id})

    def delete(self, number_id: int) -> Dict[str, Any]:
        """Delete a WhatsApp registration."""
        return self.client.delete(f"whatsapp/{number_id}")

    def send(self, number_id: int, recipient: str, text: str) -> Dict[str, Any]:
        """Send an outbound WhatsApp message."""
        return self.client.post(f"whatsapp/{number_id}/send", json_data={"recipient": recipient, "text": text})
