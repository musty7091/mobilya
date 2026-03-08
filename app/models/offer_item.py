from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class OfferItem(Base):
    __tablename__ = "offer_items"

    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(Integer, ForeignKey("offers.id"), nullable=False)
    
    # Standart bir ürün seçilirse ID'si buraya gelecek.
    # Ama özel tasarım (esnek) bir ürünse burası boş (null) kalacak.
    product_id = Column(Integer, nullable=True) 
    
    # Ürünün ekranda görünecek adı (Örn: "Özel Ölçü Gürgen Masa" veya "Standart Sandalye")
    name = Column(String, nullable=False)
    
    # Kaç adet üretilecek/satılacak?
    quantity = Column(Integer, default=1, nullable=False)
    
    # Tekinin fiyatı
    unit_price = Column(Float, nullable=False)
    
    # Toplam fiyat (Adet * Tekil Fiyat)
    total_price = Column(Float, nullable=False)

    # Teklif tablosu ile olan bağlantı
    offer = relationship("Offer", back_populates="items")