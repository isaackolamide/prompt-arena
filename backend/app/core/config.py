import os
import logging
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Settings(BaseModel):
    SUPABASE_URL: str = Field(default_factory=lambda: os.getenv("SUPABASE_URL", "https://mock.supabase.co"))
    SUPABASE_ANON_KEY: str = Field(default_factory=lambda: os.getenv("SUPABASE_ANON_KEY", "mock-anon-key"))
    SUPABASE_SERVICE_ROLE_KEY: str = Field(default_factory=lambda: os.getenv("SUPABASE_SERVICE_ROLE_KEY", "mock-service-role-key"))
    ENV: str = Field(default_factory=lambda: os.getenv("ENV", "development"))
    PORT: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    GEMINI_API_KEY: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    
    # AWS Lambda Configuration
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default_factory=lambda: os.getenv("AWS_ACCESS_KEY_ID") or None)
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("AWS_SECRET_ACCESS_KEY") or None)
    AWS_REGION: str = Field(default_factory=lambda: os.getenv("AWS_REGION", "us-east-1"))
    AWS_LAMBDA_FUNCTION_NAME: str = Field(default_factory=lambda: os.getenv("AWS_LAMBDA_FUNCTION_NAME", "prompt-arena-sandbox"))
    AWS_LAMBDA_ENDPOINT_URL: Optional[str] = Field(default_factory=lambda: os.getenv("AWS_LAMBDA_ENDPOINT_URL") or None)

settings = Settings()

# Configure logging for the "app" logger
logger = logging.getLogger("app")
logger.setLevel(logging.INFO if settings.ENV == "production" else logging.DEBUG)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
