from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from app.core.auth import ensure_company_access, get_access_token_payload
from app.db.deps import get_db
from app.models.offer import Offer, OfferItem
from app.models.customer import Customer

router = APIRouter()

# --- PYDANTIC MODELLERİ ---
class OfferItemCreate(BaseModel):
    item_name: str
    quantity: int
    unit_price: float

class OfferCreateRequest(BaseModel):
    company_id: int
    customer_id: int
    status: str = "Beklemede"
    items: List[OfferItemCreate]

class OfferItemResponse(BaseModel):
    id: int
    item_name: str
    quantity: int
    unit_price: float

class CustomerMiniResponse(BaseModel):
    id: int
    full_name: str

class OfferResponse(BaseModel):
    id: int
    company_id: int
    customer_id: int
    status: str
    total_price: float
    customer: Optional[CustomerMiniResponse] = None
    items: List[OfferItemResponse] = []

class OfferPaginatedResponse(BaseModel):
    total: int
    items: List[OfferResponse]

class MessageResponse(BaseModel):
    message: str


# --- ROTALAR (ENDPOINTS) ---

@router.post("/offers", tags=["Offers"], response_model=OfferResponse)
def create_offer(
    payload: OfferCreateRequest,
    token_payload: dict = Depends(get_access_token_payload),
    db: Session = Depends(get_db),
):
    ensure_company_access(payload.company_id, token_payload)

    # Müşteriyi kontrol et
    customer = db.scalar(select(Customer).where(Customer.id == payload.customer_id))
    if not customer or customer.company_id != payload.company_id:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı veya bu müşteriye yetkiniz yok.")

    # Toplam fiyatı esnek kalemlerden hesapla
    total_price = sum(item.quantity * item.unit_price for item in payload.items)

    # Önce ana Teklifi (Offer) oluştur
    new_offer = Offer(
        company_id=payload.company_id,
        customer_id=payload.customer_id,
        status=payload.status,
        total_price=total_price
    )
    db.add(new_offer)
    db.flush() # ID'yi almak için flush yapıyoruz (henüz veritabanına kalıcı yazmadık)

    # Sonra içindeki ürün kalemlerini (OfferItem) oluştur ve teklife bağla
    for item in payload.items:
        new_item = OfferItem(
            offer_id=new_offer.id,
            item_name=item.item_name.strip(),
            quantity=item.quantity,
            unit_price=item.unit_price
        )
        db.add(new_item)

    db.commit()
    db.refresh(new_offer)

    return get_offer(new_offer.id, token_payload, db)

@router.get("/offers", tags=["Offers"], response_model=OfferPaginatedResponse)
def list_offers(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=500),
    search: str | None = Query(default=None),
    token_payload: dict = Depends(get_access_token_payload),
    db: Session = Depends(get_db),
):
    token_company_id = token_payload.get("company_id")
    is_superuser = token_payload.get("is_superuser", False)

    # joinedload ile Müşteri ve Ürün Kalemlerini aynı anda çekiyoruz
    stmt = select(Offer).options(joinedload(Offer.customer), joinedload(Offer.items))
    count_stmt = select(func.count()).select_from(Offer)

    if not is_superuser:
        stmt = stmt.where(Offer.company_id == int(token_company_id))
        count_stmt = count_stmt.where(Offer.company_id == int(token_company_id))

    # Arama (Search) mantığı
    if search:
        search_id = None
        if search.upper().startswith("#TKF-"):
            try:
                search_id = int(search[5:])
            except ValueError:
                pass
        elif search.isdigit():
            search_id = int(search)

        if search_id:
            stmt = stmt.where(Offer.id == search_id)
            count_stmt = count_stmt.where(Offer.id == search_id)
        else:
            stmt = stmt.join(Customer).where(Customer.full_name.ilike(f"%{search}%"))
            count_stmt = count_stmt.join(Customer).where(Customer.full_name.ilike(f"%{search}%"))

    total = db.scalar(count_stmt) or 0
    
    # unique() fonksiyonu joinedload(liste) kullandığımız için şarttır
    stmt = stmt.order_by(Offer.id.desc()).offset(skip).limit(limit)
    offers = db.scalars(stmt).unique().all()

    result_items = []
    for o in offers:
        result_items.append(OfferResponse(
            id=o.id,
            company_id=o.company_id,
            customer_id=o.customer_id,
            status=o.status,
            total_price=o.total_price,
            customer=CustomerMiniResponse(id=o.customer.id, full_name=o.customer.full_name) if o.customer else None,
            items=[OfferItemResponse(id=i.id, item_name=i.item_name, quantity=i.quantity, unit_price=i.unit_price) for i in o.items]
        ))

    return OfferPaginatedResponse(total=total, items=result_items)

@router.get("/offers/{offer_id}", tags=["Offers"], response_model=OfferResponse)
def get_offer(
    offer_id: int,
    token_payload: dict = Depends(get_access_token_payload),
    db: Session = Depends(get_db),
):
    offer = db.scalar(select(Offer).options(joinedload(Offer.customer), joinedload(Offer.items)).where(Offer.id == offer_id))
    if not offer:
        raise HTTPException(status_code=404, detail="Teklif bulunamadı.")
    
    ensure_company_access(offer.company_id, token_payload)

    return OfferResponse(
        id=offer.id,
        company_id=offer.company_id,
        customer_id=offer.customer_id,
        status=offer.status,
        total_price=offer.total_price,
        customer=CustomerMiniResponse(id=offer.customer.id, full_name=offer.customer.full_name) if offer.customer else None,
        items=[OfferItemResponse(id=i.id, item_name=i.item_name, quantity=i.quantity, unit_price=i.unit_price) for i in offer.items]
    )

@router.put("/offers/{offer_id}", tags=["Offers"], response_model=OfferResponse)
def update_offer(
    offer_id: int,
    payload: OfferCreateRequest,
    token_payload: dict = Depends(get_access_token_payload),
    db: Session = Depends(get_db),
):
    offer = db.scalar(select(Offer).where(Offer.id == offer_id))
    if not offer:
        raise HTTPException(status_code=404, detail="Teklif bulunamadı.")
    
    ensure_company_access(offer.company_id, token_payload)

    if offer.customer_id != payload.customer_id:
        customer = db.scalar(select(Customer).where(Customer.id == payload.customer_id))
        if not customer or customer.company_id != offer.company_id:
            raise HTTPException(status_code=404, detail="Müşteri bulunamadı veya yetkiniz yok.")
        offer.customer_id = payload.customer_id

    offer.status = payload.status
    
    # Güncelleme için en temiz yol: Mevcut ürün kalemlerini sil ve yenilerini yaz
    db.execute(OfferItem.__table__.delete().where(OfferItem.offer_id == offer_id))
    
    total_price = 0
    for item in payload.items:
        total_price += item.quantity * item.unit_price
        new_item = OfferItem(
            offer_id=offer.id,
            item_name=item.item_name.strip(),
            quantity=item.quantity,
            unit_price=item.unit_price
        )
        db.add(new_item)
        
    offer.total_price = total_price
    db.commit()

    return get_offer(offer.id, token_payload, db)

@router.delete("/offers/{offer_id}", tags=["Offers"], response_model=MessageResponse)
def delete_offer(
    offer_id: int,
    token_payload: dict = Depends(get_access_token_payload),
    db: Session = Depends(get_db),
):
    offer = db.scalar(select(Offer).where(Offer.id == offer_id))
    if not offer:
        raise HTTPException(status_code=404, detail="Teklif bulunamadı.")
    
    ensure_company_access(offer.company_id, token_payload)

    # Önce alt ürün kalemlerini, sonra ana teklifi siliyoruz
    db.execute(OfferItem.__table__.delete().where(OfferItem.offer_id == offer_id))
    db.delete(offer)
    db.commit()
    
    return MessageResponse(message="Teklif başarıyla silindi.")