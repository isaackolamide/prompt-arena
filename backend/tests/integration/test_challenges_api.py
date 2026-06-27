import uuid
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from google.api_core.exceptions import GoogleAPICallError, ResourceExhausted

from app.main import app

try:
    from gotrue.errors import AuthApiError
except ModuleNotFoundError:
    from supabase_auth.errors import AuthApiError


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def mock_supabase():
    with patch("app.api.dependencies.get_supabase_client") as mock_dep_client, \
         patch("app.services.llm_proxy.get_supabase_client") as mock_service_client, \
         patch("app.services.llm_proxy.get_supabase_admin_client") as mock_admin_client:
        dep_client = MagicMock()
        service_client = MagicMock()
        mock_dep_client.return_value = dep_client
        mock_service_client.return_value = service_client
        mock_admin_client.return_value = service_client
        yield dep_client, service_client


@pytest.fixture
def mock_settings():
    with patch("app.services.llm_proxy.settings") as mock_s:
        mock_s.GEMINI_API_KEY = "valid-api-key"
        yield mock_s


@pytest.fixture
def mock_genai():
    with patch("app.services.llm_proxy.genai") as mock_g:
        yield mock_g


def setup_mock_auth(mock_supabase_dep, user_id="user-uuid", valid=True):
    if not valid:
        mock_supabase_dep.auth.get_user.side_effect = AuthApiError(
            "Invalid token signature", 401, "invalid_token"
        )
        return

    mock_user = MagicMock()
    mock_user.id = user_id
    mock_response = MagicMock()
    mock_response.user = mock_user
    mock_supabase_dep.auth.get_user.return_value = mock_response


def setup_mock_session(
    mock_supabase_service,
    session_id_str,
    profile_id="user-uuid",
    status="in_progress",
    token_budget=500,
    has_challenge=True,
):
    mock_table = MagicMock()
    mock_supabase_service.table.return_value = mock_table
    mock_select = MagicMock()
    mock_table.select.return_value = mock_select
    mock_eq = MagicMock()
    mock_select.eq.return_value = mock_eq

    if status is None:
        mock_eq.execute.return_value = MagicMock(data=[])
        return

    session_data = {
        "id": session_id_str,
        "profile_id": profile_id,
        "status": status,
        "token_budget": token_budget,
    }
    if has_challenge:
        session_data["challenges"] = {
            "system_prompt": "Challenge system instructions."
        }

    mock_eq.execute.return_value = MagicMock(data=[session_data])


def test_missing_token_unauthorized(client: TestClient):
    session_id = uuid.uuid4()
    # Path 1: Without /api prefix
    response = client.post(
        f"/challenges/session/{session_id}/prompt",
        json={"prompt": "Hello"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Not authenticated"

    # Path 2: With /api prefix
    response = client.post(
        f"/api/challenges/session/{session_id}/prompt",
        json={"prompt": "Hello"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Not authenticated"


def test_invalid_token_unauthorized(client: TestClient, mock_supabase):
    dep_client, _ = mock_supabase
    setup_mock_auth(dep_client, valid=False)

    session_id = uuid.uuid4()
    response = client.post(
        f"/challenges/session/{session_id}/prompt",
        json={"prompt": "Hello"},
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid or expired token" in response.json()["detail"]


def test_session_missing_forbidden(client: TestClient, mock_supabase):
    dep_client, service_client = mock_supabase
    setup_mock_auth(dep_client, user_id="user-uuid")

    session_id = uuid.uuid4()
    setup_mock_session(service_client, str(session_id), status=None)

    response = client.post(
        f"/challenges/session/{session_id}/prompt",
        json={"prompt": "Hello"},
        headers={"Authorization": "Bearer valid-token"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Active session not found"


def test_session_wrong_user_forbidden(client: TestClient, mock_supabase):
    dep_client, service_client = mock_supabase
    setup_mock_auth(dep_client, user_id="user-uuid")

    session_id = uuid.uuid4()
    setup_mock_session(service_client, str(session_id), profile_id="other-user")

    response = client.post(
        f"/challenges/session/{session_id}/prompt",
        json={"prompt": "Hello"},
        headers={"Authorization": "Bearer valid-token"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Forbidden" in response.json()["detail"]


def test_session_inactive_forbidden(client: TestClient, mock_supabase):
    dep_client, service_client = mock_supabase
    setup_mock_auth(dep_client, user_id="user-uuid")

    session_id = uuid.uuid4()
    setup_mock_session(service_client, str(session_id), status="completed")

    response = client.post(
        f"/challenges/session/{session_id}/prompt",
        json={"prompt": "Hello"},
        headers={"Authorization": "Bearer valid-token"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Active session not found"


def test_session_budget_exhausted_forbidden(client: TestClient, mock_supabase):
    dep_client, service_client = mock_supabase
    setup_mock_auth(dep_client, user_id="user-uuid")

    session_id = uuid.uuid4()
    setup_mock_session(service_client, str(session_id), token_budget=0)

    response = client.post(
        f"/challenges/session/{session_id}/prompt",
        json={"prompt": "Hello"},
        headers={"Authorization": "Bearer valid-token"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Token budget exhausted"


def test_prompt_too_long_bad_request(client: TestClient, mock_supabase):
    dep_client, service_client = mock_supabase
    setup_mock_auth(dep_client, user_id="user-uuid")

    session_id = uuid.uuid4()
    setup_mock_session(service_client, str(session_id))

    long_prompt = "a" * 10001
    response = client.post(
        f"/challenges/session/{session_id}/prompt",
        json={"prompt": long_prompt},
        headers={"Authorization": "Bearer valid-token"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "exceeds maximum length" in response.json()["detail"]


def test_prompt_empty_bad_request(client: TestClient, mock_supabase):
    dep_client, service_client = mock_supabase
    setup_mock_auth(dep_client, user_id="user-uuid")

    session_id = uuid.uuid4()
    setup_mock_session(service_client, str(session_id))

    for empty_prompt in ["", "   ", "\n  \t "]:
        response = client.post(
            f"/challenges/session/{session_id}/prompt",
            json={"prompt": empty_prompt},
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cannot be empty or whitespace-only" in response.json()["detail"]


def test_successful_prompt_execution(
    client: TestClient, mock_supabase, mock_settings, mock_genai
):
    dep_client, service_client = mock_supabase
    setup_mock_auth(dep_client, user_id="user-uuid")

    session_id = uuid.uuid4()
    setup_mock_session(service_client, str(session_id))

    # Mock RPC for budget deduction
    mock_rpc = MagicMock()
    service_client.rpc.return_value = mock_rpc
    mock_rpc.execute.return_value = MagicMock(data=350)  # remaining budget

    # Mock Gemini model response
    mock_response = MagicMock()
    mock_response.text = "Conceptual hint."
    mock_response.usage_metadata = MagicMock()
    mock_response.usage_metadata.total_token_count = 150

    mock_model = MagicMock()
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)
    mock_genai.GenerativeModel.return_value = mock_model

    # Verify both prefixed and non-prefixed routes
    for endpoint_template in [
        "/challenges/session/{session_id}/prompt",
        "/api/challenges/session/{session_id}/prompt",
    ]:
        response = client.post(
            endpoint_template.format(session_id=session_id),
            json={"prompt": "Explain binary search"},
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["response"] == "Conceptual hint."
        assert data["tokens_used"] == 150
        assert data["remaining_budget"] == 350


def test_upstream_timeout_gateway_timeout(
    client: TestClient, mock_supabase, mock_settings, mock_genai
):
    dep_client, service_client = mock_supabase
    setup_mock_auth(dep_client, user_id="user-uuid")

    session_id = uuid.uuid4()
    setup_mock_session(service_client, str(session_id))

    mock_model = MagicMock()
    mock_model.generate_content_async = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model

    with patch("app.services.llm_proxy.asyncio.wait_for") as mock_wait_for:
        mock_wait_for.side_effect = asyncio.TimeoutError()

        response = client.post(
            f"/challenges/session/{session_id}/prompt",
            json={"prompt": "Explain binary search"},
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == status.HTTP_504_GATEWAY_TIMEOUT
        assert response.json()["detail"] == "Upstream request timed out"


def test_upstream_rate_limit_exceeded(
    client: TestClient, mock_supabase, mock_settings, mock_genai
):
    dep_client, service_client = mock_supabase
    setup_mock_auth(dep_client, user_id="user-uuid")

    session_id = uuid.uuid4()
    setup_mock_session(service_client, str(session_id))

    mock_model = MagicMock()
    mock_model.generate_content_async = AsyncMock(
        side_effect=ResourceExhausted("Rate limit exceeded")
    )
    mock_genai.GenerativeModel.return_value = mock_model

    response = client.post(
        f"/challenges/session/{session_id}/prompt",
        json={"prompt": "Explain binary search"},
        headers={"Authorization": "Bearer valid-token"},
    )
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "rate limit exceeded" in response.json()["detail"].lower()


def test_upstream_connection_failed_bad_gateway(
    client: TestClient, mock_supabase, mock_settings, mock_genai
):
    dep_client, service_client = mock_supabase
    setup_mock_auth(dep_client, user_id="user-uuid")

    session_id = uuid.uuid4()
    setup_mock_session(service_client, str(session_id))

    mock_model = MagicMock()
    mock_model.generate_content_async = AsyncMock(
        side_effect=GoogleAPICallError("Internal server error")
    )
    mock_genai.GenerativeModel.return_value = mock_model

    response = client.post(
        f"/challenges/session/{session_id}/prompt",
        json={"prompt": "Explain binary search"},
        headers={"Authorization": "Bearer valid-token"},
    )
    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    assert "upstream service error" in response.json()["detail"].lower()
