from pydantic import BaseModel, Field
from typing import Optional
from datetime import date as DateType

# ===== Training Session 相關模型 =====
class TrainingSessionCreate(BaseModel):
    """建立訓練課程的請求模型"""
    title: Optional[str] = Field(None, max_length=100, description="課程標題")
    date: DateType = Field(..., description="訓練日期") # 時間格式只接受 "YYYY-MM-DD"
    note: Optional[str] = Field(None, description="備註")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "重訓日",
                "date": "2024-01-15",
                "note": "今天感覺狀態很好"
            }
        }

class TrainingSessionResponse(BaseModel):
    """訓練課程的回應模型"""
    id: str
    user_id: str
    title: Optional[str]
    date: str  # 注意：資料庫欄位是 date，所以 response 保持不變
    note: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True