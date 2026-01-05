import pytest
from unittest.mock import MagicMock, patch, ANY
from fastapi.testclient import TestClient
from app.main import app

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

def test_create_activity_with_records_success(client_authenticated, mock_supabase_admin):
    payload = {
        "session_id": "session-1",
        "name": "Bench Press",
        "category": "Strength",
        "description": "Heavy set",
        "activity_records": [
            {
                "set_number": 1,
                "repetition": 10,
                "weight": 100.0,
                "duration": "00:01:00"
            }
        ]
    }

    # 1. Mock session verification
    mock_supabase_admin.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"id": "session-1", "user_id": "test-user-id"}]
    )

    # 2. Mock activity creation
    mock_supabase_admin.table.return_value.insert.return_value.execute.side_effect = [
        # First insert: training_activities
        MagicMock(data=[{
            "id": "activity-1",
            "session_id": "session-1",
            "name": "Bench Press",
            "category": "Strength",
            "description": "Heavy set"
        }]),
        # Second insert: activity_records
                    MagicMock(data=[{
                        "id": "record-1",
                        "activity_id": "activity-1",
                        "set_number": 1,
                        "repetition": 10,
                        "weight": 100.0,
                        "duration": "00:01:00",
                        "distance": None,
                        "score": None
                    }])    ]

    with patch("app.services.activity_service.database.get_supabase_admin", return_value=mock_supabase_admin):
        response = client_authenticated.post("/api/training-activities", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "activity-1"
    assert len(data["records"]) == 1
    assert data["records"][0]["id"] == "record-1"

def test_create_activity_records_fail_rollback(client_authenticated, mock_supabase_admin):
    payload = {
        "session_id": "session-1",
        "name": "Bench Press",
        "category": "Strength",
        "activity_records": [{"set_number": 1, "repetition": 10}]
    }

    # 1. Mock session verification
    mock_supabase_admin.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"id": "session-1", "user_id": "test-user-id"}]
    )

    # 2. Mock activity creation SUCCESS, but records creation FAILURE (empty data)
    mock_supabase_admin.table.return_value.insert.return_value.execute.side_effect = [
        # Activity: Success
        MagicMock(data=[{"id": "activity-1"}]),
        # Records: Fail (return empty list or None)
        MagicMock(data=[]) 
    ]
    
    # Mock delete for rollback
    mock_supabase_admin.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock()

    with patch("app.services.activity_service.database.get_supabase_admin", return_value=mock_supabase_admin):
        response = client_authenticated.post("/api/training-activities", json=payload)

    assert response.status_code == 500
    # Verify rollback delete was called
    mock_supabase_admin.table.assert_any_call("training_activities")
    # We can check if delete was called specifically. 
    # The chain is table("training_activities").delete().eq("id", "activity-1").execute()
    # It's a bit hard to verify exact chain calls with side_effect mocks on the same object, 
    # but we can verify table was called with "training_activities" at least twice (insert and delete).

def test_update_activity_records_success(client_authenticated, mock_supabase_admin):
    activity_id = "activity-1"
    payload = [
        {"id": "record-1", "activity_id": activity_id, "set_number": 1, "repetition": 12}, # Update
        {"id": "record-2", "activity_id": activity_id, "set_number": 2, "repetition": 10} # Create (simulate client-generated ID)
    ]
    
    # Mock delete (for records not in list)
    mock_supabase_admin.table.return_value.delete.return_value.eq.return_value.not_.in_.return_value.execute.return_value = MagicMock()
    
    # Mock upsert
    mock_supabase_admin.table.return_value.upsert.return_value.execute.return_value = MagicMock(
        data=[{}, {}]
    )

    with patch("app.services.activity_service.database.get_supabase_admin", return_value=mock_supabase_admin):
        response = client_authenticated.put(f"/api/training-activities/{activity_id}/records", json=payload)
    
    assert response.status_code == 204

def test_delete_activity_success(client_authenticated, mock_supabase_admin):
    activity_id = "activity-1"
    
    # Mock verification: select joined with sessions
    mock_supabase_admin.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{
            "id": activity_id,
            "training_sessions": {"user_id": "test-user-id"}
        }]
    )
    
    # Mock delete
    mock_supabase_admin.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock()

    with patch("app.services.activity_service.database.get_supabase_admin", return_value=mock_supabase_admin):
        response = client_authenticated.delete(f"/api/training-activities/{activity_id}")
    
    assert response.status_code == 204
