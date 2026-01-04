from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import date as DateType
from .training_activities import TrainingActivityWithRecordsResponse

class TrainingSessionCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=100, description="課程標題")
    date: DateType = Field(..., description="訓練日期") # 時間格式只接受 "YYYY-MM-DD"
    note: Optional[str] = Field(None, description="備註")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "重訓日",
                "date": "2024-01-15",
                "note": "今天感覺狀態很好"
            }
        }
    )

class TrainingSessionUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=100)
    date: Optional[DateType] = None 
    note: Optional[str] = None

class TrainingSessionResponse(BaseModel):
    id: str
    user_id: str
    title: Optional[str]
    date: str
    note: Optional[str]
    created_at: str
    
    model_config = ConfigDict(from_attributes=True)

class TrainingSessionWithActivitiesResponse(BaseModel):
    id: str
    user_id: str
    title: Optional[str]
    date: str
    note: Optional[str]
    activities: list[TrainingActivityWithRecordsResponse]
    created_at: str