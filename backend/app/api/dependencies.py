import logging
from fastapi import Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.db.supabase import get_supabase_client

try:
    from gotrue.errors import AuthApiError
except ModuleNotFoundError:
    from supabase_auth.errors import AuthApiError

logger = logging.getLogger("app")

# Expose HTTPBearer dependency.
# Note: we use auto_error=False so we can raise 401 status code instead of 403.
security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Dependency injection guard that parses the Bearer token,
    verifies it with Supabase Auth, and returns the authenticated user's UUID.
    """
    if credentials is None:
        logger.warning("Authentication failed: Missing credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    if not token:
        logger.warning("Authentication failed: Empty Bearer token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    client = get_supabase_client()
    try:
        response = await run_in_threadpool(client.auth.get_user, token)
        if response is None or response.user is None:
            logger.warning("Authentication failed: get_user response has no user")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return str(response.user.id)
    except HTTPException:
        raise
    except AuthApiError as e:
        logger.warning(f"Authentication failed via Supabase AuthApiError: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {e.message}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials due to internal error",
            headers={"WWW-Authenticate": "Bearer"},
        )
