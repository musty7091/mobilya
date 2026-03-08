from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base_model import BaseModel

class Offer(BaseModel):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    
    # Yeni Profesyonel Alanlar
    currency = Column(String, default="TRY")        # TRY, USD, EUR
    tax_rate = Column(Float, default=20.0)         # KDV Oranı (Örn: 20)
    discount_amount = Column(Float, default=0.0)   # İskonto Tutarı (TL bazında)
    subtotal = Column(Float, default=0.0)          # İskontosuz Toplam
    total_price = Column(Float, default=0.0)       # İskonto düşülmüş ve KDV eklenmiş Final Fiyat
    
    status = Column(String, default="Beklemede")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # İlişkiler
    customer = relationship("Customer")
    company = relationship("Company")
    items = relationship("OfferItem", back_populates="offer", cascade="all, delete-orphan")

class OfferItem(BaseModel):
    __tablename__ = "offer_items"

    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(Integer, ForeignKey("offers.id", ondelete="CASCADE"), nullable=False)
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, default=0.0)

    # İlişkiler
    offer = relationship("Offer", back_populates="items")