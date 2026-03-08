from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.core.auth import ensure_company_access, get_access_token_payload
from app.db.deps import get_db
from app.models.company import Company
from app.models.customer import Customer

router = APIRouter()

class CustomerCreateRequest(BaseModel):
    company_id: int
    full_name: str
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    notes: str | None = None
    is_active: bool = True

class CustomerResponse(BaseModel):
    id: int
    company_id: int
    full_name: str
    phone: str | None
    email: str | None
    address: str | None
    notes: str | None
    is_active: bool

# Sayfalama için yeni veri modeli
class CustomerPaginatedResponse(BaseModel):
    total: int
    items: list[CustomerResponse]

class MessageResponse(BaseModel):
    message: str

@router.get("/customers", tags=["Customers"], response_model=CustomerPaginatedResponse)
def list_customers(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=1000),
    search: str | None = Query(default=None),
    company_id: int | None = None,
    token_payload: dict = Depends(get_access_token_payload),
    db: Session = Depends(get_db),
) -> CustomerPaginatedResponse:
    is_superuser = token_payload.get("is_superuser", False)
    token_company_id = token_payload.get("company_id")

    stmt = select(Customer)
    count_stmt = select(func.count()).select_from(Customer)

    if is_superuser:
        if company_id is not None:
            stmt = stmt.where(Customer.company_id == company_id)
            count_stmt = count_stmt.where(Customer.company_id == company_id)
    else:
        if token_company_id is None:
            raise HTTPException(status_code=401, detail="Token içinde company bilgisi yok.")

        if company_id is not None and int(company_id) != int(token_company_id):
            raise HTTPException(status_code=403, detail="Bu company verisine erişim yetkiniz yok.")

        stmt = stmt.where(Customer.company_id == int(token_company_id))
        count_stmt = count_stmt.where(Customer.company_id == int(token_company_id))

    # Arama (Search) mantığı eklendi
    if search:
        search_term = f"%{search}%"
        search_filter = or_(
            Customer.full_name.ilike(search_term),
            Customer.phone.ilike(search_term),
            Customer.email.ilike(search_term)
        )
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    total = db.scalar(count_stmt) or 0

    # En son eklenen en üstte gelsin diye order_by(desc) yapıldı
    stmt = stmt.order_by(Customer.id.desc()).offset(skip).limit(limit)
    customers = db.scalars(stmt).all()

    items = [
        CustomerResponse(
            id=customer.id,
            company_id=customer.company_id,
            full_name=customer.full_name,
            phone=customer.phone,
            email=customer.email,
            address=customer.address,
            notes=customer.notes,
            is_active=customer.is_active,
        )
        for customer in customers
    ]
    
    return CustomerPaginatedResponse(total=total, items=items)

@router.get("/customers/{customer_id}", tags=["Customers"], response_model=CustomerResponse)
def get_customer(
    customer_id: int,
    token_payload: dict = Depends(get_access_token_payload),
    db: Session = Depends(get_db),
) -> CustomerResponse:
    customer = db.scalar(select(Customer).where(Customer.id == customer_id))
    if not customer:
        raise HTTPException(status_code=404, detail="Customer bulunamadı.")

    ensure_company_access(customer.company_id, token_payload)

    return CustomerResponse(
        id=customer.id,
        company_id=customer.company_id,
        full_name=customer.full_name,
        phone=customer.phone,
        email=customer.email,
        address=customer.address,
        notes=customer.notes,
        is_active=customer.is_active,
    )

@router.post("/customers", tags=["Customers"], status_code=status.HTTP_201_CREATED, response_model=CustomerResponse)
def create_customer(
    payload: CustomerCreateRequest,
    token_payload: dict = Depends(get_access_token_payload),
    db: Session = Depends(get_db),
) -> CustomerResponse:
    ensure_company_access(payload.company_id, token_payload)

    company = db.scalar(select(Company).where(Company.id == payload.company_id))
    if not company:
        raise HTTPException(status_code=404, detail="Company bulunamadı.")

    customer = Customer(
        company_id=payload.company_id,
        full_name=payload.full_name.strip(),
        phone=payload.phone.strip() if payload.phone else None,
        email=payload.email.strip().lower() if payload.email else None,
        address=payload.address.strip() if payload.address else None,
        notes=payload.notes.strip() if payload.notes else None,
        is_active=payload.is_active,
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return CustomerResponse(
        id=customer.id,
        company_id=customer.company_id,
        full_name=customer.full_name,
        phone=customer.phone,
        email=customer.email,
        address=customer.address,
        notes=customer.notes,
        is_active=customer.is_active,
    )

@router.put("/customers/{customer_id}", tags=["Customers"], response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    payload: CustomerCreateRequest,
    token_payload: dict = Depends(get_access_token_payload),
    db: Session = Depends(get_db),
) -> CustomerResponse:
    customer = db.scalar(select(Customer).where(Customer.id == customer_id))
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı.")

    ensure_company_access(customer.company_id, token_payload)

    customer.full_name = payload.full_name.strip()
    customer.phone = payload.phone.strip() if payload.phone else None
    customer.email = payload.email.strip().lower() if payload.email else None
    customer.address = payload.address.strip() if payload.address else None
    customer.notes = payload.notes.strip() if payload.notes else None
    customer.is_active = payload.is_active

    db.commit()
    db.refresh(customer)
    return CustomerResponse(
        id=customer.id,
        company_id=customer.company_id,
        full_name=customer.full_name,
        phone=customer.phone,
        email=customer.email,
        address=customer.address,
        notes=customer.notes,
        is_active=customer.is_active,
    )

# Silme (DELETE) mantığı eklendi
@router.delete("/customers/{customer_id}", tags=["Customers"], response_model=MessageResponse)
def delete_customer(
    customer_id: int,
    token_payload: dict = Depends(get_access_token_payload),
    db: Session = Depends(get_db),
) -> MessageResponse:
    customer = db.scalar(select(Customer).where(Customer.id == customer_id))
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı.")
    
    ensure_company_access(customer.company_id, token_payload)

    db.delete(customer)
    db.commit()
    
    return MessageResponse(message="Müşteri başarıyla silindi.")