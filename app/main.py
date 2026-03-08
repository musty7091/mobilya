from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.APP_DEBUG
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tüm rotalarımız (müşteriler, teklifler, auth) artık api_router içinde olduğu için tek satır yeterli:
app.include_router(api_router, prefix="/api/v1")

@app.get("/", tags=["Root"])
def root() -> dict:
    return {
        "message": "mobilya backend is running"
    }