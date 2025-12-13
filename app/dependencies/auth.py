from fastapi import HTTPException, status, Request
from app.database import database

supabase = database.get_supabase_client()

# 請求身份驗證
async def get_current_user(request: Request):
    """從 Cookie 取得使用者驗證資訊"""
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        response = supabase.auth.get_user(access_token)
        if not response.user:
            raise HTTPException(401, "Invalid or expired token")
        
        # 回傳使用者資料
        return {
            "id": response.user.id,
            "email": response.user.email,
            "username": response.user.user_metadata.get("username")
        }
    except Exception:
        raise HTTPException(401, "Invalid or expired token")
