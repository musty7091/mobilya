# mobilya

Mobilya işletmeleri için geliştirilen, sipariş merkezli çalışan, güvenli, modüler ve ticari olarak satılabilir bir web uygulama projesidir.

## Proje Amacı

Bu proje;

- teklif sürecini,
- sipariş yönetimini,
- üretim takibini,
- montaj sürecini,
- dosya ve not yönetimini,
- iş bazlı finansal takibi,
- kaporo, ödeme ve ekstre mantığını

tek çatı altında yöneten modern bir web uygulama olarak tasarlanmaktadır.

## Temel Yaklaşım

Sistem aşağıdaki temel ilkelere göre geliştirilecektir:

- güvenlik tavizsiz olacak
- veritabanı değişiklikleri yalnızca migration ile yapılacak
- sistem baştan büyümeye uygun tasarlanacak
- dosya yapısı modüler olacak
- devasa tek dosya mantığı olmayacak
- para hesaplarında float kullanılmayacak
- kritik kayıtlar sessizce değiştirilmeyecek
- role + permission birlikte kullanılacak
- tenant / kapsam kontrolü uygulanacak
- API-first yaklaşımı benimsenecek

## Teknoloji Kararları

### Backend
- FastAPI
- PostgreSQL
- SQLAlchemy 2.x style
- Alembic
- Pydantic

### Frontend
- Next.js
- TypeScript
- Tailwind CSS

## Ana Sistem Mantığı

Sistemin kalbi sipariş olacaktır.

Sipariş altında aşağıdaki yapılar toplanacaktır:

- müşteri bilgisi
- teklif ilişkisi
- üretim görevi
- montaj görevi
- notlar
- dosyalar
- finans hareketleri
- sipariş bazlı ekstre
- durum geçmişi

## Geliştirme Yaklaşımı

Bu proje adım adım, modüler ve deploy edilebilir şekilde geliştirilecektir.

Her aşamada:

- tam dosya mantığı ile ilerlenir
- dosya konumu açıkça belirtilir
- kopyala-yapıştır uygulanabilir içerik üretilir
- güvenlik ve mimari kurallar korunur

## Repo Yapısı

```text
mobilya/
  backend/
  frontend/
  docs/
  infra/
  .gitignore
  README.md