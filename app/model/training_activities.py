from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal

class ActivityRecordCreate(BaseModel):
    set_number: int = Field(..., ge=1, description="第幾組")
    reps: Optional[int] = Field(None, ge=0, description="次數")
    weight: Optional[Decimal] = Field(None, ge=0, max_digits=5, decimal_places=2, description="重量(kg)")
    duration: Optional[str] = Field(None, description="持續時間 (例如: '00:30:00')")
    distance: Optional[Decimal] = Field(None, ge=0, max_digits=6, decimal_places=1, description="距離(km)")
    score: Optional[Decimal] = Field(None, ge=0, max_digits=4, decimal_places=1, description="分數")
    
    # 支援 repetition 作為 reps 的別名
    repetition: Optional[int] = Field(None, ge=0, description="次數（別名）")
    
    @property
    def get_reps(self) -> Optional[int]:
        """取得次數，優先使用 repetition"""
        return self.repetition if self.repetition is not None else self.reps
    
    class Config:
        json_schema_extra = {
            "example": {
                "set_number": 1,
                "reps": 10,
                "weight": 80.5,
                "duration": None,
                "distance": None,
                "score": None
            }
        }


class TrainingActivityWithRecordsCreate(BaseModel):
    session_id: str = Field(..., description="訓練課程 ID")
    name: str = Field(..., max_length=100, description="活動名稱")
    category: Optional[str] = Field(None, max_length=50, description="類別")
    description: Optional[str] = Field(None, description="描述")
    activity_records: list[ActivityRecordCreate] = Field(
        default_factory=list,
        description="活動記錄列表"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "4f521a2f-713a-4383-9999-1d51deedb1e3",
                "name": "硬舉",
                "category": "strength",
                "activity_records": [
                    {"set_number": 1, "weight": 150, "repetition": 6},
                    {"set_number": 2, "weight": 150, "repetition": 6},
                    {"set_number": 3, "weight": 150, "repetition": 6}
                ]
            }
        }

class ActivityRecordResponse(BaseModel):
    id: str
    activity_id: str
    set_number: int
    repetition: Optional[int]
    weight: Optional[float]
    duration: Optional[str]
    distance: Optional[float]
    score: Optional[float]

class TrainingActivityWithRecordsResponse(BaseModel):
    id: str
    session_id: str
    name: str
    category: Optional[str]
    description: Optional[str]
    records: list[ActivityRecordResponse]

class ActivityRecordUpdate(BaseModel):
    id: str  # 必須提供 Record 的 ID
    activity_id: str  # 必須提供所屬 Activity 的 ID
    set_number: int
    repetition: Optional[int]
    weight: Optional[Decimal] = Field(None, ge=0, max_digits=5, decimal_places=2, description="重量(kg)")
    duration: Optional[str] = Field(None, description="持續時間 (例如: '00:30:00')")
    distance: Optional[Decimal] = Field(None, ge=0, max_digits=6, decimal_places=1, description="距離(km)")
    score: Optional[Decimal] = Field(None, ge=0, max_digits=4, decimal_places=1, description="分數")