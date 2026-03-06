from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.auth import require_superuser
from app.db.deps import get_db
from app.models.company import Company

router = APIRouter()


class CompanyCreateRequest(BaseModel):
    name: str
    code: str


class CompanyResponse(BaseModel):
    id: int
    name: str
    code: str
    is_active: bool


class CompanyCountResponse(BaseModel):
    count: int


@router.get("/companies/count", tags=["Companies"], response_model=CompanyCountResponse)
def get_companies_count(
    db: Session = Depends(get_db),
) -> CompanyCountResponse:
    count = db.scalar(select(func.count()).select_from(Company)) or 0
    return CompanyCountResponse(count=count)


@router.post(
    "/companies",
    tags=["Companies"],
    status_code=status.HTTP_201_CREATED,
    response_model=CompanyResponse,
)
def create_company(
    payload: CompanyCreateRequest,
    token_payload: dict = Depends(require_superuser),
    db: Session = Depends(get_db),
) -> CompanyResponse:
    normalized_name = payload.name.strip()
    normalized_code = payload.code.strip().upper()

    existing_company_by_name = db.scalar(
        select(Company).where(func.lower(Company.name) == normalized_name.lower())
    )
    if existing_company_by_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu company adı zaten kayıtlı.",
        )

    existing_company_by_code = db.scalar(
        select(Company).where(func.upper(Company.code) == normalized_code)
    )
    if existing_company_by_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu company code zaten kayıtlı.",
        )

    company = Company(
        name=normalized_name,
        code=normalized_code,
        is_active=True,
    )

    db.add(company)
    db.commit()
    db.refresh(company)

    return CompanyResponse(
        id=company.id,
        name=company.name,
        code=company.code,
        is_active=company.is_active,
    )