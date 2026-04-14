from fastapi import APIRouter, HTTPException, Depends
from app.schemas import RegisterRequest, LoginRequest, TokenResponse
from app.auth import hash_password, verify_password, create_access_token
from app.database import get_db
from sqlalchemy.orm import Session
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])
@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user = User(username=data.username, hashed_password=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User registered successfully"}

@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    
    token = create_access_token(data.username)
    return TokenResponse(access_token=token)