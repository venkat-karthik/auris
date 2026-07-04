from typing import Optional, Dict, Any, List

class CallsModule:
    def __init__(self, client):
        self.client = client

    def list(self) -> List[Dict[str, Any]]:
        """List all call runs."""
        return self.client.get("calls")

    def get(self, call_id: str) -> Dict[str, Any]:
        """Get details of a specific call run."""
        return self.client.get(f"calls/{call_id}")

    def get_analysis(self, call_id: str) -> Dict[str, Any]:
        """Get AI analysis and metrics for a call."""
        return self.client.get(f"calls/{call_id}/analysis")

    def get_transcript(self, call_id: str) -> Dict[str, Any]:
        """Get call transcript."""
        return self.client.get(f"calls/{call_id}/transcript")

    def dispatch(
        self,
        agent_id: int,
        to_number: str,
        from_number: Optional[str] = None,
        call_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Dispatch an outbound phone call."""
        data = {
            "agent_id": agent_id,
            "to_number": to_number,
            "from_number": from_number,
            "call_context": call_context or {},
        }
        data = {k: v for k, v in data.items() if v is not None}
        return self.client.post("calls", json_data=data)

    def warm_transfer(self, call_id: str, target_number: str) -> Dict[str, Any]:
        """Initiate a warm transfer for an active call."""
        return self.client.post(f"calls/{call_id}/warm_transfer", json_data={"target_number": target_number})

    def send_dtmf(self, call_id: str, digits: str) -> Dict[str, Any]:
        """Send DTMF digits to an active call."""
        return self.client.post(f"calls/{call_id}/dtmf", json_data={"digits": digits})
