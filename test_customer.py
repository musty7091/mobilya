from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.customer import Customer
from app.models.company import Company

DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/mobilya"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def create_test_customer():
    db = SessionLocal()
    # 1. Şirket var mı bak
    company = db.query(Company).first()
    if not company:
        print("Önce bir şirket lazım!")
        return

    # 2. Müşteri ekle
    new_customer = Customer(
        company_id=company.id,
        full_name="Test Müşterisi",
        phone="5551234567",
        email="test@musteri.com",
        address="Ev Adresi",
        notes="Bu bir test kaydıdır.",
        is_active=True
    )
    db.add(new_customer)
    db.commit()
    print(f"Başarıyla eklendi! Müşteri ID: {new_customer.id}")
    db.close()

create_test_customer()