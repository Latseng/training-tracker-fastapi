from fastapi import APIRouter, Depends, HTTPException, status
from app.database import database
from app.dependencies.auth import get_current_user
from typing import List
from app.models import (
    TrainingSessionCreate,
    TrainingSessionResponse
)

supabase = database.get_supabase()

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
    
    回傳按資料建立時間降冪排序的課程列表
    """
    try:
        response = supabase.table("training_sessions")\
            .select("*")\
            .eq("user_id", current_user["id"])\
            .order("created_at", desc=True)\
            .execute()
        
        return response.data if response.data else []
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch training sessions: {str(e)}"
        )
    
@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_training_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """刪除訓練課程"""
    try:
        response = supabase.table("training_sessions")\
            .delete()\
            .eq("id", session_id)\
            .eq("user_id", current_user["id"])\
            .execute()
        # 檢查是否成功刪除（data為空表示沒有匹配到可刪除的行，可能是資料ID不存在或User ID不匹配）
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training session not found or you don't have permission to delete it."
            )
        
        return
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete training session: {str(e)}"
        )