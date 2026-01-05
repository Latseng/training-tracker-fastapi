import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from datetime import date

@pytest.fixture
def client_authenticated():
    from app.dependencies.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: {"id": "test-user-id", "email": "test@example.com"}
    with TestClient(app) as c:
        yield c
    app.dependency_overrides = {}

@pytest.fixture
def mock_supabase_admin():
    return MagicMock()

@pytest.fixture
def mock_gemini_client():
    mock_client = MagicMock()
    # Mock aio.models.generate_content
    mock_client.aio.models.generate_content = AsyncMock()
    mock_client.aio.models.generate_content.return_value = MagicMock(text="AI Response")
    return mock_client

def test_ai_chat_success(client_authenticated, mock_supabase_admin, mock_gemini_client):
    payload = {
        "message": "How is my progress?",
        "range": {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31"
        }
    }
    
    # Mock Supabase data
    mock_supabase_admin.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[
            {
                "date": "2024-01-15",
                "note": "Good session",
                "activities": [
                    {"name": "Squat", "records": [{"weight": 100, "repetition": 5}]}
                ]
            }
        ]
    )

    # Patch both supabase and gemini_client
    # Patch both supabase and gemini_client
    # We patch the class genai.Client so that when it is instantiated, it returns our mock
    with patch("app.services.ai_service.database.get_supabase_admin", return_value=mock_supabase_admin), \
         patch("app.services.ai_service.genai.Client", return_value=mock_gemini_client):
        
        response = client_authenticated.post("/api/analysis/ai/chat", json=payload)

    assert response.status_code == 200
    assert response.json() == {"reply": "AI Response"}
    
    # Verify Gemimi called
    mock_gemini_client.aio.models.generate_content.assert_called_once()
    
    # Verify prompt contains context
    call_args = mock_gemini_client.aio.models.generate_content.call_args
    prompt_sent = call_args.kwargs['contents'] if 'contents' in call_args.kwargs else call_args.args[1]
    assert "Good session" in prompt_sent
    assert "Squat" in prompt_sent

def test_ai_chat_no_range(client_authenticated, mock_supabase_admin, mock_gemini_client):
    payload = {
        "message": "General question"
    }
    
    # Patch both supabase and gemini_client
    # We patch the class genai.Client so that when it is instantiated, it returns our mock
    with patch("app.services.ai_service.database.get_supabase_admin", return_value=mock_supabase_admin), \
         patch("app.services.ai_service.genai.Client", return_value=mock_gemini_client):
        
        response = client_authenticated.post("/api/analysis/ai/chat", json=payload)

    assert response.status_code == 200
    
    # Verify Supabase NOT called (since no range provided in current logic? 
    # Wait, the code says `if payload.range: ... sessions_data = ...`
    # So if no range, sessions_data is empty list.
    assert not mock_supabase_admin.table.called
