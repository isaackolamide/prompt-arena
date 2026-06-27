from unittest.mock import MagicMock, patch
import pytest
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user

try:
    from gotrue.errors import AuthApiError
except ModuleNotFoundError:
    from supabase_auth.errors import AuthApiError


# Define anyio backend for async test execution
@pytest.fixture
def anyio_backend():
    return "asyncio"


# Define a dummy FastAPI app to test the dependency injection integration
app = FastAPI()

@app.get("/test-auth")
async def dummy_auth_route(user_id: str = Depends(get_current_user)):
    return {"user_id": user_id}


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_supabase():
    with patch("app.api.dependencies.get_supabase_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        yield mock_client


# -----------------------------------------------------------------------------
# Unit Tests (Direct Invocation)
# -----------------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_current_user_success_direct(mock_supabase):
    # Setup mock user response
    mock_user = MagicMock()
    mock_user.id = "12345678-1234-1234-1234-123456789012"
    
    mock_response = MagicMock()
    mock_response.user = mock_user
    mock_supabase.auth.get_user.return_value = mock_response

    # Call direct function
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")
    user_id = await get_current_user(credentials)

    assert user_id == "12345678-1234-1234-1234-123456789012"
    mock_supabase.auth.get_user.assert_called_once_with("valid-token")


@pytest.mark.anyio
async def test_get_current_user_missing_credentials_direct():
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(None)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Not authenticated"


@pytest.mark.anyio
async def test_get_current_user_empty_token_direct():
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="")
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Invalid token format"


@pytest.mark.anyio
async def test_get_current_user_invalid_token_direct(mock_supabase):
    # Setup mock to raise AuthApiError
    mock_supabase.auth.get_user.side_effect = AuthApiError(
        "Invalid token signature", 401, "invalid_token"
    )

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid or expired token" in exc_info.value.detail
    mock_supabase.auth.get_user.assert_called_once_with("invalid-token")


@pytest.mark.anyio
async def test_get_current_user_expired_token_direct(mock_supabase):
    # Setup mock to raise AuthApiError indicating token expired
    mock_supabase.auth.get_user.side_effect = AuthApiError(
        "Token has expired", 401, "token_expired"
    )

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="expired-token")
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid or expired token" in exc_info.value.detail
    mock_supabase.auth.get_user.assert_called_once_with("expired-token")


@pytest.mark.anyio
async def test_get_current_user_none_response_user_direct(mock_supabase):
    # Setup mock to return a response with None user
    mock_response = MagicMock()
    mock_response.user = None
    mock_supabase.auth.get_user.return_value = mock_response

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="some-token")
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Invalid or expired token"


@pytest.mark.anyio
async def test_get_current_user_unexpected_exception_direct(mock_supabase):
    # Setup mock to raise unexpected Exception
    mock_supabase.auth.get_user.side_effect = Exception("Supabase is down")

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="some-token")
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials due to internal error" in exc_info.value.detail


# -----------------------------------------------------------------------------
# Integration / HTTP Route Tests
# -----------------------------------------------------------------------------

def test_route_auth_success(client, mock_supabase):
    # Setup mock user response
    mock_user = MagicMock()
    mock_user.id = "12345678-1234-1234-1234-123456789012"
    
    mock_response = MagicMock()
    mock_response.user = mock_user
    mock_supabase.auth.get_user.return_value = mock_response

    response = client.get(
        "/test-auth",
        headers={"Authorization": "Bearer valid-token"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"user_id": "12345678-1234-1234-1234-123456789012"}


def test_route_auth_missing_header(client):
    # If no header is provided, credentials will be None and raise 401
    response = client.get("/test-auth")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Not authenticated"


def test_route_auth_invalid_header_format(client):
    # If header does not follow bearer scheme, HTTPBearer will still trigger but credentials might be empty/invalid
    response = client.get(
        "/test-auth",
        headers={"Authorization": "NotBearer token"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Not authenticated"


def test_route_auth_invalid_token(client, mock_supabase):
    mock_supabase.auth.get_user.side_effect = AuthApiError(
        "Invalid token signature", 401, "invalid_token"
    )

    response = client.get(
        "/test-auth",
        headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid or expired token" in response.json()["detail"]
