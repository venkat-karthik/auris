from typing import Optional, Dict, Any, List

class ClonedVoicesModule:
    def __init__(self, client):
        self.client = client

    def list(self) -> List[Dict[str, Any]]:
        """List all custom cloned voices."""
        return self.client.get("cloned-voices")

    def upload(self, name: str, file_path: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Upload an audio sample to clone a custom voice."""
        with open(file_path, "rb") as f:
            files = {"file": (file_path.split("/")[-1], f)}
            data = {"name": name, "description": description or ""}
            return self.client.post("cloned-voices/upload", json_data=data, files=files)
