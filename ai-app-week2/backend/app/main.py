from fastapi import FastAPI, HTTPException, Depends
from app.schemas import RegisterRequest, LoginRequest, TokenResponse, UserInfo
from app.db import fake_users_db
from app.auth import hash_password, verify_password, create_access_token, get_current_user

app = FastAPI(title="AI App API", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "OK"}

@app.post("/auth/register")
def register(data: RegisterRequest):
    if data.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    fake_users_db[data.username]={
        "username": data.username,
        "hashed_password": hash_password(data.password)
    }
    return {"message": "User registered successfully"}

@app.post("/auth/login")
def login(data: LoginRequest):
    user = fake_users_db.get(data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    if not verify_password(data.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    
    token = create_access_token(data.username)
    return TokenResponse(access_token=token)

@app.get("/users/me", response_model=UserInfo)
def read_me(current_user=Depends(get_current_user)):
    return UserInfo(username=current_user["username"])