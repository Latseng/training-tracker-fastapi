from fastapi import APIRouter, Request, Response, Depends
from app.models.auth import (
    SignupRequest,
    LoginRequest,
    EmailSchema
)
from app.dependencies.auth import get_current_user, get_auth_service
from app.dependencies.limiter import limiter
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/signup")
def signup(request: SignupRequest, auth_service: AuthService = Depends(get_auth_service)):
    """使用者註冊 - 使用 Supabase Auth"""
    return auth_service.signup(request.email, request.password, request.username)

@router.post("/resend-verify")
@limiter.limit("3/minute")
async def resend_verify(request: Request, body: EmailSchema, auth_service: AuthService = Depends(get_auth_service)):
    """
    重新寄發註冊驗證信
    """
    return auth_service.resend_verification(body.email)

@router.post("/login")
async def login(request: LoginRequest, response: Response, auth_service: AuthService = Depends(get_auth_service)):
    """使用者登入 - 使用 Supabase Auth"""
    supabase_response = auth_service.login(request.email, request.password)
    
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
