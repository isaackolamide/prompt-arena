import os
from unittest.mock import patch
from app.core.config import Settings


def test_settings_default_values():
    """Test that default values are applied when environment variables are not set."""
    # We clear the specific AWS env vars to ensure we fall back to defaults
    aws_vars = [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_REGION",
        "AWS_LAMBDA_FUNCTION_NAME",
        "AWS_LAMBDA_ENDPOINT_URL",
    ]
    with patch.dict(os.environ, {}, clear=False):
        for var in aws_vars:
            os.environ.pop(var, None)
            
        settings = Settings()
        assert settings.AWS_ACCESS_KEY_ID == "mock-aws-access-key-id"
        assert settings.AWS_SECRET_ACCESS_KEY == "mock-aws-secret-access-key"
        assert settings.AWS_REGION == "us-east-1"
        assert settings.AWS_LAMBDA_FUNCTION_NAME == "prompt-arena-sandbox"
        assert settings.AWS_LAMBDA_ENDPOINT_URL is None


def test_settings_from_env():
    """Test that environment variables are correctly loaded into Settings."""
    env_mock = {
        "AWS_ACCESS_KEY_ID": "test-key-id",
        "AWS_SECRET_ACCESS_KEY": "test-secret-key",
        "AWS_REGION": "us-west-2",
        "AWS_LAMBDA_FUNCTION_NAME": "test-sandbox-fn",
        "AWS_LAMBDA_ENDPOINT_URL": "http://localhost:4566",
    }
    with patch.dict(os.environ, env_mock):
        settings = Settings()
        assert settings.AWS_ACCESS_KEY_ID == "test-key-id"
        assert settings.AWS_SECRET_ACCESS_KEY == "test-secret-key"
        assert settings.AWS_REGION == "us-west-2"
        assert settings.AWS_LAMBDA_FUNCTION_NAME == "test-sandbox-fn"
        assert settings.AWS_LAMBDA_ENDPOINT_URL == "http://localhost:4566"
