from fastapi import HTTPException, status
from google import genai
from app.database import database
from app.models.ai import DateRange
import os

class AIService:
    def __init__(self):
        self.supabase = database.get_supabase_admin()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
             # Just a warning or handle gracefully, though env should have it
             pass
        self.gemini_client = genai.Client(api_key=self.gemini_api_key)

    def _format_training_data(self, sessions: list) -> str:
        """將訓練數據格式化為精簡文字以節省 Token"""
        if not sessions:
            return "無近期訓練紀錄。"
        
        formatted_text = "近期訓練紀錄:\n"
        for session in sessions:
            date_str = session.get("date", "Unknown Date")
            note = session.get("note", "")
            formatted_text += f"=== 日期: {date_str} ===\n"
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

    async def chat_with_analysis(self, user_id: str, message: str, date_range: DateRange | None):
        try:
            sessions_data = []

            if date_range:
                query = self.supabase.table("training_sessions")\
                .select("date, note, title, activities:training_activities(category, description, name, records:activity_records(repetition, set_number, weight))")\
                .eq("user_id", user_id)
                
                if date_range.start_date:
                    query = query.gte("date", date_range.start_date.isoformat())
                if date_range.end_date:
                    query = query.lte("date", date_range.end_date.isoformat())
                
                query = query.order("date", desc=True).limit(20)
                
                sessions_response = query.execute()
                if sessions_response.data:
                    sessions_data = sessions_response.data

            context_str = self._format_training_data(sessions_data)
            
            prompt = f"""
            你是一位專業的肌力與體能訓練教練。
            請根據使用者的提問與提供的近期訓練紀錄進行評估與分析。
            
            使用者問題: {message}
            
            {context_str}
            
            指示：
            1. 若有訓練紀錄，請具體引用數據來支持你的建議。
            2. 若無相關紀錄或問題與訓練無關，請委婉說明。
            3. 回答請保持簡潔專業，重點在於優化訓練成效。
            """
            
            response = await self.gemini_client.aio.models.generate_content(
                model="gemini-2.5-flash", 
                contents=prompt
            )

            return {"reply": response.text}

        except Exception as e:
            # Optionally log error here
            print(f"Error in AI Service: {e}")
            raise HTTPException(status_code=500, detail="AI Service Error")
