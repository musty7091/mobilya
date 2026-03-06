from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.jwt import create_access_token, create_refresh_token
from app.core.security import verify_password
from app.db.deps import get_db
from app.models.user import User

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/auth/login", tags=["Auth"])
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict:
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user:
        raise HTTPException(status_code=401, detail="Email veya şifre hatalı.")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Kullanıcı pasif durumda.")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email veya şifre hatalı.")

    subject = str(user.id)

    access_token = create_access_token(
        subject=subject,
        extra_claims={
            "company_id": user.company_id,
            "is_superuser": user.is_superuser,
        },
    )

    refresh_token = create_refresh_token(
        subject=subject,
        extra_claims={
            "company_id": user.company_id,
        },
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "company_id": user.company_id,
            "full_name": user.full_name,
            "email": user.email,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
        }
    }