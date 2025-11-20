from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import date as DateType
from decimal import Decimal

class SignupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class EmailSchema(BaseModel):
    email: EmailStr

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

class TrainingSessionUpdate(BaseModel):
    """更新訓練課程的請求模型"""
    title: Optional[str] = Field(None, max_length=100)
    date: Optional[DateType] = None 
    note: Optional[str] = None

class TrainingSessionResponse(BaseModel):
    """訓練課程的回應模型"""
    id: str
    user_id: str
    title: Optional[str]
    date: str
    note: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True

class ActivityRecordCreate(BaseModel):
    """建立活動記錄的請求模型"""
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

class ActivityRecordResponse(BaseModel):
    """活動記錄的回應模型"""
    id: str
    activity_id: str
    set_number: int
    repetition: Optional[int]
    weight: Optional[float]
    duration: Optional[str]
    distance: Optional[float]
    score: Optional[float]

class TrainingActivityWithRecordsCreate(BaseModel):
    """建立訓練活動（包含記錄）的請求模型"""
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

class TrainingActivityWithRecordsResponse(BaseModel):
    """訓練活動（包含記錄）的回應模型"""
    id: str
    session_id: str
    name: str
    category: Optional[str]
    description: Optional[str]
    records: list[ActivityRecordResponse]

class TrainingSessionWithActivitiesResponse(BaseModel):
    """訓練計劃包含訓練項目與訓練紀錄"""
    id: str
    user_id: str
    title: Optional[str]
    date: str
    note: Optional[str]
    activities: list[TrainingActivityWithRecordsResponse]
    created_at: str

class ActivityRecordUpdate(BaseModel):
    """
    用於接收前端單筆 Record 更新的 Pydantic 模型。
    - id 欄位是必須的，用於定位要更新的 Record。
    """
    id: str  # 必須提供 Record 的 ID
    activity_id: str  # 必須提供所屬 Activity 的 ID
    set_number: int
    repetition: Optional[int]
    weight: Optional[Decimal] = Field(None, ge=0, max_digits=5, decimal_places=2, description="重量(kg)")
    duration: Optional[str] = Field(None, description="持續時間 (例如: '00:30:00')")
    distance: Optional[Decimal] = Field(None, ge=0, max_digits=6, decimal_places=1, description="距離(km)")
    score: Optional[Decimal] = Field(None, ge=0, max_digits=4, decimal_places=1, description="分數")