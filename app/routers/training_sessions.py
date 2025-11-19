from fastapi import APIRouter, Depends, HTTPException, status
from datetime import date
from app.database import database
from app.dependencies.auth import get_current_user
from typing import List
from app.models import (
    TrainingSessionCreate,
    TrainingSessionUpdate,
    TrainingSessionResponse,
    TrainingSessionWithActivitiesResponse
)

supabase = database.get_supabase()

router = APIRouter(
    prefix="/api/training-sessions",
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

# @router.get("", response_model=List[TrainingSessionResponse])
# async def get_training_sessions(
#     start_date: date | None = None,
#     end_date: date | None = None,
#     current_user: dict = Depends(get_current_user)
# ):
#     """
#     取得當前使用者的所有訓練課程
    
#     回傳按資料建立時間降冪排序的課程列表
#     """
#     try:
#          # 初始化基礎查詢
#         query = supabase.table("training_sessions")\
#             .select("*")\
#             .eq("user_id", current_user["id"])
            
#         # 選擇性地加入日期過濾條件
#         if start_date:
#             query = query.gte("date", start_date.isoformat())
            
#         if end_date:
#             # PostgreSQL/Supabase 查詢：date 小於等於 end_date (lte)
#             query = query.lte("date", end_date.isoformat())
#         else:
#             query = query.lte("date", start_date.isoformat())
#         # 執行排序和查詢
#         response = query.order("created_at", desc=True).execute()
        
#         return response.data if response.data else []
    
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to fetch training sessions: {str(e)}"


@router.get("/with-activities", response_model=List[TrainingSessionWithActivitiesResponse])
async def get_training_sessions_with_activities(
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: dict = Depends(get_current_user)
):
    """
    取得訓練課程（包含活動和記錄）- **單次查詢優化**
    """
    try:
        # 建立單次巢狀查詢
        # select("*, activities:training_activities(*, records:activity_records(*))")
        query = supabase.table("training_sessions")\
            .select("*, activities:training_activities(*, records:activity_records(*))")\
            .eq("user_id", current_user["id"])
        
        # 處理日期過濾
        if start_date:
            query = query.gte("date", start_date.isoformat())
            
        if end_date:
            query = query.lte("date", end_date.isoformat())
        elif start_date:
            # 如果只有 start_date，查詢當天或之後的課程
            query = query.lte("date", start_date.isoformat()) 
            
        # 執行查詢
        query = query.order("created_at", desc=True)
        sessions_response = query.execute()
   
        if not sessions_response.data:
            return []

        return sessions_response.data
    
    except Exception as e:
        print(f"Error fetching sessions with activities: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch sessions with activities: {str(e)}"
        )

# @router.get("/{session_id}", response_model=TrainingSessionResponse)
# async def get_training_session(
#     session_id: str,
#     current_user: dict = Depends(get_current_user)
# ):
#     """取得特定訓練課程的詳細資訊"""
#     try:
#         response = supabase.table("training_sessions")\
#             .select("*")\
#             .eq("id", session_id)\
#             .eq("user_id", current_user["id"])\
#             .execute()
        
#         if not response.data:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Training session not found"
#             )
        
#         return response.data[0]
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to fetch training session: {str(e)}"
#         )

@router.put("/{session_id}", response_model=TrainingSessionResponse)
async def update_training_session(
    session_id: str,
    session_update: TrainingSessionUpdate,
    current_user: dict = Depends(get_current_user)
):
    """更新選定課程（id）資訊"""
    try:
        # 確認該課程存在且屬於當前使用者
        existing = supabase.table("training_sessions")\
            .select("*")\
            .eq("id", session_id)\
            .eq("user_id", current_user["id"])\
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training session not found"
            )
        
        # 準備更新資料（只更新有提供的欄位）
        update_data = {}
        if session_update.title is not None:
            update_data["title"] = session_update.title
        if session_update.date is not None:
            update_data["date"] = session_update.date.isoformat()
        if session_update.note is not None:
            update_data["note"] = session_update.note
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # 執行更新
        response = supabase.table("training_sessions")\
            .update(update_data)\
            .eq("id", session_id)\
            .execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update training session"
            )
        
        return response.data[0]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update training session: {str(e)}"
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