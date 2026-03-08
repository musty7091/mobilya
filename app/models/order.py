from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), index=True)
    
    # Eğer bu sipariş bir tekliften dönüştürüldüyse, o teklifin ID'si burada tutulur
    offer_id = Column(Integer, ForeignKey("offers.id"), nullable=True)
    
    # Sipariş numarası veya başlığı (Örn: "SIP-2026-001" veya "Mutfak Dolabı Siparişi")
    order_number = Column(String, nullable=False)
    
    total_amount = Column(Float, default=0.0)
    
    # Siparişin durumu: pending (bekliyor), production (üretimde), completed (tamamlandı), cancelled (iptal)
    status = Column(String, default="pending") 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # İlişkiler
    customer = relationship("Customer", backref="orders")
    company = relationship("Company", backref="orders")
    offer = relationship("Offer", backref="orders")
    
    # Siparişin içindeki kalemler silinirse veya güncellenirse otomatik algıla
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")