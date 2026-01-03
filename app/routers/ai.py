from fastapi import APIRouter, Depends, HTTPException, Request
from google import genai
from app.dependencies.auth import get_current_user
from app.database import database
from app.model.ai import ChatMessage
from app.dependencies.limiter import limiter
import os
from dotenv import load_dotenv 

load_dotenv()

supabase = database.get_supabase_admin()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

router = APIRouter(
    prefix="/api/analysis",
    tags=["analysis"]
)

def format_training_data(sessions: list) -> str:
    """將訓練數據格式化為精簡文字以節省 Token"""
    if not sessions:
        return "無近期訓練紀錄。"
    
    formatted_text = "近期訓練紀錄:\n"
    for session in sessions:
        date = session.get("date", "Unknown Date")
        note = session.get("note", "")
        formatted_text += f"=== 日期: {date} ===\n"
        if note:
            formatted_text += f"心得: {note}\n"
        
        activities = session.get("activities", [])
        for act in activities:
            name = act.get("name", "Unknown")
            records = act.get("records", [])
            record_str = ", ".join([f"{r.get('weight')}kgx{r.get('repetition')}" for r in records])
            formatted_text += f"- {name}: {record_str}\n"
        formatted_text += "\n"
    return formatted_text

@router.post("/ai/chat")
@limiter.limit("5/minute") # 限制每分鐘 5 次請求
async def gemini_chat(request: Request, payload: ChatMessage, current_user: dict = Depends(get_current_user)):
    try:
        sessions_data = []

        if payload.range:
            query = supabase.table("training_sessions")\
            .select("date, note, title, activities:training_activities(category, description, name, records:activity_records(repetition, set_number, weight))")\
            .eq("user_id", current_user["id"])
            
            # 修正日期查詢邏輯
            if payload.range.start_date:
                query = query.gte("date", payload.range.start_date.isoformat())
            if payload.range.end_date:
                query = query.lte("date", payload.range.end_date.isoformat())
            
            query = query.order("date", desc=True).limit(20)
            
            sessions_response = query.execute()
            if sessions_response.data:
                sessions_data = sessions_response.data

        context_str = format_training_data(sessions_data)
        
        prompt = f"""
        你是一位專業的肌力與體能訓練教練。
        請根據使用者的提問與提供的近期訓練紀錄進行評估與分析。
        
        使用者問題: {payload.message}
        
        {context_str}
        
        指示：
        1. 若有訓練紀錄，請具體引用數據來支持你的建議。
        2. 若無相關紀錄或問題與訓練無關，請委婉說明。
        3. 回答請保持簡潔專業，重點在於優化訓練成效。
        """
        
        response = await gemini_client.aio.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt
        )

        return {"reply": response.text}

    except Exception:
        raise HTTPException(status_code=500)