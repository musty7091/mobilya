from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    
    # Standart ürünse ID'si, özel üretimse boş (null) kalacak
    product_id = Column(Integer, nullable=True) 
    
    # Ürünün ekranda görünecek adı
    name = Column(String, nullable=False)
    
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)

    # Sipariş tablosu ile olan bağlantı
    order = relationship("Order", back_populates="items")