import pytest
from unittest.mock import MagicMock, patch
from datetime import date
from fastapi import HTTPException
from app.services.training_session_service import TrainingSessionService
from app.models.training_sessions import TrainingSessionCreate, TrainingSessionUpdate

@pytest.fixture
def mock_supabase_admin():
    return MagicMock()

@pytest.fixture
def service(mock_supabase_admin):
    with patch("app.services.training_session_service.database.get_supabase_admin", return_value=mock_supabase_admin):
        svc = TrainingSessionService()
        yield svc

def test_create_session(service, mock_supabase_admin):
    user_id = "user-123"
    session_data = TrainingSessionCreate(title="Test", date=date(2024, 1, 1), note="Note")
    
    mock_supabase_admin.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": "session-1", "user_id": user_id, "title": "Test"}]
    )
    
    result = service.create_session(user_id, session_data)
    
    assert result["id"] == "session-1"
    mock_supabase_admin.table.assert_called_with("training_sessions")
    # Verify insert data
    args, _ = mock_supabase_admin.table.return_value.insert.call_args
    assert args[0]["user_id"] == user_id
    assert args[0]["title"] == "Test"

def test_get_sessions_with_activities(service, mock_supabase_admin):
    user_id = "user-123"
    
    # Mock chain
    mock_query = MagicMock()
    mock_query.execute.return_value = MagicMock(data=[{"id": "session-1"}])
    
    # Chain setup: table -> select -> eq -> order -> execute
    # Code:
    # query = table().select().eq()
    # query = query.order()
    # result = query.execute()
    
    mock_step1 = MagicMock()
    mock_supabase_admin.table.return_value.select.return_value.eq.return_value = mock_step1
    mock_step1.order.return_value = mock_query

    result = service.get_sessions_with_activities(user_id)
    
    assert len(result) == 1
    assert result[0]["id"] == "session-1"

def test_update_session_not_found(service, mock_supabase_admin):
    user_id = "user-123"
    session_id = "non-existent"
    update_data = TrainingSessionUpdate(title="New Title")
    
    # Mock existing check returning empty data
    mock_supabase_admin.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[]
    )
    
    with pytest.raises(HTTPException) as exc:
        service.update_session(user_id, session_id, update_data)
    
    assert exc.value.status_code == 404

def test_delete_session_success(service, mock_supabase_admin):
    user_id = "user-123"
    session_id = "session-1"
    
    mock_supabase_admin.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"id": session_id}]
    )
    
    service.delete_session(user_id, session_id)
    
    mock_supabase_admin.table.return_value.delete.assert_called_once()
