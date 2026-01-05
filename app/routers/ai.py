from fastapi import APIRouter, Depends, Request
from app.dependencies.auth import get_current_user
from app.models.ai import ChatMessage
from app.dependencies.limiter import limiter
from app.services.ai_service import AIService

router = APIRouter(
    prefix="/api/analysis",
    tags=["analysis"]
)

@router.post("/ai/chat")
@limiter.limit("5/minute")
async def gemini_chat(
    request: Request, 
    payload: ChatMessage, 
    current_user: dict = Depends(get_current_user),
    service: AIService = Depends()
):
    """
    AI 訓練分析聊天機器人
    """
    return await service.chat_with_analysis(current_user["id"], payload.message, payload.range)
