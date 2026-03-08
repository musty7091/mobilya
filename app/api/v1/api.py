from fastapi import APIRouter

from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.db_ping import router as db_ping_router
from app.api.v1.routes.companies import router as companies_router
from app.api.v1.routes.users import router as users_router
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.customers import router as customers_router
from app.api.v1.routes.offers import router as offers_router
from app.api.v1.routes.orders import router as orders_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(db_ping_router)
api_router.include_router(companies_router)
api_router.include_router(users_router)
api_router.include_router(auth_router)
api_router.include_router(customers_router)
api_router.include_router(offers_router)
api_router.include_router(orders_router)