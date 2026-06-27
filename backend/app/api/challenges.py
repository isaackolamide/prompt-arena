import uuid
from typing import Any
from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.schemas.challenges import PromptRequest, PromptResponse
from app.services.llm_proxy import execute_prompt

router = APIRouter(tags=["challenges"])


@router.post(
    "/api/challenges/session/{session_id}/prompt",
    response_model=PromptResponse,
    summary="Submit prompt for a challenge session (with /api prefix)",
)
@router.post(
    "/challenges/session/{session_id}/prompt",
    response_model=PromptResponse,
    summary="Submit prompt for a challenge session",
)
async def prompt_session_endpoint(
    session_id: uuid.UUID,
    body: PromptRequest,
    user_id: str = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Exposes the POST /challenges/session/{session_id}/prompt endpoint.
    Validates input prompt, enforces authentication, checks session budget
    and permissions, and returns the response from the LLM proxy service.
    """
    return await execute_prompt(
        session_id=session_id,
        prompt=body.prompt,
        user_id=user_id,
    )
