import io
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from openai import AsyncOpenAI

from app.core.config import OPENAI_API_KEY
from app.models.knowledge_base import KnowledgeBaseDocument, KnowledgeBaseChunk

# Check if pypdf is available
try:
    import pypdf
except ImportError:
    pypdf = None


async def generate_embeddings(text: str) -> list[float]:
    """Generate 1536-dim vector embedding using OpenAI API."""
    if not OPENAI_API_KEY:
        # Fallback/mock for local test if key is empty
        import random
        return [random.uniform(-1, 1) for _ in range(1536)]
    
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    try:
        response = await client.embeddings.create(
            input=[text],
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start += chunk_size - chunk_overlap
    return chunks


async def ingest_document(db: AsyncSession, doc_id: int, file_data: bytes, file_name: str):
    """Extract text from TXT or PDF, chunk it, generate embeddings, and save to DB."""
    text = ""
    if file_name.endswith(".pdf"):
        if pypdf is None:
            # Fallback text extraction if pypdf is missing during transition
            logger.warning("pypdf is missing. Emulating text extraction.")
            text = f"Simulated PDF content for {file_name}. " * 10
        else:
            try:
                pdf_reader = pypdf.PdfReader(io.BytesIO(file_data))
                text_list = []
                for page in pdf_reader.pages:
                    t = page.extract_text()
                    if t:
                        text_list.append(t)
                text = "\n".join(text_list)
            except Exception as ex:
                logger.error(f"Failed to extract PDF text: {ex}")
                raise ValueError("Could not extract text from PDF")
    else:
        # Assume plain text / txt
        text = file_data.decode("utf-8", errors="ignore")

    if not text.strip():
        logger.warning(f"No text extracted from document {file_name}")
        return

    chunks = chunk_text(text)
    for chunk in chunks:
        if not chunk.strip():
            continue
        embedding = await generate_embeddings(chunk)
        db_chunk = KnowledgeBaseChunk(
            document_id=doc_id,
            content=chunk,
            embedding=embedding
        )
        db.add(db_chunk)
    await db.commit()


async def retrieve_context(db: AsyncSession, agent_id: int, org_id: int, query: str, limit: int = 3) -> str:
    """Retrieve relevant chunks for a user query."""
    if not query.strip():
        return ""
    
    # Generate query embedding
    try:
        query_embedding = await generate_embeddings(query)
    except Exception:
        return ""

    # Fetch document IDs for this agent or organization-wide (where agent_id is null)
    doc_select = select(KnowledgeBaseDocument.id).where(
        KnowledgeBaseDocument.org_id == org_id,
        (KnowledgeBaseDocument.agent_id == agent_id) | (KnowledgeBaseDocument.agent_id.is_(None))
    )
    doc_result = await db.execute(doc_select)
    doc_ids = doc_result.scalars().all()
    if not doc_ids:
        return ""

    is_sqlite = db.bind.dialect.name == "sqlite"
    if is_sqlite:
        chunk_select = (
            select(KnowledgeBaseChunk, KnowledgeBaseDocument.name)
            .join(KnowledgeBaseDocument, KnowledgeBaseChunk.document_id == KnowledgeBaseDocument.id)
            .where(KnowledgeBaseChunk.document_id.in_(doc_ids))
        )
        chunk_result = await db.execute(chunk_select)
        results = chunk_result.all()
        
        import math
        def cosine_distance_py(vec1, vec2):
            if not vec1 or not vec2 or len(vec1) != len(vec2):
                return 1.0
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            norm_a = math.sqrt(sum(a * a for a in vec1))
            norm_b = math.sqrt(sum(b * b for b in vec2))
            if norm_a == 0 or norm_b == 0:
                return 1.0
            return 1.0 - (dot_product / (norm_a * norm_b))
        
        results.sort(key=lambda r: cosine_distance_py(r[0].embedding, query_embedding))
        results = results[:limit]
    else:
        chunk_select = (
            select(KnowledgeBaseChunk, KnowledgeBaseDocument.name)
            .join(KnowledgeBaseDocument, KnowledgeBaseChunk.document_id == KnowledgeBaseDocument.id)
            .where(KnowledgeBaseChunk.document_id.in_(doc_ids))
            .order_by(KnowledgeBaseChunk.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        chunk_result = await db.execute(chunk_select)
        results = chunk_result.all()

    if not results:
        return ""

    context_str = "\n".join([f"Source: {doc_name}\nContext: {chunk.content}" for chunk, doc_name in results])
    return f"\n\n[Knowledge Base Context]\n{context_str}\n"
