from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.auth import (
    decode_token,
    get_current_user,
    require_refresh_token,
)
from app.core.jwt import create_access_token, create_refresh_token
from app.core.security import verify_password
from app.db.deps import get_db
from app.models.user import User

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class AuthUserResponse(BaseModel):
    id: int
    company_id: int
    full_name: str
    email: str
    is_active: bool
    is_superuser: bool


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: AuthUserResponse


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str


@router.post("/auth/login", tags=["Auth"], response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    normalized_email = payload.email.strip().lower()

    user = db.scalar(
        select(User).where(func.lower(User.email) == normalized_email)
    )
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

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=AuthUserResponse(
            id=user.id,
            company_id=user.company_id,
            full_name=user.full_name,
            email=user.email,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
        ),
    )


@router.get("/auth/me", tags=["Auth"], response_model=AuthUserResponse)
def auth_me(
    current_user: User = Depends(get_current_user),
) -> AuthUserResponse:
    return AuthUserResponse(
        id=current_user.id,
        company_id=current_user.company_id,
        full_name=current_user.full_name,
        email=current_user.email,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
    )


@router.post("/auth/refresh", tags=["Auth"], response_model=RefreshResponse)
def refresh_token(
    payload: RefreshRequest,
    db: Session = Depends(get_db),
) -> RefreshResponse:
    token_payload = decode_token(payload.refresh_token)
    token_payload = require_refresh_token(token_payload)

    user_id = token_payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token içeriği geçersiz.")

    user = db.scalar(select(User).where(User.id == int(user_id)))
    if not user:
        raise HTTPException(status_code=404, detail="User bulunamadı.")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Kullanıcı pasif durumda.")

    new_access_token = create_access_token(
        subject=str(user.id),
        extra_claims={
            "company_id": user.company_id,
            "is_superuser": user.is_superuser,
        },
    )

    return RefreshResponse(
        access_token=new_access_token,
        token_type="bearer",
    )