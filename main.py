from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.contacts import router as contacts_router
from app.api.auth import router as auth_router
from app.core.config import settings

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Contacts API",
    description="API for managing contacts with CRUD operations and JWT authentication",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

app.include_router(auth_router)
app.include_router(contacts_router)


@app.get("/")
def read_root():
    return {"message": "Contacts API", "docs": "/docs"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
