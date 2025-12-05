
from fastapi import APIRouter, Depends, HTTPException, status, Response
from app.model.training_activities import (
    TrainingActivityWithRecordsCreate,
    TrainingActivityWithRecordsResponse,
    ActivityRecordUpdate
)
from app.dependencies.auth import get_current_user
from app.database import database
from typing import List
from decimal import Decimal

router = APIRouter(
    prefix="/api/training-activities",
    tags=["Training Activities"]
)
supabase = database.get_supabase()

@router.post("", response_model=TrainingActivityWithRecordsResponse, status_code=status.HTTP_201_CREATED)
async def create_activity_with_records(
    activity: TrainingActivityWithRecordsCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    建立訓練活動（包含記錄）
    
    一次性建立活動和所有相關的記錄，確保資料一致性。
    如果任何步驟失敗，會回滾所有變更。
    """
    try:
        # 1. 驗證 session 存在且屬於當前使用者
        session_response = supabase.table("training_sessions")\
            .select("*")\
            .eq("id", activity.session_id)\
            .eq("user_id", current_user["id"])\
            .execute()
        
        if not session_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training session not found or you don't have permission"
            )
        
        # 2. 建立 training_activity
        activity_data = {
            "session_id": activity.session_id,
            "name": activity.name,
            "category": activity.category,
            "description": activity.description
        }
        
        activity_response = supabase.table("training_activities")\
            .insert(activity_data)\
            .execute()

        if not activity_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create training activity"
            )
        
        created_activity = activity_response.data[0]
        activity_id = created_activity["id"]
        
        # 3. 建立 activity_records（批次插入）
        created_records = []
        
        if activity.activity_records:
            records_data = []
            for record in activity.activity_records:
                record_data = {
                    "activity_id": activity_id,
                    "set_number": record.set_number,
                    "repetition": record.repetition,
                    "weight": float(record.weight) if record.weight else None,
                    "duration": record.duration,
                    "distance": float(record.distance) if record.distance else None,
                    "score": float(record.score) if record.score else None
                }
                records_data.append(record_data)
            
            # 批次插入所有 records
            if records_data:
                records_response = supabase.table("activity_records")\
                    .insert(records_data)\
                    .execute()
                
                if not records_response.data:
                    # 如果 records 插入失敗，刪除已建立的 activity
                    supabase.table("training_activities").delete().eq("id", activity_id).execute()
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to create activity records"
                    )
                
                created_records = records_response.data

        # 4. 組合回應
        return {
            "id": created_activity["id"],
            "session_id": created_activity["session_id"],
            "name": created_activity["name"],
            "category": created_activity["category"],
            "description": created_activity["description"],
            "records": created_records
        }
    
    except Exception as e:
        print(f"Error creating activity with records: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create activity: {str(e)}"
        )

@router.put("/{activity_id}/records", status_code=status.HTTP_204_NO_CONTENT)
async def update_activity_records(
    activity_id: str,
    records_to_process: List[ActivityRecordUpdate], 
    current_user: dict = Depends(get_current_user)
):
    """
    批量更新特定 Activity 底下的所有（Records），
    同時處理被刪除的記錄 (執行集合替換邏輯)。
    注意：本路由操作目前並未有事務更新機制，若部分失敗無回滾機制
    """
    
    # 1. 數據驗證與準備
    if not records_to_process:
        # 如果前端傳來空列表，意味著要刪除該 activity 下所有 records
        ids_to_keep = []
    else:
        # 提取所有需要保留 (更新/插入) 的 Record ID 集合
        ids_to_keep = [record.id for record in records_to_process if record.id]
        
        # 確保所有傳入的 records 都屬於這個 activity_id
        for record in records_to_process:
            if record.activity_id != activity_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Record ID {record.id} belongs to a different activity."
                )
    try:
        # 刪除不再存在的 Records ---
        if ids_to_keep:
            # 刪除所有屬於該 activity，但其 ID 不在 ids_to_keep 列表中的記錄
            supabase.table("activity_records")\
                .delete()\
                .eq("activity_id", activity_id)\
                .not_.in_("id", ids_to_keep)\
                .execute()
        else:
            # 如果 ids_to_keep 為空，則刪除該 activity 下所有記錄
            supabase.table("activity_records")\
                .delete()\
                .eq("activity_id", activity_id)\
                .execute()
            
        # 更新/插入現有及新增的 Records ---
        updates = []
        for record in records_to_process:
            record_dict = record.model_dump(exclude_none=True, by_alias=False)
            
            # **關鍵修復：手動將 Decimal 轉換為 float**
            # 遍歷字典並轉換 Decimal 物件
            cleaned_dict = {}
            for key, value in record_dict.items():
                if isinstance(value, Decimal):
                    # 將 Decimal 轉換為 float
                    cleaned_dict[key] = float(value) 
                else:
                    cleaned_dict[key] = value
            
            updates.append(cleaned_dict)

        if updates:
            # 執行 upsert
            # 必須依賴 activity_records 表中的 primary key (id) 來判斷是更新還是插入
            upsert_response = supabase.table("activity_records").upsert(updates)\
                .execute()
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except Exception as e:
        print(f"Error during set replacement for activity {activity_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update activity records: {str(e)}"
        )

@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_training_session(
    activity_id: str,
    current_user: dict = Depends(get_current_user)
):
    """刪除訓練項目。由於設定了 ON DELETE CASCADE，相關的 records 會自動刪除"""
    try:
        # 驗證 activity 存在且屬於當前使用者的 session
        activity_response = supabase.table("training_activities")\
            .select("*, training_sessions!inner(user_id)")\
            .eq("id", activity_id)\
            .execute()
        
        if not activity_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training activity not found"
            )
        
        # 檢查是否屬於當前使用者
        if activity_response.data[0]["training_sessions"]["user_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this activity"
            )
        
        # 刪除活動（records 會自動刪除）
        supabase.table("training_activities").delete().eq("id", activity_id).execute()
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete activity: {str(e)}"
        )