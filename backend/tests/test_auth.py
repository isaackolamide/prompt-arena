from unittest.mock import MagicMock, patch
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.api.auth import send_magic_link, verify_otp, SessionCreationError
try:
    from gotrue.errors import AuthApiError
except ModuleNotFoundError:
    from supabase_auth.errors import AuthApiError

client = TestClient(app)

@pytest.fixture
def mock_supabase():
    with patch("app.api.auth.get_supabase_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        yield mock_client

def test_send_magic_link_success(mock_supabase):
    # Setup mock
    mock_supabase.auth.sign_in_with_otp.return_value = MagicMock()

    # Call logic function directly
    res = send_magic_link("user@example.com")
    assert res == {"status": "success"}
    mock_supabase.auth.sign_in_with_otp.assert_called_once_with({"email": "user@example.com"})

    # Call via endpoint
    response = client.post("/api/auth/magic-link", json={"email": "user@example.com"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "success"}

def test_send_magic_link_failure(mock_supabase):
    # Setup mock to raise AuthApiError
    mock_supabase.auth.sign_in_with_otp.side_effect = AuthApiError("Failed to send OTP", 400, "otp_failed")

    # Direct function call
    with pytest.raises(AuthApiError) as exc_info:
        send_magic_link("user@example.com")
    assert exc_info.value.message == "Failed to send OTP"

    # API Endpoint call
    response = client.post("/api/auth/magic-link", json={"email": "user@example.com"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Auth error" in response.json()["detail"]

def test_verify_otp_success(mock_supabase):
    # Setup mock
    mock_auth_res = MagicMock()
    mock_session = MagicMock()
    mock_session.access_token = "mock-jwt-token"
    mock_auth_res.session = mock_session
    mock_supabase.auth.verify_otp.return_value = mock_auth_res

    # Call logic function directly
    res = verify_otp("user@example.com", "123456")
    assert res == {"access_token": "mock-jwt-token"}
    mock_supabase.auth.verify_otp.assert_called_once_with({
        "email": "user@example.com",
        "token": "123456",
        "type": "magiclink"
    })

    # Call via endpoint
    response = client.post("/api/auth/verify", json={"email": "user@example.com", "token": "123456"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"access_token": "mock-jwt-token"}

def test_verify_otp_failure(mock_supabase):
    # Setup mock to raise AuthApiError
    mock_supabase.auth.verify_otp.side_effect = AuthApiError("Invalid OTP token", 401, "invalid_otp")

    # Direct function call
    with pytest.raises(AuthApiError) as exc_info:
        verify_otp("user@example.com", "wrong-otp")
    assert exc_info.value.message == "Invalid OTP token"

    # API Endpoint call
    response = client.post("/api/auth/verify", json={"email": "user@example.com", "token": "wrong-otp"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Auth verification failed" in response.json()["detail"]

def test_verify_otp_no_session(mock_supabase):
    # Setup mock to return response with no session
    mock_auth_res = MagicMock()
    mock_auth_res.session = None
    mock_supabase.auth.verify_otp.return_value = mock_auth_res

    # Direct function call
    with pytest.raises(SessionCreationError) as exc_info:
        verify_otp("user@example.com", "123456")
    assert "Session could not be created." in str(exc_info.value)

    # API Endpoint call
    response = client.post("/api/auth/verify", json={"email": "user@example.com", "token": "123456"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Verification failed" in response.json()["detail"]

def test_send_magic_link_unexpected_error(mock_supabase):
    # Setup mock to raise unexpected Exception
    mock_supabase.auth.sign_in_with_otp.side_effect = Exception("Database is down")

    # API Endpoint call
    response = client.post("/api/auth/magic-link", json={"email": "user@example.com"})
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["detail"] == "Internal server error"

def test_verify_otp_unexpected_error(mock_supabase):
    # Setup mock to raise unexpected Exception
    mock_supabase.auth.verify_otp.side_effect = Exception("Database is down")

    # API Endpoint call
    response = client.post("/api/auth/verify", json={"email": "user@example.com", "token": "123456"})
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["detail"] == "Internal server error"

def test_send_magic_link_invalid_email():
    # Attempting to call magic-link with invalid email format
    response = client.post("/api/auth/magic-link", json={"email": "not-an-email"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Verify the error detail mentions the email validation failure
    errors = response.json()["detail"]
    assert any(err["loc"] == ["body", "email"] for err in errors)

def test_verify_otp_invalid_email():
    # Attempting to call verify with invalid email format
    response = client.post("/api/auth/verify", json={"email": "not-an-email", "token": "123456"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Verify the error detail mentions the email validation failure
    errors = response.json()["detail"]
    assert any(err["loc"] == ["body", "email"] for err in errors)

def test_register_success(mock_supabase):
    # Setup mock for sign_up
    mock_auth_res = MagicMock()
    mock_user = MagicMock()
    mock_user.id = "user-uuid-123"
    mock_auth_res.user = mock_user
    mock_supabase.auth.sign_up.return_value = mock_auth_res

    # Call endpoint
    payload = {"email": "test@example.com", "password": "password123", "username": "testuser"}
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "success", "user_id": "user-uuid-123"}
    mock_supabase.auth.sign_up.assert_called_once_with({
        "email": "test@example.com",
        "password": "password123",
        "options": {
            "data": {
                "username": "testuser"
            }
        }
    })

def test_register_failure(mock_supabase):
    # Setup mock to raise AuthApiError
    mock_supabase.auth.sign_up.side_effect = AuthApiError("User already exists", 400, "user_exists")

    payload = {"email": "test@example.com", "password": "password123", "username": "testuser"}
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Auth error" in response.json()["detail"]

def test_login_success(mock_supabase):
    # Setup mock for sign_in_with_password
    mock_auth_res = MagicMock()
    mock_session = MagicMock()
    mock_session.access_token = "mock-jwt-token"
    mock_user = MagicMock()
    mock_user.email = "alice@example.com"
    mock_user.user_metadata = {"username": "alice"}
    mock_auth_res.session = mock_session
    mock_auth_res.user = mock_user
    mock_supabase.auth.sign_in_with_password.return_value = mock_auth_res

    # Call endpoint
    payload = {"email": "alice@example.com", "password": "password123"}
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "access_token": "mock-jwt-token",
        "email": "alice@example.com",
        "username": "alice"
    }
    mock_supabase.auth.sign_in_with_password.assert_called_once_with({
        "email": "alice@example.com",
        "password": "password123"
    })

def test_login_failure(mock_supabase):
    # Setup mock to raise AuthApiError
    mock_supabase.auth.sign_in_with_password.side_effect = AuthApiError("Invalid login credentials", 400, "invalid_credentials")

    payload = {"email": "alice@example.com", "password": "wrongpassword"}
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Auth verification failed" in response.json()["detail"]
