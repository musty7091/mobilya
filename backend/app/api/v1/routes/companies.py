from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.company import Company

router = APIRouter()


@router.get("/companies/count", tags=["Companies"])
def get_companies_count(db: Session = Depends(get_db)) -> dict:
    total_companies = db.scalar(select(func.count()).select_from(Company))
    return {"count": total_companies or 0}


@router.post("/companies", tags=["Companies"])
def create_company(
    name: str,
    code: str,
    db: Session = Depends(get_db)
) -> dict:
    existing_company = db.scalar(
        select(Company).where(Company.code == code)
    )
    if existing_company:
        raise HTTPException(status_code=400, detail="Bu company code zaten mevcut.")

    company = Company(
        name=name,
        code=code,
        is_active=True,
    )

    db.add(company)
    db.commit()
    db.refresh(company)

    return {
        "id": company.id,
        "name": company.name,
        "code": company.code,
        "is_active": company.is_active,
    }