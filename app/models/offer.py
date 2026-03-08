from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class Offer(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), index=True)
    
    title = Column(String, nullable=False)
    total_amount = Column(Float, default=0.0)
    status = Column(String, default="draft")  # draft, sent, approved, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # İlişkiler
    customer = relationship("Customer", backref="offers")
    company = relationship("Company", backref="offers")
    
    # Bir teklif silinirse, içindeki kalemler de silinsin (cascade)
    items = relationship("OfferItem", back_populates="offer", cascade="all, delete-orphan")