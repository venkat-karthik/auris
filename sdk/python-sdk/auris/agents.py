from typing import Optional, Dict, Any, List

class AgentsModule:
    def __init__(self, client):
        self.client = client

    def list(self) -> List[Dict[str, Any]]:
        """List all virtual agents."""
        return self.client.get("agents")

    def get(self, agent_id: int) -> Dict[str, Any]:
        """Get details of a specific agent by ID."""
        return self.client.get(f"agents/{agent_id}")

    def create(
        self,
        name: str,
        system_prompt: str,
        welcome_message: Optional[str] = None,
        voice_id: Optional[str] = "cartesia_en_male",
        language: Optional[str] = "en",
        stt_provider: Optional[str] = "deepgram",
        llm_provider: Optional[str] = "openai",
        tts_provider: Optional[str] = "cartesia",
        model: Optional[str] = "gpt-4o",
        temperature: Optional[float] = 0.7,
        max_tokens: Optional[int] = 300,
        webhook_url: Optional[str] = None,
        workflow_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new voice AI agent."""
        data = {
            "name": name,
            "system_prompt": system_prompt,
            "welcome_message": welcome_message,
            "voice_id": voice_id,
            "language": language,
            "stt_provider": stt_provider,
            "llm_provider": llm_provider,
            "tts_provider": tts_provider,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "webhook_url": webhook_url,
            "workflow_id": workflow_id,
        }
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        return self.client.post("agents", json_data=data)

    def update(self, agent_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing agent."""
        return self.client.put(f"agents/{agent_id}", json_data=data)

    def delete(self, agent_id: int) -> Dict[str, Any]:
        """Delete an agent."""
        return self.client.delete(f"agents/{agent_id}")
