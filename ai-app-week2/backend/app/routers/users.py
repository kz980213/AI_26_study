from fastapi import APIRouter,Depends, HTTPException
from app.schemas import UserInfo
from app.auth import get_current_user, hash_password, verify_password
from app.schemas import ChangePasswordRequest
from app.database import get_db
from app.models import User
from sqlalchemy.orm import Session

router = APIRouter(prefix="/users",tags=["users"])

@router.get("/me", response_model=UserInfo)
def read_me(current_user:User=Depends(get_current_user)):
    return UserInfo(username=current_user.username)

@router.put("/me/password")
def change_password(
        data: ChangePasswordRequest, 
        current_user:User=Depends(get_current_user),
        db:Session=Depends(get_db)
    ):
    if not verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="old password is incorrect")
    if data.new_password == data.old_password:
        raise HTTPException(status_code=400, detail="new password cannot be the same as old password")
    current_user.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"message": "Password updated successfully"}