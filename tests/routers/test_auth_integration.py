import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app

# Disable the default client fixture's dependency override for these tests
# We want to test the actual auth logic, or at least independent of the global override
@pytest.fixture
def client_no_auth():
    # Ensure no overrides are present
    app.dependency_overrides = {}
    with TestClient(app) as c:
        yield c
    app.dependency_overrides = {}

@pytest.fixture
def mock_supabase_client():
    mock = MagicMock()
    # Mock auth.sign_up
    mock.auth.sign_up.return_value = MagicMock(
        user=MagicMock(id="test-user-id", email="test@example.com"),
        session=None
    )
    # Mock table("users").insert().execute()
    mock.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[])
    
    # Mock auth.sign_in_with_password
    mock.auth.sign_in_with_password.return_value = MagicMock(
        user=MagicMock(id="test-user-id"),
        session=MagicMock(
            access_token="fake-access-token",
            refresh_token="fake-refresh-token"
        )
    )
    
    # Mock auth.resend
    mock.auth.resend.return_value = MagicMock()
    
    return mock

def test_signup_success(client_no_auth, mock_supabase_client):
    payload = {
        "email": "test@example.com",
        "password": "password123",
        "username": "testuser"
    }
    
    # Patch the supabase client in app.routers.auth
    # Patch the supabase client in app.services.auth_service
    with patch("app.services.auth_service.database.get_supabase_client", return_value=mock_supabase_client):
        response = client_no_auth.post("/api/auth/signup", json=payload)
        
    assert response.status_code == 200
    assert response.json() == {
        "message": "註冊成功", 
        "user_id": "test-user-id", 
        "email": "test@example.com"
    }
    
    # Verify mock calls
    mock_supabase_client.auth.sign_up.assert_called_once()
    mock_supabase_client.table.assert_called_with("users")
    mock_supabase_client.table().insert.assert_called_once()

def test_login_success(client_no_auth, mock_supabase_client):
    payload = {
        "email": "test@example.com",
        "password": "password123"
    }
    
    # Patch the supabase client in app.services.auth_service
    with patch("app.services.auth_service.database.get_supabase_client", return_value=mock_supabase_client):
        response = client_no_auth.post("/api/auth/login", json=payload)
        
    assert response.status_code == 200
    assert response.json()["message"] == "login ok"
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies

def test_resend_verify_success(client_no_auth, mock_supabase_client):
    payload = {"email": "test@example.com"}
    
    # Patch the supabase client in app.services.auth_service
    with patch("app.services.auth_service.database.get_supabase_client", return_value=mock_supabase_client):
        response = client_no_auth.post("/api/auth/resend-verify", json=payload)
        
    assert response.status_code == 200
    assert response.json()["message"] == "驗證信已重新寄送，請檢查您的信箱"
    mock_supabase_client.auth.resend.assert_called_once()