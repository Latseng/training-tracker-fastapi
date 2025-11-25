from fastapi import APIRouter, Depends, HTTPException
from google import genai
from app.dependencies.auth import get_current_user
from app.database import database
from app.models import ChatMessage
import os

supabase = database.get_supabase()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

router = APIRouter(
    prefix="/api/analysis",
    tags=["analysis"]
)

@router.post("/ai/chat")
async def gemini_chat(request: ChatMessage, current_user: dict = Depends(get_current_user)):
    try:
        sessions_response = None
        # 使用者需要依照訓練資料詢問AI
        if request.range:
            query = supabase.table("training_sessions")\
            .select("date, note, title, activities:training_activities(category, description, name, records:activity_records(repetition, set_number, weight))")\
            .eq("user_id", current_user["id"])
            
            if request.range.start_date:
                query = query.gte("date", request.range.start_date.isoformat())
            if request.range.end_date:
                query = query.lte("date", request.range.end_date.isoformat())
            elif request.range.start_date:
                query = query.lte("date", request.range.start_date.isoformat()) 

            query = query.order("created_at", desc=True)
            sessions_response = query.execute()
            
            if not sessions_response.data:
                sessions_response.data = []

        # 構建給 Gemini 的 Prompt (提示詞)
        # 我們將數據轉為字串，讓 AI 當作背景知識
        if sessions_response is not None:
            context_str = f"這是使用者的近期訓練紀錄: {sessions_response}"
        else:
            # 如果沒有資料，提供一個替代的訊息
            context_str = "沒有使用者的訓練紀錄。"
        
        prompt = f"""
        你是一位專業的肌力與體能訓練教練。
        使用者有可能會附帶一段期間的訓練紀錄給你（從supabase抓取的資料）。
        如果使用者有提供，請協助使用者評估與分析訓練紀錄。
        如果沒有，請直接回答使用者的提問。
        
        使用者問題: {request.message}
        訓練紀錄: {context_str}
        
        若使用者提出與訓練無關的問題，請委婉提醒使用者，你不便回答在你專業領域外的問題。
        """
        
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)

        print(response)

        return {"reply": response.text}

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="AI 處理失敗")