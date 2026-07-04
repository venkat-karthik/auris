import requests
from typing import Optional, Dict, Any, List

class APIError(Exception):
    """Exception raised for Auris API errors."""
    def __init__(self, status_code: int, message: str, response: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self.message = message
        self.response = response
        super().__init__(f"Auris API Error ({status_code}): {message}")

class AurisClient:
    """
    Client for interacting with the Auris Enterprise Voice AI Platform API.
    """
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000/api/v1"):
        if not api_key:
            raise ValueError("API key is required.")
        
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        
        # Lazy-loaded domain modules
        self._agents = None
        self._calls = None
        self._campaigns = None
        self._knowledge_base = None
        self._phone_numbers = None
        self._integrations = None
        self._whatsapp = None
        self._cloned_voices = None
        self._billing = None

    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Universal HTTP request handler."""
        headers = headers or {}
        params = params or {}
        method = method.upper()
        
        headers.setdefault("Authorization", f"Bearer {self.api_key}")
        if not files:
            headers.setdefault("Content-Type", "application/json")
        headers.setdefault("Accept", "application/json")
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                data=data,
                json=json_data,
                files=files,
            )
            response.raise_for_status()
            if method == "DELETE" and not response.content:
                return {"status": "success"}
            return response.json() if response.content else {}
        except requests.exceptions.HTTPError as e:
            error_message = "Unknown error"
            error_data = {}
            try:
                error_data = e.response.json()
                error_message = error_data.get("detail", error_data.get("error", str(e)))
            except Exception:
                error_message = str(e)
            raise APIError(status_code=e.response.status_code, message=error_message, response=error_data)
        except requests.exceptions.RequestException as e:
            raise APIError(status_code=0, message=f"Network error: {str(e)}")

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.request("GET", endpoint, params=params)

    def post(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None, files: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.request("POST", endpoint, json_data=json_data, files=files)

    def put(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.request("PUT", endpoint, json_data=json_data)

    def delete(self, endpoint: str) -> Dict[str, Any]:
        return self.request("DELETE", endpoint)

    @property
    def agents(self):
        if self._agents is None:
            from .agents import AgentsModule
            self._agents = AgentsModule(self)
        return self._agents

    @property
    def calls(self):
        if self._calls is None:
            from .calls import CallsModule
            self._calls = CallsModule(self)
        return self._calls

    @property
    def campaigns(self):
        if self._campaigns is None:
            from .campaigns import CampaignsModule
            self._campaigns = CampaignsModule(self)
        return self._campaigns

    @property
    def knowledge_base(self):
        if self._knowledge_base is None:
            from .knowledge_base import KnowledgeBaseModule
            self._knowledge_base = KnowledgeBaseModule(self)
        return self._knowledge_base

    @property
    def phone_numbers(self):
        if self._phone_numbers is None:
            from .phone_numbers import PhoneNumbersModule
            self._phone_numbers = PhoneNumbersModule(self)
        return self._phone_numbers

    @property
    def integrations(self):
        if self._integrations is None:
            from .integrations import IntegrationsModule
            self._integrations = IntegrationsModule(self)
        return self._integrations

    @property
    def whatsapp(self):
        if self._whatsapp is None:
            from .whatsapp import WhatsappModule
            self._whatsapp = WhatsappModule(self)
        return self._whatsapp

    @property
    def cloned_voices(self):
        if self._cloned_voices is None:
            from .cloned_voices import ClonedVoicesModule
            self._cloned_voices = ClonedVoicesModule(self)
        return self._cloned_voices

    @property
    def billing(self):
        if self._billing is None:
            from .billing import BillingModule
            self._billing = BillingModule(self)
        return self._billing
