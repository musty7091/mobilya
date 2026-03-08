from fastapi import APIRouter, Depends, HTTPException, Query, status
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


class CompanyUpdateRequest(BaseModel):
    name: str
    code: str
    is_active: bool


class CompanyResponse(BaseModel):
    id: int
    name: str
    code: str
    is_active: bool


class CompanyCountResponse(BaseModel):
    count: int


class MessageResponse(BaseModel):
    message: str


@router.get("/companies/count", tags=["Companies"], response_model=CompanyCountResponse)
def get_companies_count(
    db: Session = Depends(get_db),
) -> CompanyCountResponse:
    count = db.scalar(select(func.count()).select_from(Company)) or 0
    return CompanyCountResponse(count=count)


@router.get("/companies", tags=["Companies"], response_model=list[CompanyResponse])
def list_companies(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    token_payload: dict = Depends(require_superuser),
    db: Session = Depends(get_db),
) -> list[CompanyResponse]:
    companies = db.scalars(
        select(Company).order_by(Company.id).offset(skip).limit(limit)
    ).all()

    return [
        CompanyResponse(
            id=company.id,
            name=company.name,
            code=company.code,
            is_active=company.is_active,
        )
        for company in companies
    ]


@router.get("/companies/{company_id}", tags=["Companies"], response_model=CompanyResponse)
def get_company(
    company_id: int,
    token_payload: dict = Depends(require_superuser),
    db: Session = Depends(get_db),
) -> CompanyResponse:
    company = db.scalar(
        select(Company).where(Company.id == company_id)
    )
    if not company:
        raise HTTPException(status_code=404, detail="Company bulunamadı.")

    return CompanyResponse(
        id=company.id,
        name=company.name,
        code=company.code,
        is_active=company.is_active,
    )


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


@router.put("/companies/{company_id}", tags=["Companies"], response_model=CompanyResponse)
def update_company(
    company_id: int,
    payload: CompanyUpdateRequest,
    token_payload: dict = Depends(require_superuser),
    db: Session = Depends(get_db),
) -> CompanyResponse:
    company = db.scalar(
        select(Company).where(Company.id == company_id)
    )
    if not company:
        raise HTTPException(status_code=404, detail="Company bulunamadı.")

    normalized_name = payload.name.strip()
    normalized_code = payload.code.strip().upper()

    existing_company_by_name = db.scalar(
        select(Company).where(
            func.lower(Company.name) == normalized_name.lower(),
            Company.id != company_id,
        )
    )
    if existing_company_by_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu company adı zaten kayıtlı.",
        )

    existing_company_by_code = db.scalar(
        select(Company).where(
            func.upper(Company.code) == normalized_code,
            Company.id != company_id,
        )
    )
    if existing_company_by_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu company code zaten kayıtlı.",
        )

    company.name = normalized_name
    company.code = normalized_code
    company.is_active = payload.is_active

    db.commit()
    db.refresh(company)

    return CompanyResponse(
        id=company.id,
        name=company.name,
        code=company.code,
        is_active=company.is_active,
    )


@router.delete("/companies/{company_id}", tags=["Companies"], response_model=MessageResponse)
def delete_company(
    company_id: int,
    token_payload: dict = Depends(require_superuser),
    db: Session = Depends(get_db),
) -> MessageResponse:
    company = db.scalar(
        select(Company).where(Company.id == company_id)
    )
    if not company:
        raise HTTPException(status_code=404, detail="Company bulunamadı.")

    db.delete(company)
    db.commit()

    return MessageResponse(
        message="Company silindi."
    )