from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.auth import get_access_token_payload, ensure_company_access
from app.db.deps import get_db
from app.models.order import Order
from app.models.order_item import OrderItem

router = APIRouter()

# --- PYDANTIC MODELLERİ (Gelen ve Giden Veri Yapıları) ---

class OrderItemCreate(BaseModel):
    product_id: Optional[int] = None
    name: str
    quantity: int
    unit_price: float

class OrderCreateRequest(BaseModel):
    company_id: int
    customer_id: int
    offer_id: Optional[int] = None
    order_number: str
    items: List[OrderItemCreate]

class OrderItemResponse(BaseModel):
    id: int
    product_id: Optional[int]
    name: str
    quantity: int
    unit_price: float
    total_price: float

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    company_id: int
    customer_id: int
    offer_id: Optional[int]
    order_number: str
    total_amount: float
    status: str
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True

# --- UÇ NOKTALAR (Endpoints) ---

@router.post("/orders", tags=["Orders"], response_model=OrderResponse)
def create_order(
    payload: OrderCreateRequest,
    token_payload: dict = Depends(get_access_token_payload),
    db: Session = Depends(get_db),
):
    # Yetki kontrolü
    ensure_company_access(payload.company_id, token_payload)
    
    # 1. Önce Siparişin "Başlığını" oluşturuyoruz
    new_order = Order(
        company_id=payload.company_id,
        customer_id=payload.customer_id,
        offer_id=payload.offer_id,
        order_number=payload.order_number,
        status="pending", # Başlangıç durumu: Bekliyor
        total_amount=0.0
    )
    db.add(new_order)
    db.flush() # Veritabanına yazdırıp yeni oluşan siparişin ID'sini alıyoruz
    
    # 2. İçindeki ürünleri (kalemleri) tek tek ekleyip fiyatı topluyoruz
    calculated_total = 0.0
    for item in payload.items:
        line_total = item.quantity * item.unit_price
        calculated_total += line_total
        
        new_item = OrderItem(
            order_id=new_order.id,
            product_id=item.product_id,
            name=item.name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=line_total
        )
        db.add(new_item)
        
    # 3. Hesaplanan toplam fiyatı sipariş başlığına yazıyoruz
    new_order.total_amount = calculated_total
    db.commit()
    db.refresh(new_order)
    
    return new_order

@router.get("/orders", tags=["Orders"], response_model=List[OrderResponse])
def list_orders(
    company_id: int,
    token_payload: dict = Depends(get_access_token_payload),
    db: Session = Depends(get_db),
):
    # Yetki kontrolü
    ensure_company_access(company_id, token_payload)
    
    # Şirkete ait siparişleri getir
    stmt = select(Order).where(Order.company_id == company_id)
    orders = db.scalars(stmt).all()
    
    return orders