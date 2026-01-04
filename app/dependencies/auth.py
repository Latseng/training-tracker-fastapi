from fastapi import HTTPException, status, Request, Depends
from app.services.auth_service import AuthService

def get_auth_service() -> AuthService:
    return AuthService()

# 請求身份驗證
async def get_current_user(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """從 Cookie 取得使用者驗證資訊"""
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return auth_service.get_user_by_token(access_token)
