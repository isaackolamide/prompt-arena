from unittest.mock import MagicMock, patch
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.api.auth import send_magic_link, verify_otp
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

    # API Endpoint call
    response = client.post("/api/auth/verify", json={"email": "user@example.com", "token": "123456"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Verification failed" in response.json()["detail"]
