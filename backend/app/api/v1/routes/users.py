from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.deps import get_db
from app.models.company import Company
from app.models.user import User

router = APIRouter()


@router.post("/users", tags=["Users"])
def create_user(
    company_id: int,
    full_name: str,
    email: str,
    password: str,
    is_active: bool = True,
    is_superuser: bool = False,
    db: Session = Depends(get_db),
) -> dict:
    company = db.scalar(
        select(Company).where(Company.id == company_id)
    )
    if not company:
        raise HTTPException(status_code=404, detail="Company bulunamadı.")

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu email zaten kullanılıyor.")

    user = User(
        company_id=company_id,
        full_name=full_name,
        email=email,
        password_hash=get_password_hash(password),
        is_active=is_active,
        is_superuser=is_superuser,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "company_id": user.company_id,
        "full_name": user.full_name,
        "email": user.email,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
    }