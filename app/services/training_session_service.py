from fastapi import HTTPException, status
from typing import List, Optional
from datetime import date
from supabase import Client
from app.database import database
from app.models.training_sessions import TrainingSessionCreate, TrainingSessionUpdate

class TrainingSessionService:
    def __init__(self):
        self.supabase: Client = database.get_supabase_admin()

    def create_session(self, user_id: str, session: TrainingSessionCreate):
        try:
            session_data = {
                "user_id": user_id,
                "title": session.title,
                "date": session.date.isoformat(),
                "note": session.note
            }
            
            response = self.supabase.table("training_sessions").insert(session_data).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create training session"
                )
            
            return response.data[0]
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )

    def get_sessions_with_activities(self, user_id: str, start_date: Optional[date] = None, end_date: Optional[date] = None):
        try:
            query = (
                self.supabase.table("training_sessions")
                .select("*, activities:training_activities(*, records:activity_records(*))")
                .eq("user_id", user_id)
            )
            
            if start_date:
                query = query.gte("date", start_date.isoformat())
                
            if end_date:
                query = query.lte("date", end_date.isoformat())
            elif start_date:
                # Original logic preservation: limits to exactly the start_date if no end_date provided
                query = query.lte("date", start_date.isoformat()) 
                
            query = query.order("created_at", desc=True)
            sessions_response = query.execute()
    
            if not sessions_response.data:
                return []

            return sessions_response.data
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch sessions with activities: {str(e)}"
            )

    def update_session(self, user_id: str, session_id: str, session_update: TrainingSessionUpdate):
        try:
            existing = (
                self.supabase.table("training_sessions")
                .select("*")
                .eq("id", session_id)
                .eq("user_id", user_id)
                .execute()
            )
            
            if not existing.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Training session not found"
                )
            
            update_data = {}
            if session_update.title is not None:
                update_data["title"] = session_update.title
            if session_update.date is not None:
                update_data["date"] = session_update.date.isoformat()
            if session_update.note is not None:
                update_data["note"] = session_update.note
            
            if not update_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fields to update"
                )
            
            response = (
                self.supabase.table("training_sessions")
                .update(update_data)
                .eq("id", session_id)
                .execute()
            )
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update training session"
                )
            
            return response.data[0]
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update training session: {str(e)}"
            )

    def delete_session(self, user_id: str, session_id: str):
        try:
            response = (
                self.supabase.table("training_sessions")
                .delete()
                .eq("id", session_id)
                .eq("user_id", user_id)
                .execute()
            )
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Training session not found or you don't have permission to delete it."
                )
            
            return
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete training session: {str(e)}"
            )