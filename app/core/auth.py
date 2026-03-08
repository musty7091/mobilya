from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.jwt import ALGORITHM
from app.db.deps import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def decode_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token süresi dolmuş.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz token.",
        )


def require_access_token(payload: dict[str, Any]) -> dict[str, Any]:
    token_type = payload.get("type")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token gerekli.",
        )
    return payload


def require_refresh_token(payload: dict[str, Any]) -> dict[str, Any]:
    token_type = payload.get("type")
    if token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token gerekli.",
        )
    return payload


def get_access_token_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header gerekli.",
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token gerekli.",
        )

    payload = decode_token(credentials.credentials)
    return require_access_token(payload)


def require_superuser(
    token_payload: dict[str, Any] = Depends(get_access_token_payload),
) -> dict[str, Any]:
    if not token_payload.get("is_superuser", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için superuser yetkisi gerekli.",
        )
    return token_payload


def get_current_user(
    token_payload: dict[str, Any] = Depends(get_access_token_payload),
    db: Session = Depends(get_db),
) -> User:
    user_id = token_payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token içeriği geçersiz.",
        )

    user = db.scalar(select(User).where(User.id == int(user_id)))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User bulunamadı.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kullanıcı pasif durumda.",
        )

    return user


def get_current_company_id(
    token_payload: dict[str, Any] = Depends(get_access_token_payload),
) -> int:
    company_id = token_payload.get("company_id")
    if company_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token içinde company bilgisi yok.",
        )
    return int(company_id)


def ensure_company_access(
    target_company_id: int,
    token_payload: dict[str, Any],
) -> None:
    if token_payload.get("is_superuser", False):
        return

    token_company_id = token_payload.get("company_id")
    if token_company_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token içinde company bilgisi yok.",
        )

    if int(token_company_id) != int(target_company_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu company verisine erişim yetkiniz yok.",
        )