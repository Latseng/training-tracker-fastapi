from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from app.database import database
from supabase import AuthApiError

router = APIRouter(tags=["auth"])

supabase = database.get_supabase()

class SignupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/signup")
def signup(payload: SignupRequest):
    """使用者註冊 - 使用 Supabase Auth"""
    try:
        # 呼叫 Supabase Auth API
        response = supabase.auth.sign_up({
            "email": payload.email,
            "password": payload.password,
            "options": {
                "data": {"username": payload.username}
            }
        })

        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="使用者註冊失敗"
            )
        
        # 若帳號註冊成功則建立一筆使用者資料，並回傳給前端
        auth_user_id = response.user.id  
        supabase.table("users").insert({
        "id": auth_user_id,  # 關鍵：用同樣的 id
        "email": payload.email,
        "username": payload.username
        }).execute()

        return {"message": "註冊成功", "user_id": auth_user_id}

    except AuthApiError as e:
        error_msg = str(e).lower()
        if "already registered" in error_msg or "user already registered" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email已註冊"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login")
async def login(payload: LoginRequest):
    """使用者登入 - 使用 Supabase Auth"""
    try:
        # 使用 Supabase 進行身份驗證
        response = supabase.auth.sign_in_with_password({
            "email": payload.email,
            "password": payload.password
        })
        
        # 檢查是否登入成功
        if not response.user or not response.session:
            raise HTTPException(
                status_code=401,
                detail="登入失敗：電子郵件或密碼錯誤"
            )
        
        # 回傳登入資訊
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user": {
                "id": response.user.id,
                # "email": response.user.email,
                "username": response.user.user_metadata.get("username")
            }
        }
        
    except AuthApiError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=" Email 或密碼錯誤"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )
