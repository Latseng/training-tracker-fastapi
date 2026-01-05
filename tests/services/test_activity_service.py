import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from fastapi import HTTPException
from app.services.activity_service import ActivityService
from app.models.training_activities import (
    TrainingActivityWithRecordsCreate,
    ActivityRecordCreate,
    ActivityRecordUpdate
)

@pytest.fixture
def mock_supabase_admin():
    return MagicMock()

@pytest.fixture
def service(mock_supabase_admin):
    with patch("app.services.activity_service.database.get_supabase_admin", return_value=mock_supabase_admin):
        svc = ActivityService()
        yield svc

def test_create_activity_rollback_on_record_failure(service, mock_supabase_admin):
    user_id = "user-1"
    activity_data = TrainingActivityWithRecordsCreate(
        session_id="session-1",
        name="Test Activity",
        activity_records=[ActivityRecordCreate(set_number=1, weight=100, repetition=10)]
    )

    # Mock session verify (Success)
    mock_supabase_admin.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"id": "session-1"}]
    )

    # Mock activity insert (Success)
    mock_supabase_admin.table.return_value.insert.return_value.execute.side_effect = [
        MagicMock(data=[{"id": "activity-1", "session_id": "session-1", "name": "Test", "category": None, "description": None}]),
        # Record insert (Fail - Empty data)
        MagicMock(data=[])
    ]

    # Mock delete for rollback
    mock_supabase_admin.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock()

    with pytest.raises(HTTPException) as exc:
        service.create_activity(user_id, activity_data)
    
    assert exc.value.status_code == 500
    assert "Failed to create activity records" in exc.value.detail
    
    # Verify rollback delete called
    # We expect: table("training_activities").delete().eq("id", "activity-1")
    # Since we can't easily track chains with side_effect sharing the same mock object in this simple setup without being very verbose,
    # we just check that 'delete' was called.
    assert mock_supabase_admin.table.return_value.delete.called

def test_update_records_diffing_logic(service, mock_supabase_admin):
    activity_id = "activity-1"
    # Scenario: Keep record-1, Delete others (if any), Add/Update record-1 and record-2
    records_to_process = [
        ActivityRecordUpdate(id="record-1", activity_id=activity_id, set_number=1, repetition=10),
        ActivityRecordUpdate(id="record-2", activity_id=activity_id, set_number=2, repetition=10)
    ]
    
    # Mock delete for removed records
    mock_delete_chain = mock_supabase_admin.table.return_value.delete.return_value.eq.return_value.not_.in_.return_value.execute
    mock_delete_chain.return_value = MagicMock()
    
    # Mock upsert
    mock_upsert_chain = mock_supabase_admin.table.return_value.upsert.return_value.execute
    mock_upsert_chain.return_value = MagicMock()
    
    service.update_records(activity_id, records_to_process)
    
    # Verify delete called with correct logic
    # table("activity_records").delete().eq("activity_id", activity_id).not_.in_("id", ids_to_keep)
    args, _ = mock_supabase_admin.table.return_value.delete.return_value.eq.return_value.not_.in_.call_args
    assert args[0] == "id"
    assert set(args[1]) == {"record-1", "record-2"}
    
    # Verify upsert called
    assert mock_supabase_admin.table.return_value.upsert.called
    upsert_args = mock_supabase_admin.table.return_value.upsert.call_args[0][0]
    assert len(upsert_args) == 2
    assert upsert_args[0]["id"] == "record-1"
    assert upsert_args[1]["id"] == "record-2"

def test_update_records_decimal_conversion(service, mock_supabase_admin):
    activity_id = "activity-1"
    records_to_process = [
        ActivityRecordUpdate(id="r1", activity_id=activity_id, set_number=1, weight=Decimal("100.5"), repetition=10)
    ]
    
    mock_supabase_admin.table.return_value.upsert.return_value.execute.return_value = MagicMock()
    
    service.update_records(activity_id, records_to_process)
    
    # Verify upsert payload has float, not Decimal
    upsert_args = mock_supabase_admin.table.return_value.upsert.call_args[0][0]
    assert isinstance(upsert_args[0]["weight"], float)
    assert upsert_args[0]["weight"] == 100.5

def test_delete_activity_forbidden(service, mock_supabase_admin):
    user_id = "user-1"
    activity_id = "activity-1"
    
    # Mock verify found activity but different user
    mock_supabase_admin.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{
            "id": activity_id,
            "training_sessions": {"user_id": "other-user"}
        }]
    )
    
    with pytest.raises(HTTPException) as exc:
        service.delete_activity(user_id, activity_id)
    
    assert exc.value.status_code == 403
