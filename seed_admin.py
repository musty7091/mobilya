from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.models.company import Company
from app.core.security import get_password_hash
from app.db.base import Base
import os

# Veritabanı bağlantısı (.env dosyasındaki URL ile aynı olmalı)
DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/mobilya"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_data():
    db = SessionLocal()
    
    # 1. Önce bir şirket oluşturalım
    company = db.query(Company).filter(Company.name == "Test Mobilya").first()
    if not company:
        company = Company(name="Test Mobilya", code="MOB01")
        db.add(company)
        db.commit()
        db.refresh(company)
        print("Şirket oluşturuldu.")

    # 2. Admin kullanıcısını oluşturalım
    admin = db.query(User).filter(User.email == "admin@mobilya.com").first()
    if not admin:
        admin = User(
            company_id=company.id,
            full_name="Admin",
            email="admin@mobilya.com",
            password_hash=get_password_hash("sifre123"),
            is_active=True,
            is_superuser=True
        )
        db.add(admin)
        db.commit()
        print("Admin kullanıcısı oluşturuldu: admin@mobilya.com / sifre123")
    else:
        print("Admin zaten mevcut.")
    
    db.close()

if __name__ == "__main__":
    seed_data()