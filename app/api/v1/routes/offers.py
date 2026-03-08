from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.auth import get_access_token_payload, ensure_company_access
from app.db.deps import get_db
from app.models.offer import Offer
from app.models.offer_item import OfferItem

router = APIRouter()

# --- PYDANTIC MODELLERİ (Gelen ve Giden Veri Yapıları) ---

class OfferItemCreate(BaseModel):
    product_id: Optional[int] = None
    name: str
    quantity: int
    unit_price: float

class OfferCreateRequest(BaseModel):
    company_id: int
    customer_id: int
    title: str
    items: List[OfferItemCreate]

class OfferItemResponse(BaseModel):
    id: int
    product_id: Optional[int]
    name: str
    quantity: int
    unit_price: float
    total_price: float

    class Config:
        from_attributes = True

class OfferResponse(BaseModel):
    id: int
    company_id: int
    customer_id: int
    title: str
    total_amount: float
    status: str
    items: List[OfferItemResponse] = []

    class Config:
        from_attributes = True

# --- UÇ NOKTALAR (Endpoints) ---

@router.post("/offers", tags=["Offers"], response_model=OfferResponse)
def create_offer(
    payload: OfferCreateRequest,
    token_payload: dict = Depends(get_access_token_payload),
    db: Session = Depends(get_db),
):
    # Yetki kontrolü
    ensure_company_access(payload.company_id, token_payload)
    
    # 1. Önce Teklifin "Başlığını" oluşturuyoruz
    new_offer = Offer(
        company_id=payload.company_id,
        customer_id=payload.customer_id,
        title=payload.title,
        status="draft",
        total_amount=0.0  # Şimdilik 0, kalemleri ekledikçe hesaplayacağız
    )
    db.add(new_offer)
    db.flush() # Veritabanına yazdırıp yeni oluşan teklifin ID'sini alıyoruz
    
    # 2. İçindeki ürünleri (kalemleri) tek tek ekleyip fiyatı topluyoruz
    calculated_total = 0.0
    for item in payload.items:
        line_total = item.quantity * item.unit_price
        calculated_total += line_total
        
        new_item = OfferItem(
            offer_id=new_offer.id,
            product_id=item.product_id,
            name=item.name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=line_total
        )
        db.add(new_item)
        
    # 3. Hesaplanan toplam fiyatı teklif başlığına yazıyoruz
    new_offer.total_amount = calculated_total
    db.commit()
    db.refresh(new_offer)
    
    return new_offer

@router.get("/offers", tags=["Offers"], response_model=List[OfferResponse])
def list_offers(
    company_id: int,
    token_payload: dict = Depends(get_access_token_payload),
    db: Session = Depends(get_db),
):
    # Yetki kontrolü
    ensure_company_access(company_id, token_payload)
    
    # Şirkete ait teklifleri getir
    stmt = select(Offer).where(Offer.company_id == company_id)
    offers = db.scalars(stmt).all()
    
    return offers