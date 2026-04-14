from fastapi import FastAPI
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from app.routers import health, auth, users
from app.exceptions import http_exception_handler
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI App API", version="0.1.0")
app.add_exception_handler(FastAPIHTTPException, http_exception_handler)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)