import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from app.main import app
from app.dependencies.auth import get_current_user

@pytest.fixture
def mock_user():
    return {
        "id": "test-user-id-123",
        "email": "test@example.com",
        "role": "authenticated"
    }

@pytest.fixture
def client(mock_user):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.clear()

@pytest.fixture
def mock_supabase(mocker):
    mock_client = MagicMock()
    
    mock_query = MagicMock()
    mock_query.execute.return_value.data = []
    
    mock_client.table.return_value.select.return_value = mock_query
    
    return mock_client