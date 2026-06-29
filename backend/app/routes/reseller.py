from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.reseller_query import ResellerQuery

router = APIRouter(prefix="/reseller", tags=["Reseller Program"])


class ResellerQueryRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    volume: str
    interest: str
    use_case: str


class ResellerQueryResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    volume: str
    interest: str
    use_case: str
    created_at: datetime


@router.post("", response_model=ResellerQueryResponse, status_code=status.HTTP_201_CREATED)
async def submit_reseller_query(
    req: ResellerQueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """Submit a reseller partnership application inquiry request."""
    query = ResellerQuery(
        name=req.name,
        email=req.email,
        phone=req.phone,
        volume=req.volume,
        interest=req.interest,
        use_case=req.use_case
    )
    db.add(query)
    await db.commit()
    await db.refresh(query)
    return query
