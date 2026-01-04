from fastapi import HTTPException, status
from supabase import Client, AuthApiError
from app.database import database

class AuthService:
    def __init__(self):
        self.supabase: Client = database.get_supabase_client()

    def signup(self, email: str, password: str, username: str):
        try:
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {"username": username}
                }
            })

            if not response.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="使用者註冊失敗"
                )
            
            auth_user_id = response.user.id 

            self.supabase.table("users").insert({
                "id": auth_user_id,
                "email": email,
                "username": username
            }).execute()

            return {
                "message": "註冊成功", 
                "user_id": auth_user_id, 
                "email": response.user.email
            }

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
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(e)}"
            )

    def login(self, email: str, password: str):
        try:
            supabase_response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if not supabase_response.user or not supabase_response.session:
                raise HTTPException(
                    status_code=401,
                    detail="登入失敗：電子郵件或密碼錯誤"
                )
            
            return supabase_response
            
        except AuthApiError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=" Email 或密碼錯誤"
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Login failed: {str(e)}"
            )

    def resend_verification(self, email: str):
        try:
            self.supabase.auth.resend({
                "type": "signup",
                "email": email
            })
            return {"message": "驗證信已重新寄送，請檢查您的信箱"}
        except Exception as e:
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

    def get_user_by_token(self, access_token: str):
        try:
            response = self.supabase.auth.get_user(access_token)
            if not response.user:
                raise HTTPException(401, "Invalid or expired token")
            
            return {
                "id": response.user.id,
                "email": response.user.email,
                "username": response.user.user_metadata.get("username")
            }
        except Exception:
            raise HTTPException(401, "Invalid or expired token")
