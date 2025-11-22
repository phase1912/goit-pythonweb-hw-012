from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.contacts import router as contacts_router
from app.api.auth import router as auth_router

app = FastAPI(
    title="Contacts API",
    description="API for managing contacts with CRUD operations and JWT authentication",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
