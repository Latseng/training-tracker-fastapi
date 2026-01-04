import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client_authenticated():
    # Override get_current_user dependency
    from app.dependencies.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: {"id": "test-user-id", "email": "test@example.com"}
    with TestClient(app) as c:
        yield c
    app.dependency_overrides = {}

@pytest.fixture
def mock_supabase_admin():
    mock = MagicMock()
    return mock

def test_create_training_session_success(client_authenticated, mock_supabase_admin):
    payload = {
        "title": "Test Session",
        "date": "2024-01-01",
        "note": "Test Note"
    }
    
    # Mock return value
    mock_supabase_admin.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[{
            "id": "session-123", 
            "user_id": "test-user-id", 
            "created_at": "2024-01-01T10:00:00Z",
            **payload
        }]
    )

    with patch("app.services.training_session_service.database.get_supabase_admin", return_value=mock_supabase_admin):
        response = client_authenticated.post("/api/training-sessions", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["id"] == "session-123"

def test_get_sessions_with_activities_success(client_authenticated, mock_supabase_admin):
    # Mock return value for the chain: table().select().eq().order().execute()
    # Note: get_training_sessions_with_activities has additional logic for start_date/end_date which adds .gte/.lte calls.
    # Here we test the default case.
    
    # We need to be careful with the chaining. 
    # query = supabase.table("training_sessions").select(...)
    # query = query.eq(...)
    # query = query.order(...)
    # response = query.execute()
    
    mock_query = MagicMock()
    mock_query.execute.return_value = MagicMock(
        data=[
            {
                "id": "session-123",
                "user_id": "test-user-id",
                "title": "Test Session",
                "date": "2024-01-01",
                "note": "Test Note",
                "activities": [],
                "created_at": "2024-01-01T10:00:00Z"
            }
        ]
    )
    
    # Setup chain
    mock_supabase_admin.table.return_value.select.return_value.eq.return_value.order.return_value = mock_query
    # For cases without date filters, it goes table -> select -> eq -> order -> execute
    
    # Wait, the code has:
    # query = supabase.table(...).select(...).eq(...)
    # if start_date ...
    # query = query.order(...)
    # sessions_response = query.execute()
    
    # So table().select().eq() returns the query object that .order() is called on.
    
    mock_step1 = MagicMock() # result of eq
    mock_supabase_admin.table.return_value.select.return_value.eq.return_value = mock_step1
    mock_step1.order.return_value = mock_query

    with patch("app.services.training_session_service.database.get_supabase_admin", return_value=mock_supabase_admin):
        response = client_authenticated.get("/api/training-sessions/with-activities")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "session-123"

def test_update_training_session_success(client_authenticated, mock_supabase_admin):
    session_id = "session-123"
    payload = {"title": "Updated Title"}
    
    # Mock existing check: table().select().eq().eq().execute()
    mock_supabase_admin.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"id": session_id}]
    )
    
    # Mock update: table().update().eq().execute()
    mock_supabase_admin.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{
            "id": session_id, 
            "user_id": "test-user-id", 
            "date": "2024-01-01", 
            "note": "Old Note",
            "created_at": "2024-01-01T10:00:00Z",
            **payload
        }]
    )

    with patch("app.services.training_session_service.database.get_supabase_admin", return_value=mock_supabase_admin):
        response = client_authenticated.put(f"/api/training-sessions/{session_id}", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"

def test_delete_training_session_success(client_authenticated, mock_supabase_admin):
    session_id = "session-123"
    
    # Mock delete: table().delete().eq().eq().execute()
    mock_supabase_admin.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"id": session_id}]
    )

    with patch("app.services.training_session_service.database.get_supabase_admin", return_value=mock_supabase_admin):
        response = client_authenticated.delete(f"/api/training-sessions/{session_id}")
    
    assert response.status_code == 204
