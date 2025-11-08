from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(tags=["auth"])

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")  

supabase: Client = create_client(url, key)

class SignupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/signup")
def signup(payload: SignupRequest):
    try:
        # 呼叫 Supabase Auth API
        res = supabase.auth.sign_up({
            "email": payload.email,
            "password": payload.password,
            "options": {
                "data": {"username": payload.username}
            }
        })

        if res.user is None:
            raise HTTPException(status_code=400, detail="註冊失敗，Email 可能已被使用")
        
        # 若帳號註冊成功則建立一筆使用者資料，並回傳給前端
        auth_user_id = res.user.id  
        supabase.table("users").insert({
        "id": auth_user_id,  # 關鍵：用同樣的 id
        "email": payload.email,
        "username": payload.username
        }).execute()

        return {"message": "註冊成功", "user_id": auth_user_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/login")
async def login(user: LoginRequest):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": user.email,
            "password": user.password,
        })
        print(response)
        # 取出 token 與使用者資訊
        return {
            "access_token": response.session.access_token,
            "user": {
                "id": response.user.id,
                "email": response.user.email,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))