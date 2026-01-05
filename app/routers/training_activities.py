from fastapi import APIRouter, Depends, status, Response
from app.models.training_activities import (
    TrainingActivityWithRecordsCreate,
    TrainingActivityWithRecordsResponse,
    ActivityRecordUpdate
)
from app.dependencies.auth import get_current_user
from app.services.activity_service import ActivityService
from typing import List

router = APIRouter(
    prefix="/api/training-activities",
    tags=["Training Activities"]
)

@router.post("", response_model=TrainingActivityWithRecordsResponse, status_code=status.HTTP_201_CREATED)
async def create_activity_with_records(
    activity: TrainingActivityWithRecordsCreate,
    current_user: dict = Depends(get_current_user),
    service: ActivityService = Depends()
):
    """
    建立訓練活動（包含記錄）
    
    一次性建立活動和所有相關的記錄，確保資料一致性。
    如果任何步驟失敗，會回滾所有變更。
    """
    return service.create_activity(current_user["id"], activity)

@router.put("/{activity_id}/records", status_code=status.HTTP_204_NO_CONTENT)
async def update_activity_records(
    activity_id: str,
    records_to_process: List[ActivityRecordUpdate], 
    current_user: dict = Depends(get_current_user),
    service: ActivityService = Depends()
):
    """
    批量更新特定 Activity 底下的所有（Records），
    同時處理被刪除的記錄 (執行集合替換邏輯)。
    注意：本路由操作目前並未有事務更新機制，若部分失敗無回滾機制
    """
    service.update_records(activity_id, records_to_process)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_training_activity(
    activity_id: str,
    current_user: dict = Depends(get_current_user),
    service: ActivityService = Depends()
):
    """刪除訓練項目。由於設定了 ON DELETE CASCADE，相關的 records 會自動刪除"""
    service.delete_activity(current_user["id"], activity_id)