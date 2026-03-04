from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.company import Company

router = APIRouter()


@router.get("/companies/count", tags=["Companies"])
def get_companies_count(db: Session = Depends(get_db)) -> dict:
    total_companies = db.scalar(select(func.count()).select_from(Company))
    return {"count": total_companies or 0}