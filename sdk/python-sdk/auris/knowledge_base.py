from typing import Optional, Dict, Any, List

class KnowledgeBaseModule:
    def __init__(self, client):
        self.client = client

    def list(self) -> List[Dict[str, Any]]:
        """List all uploaded knowledge base documents."""
        return self.client.get("knowledge_base")

    def upload(self, file_path: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Upload a document (PDF, TXT, DOCX) for pgvector RAG grounding."""
        with open(file_path, "rb") as f:
            files = {"file": (file_path.split("/")[-1], f)}
            data = {"title": title} if title else None
            return self.client.post("knowledge_base/upload", json_data=data, files=files)

    def delete(self, doc_id: int) -> Dict[str, Any]:
        """Delete a document from the knowledge base."""
        return self.client.delete(f"knowledge_base/{doc_id}")
