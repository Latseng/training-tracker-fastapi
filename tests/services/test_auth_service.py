import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from supabase import AuthApiError
from app.services.auth_service import AuthService

@pytest.fixture
def mock_supabase_client():
    mock = MagicMock()
    return mock

@pytest.fixture
def auth_service(mock_supabase_client):
    # Patch the database.get_supabase_client to return our mock
    with patch("app.services.auth_service.database.get_supabase_client", return_value=mock_supabase_client):
        service = AuthService()
        yield service

def test_signup_success(auth_service, mock_supabase_client):
    # Setup mock
    mock_supabase_client.auth.sign_up.return_value = MagicMock(
        user=MagicMock(id="test-id", email="test@example.com"),
        session=None
    )
    mock_supabase_client.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[])

    result = auth_service.signup("test@example.com", "password", "username")
    
    assert result["message"] == "註冊成功"
    assert result["user_id"] == "test-id"
    mock_supabase_client.auth.sign_up.assert_called_with({
        "email": "test@example.com",
        "password": "password",
        "options": {"data": {"username": "username"}}
    })
    mock_supabase_client.table.assert_called_with("users")

def test_signup_failure_no_user(auth_service, mock_supabase_client):
    mock_supabase_client.auth.sign_up.return_value = MagicMock(user=None)
    
    with pytest.raises(HTTPException) as exc:
        auth_service.signup("test@example.com", "password", "username")
    
    assert exc.value.status_code == 400
    assert exc.value.detail == "使用者註冊失敗"

def test_signup_existing_email(auth_service, mock_supabase_client):
    # Mock AuthApiError
    error = AuthApiError(message="User already registered", status=400, code="400")
    mock_supabase_client.auth.sign_up.side_effect = error
    
    with pytest.raises(HTTPException) as exc:
        auth_service.signup("test@example.com", "password", "username")
        
    assert exc.value.status_code == 400
    assert exc.value.detail == "Email已註冊"

def test_login_success(auth_service, mock_supabase_client):
    mock_response = MagicMock(
        user=MagicMock(id="test-id"),
        session=MagicMock(access_token="token", refresh_token="refresh")
    )
    mock_supabase_client.auth.sign_in_with_password.return_value = mock_response
    
    result = auth_service.login("test@example.com", "password")
    
    assert result == mock_response

def test_login_failure(auth_service, mock_supabase_client):
    mock_supabase_client.auth.sign_in_with_password.return_value = MagicMock(user=None, session=None)
    
    with pytest.raises(HTTPException) as exc:
        auth_service.login("test@example.com", "password")
        
    assert exc.value.status_code == 401
    assert exc.value.detail == "登入失敗：電子郵件或密碼錯誤"

def test_resend_verification_success(auth_service, mock_supabase_client):
    auth_service.resend_verification("test@example.com")
    mock_supabase_client.auth.resend.assert_called_with({
        "type": "signup",
        "email": "test@example.com"
    })

def test_resend_verification_rate_limit(auth_service, mock_supabase_client):
    mock_supabase_client.auth.resend.side_effect = Exception("Rate limit exceeded")
    
    with pytest.raises(HTTPException) as exc:
        auth_service.resend_verification("test@example.com")
        
    assert exc.value.status_code == 429
    assert exc.value.detail == "發送過於頻繁，請稍後再試"

def test_get_user_by_token_success(auth_service, mock_supabase_client):
    mock_supabase_client.auth.get_user.return_value = MagicMock(
        user=MagicMock(
            id="test-id",
            email="test@example.com",
            user_metadata={"username": "testuser"}
        )
    )
    
    user = auth_service.get_user_by_token("valid-token")
    
    assert user["id"] == "test-id"
    assert user["username"] == "testuser"

def test_get_user_by_token_invalid(auth_service, mock_supabase_client):
    mock_supabase_client.auth.get_user.side_effect = Exception("Invalid token")
    
    with pytest.raises(HTTPException) as exc:
        auth_service.get_user_by_token("invalid-token")
        
    assert exc.value.status_code == 401
