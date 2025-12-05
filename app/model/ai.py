from pydantic import BaseModel, Field
from typing import Optional
from datetime import date as DateType

class DateRange(BaseModel):
    """
    用於處理 'range' 物件中的開始和結束日期。
    """
    # date 類型可以確保 Pydantic 自動將 "2025-11-11" 轉換為 date 對象
    start_date: DateType
    end_date: DateType

class ChatMessage(BaseModel):
    message: str = Field(..., example="我想問以下問題")
    range: Optional[DateRange] = None