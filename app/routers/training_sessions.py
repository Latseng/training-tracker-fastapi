from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import database
from typing import List
from app.models import (
    TrainingSessionCreate,
    TrainingSessionResponse
)

supabase = database.get_supabase()
oauth2_scheme = HTTPBearer()

# 使用者驗證
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    """
    這個函數會：
    1. 自動從 Authorization header 取得 Token
    2. 驗證 Token 的有效性
    3. 從 Token 或資料庫取得使用者資料
    4. 回傳使用者資料
    
    參數說明：
    - credentials: HTTPAuthorizationCredentials
      - credentials.scheme: "Bearer"
      - credentials.credentials: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    """
    token = credentials.credentials
    
    try:
        response = supabase.auth.get_user(token)
        print("使用者資料", response)
        if not response.user:
            raise HTTPException(401, "Invalid token")
        # 回傳使用者資料
        return {
            "id": response.user.id,
            "email": response.user.email,
            "username": response.user.user_metadata.get("username")
        }
    except Exception:
        raise HTTPException(401, "Invalid or expired token")


router = APIRouter(
    prefix="/training-sessions",
    tags=["training sessions"]
)

@router.post("", response_model=TrainingSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_training_session(
    session: TrainingSessionCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    建立新的訓練課程
    
    - **title**: 訓練標題（可選）
    - **date**: 訓練日期（必填）
    - **note**: 備註（可選）
    
    必須通過身份驗證
    """
    try:
        # 準備要插入到 Table的資料
        session_data = {
            "user_id": current_user["id"],
            "title": session.title,
            "date": session.date.isoformat(),
            "note": session.note
        }
        
        # 插入資料到 Supabase
        response = supabase.table("training_sessions").insert(session_data).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create training session"
            )
        
        return response.data[0]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@router.get("", response_model=List[TrainingSessionResponse])
async def get_training_sessions(
    current_user: dict = Depends(get_current_user)
):
    """
    取得當前使用者的所有訓練課程
    
    回傳按日期降冪排序的課程列表
    """
    try:
        response = supabase.table("training_sessions")\
            .select("*")\
            .eq("user_id", current_user["id"])\
            .order("date", desc=True)\
            .execute()
        
        return response.data if response.data else []
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch training sessions: {str(e)}"
        )