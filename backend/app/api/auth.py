import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from app.db.supabase import get_supabase_client
try:
    from gotrue.errors import AuthApiError
except ModuleNotFoundError:
    from supabase_auth.errors import AuthApiError

logger = logging.getLogger("app")

def mask_email(email: str) -> str:
    """
    Masks user email (e.g. user@example.com -> u***r@example.com) to prevent writing plaintext PII in logs.
    """
    if not email or "@" not in email:
        return email
    try:
        local_part, domain = email.split("@", 1)
        if len(local_part) <= 2:
            masked_local = local_part[0] + "*" * (len(local_part) - 1)
        else:
            masked_local = local_part[0] + "*" * (len(local_part) - 2) + local_part[-1]
        return f"{masked_local}@{domain}"
    except Exception:
        return email

class SessionCreationError(Exception):
    """Exception raised when a session cannot be created from OTP verification."""
    pass

router = APIRouter(prefix="/api/auth", tags=["auth"])

class MagicLinkRequest(BaseModel):
    email: EmailStr = Field(..., description="The user's email address")

class MagicLinkResponse(BaseModel):
    status: str = Field(..., description="The status of the magic link request")

class VerifyRequest(BaseModel):
    email: EmailStr = Field(..., description="The user's email address")
    token: str = Field(..., description="The OTP/token received by the user")

class VerifyResponse(BaseModel):
    access_token: str = Field(..., description="The access token for authentication")

class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="The user's email address")
    password: str = Field(..., min_length=6, description="The user's password")
    username: str = Field(..., min_length=3, description="The user's username")

class RegisterResponse(BaseModel):
    status: str = Field(..., description="The status of the registration")
    user_id: str = Field(..., description="The registered user's ID")

class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="The user's email address")
    password: str = Field(..., description="The user's password")

class LoginResponse(BaseModel):
    access_token: str = Field(..., description="The access token for authentication")
    email: str = Field(..., description="The logged in user's email")
    username: str = Field(..., description="The logged in user's username")

def send_magic_link(email: str) -> dict[str, str]:
    """
    Sends a magic link to the user's email using Supabase Auth.
    """
    logger.info(f"Attempting to send magic link to email: {mask_email(email)}")
    client = get_supabase_client()
    try:
        client.auth.sign_in_with_otp({"email": email})
        logger.info(f"Magic link sent successfully to email: {mask_email(email)}")
        return {"status": "success"}
    except AuthApiError as e:
        logger.error(f"Failed to send magic link via Supabase Auth for {mask_email(email)}: {e}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error sending magic link for {mask_email(email)}: {e}")
        raise e

def verify_otp(email: str, token: str) -> dict[str, str]:
    """
    Verifies the OTP token for the user's email using Supabase Auth.
    """
    logger.info(f"Attempting to verify OTP for email: {mask_email(email)}")
    client = get_supabase_client()
    try:
        res = client.auth.verify_otp({
            "email": email,
            "token": token,
            "type": "magiclink"
        })
        if not res or not res.session:
            logger.error(f"No session returned for {mask_email(email)} after OTP verification")
            raise SessionCreationError("Session could not be created.")
        logger.info(f"OTP verification successful for email: {mask_email(email)}")
        return {"access_token": res.session.access_token}
    except AuthApiError as e:
        logger.error(f"Failed to verify OTP via Supabase Auth for {mask_email(email)}: {e}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error verifying OTP for {mask_email(email)}: {e}")
        raise e

def sign_up_user(email: str, password: str, username: str) -> dict[str, str]:
    """
    Registers a new user using Supabase Auth.
    """
    logger.info(f"Attempting to register user: {mask_email(email)}")
    client = get_supabase_client()
    try:
        res = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "username": username
                }
            }
        })
        if not res or not res.user:
            logger.error(f"Failed to create user object for {mask_email(email)}")
            raise Exception("Registration failed to create user object.")
        logger.info(f"User registration successful: {mask_email(email)} with ID {res.user.id}")
        return {"status": "success", "user_id": str(res.user.id)}
    except AuthApiError as e:
        logger.error(f"Failed to register user via Supabase Auth for {mask_email(email)}: {e}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error registering user for {mask_email(email)}: {e}")
        raise e

def login_user(email: str, password: str) -> dict[str, str]:
    """
    Authenticates a user using email and password.
    """
    logger.info(f"Attempting login for user: {mask_email(email)}")
    client = get_supabase_client()
    try:
        res = client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if not res or not res.session or not res.user:
            logger.error(f"No session/user returned for {mask_email(email)} after password sign-in")
            raise SessionCreationError("Session could not be created.")
        
        user_metadata = res.user.user_metadata or {}
        username = user_metadata.get("username", "")
        
        logger.info(f"Password login successful for user: {mask_email(email)}")
        return {
            "access_token": res.session.access_token,
            "email": res.user.email,
            "username": username
        }
    except AuthApiError as e:
        logger.error(f"Failed to authenticate via Supabase Auth for {mask_email(email)}: {e}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error authenticating for {mask_email(email)}: {e}")
        raise e

@router.post("/magic-link", response_model=MagicLinkResponse)
def post_magic_link(payload: MagicLinkRequest):
    try:
        result = send_magic_link(payload.email)
        return result
    except AuthApiError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Auth error: {e.message}"
        )
    except Exception:
        logger.exception("Unexpected error sending magic link")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/verify", response_model=VerifyResponse)
def post_verify(payload: VerifyRequest):
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
    except Exception:
        logger.exception("Unexpected error verifying OTP")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/register", response_model=RegisterResponse)
def post_register(payload: RegisterRequest):
    try:
        result = sign_up_user(payload.email, payload.password, payload.username)
        return result
    except AuthApiError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Auth error: {e.message}"
        )
    except Exception as e:
        logger.exception("Unexpected error during registration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/login", response_model=LoginResponse)
def post_login(payload: LoginRequest):
    try:
        result = login_user(payload.email, payload.password)
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
    except Exception:
        logger.exception("Unexpected error during login")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
