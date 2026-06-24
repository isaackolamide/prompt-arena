import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.db.supabase import get_supabase_client
try:
    from gotrue.errors import AuthApiError
except ModuleNotFoundError:
    from supabase_auth.errors import AuthApiError

logger = logging.getLogger("app")

class SessionCreationError(Exception):
    """Exception raised when a session cannot be created from OTP verification."""
    pass

router = APIRouter(prefix="/api/auth", tags=["auth"])

class MagicLinkRequest(BaseModel):
    email: str = Field(..., description="The user's email address")

class MagicLinkResponse(BaseModel):
    status: str = Field(..., description="The status of the magic link request")

class VerifyRequest(BaseModel):
    email: str = Field(..., description="The user's email address")
    token: str = Field(..., description="The OTP/token received by the user")

class VerifyResponse(BaseModel):
    access_token: str = Field(..., description="The access token for authentication")

def send_magic_link(email: str) -> dict[str, str]:
    """
    Sends a magic link to the user's email using Supabase Auth.
    """
    logger.info(f"Attempting to send magic link to email: {email}")
    client = get_supabase_client()
    try:
        client.auth.sign_in_with_otp({"email": email})
        logger.info(f"Magic link sent successfully to email: {email}")
        return {"status": "success"}
    except AuthApiError as e:
        logger.error(f"Failed to send magic link via Supabase Auth for {email}: {e}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error sending magic link for {email}: {e}")
        raise e

def verify_otp(email: str, token: str) -> dict[str, str]:
    """
    Verifies the OTP token for the user's email using Supabase Auth.
    """
    logger.info(f"Attempting to verify OTP for email: {email}")
    client = get_supabase_client()
    try:
        res = client.auth.verify_otp({
            "email": email,
            "token": token,
            "type": "magiclink"
        })
        if not res or not res.session:
            logger.error(f"No session returned for {email} after OTP verification")
            raise SessionCreationError("Session could not be created.")
        logger.info(f"OTP verification successful for email: {email}")
        return {"access_token": res.session.access_token}
    except AuthApiError as e:
        logger.error(f"Failed to verify OTP via Supabase Auth for {email}: {e}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error verifying OTP for {email}: {e}")
        raise e

@router.post("/magic-link", response_model=MagicLinkResponse)
async def post_magic_link(payload: MagicLinkRequest):
    try:
        result = send_magic_link(payload.email)
        return result
    except AuthApiError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Auth error: {e.message}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/verify", response_model=VerifyResponse)
async def post_verify(payload: VerifyRequest):
    try:
        result = verify_otp(payload.email, payload.token)
        return result
    except AuthApiError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Auth verification failed: {e.message}"
        )
    except SessionCreationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Verification failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
