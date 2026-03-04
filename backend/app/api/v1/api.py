from fastapi import APIRouter

from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.db_ping import router as db_ping_router
from app.api.v1.routes.companies import router as companies_router
from app.api.v1.routes.users import router as users_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(db_ping_router)
api_router.include_router(companies_router)
api_router.include_router(users_router)