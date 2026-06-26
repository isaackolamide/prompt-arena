import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException, status
import pytest
from google.api_core.exceptions import GoogleAPICallError, ResourceExhausted
from postgrest.exceptions import APIError

from app.services.llm_proxy import execute_prompt


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def mock_supabase():
    with patch(
        "app.services.llm_proxy.get_supabase_client"
    ) as mock_get_client:
        client = MagicMock()
        mock_get_client.return_value = client
        yield client


@pytest.fixture
def mock_genai():
    with patch("app.services.llm_proxy.genai") as mock_g:
        yield mock_g


@pytest.fixture
def mock_settings():
    with patch("app.services.llm_proxy.settings") as mock_s:
        # Default API Key is valid
        mock_s.GEMINI_API_KEY = "valid-api-key"
        yield mock_s


# Setup helpers for supabase queries
def setup_mock_session(
    mock_supabase_client,
    profile_id="user-uuid",
    status="in_progress",
    token_budget=500,
    has_challenge=True,
):
    mock_table = MagicMock()
    mock_supabase_client.table.return_value = mock_table
    mock_select = MagicMock()
    mock_table.select.return_value = mock_select
    mock_eq = MagicMock()
    mock_select.eq.return_value = mock_eq

    if status is None:
        # session not found
        mock_eq.execute.return_value = MagicMock(data=[])
        return

    session_data = {
        "id": "session-uuid",
        "profile_id": profile_id,
        "status": status,
        "token_budget": token_budget,
    }
    if has_challenge:
        session_data["challenges"] = {
            "system_prompt": "Challenge system instructions."
        }

    mock_eq.execute.return_value = MagicMock(data=[session_data])


@pytest.mark.anyio
async def test_execute_prompt_success(
    mock_supabase, mock_genai, mock_settings
):
    # Setup mock session and RPC
    setup_mock_session(mock_supabase, profile_id="user-uuid", token_budget=500)
    mock_rpc = MagicMock()
    mock_supabase.rpc.return_value = mock_rpc
    mock_rpc.execute.return_value = MagicMock(data=350)  # remaining budget

    # Setup mock Gemini model response
    mock_response = MagicMock()
    mock_response.text = "Conceptual hint for binary search."
    mock_response.usage_metadata = MagicMock()
    mock_response.usage_metadata.total_token_count = 150

    mock_model = MagicMock()
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)
    mock_genai.GenerativeModel.return_value = mock_model

    session_id = uuid.uuid4()
    result = await execute_prompt(
        session_id=session_id,
        prompt="How to do binary search?",
        user_id="user-uuid",
    )

    assert result["response"] == "Conceptual hint for binary search."
    assert result["tokens_used"] == 150
    assert result["remaining_budget"] == 350

    # Verify Gemini was configured and initialized correctly
    mock_genai.configure.assert_called_once_with(api_key="valid-api-key")
    mock_genai.GenerativeModel.assert_called_once()
    system_inst = mock_genai.GenerativeModel.call_args[1]["system_instruction"]
    assert "Guardrails:" in system_inst

    # Verify budget was deducted
    mock_supabase.rpc.assert_called_once_with(
        "deduct_session_budget",
        {"session_id": str(session_id), "tokens_to_deduct": 150},
    )


@pytest.mark.anyio
async def test_execute_prompt_missing_session(
    mock_supabase, mock_genai, mock_settings
):
    # Setup session as missing (empty data list)
    setup_mock_session(mock_supabase, status=None)

    session_id = uuid.uuid4()
    with pytest.raises(HTTPException) as exc_info:
        await execute_prompt(
            session_id=session_id, prompt="Help", user_id="user-uuid"
        )

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "Active session not found"
    mock_genai.GenerativeModel.assert_not_called()


@pytest.mark.anyio
async def test_execute_prompt_unauthorized_user(
    mock_supabase, mock_genai, mock_settings
):
    # Setup session with different profile_id
    setup_mock_session(mock_supabase, profile_id="other-user")

    session_id = uuid.uuid4()
    with pytest.raises(HTTPException) as exc_info:
        await execute_prompt(
            session_id=session_id, prompt="Help", user_id="user-uuid"
        )

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "Forbidden" in exc_info.value.detail
    mock_genai.GenerativeModel.assert_not_called()


@pytest.mark.anyio
async def test_execute_prompt_inactive_session(
    mock_supabase, mock_genai, mock_settings
):
    # Setup session as completed
    setup_mock_session(mock_supabase, status="completed")

    session_id = uuid.uuid4()
    with pytest.raises(HTTPException) as exc_info:
        await execute_prompt(
            session_id=session_id, prompt="Help", user_id="user-uuid"
        )

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "Active session not found"
    mock_genai.GenerativeModel.assert_not_called()


@pytest.mark.anyio
async def test_execute_prompt_budget_exhausted(
    mock_supabase, mock_genai, mock_settings
):
    # Setup session with zero budget
    setup_mock_session(mock_supabase, token_budget=0)

    session_id = uuid.uuid4()
    with pytest.raises(HTTPException) as exc_info:
        await execute_prompt(
            session_id=session_id, prompt="Help", user_id="user-uuid"
        )

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "Token budget exhausted"
    mock_genai.GenerativeModel.assert_not_called()


@pytest.mark.anyio
async def test_execute_prompt_too_long(
    mock_supabase, mock_genai, mock_settings
):
    # Prompt is 10001 characters
    long_prompt = "a" * 10001
    session_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc_info:
        await execute_prompt(
            session_id=session_id, prompt=long_prompt, user_id="user-uuid"
        )

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "exceeds maximum length" in exc_info.value.detail
    mock_supabase.table.assert_not_called()


@pytest.mark.anyio
async def test_execute_prompt_timeout(
    mock_supabase, mock_genai, mock_settings
):
    setup_mock_session(mock_supabase)

    # Setup Gemini model to return a mock
    mock_model = MagicMock()
    mock_model.generate_content_async = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model

    session_id = uuid.uuid4()
    with patch("app.services.llm_proxy.asyncio.wait_for") as mock_wait_for:
        # Mock wait_for to raise TimeoutError to avoid actually sleeping
        mock_wait_for.side_effect = asyncio.TimeoutError()

        with pytest.raises(HTTPException) as exc_info:
            await execute_prompt(
                session_id=session_id, prompt="Help", user_id="user-uuid"
            )

    assert exc_info.value.status_code == status.HTTP_504_GATEWAY_TIMEOUT
    # Verify no tokens were deducted
    mock_supabase.rpc.assert_not_called()


@pytest.mark.anyio
async def test_execute_prompt_rate_limit(
    mock_supabase, mock_genai, mock_settings
):
    setup_mock_session(mock_supabase)

    # Setup Gemini model to raise ResourceExhausted exception
    mock_model = MagicMock()
    mock_model.generate_content_async = AsyncMock(
        side_effect=ResourceExhausted("Rate limit exceeded")
    )
    mock_genai.GenerativeModel.return_value = mock_model

    session_id = uuid.uuid4()
    with pytest.raises(HTTPException) as exc_info:
        await execute_prompt(
            session_id=session_id, prompt="Help", user_id="user-uuid"
        )

    assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    mock_supabase.rpc.assert_not_called()


@pytest.mark.anyio
async def test_execute_prompt_google_api_error(
    mock_supabase, mock_genai, mock_settings
):
    setup_mock_session(mock_supabase)

    # Setup Gemini model to raise GoogleAPICallError
    mock_model = MagicMock()
    mock_model.generate_content_async = AsyncMock(
        side_effect=GoogleAPICallError("Internal server error")
    )
    mock_genai.GenerativeModel.return_value = mock_model

    session_id = uuid.uuid4()
    with pytest.raises(HTTPException) as exc_info:
        await execute_prompt(
            session_id=session_id, prompt="Help", user_id="user-uuid"
        )

    assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY
    mock_supabase.rpc.assert_not_called()


@pytest.mark.anyio
async def test_execute_prompt_development_fallback(
    mock_supabase, mock_genai, mock_settings
):
    setup_mock_session(mock_supabase)
    mock_rpc = MagicMock()
    mock_supabase.rpc.return_value = mock_rpc
    mock_rpc.execute.return_value = MagicMock(data=400)  # remaining budget

    # Set config to placeholder/mock value
    mock_settings.GEMINI_API_KEY = "placeholder"

    session_id = uuid.uuid4()
    result = await execute_prompt(
        session_id=session_id,
        prompt="How to do bubble sort?",
        user_id="user-uuid",
    )

    assert "Mock LLM Response" in result["response"]
    assert "bubble sort" in result["response"]
    assert result["tokens_used"] == 100
    assert result["remaining_budget"] == 400

    # Verify Gemini model was NOT called
    mock_genai.GenerativeModel.assert_not_called()

    # Verify tokens were deducted
    mock_supabase.rpc.assert_called_once_with(
        "deduct_session_budget",
        {"session_id": str(session_id), "tokens_to_deduct": 100},
    )


@pytest.mark.anyio
async def test_execute_prompt_deduction_insufficient_budget(
    mock_supabase, mock_genai, mock_settings
):
    setup_mock_session(mock_supabase)
    mock_rpc = MagicMock()
    mock_supabase.rpc.return_value = mock_rpc
    # Mock RPC raising APIError
    mock_rpc.execute.side_effect = APIError(
        {"message": "Insufficient token budget or session not found"}
    )

    # Set config to placeholder/mock value
    mock_settings.GEMINI_API_KEY = "placeholder"

    session_id = uuid.uuid4()
    with pytest.raises(HTTPException) as exc_info:
        await execute_prompt(
            session_id=session_id,
            prompt="How to do bubble sort?",
            user_id="user-uuid",
        )

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "Token budget exhausted" in exc_info.value.detail
