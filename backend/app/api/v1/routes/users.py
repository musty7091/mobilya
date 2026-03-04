from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.deps import get_db
from app.models.company import Company
from app.models.user import User

router = APIRouter()


class UserCreateRequest(BaseModel):
    company_id: int
    full_name: str
    email: str
    password: str
    is_active: bool = True
    is_superuser: bool = False


class UserUpdateRequest(BaseModel):
    company_id: int
    full_name: str
    email: str
    password: str | None = None
    is_active: bool
    is_superuser: bool


class UserResponse(BaseModel):
    id: int
    company_id: int
    full_name: str
    email: str
    is_active: bool
    is_superuser: bool


class MessageResponse(BaseModel):
    message: str


@router.get("/users", tags=["Users"], response_model=list[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    company_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[UserResponse]:
    stmt = select(User).order_by(User.id).offset(skip).limit(limit)

    if company_id is not None:
        stmt = stmt.where(User.company_id == company_id)

    users = db.scalars(stmt).all()

    return [
        UserResponse(
            id=u.id,
            company_id=u.company_id,
            full_name=u.full_name,
            email=u.email,
            is_active=u.is_active,
            is_superuser=u.is_superuser,
        )
        for u in users
    ]


@router.get("/users/{user_id}", tags=["Users"], response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
) -> UserResponse:
    user = db.scalar(
        select(User).where(User.id == user_id)
    )
    if not user:
        raise HTTPException(status_code=404, detail="User bulunamadı.")

    return UserResponse(
        id=user.id,
        company_id=user.company_id,
        full_name=user.full_name,
        email=user.email,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
    )


@router.post(
    "/users",
    tags=["Users"],
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
)
def create_user(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    company = db.scalar(
        select(Company).where(Company.id == payload.company_id)
    )
    if not company:
        raise HTTPException(status_code=404, detail="Company bulunamadı.")

    existing_user = db.scalar(
        select(User).where(User.email == payload.email)
    )
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu email zaten kullanılıyor.")

    user = User(
        company_id=payload.company_id,
        full_name=payload.full_name,
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        is_active=payload.is_active,
        is_superuser=payload.is_superuser,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,
        company_id=user.company_id,
        full_name=user.full_name,
        email=user.email,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
    )


@router.put("/users/{user_id}", tags=["Users"], response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    user = db.scalar(
        select(User).where(User.id == user_id)
    )
    if not user:
        raise HTTPException(status_code=404, detail="User bulunamadı.")

    company = db.scalar(
        select(Company).where(Company.id == payload.company_id)
    )
    if not company:
        raise HTTPException(status_code=404, detail="Company bulunamadı.")

    existing_user = db.scalar(
        select(User).where(User.email == payload.email, User.id != user_id)
    )
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu email zaten kullanılıyor.")

    user.company_id = payload.company_id
    user.full_name = payload.full_name
    user.email = payload.email
    user.is_active = payload.is_active
    user.is_superuser = payload.is_superuser

    if payload.password is not None and payload.password.strip() != "":
        user.password_hash = get_password_hash(payload.password)

    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,
        company_id=user.company_id,
        full_name=user.full_name,
        email=user.email,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
    )


@router.delete("/users/{user_id}", tags=["Users"], response_model=MessageResponse)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
) -> MessageResponse:
    user = db.scalar(
        select(User).where(User.id == user_id)
    )
    if not user:
        raise HTTPException(status_code=404, detail="User bulunamadı.")

    db.delete(user)
    db.commit()

    return MessageResponse(
        message="User silindi."
    )