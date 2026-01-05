import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.ai_service import AIService
from app.models.ai import DateRange
from datetime import date
from fastapi import HTTPException

@pytest.fixture
def mock_supabase_admin():
    return MagicMock()

@pytest.fixture
def mock_gemini_client():
    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock()
    return mock_client

@pytest.fixture
def service(mock_supabase_admin, mock_gemini_client):
    # Patch dependencies
    with patch("app.services.ai_service.database.get_supabase_admin", return_value=mock_supabase_admin), \
         patch("app.services.ai_service.genai.Client", return_value=mock_gemini_client):
        svc = AIService()
        yield svc

@pytest.mark.asyncio
async def test_chat_with_analysis_no_records(service):
    # Mock empty data
    service.supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
    service.gemini_client.aio.models.generate_content.return_value = MagicMock(text="Response")

    user_id = "user-1"
    message = "Hello"
    date_range = DateRange(start_date=date(2024,1,1), end_date=date(2024,1,31))
    
    result = await service.chat_with_analysis(user_id, message, date_range)
    
    assert result["reply"] == "Response"
    # Check prompt context
    call_args = service.gemini_client.aio.models.generate_content.call_args
    prompt = call_args.kwargs.get('contents') or call_args.args[1]
    assert "無近期訓練紀錄" in prompt

def test_format_training_data(service):
    # Test private method via public access or just access it (it's python)
    sessions = [
        {
            "date": "2024-01-01",
            "note": "Hard",
            "activities": [
                {
                    "name": "Bench",
                    "records": [{"weight": 100, "repetition": 5}]
                }
            ]
        }
    ]
    
    formatted = service._format_training_data(sessions)
    assert "2024-01-01" in formatted
    assert "Hard" in formatted
    assert "Bench: 100kgx5" in formatted

@pytest.mark.asyncio
async def test_chat_service_error(service):
    service.gemini_client.aio.models.generate_content.side_effect = Exception("API Error")
    
    with pytest.raises(HTTPException) as exc:
        await service.chat_with_analysis("user-1", "msg", None)
    
    assert exc.value.status_code == 500
