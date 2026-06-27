import asyncio
import json
import logging
import uuid
from typing import Any

from fastapi import HTTPException, status
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPICallError, ResourceExhausted
from postgrest.exceptions import APIError

from app.core.config import settings
from app.db.supabase import get_supabase_admin_client, get_supabase_client

logger = logging.getLogger("app")


def log_event(event_name: str, **kwargs: Any) -> None:
    """Emits structured JSON log events."""
    log_data = {"event": event_name, **kwargs}
    logger.info(json.dumps(log_data))


async def execute_prompt(
    session_id: uuid.UUID, prompt: str, user_id: str
) -> dict[str, Any]:
    """Verifies session status, calls Gemini API, deducts tokens, maps errors."""
    session_id_str = str(session_id)
    user_id_str = str(user_id)

    # 1. Telemetry: log prompt started
    log_event("llm_prompt_started", session_id=session_id_str, user_id=user_id_str)

    try:
        # 2. Prompt Validation
        if not prompt or not prompt.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt cannot be empty or whitespace-only",
            )
        if len(prompt) > 10000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt exceeds maximum length of 10000 characters",
            )

        # 3. Session Verification
        supabase = get_supabase_client()

        def fetch_session() -> Any:
            return (
                supabase.table("game_sessions")
                .select("*, challenges(*)")
                .eq("id", session_id_str)
                .execute()
            )

        response = await asyncio.to_thread(fetch_session)

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Active session not found",
            )

        session = response.data[0]

        if str(session.get("profile_id")) != user_id_str:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Session does not belong to this user",
            )

        if session.get("status") != "in_progress":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Active session not found",
            )

        current_budget = session.get("token_budget") or 0
        if current_budget <= 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token budget exhausted",
            )

        challenge = session.get("challenges")
        if not challenge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Challenge details not found",
            )

        system_prompt = challenge.get("system_prompt", "")

        # 4. Upstream Call Guardrails injection
        guardrails = (
            "\n\nGuardrails: You are an AI assistant helping the user solve a "
            "programming challenge. Guide the player by providing conceptual "
            "hints, explanations, and advice, but DO NOT output direct code "
            "solutions, complete implementations, or copy-pasteable blocks "
            "of code for the challenge."
        )
        full_system_prompt = f"{system_prompt}{guardrails}"

        # Determine development key fallback
        api_key = settings.GEMINI_API_KEY
        is_placeholder = (
            not api_key
            or api_key.strip().lower() in {"placeholder", "dummy", "mock"}
        )

        if is_placeholder:
            # Return a deterministic mock response
            prompt_prefix = prompt[:50]
            mock_text = f"Mock LLM Response: {prompt_prefix}"
            tokens_used = 100

            # Deduct tokens using Supabase RPC with admin client
            supabase_admin = get_supabase_admin_client()

            def deduct_budget() -> Any:
                return supabase_admin.rpc(
                    "deduct_session_budget",
                    {"session_id": session_id_str, "tokens_to_deduct": tokens_used},
                ).execute()

            try:
                rpc_response = await asyncio.to_thread(deduct_budget)
                remaining_budget = rpc_response.data
            except APIError as e:
                if "Session not found" in e.message or "Insufficient token budget" in e.message:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Token budget exhausted or session not found: {e.message}",
                    )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Database error during token deduction: {e.message}",
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Failed to update token budget: {str(e)}",
                )

            log_event(
                "llm_prompt_success",
                session_id=session_id_str,
                tokens_used=tokens_used,
                remaining_budget=remaining_budget,
            )
            return {
                "response": mock_text,
                "tokens_used": tokens_used,
                "remaining_budget": remaining_budget,
            }

        # Otherwise make upstream Gemini API call
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=full_system_prompt,
        )

        try:
            # 10-second timeout restriction
            response = await asyncio.wait_for(
                model.generate_content_async(prompt), timeout=10.0
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Upstream request timed out",
            )
        except ResourceExhausted as e:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Upstream rate limit exceeded: {str(e)}",
            )
        except GoogleAPICallError as e:
            # Map upstream rate limits / quota to 429
            status_code = getattr(e, "code", None)
            if (
                status_code == 429
                or "rate limit" in str(e).lower()
                or "quota" in str(e).lower()
            ):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Upstream rate limit exceeded: {str(e)}",
                )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Upstream service error: {str(e)}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Upstream connection failed: {str(e)}",
            )

        try:
            response_text = response.text
        except ValueError as safety_err:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    f"Response blocked by safety filters or empty response: "
                    f"{str(safety_err)}"
                ),
            )

        tokens_used = 100
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            tokens_used = getattr(response.usage_metadata, "total_token_count", 100)

        # 5. Token Deduction
        supabase_admin = get_supabase_admin_client()

        def deduct_budget_gemini() -> Any:
            return supabase_admin.rpc(
                "deduct_session_budget",
                {"session_id": session_id_str, "tokens_to_deduct": tokens_used},
            ).execute()

        try:
            rpc_response = await asyncio.to_thread(deduct_budget_gemini)
            remaining_budget = rpc_response.data
        except APIError as e:
            if "Session not found" in e.message or "Insufficient token budget" in e.message:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Token budget exhausted or session not found: {e.message}",
                )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Database error during token deduction: {e.message}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to update token budget: {str(e)}",
            )

        log_event(
            "llm_prompt_success",
            session_id=session_id_str,
            tokens_used=tokens_used,
            remaining_budget=remaining_budget,
        )
        return {
            "response": response_text,
            "tokens_used": tokens_used,
            "remaining_budget": remaining_budget,
        }

    except HTTPException as http_exc:
        # Structured log failure
        log_event(
            "llm_prompt_failed",
            session_id=session_id_str,
            error_type="HTTPException",
            error_message=http_exc.detail,
        )
        raise
    except Exception as exc:
        log_event(
            "llm_prompt_failed",
            session_id=session_id_str,
            error_type=exc.__class__.__name__,
            error_message=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Internal proxy error: {str(exc)}",
        )
