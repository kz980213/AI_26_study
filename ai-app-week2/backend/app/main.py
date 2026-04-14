from fastapi import FastAPI
from fastapi.exceptions import HTTPException as FastAPIHTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from app.routers import health, auth, users
from app.exceptions import http_exception_handler, validation_exception_handler
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI App API", version="0.1.0")
app.add_exception_handler(FastAPIHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_middleware(
    CORSMiddleware, 
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        ], 
        allow_methods=["*"], 
        allow_headers=["*"]
)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)