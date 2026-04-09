from fastapi import APIRouter,Depends
from app.schemas import UserInfo
from app.auth import get_current_user

router = APIRouter(prefix="/users",tags=["users"])

@router.get("/me", response_model=UserInfo)
def read_me(current_user=Depends(get_current_user)):
    return UserInfo(username=current_user["username"])