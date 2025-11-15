
from fastapi import APIRouter, Depends, HTTPException, status
from app.models import (
    TrainingActivityWithRecordsCreate,
    TrainingActivityWithRecordsResponse,
)
from app.dependencies.auth import get_current_user
from app.database import database

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
            "activity_records": created_records
        }
    
    except Exception as e:
        print(f"Error creating activity with records: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create activity: {str(e)}"
        )