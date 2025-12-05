from fastapi import APIRouter, HTTPException, status, Request, Response, Depends
from app.model.auth import (
    SignupRequest,
    LoginRequest,
    EmailSchema
)
from app.database import database
from supabase import AuthApiError
from app.dependencies.auth import get_current_user
from app.dependencies.limiter import limiter

router = APIRouter(prefix="/api/auth", tags=["auth"])

supabase = database.get_supabase()

@router.post("/signup")
def signup(request: SignupRequest):
    """使用者註冊 - 使用 Supabase Auth"""
    try:
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
        
        auth_user_id = response.user.id 

        supabase.table("users").insert({
        "id": auth_user_id,  # 關鍵：用同樣的 id
        "email": request.email,
        "username": request.username
        }).execute()

        return {"message": "註冊成功", "user_id": auth_user_id, "email":response.user.email}

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

@router.post("/resend-verify")
@limiter.limit("3/minute")
async def resend_verify(request: Request, body: EmailSchema):
    """
    重新寄發註冊驗證信
    """
    try:
        supabase.auth.resend(
            {
                "type": "signup",
                "email": body.email
            }
        )
        return {"message": "驗證信已重新寄送，請檢查您的信箱"}
    except Exception as e:
        # Supabase 對重發信件有頻率限制（Rate Limit），通常是每分鐘一次
        error_msg = str(e).lower()
        if "rate limit" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="發送過於頻繁，請稍後再試"
            )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"重發失敗: {str(e)}"
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
        response.set_cookie("access_token", supabase_response.session.access_token, httponly=True, secure=True, samesite="Lax", max_age=60*60)
        response.set_cookie("refresh_token", supabase_response.session.refresh_token, httponly=True, secure=True, samesite="Lax", max_age=60*60*24*30)

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
    
@router.get("/users/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """
    前端用來確認使用者是否登入，並獲取使用者資料的接口。
    如果 cookie 無效，get_current_user 會直接拋出 401 錯誤。
    """
    return current_user
    
@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logout successful"}