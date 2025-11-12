from fastapi import APIRouter, HTTPException, status, Response
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
def signup(request: SignupRequest):
    """使用者註冊 - 使用 Supabase Auth"""
    try:
        # 呼叫 Supabase Auth API
        response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {"username": request.username}
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
        "email": request.email,
        "username": request.username
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
async def login(request: LoginRequest, response: Response):
    """使用者登入 - 使用 Supabase Auth"""
    try:
        # 使用 Supabase 進行身份驗證
        supabase_response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        # 檢查是否登入成功
        if not supabase_response.user or not supabase_response.session:
            raise HTTPException(
                status_code=401,
                detail="登入失敗：電子郵件或密碼錯誤"
            )
        
        # 設定HttpOnly Cookies
        response.set_cookie("access_token", supabase_response.session.access_token, httponly=True, secure=False, samesite="lax", max_age=60*60)
        response.set_cookie("refresh_token", supabase_response.session.refresh_token, httponly=True, secure=False, samesite="lax", max_age=60*60*24*30)

        # 回傳登入資訊
        return {
            "message": "login ok",
            "user": {
                "id": supabase_response.user.id,
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
    
@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logout successful"}