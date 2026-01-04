from fastapi import APIRouter, Depends, status
from datetime import date
from app.dependencies.auth import get_current_user
from typing import List
from app.models.training_sessions import (
    TrainingSessionCreate,
    TrainingSessionUpdate,
    TrainingSessionResponse,
    TrainingSessionWithActivitiesResponse
)
from app.services.training_session_service import TrainingSessionService

router = APIRouter(
    prefix="/api/training-sessions",
    tags=["training sessions"]
)

@router.post("", response_model=TrainingSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_training_session(
    session: TrainingSessionCreate,
    current_user: dict = Depends(get_current_user),
    service: TrainingSessionService = Depends()
):
    """
    建立新的訓練課程
    
    - **title**: 訓練標題（可選）
    - **date**: 訓練日期（必填）
    - **note**: 備註（可選）
    
    必須通過身份驗證
    """
    return service.create_session(current_user["id"], session)

@router.get("/with-activities", response_model=List[TrainingSessionWithActivitiesResponse])
async def get_training_sessions_with_activities(
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: dict = Depends(get_current_user),
    service: TrainingSessionService = Depends()
):
    """
    取得訓練課程（包含活動和記錄）- **單次查詢優化**
    """
    return service.get_sessions_with_activities(current_user["id"], start_date, end_date)

@router.put("/{session_id}", response_model=TrainingSessionResponse)
async def update_training_session(
    session_id: str,
    session_update: TrainingSessionUpdate,
    current_user: dict = Depends(get_current_user),
    service: TrainingSessionService = Depends()
):
    """更新選定課程（id）資訊"""
    return service.update_session(current_user["id"], session_id, session_update)
    
@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_training_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    service: TrainingSessionService = Depends()
):
    """刪除訓練課程"""
    service.delete_session(current_user["id"], session_id)
