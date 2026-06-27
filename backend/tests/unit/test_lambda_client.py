import io
import json
import pytest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError, ConnectTimeoutError, ReadTimeoutError

from app.core.config import Settings
from app.services.lambda_client import (
    LambdaClient,
    SandboxTimeoutError,
    SandboxExecutionError,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        AWS_ACCESS_KEY_ID="test-key",
        AWS_SECRET_ACCESS_KEY="test-secret",
        AWS_REGION="us-west-2",
        AWS_LAMBDA_FUNCTION_NAME="test-sandbox",
        AWS_LAMBDA_ENDPOINT_URL="http://localhost:4566",
    )


@pytest.fixture
def mock_boto_client():
    with patch("app.services.lambda_client.boto3.client") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.mark.anyio
async def test_execute_in_sandbox_success(test_settings, mock_boto_client):
    # Setup mock payload stream
    payload_data = {
        "stdout": "hello world\n",
        "stderr": "",
        "passed": True,
        "test_results": [
            {"name": "test_addition", "passed": True, "message": ""}
        ],
    }
    mock_payload = io.BytesIO(json.dumps(payload_data).encode("utf-8"))
    mock_boto_client.invoke.return_value = {
        "StatusCode": 200,
        "Payload": mock_payload,
    }

    client = LambdaClient(test_settings)
    result = await client.execute_in_sandbox(
        code="def add(a, b): return a + b",
        test_suite="assert add(1, 2) == 3",
        language="python",
    )

    # Verify Boto3 call parameters
    mock_boto_client.invoke.assert_called_once_with(
        FunctionName="test-sandbox",
        InvocationType="RequestResponse",
        Payload=json.dumps(
            {
                "language": "python",
                "code": "def add(a, b): return a + b",
                "test_suite": "assert add(1, 2) == 3",
            }
        ).encode("utf-8"),
    )

    assert result["passed"] is True
    assert result["stdout"] == "hello world\n"
    assert result["stderr"] == ""
    assert len(result["test_results"]) == 1
    assert result["test_results"][0]["name"] == "test_addition"
    assert result["test_results"][0]["passed"] is True


@pytest.mark.anyio
async def test_execute_in_sandbox_timeout(test_settings, mock_boto_client):
    # 1. AWS Lambda Function timeout indicated by FunctionError in response
    payload_data = {
        "errorMessage": "2026-06-27T08:50:52.484Z c12919e9-5377-47f9-bde5-6e890924bec0 Task timed out after 5.01 seconds",
        "errorType": "Unhandled",
    }
    mock_payload = io.BytesIO(json.dumps(payload_data).encode("utf-8"))
    mock_boto_client.invoke.return_value = {
        "StatusCode": 200,
        "FunctionError": "Unhandled",
        "Payload": mock_payload,
    }

    client = LambdaClient(test_settings)
    with pytest.raises(SandboxTimeoutError) as exc_info:
        await client.execute_in_sandbox(
            code="sleep(10)", test_suite="assert True", language="python"
        )
    assert "timed out" in str(exc_info.value)

    # 2. Client side ReadTimeoutError
    mock_boto_client.invoke.side_effect = ReadTimeoutError(
        endpoint_url="http://localhost:4566", operation_name="Invoke"
    )
    with pytest.raises(SandboxTimeoutError) as exc_info:
        await client.execute_in_sandbox(
            code="sleep(10)", test_suite="assert True", language="python"
        )
    assert "timed out" in str(exc_info.value)


@pytest.mark.anyio
async def test_execute_in_sandbox_aws_error(test_settings, mock_boto_client):
    # 1. AWS client error (e.g. ResourceNotFoundException)
    error_response = {
        "Error": {
            "Code": "ResourceNotFoundException",
            "Message": "Function not found: test-sandbox",
        }
    }
    mock_boto_client.invoke.side_effect = ClientError(
        error_response=error_response, operation_name="Invoke"
    )

    client = LambdaClient(test_settings)
    with pytest.raises(SandboxExecutionError) as exc_info:
        await client.execute_in_sandbox(
            code="print(1)", test_suite="assert True", language="python"
        )
    assert "ResourceNotFoundException" in str(exc_info.value)

    # 2. AWS connection timeout (network connect error)
    mock_boto_client.invoke.side_effect = ConnectTimeoutError(
        endpoint_url="http://localhost:4566"
    )
    with pytest.raises(SandboxExecutionError) as exc_info:
        await client.execute_in_sandbox(
            code="print(1)", test_suite="assert True", language="python"
        )
    assert "connection timed out" in str(exc_info.value)

    # 3. AWS Lambda unhandled non-timeout error
    mock_boto_client.invoke.side_effect = None
    payload_data = {
        "errorMessage": "SyntaxError: invalid syntax",
        "errorType": "SyntaxError",
    }
    mock_payload = io.BytesIO(json.dumps(payload_data).encode("utf-8"))
    mock_boto_client.invoke.return_value = {
        "StatusCode": 200,
        "FunctionError": "Unhandled",
        "Payload": mock_payload,
    }
    with pytest.raises(SandboxExecutionError) as exc_info:
        await client.execute_in_sandbox(
            code="print(1)", test_suite="assert True", language="python"
        )
    assert "SyntaxError" in str(exc_info.value)


@pytest.mark.anyio
async def test_execute_in_sandbox_invalid_json(test_settings, mock_boto_client):
    # Payload is not valid JSON
    mock_payload = io.BytesIO(b"not-a-json-string")
    mock_boto_client.invoke.return_value = {
        "StatusCode": 200,
        "Payload": mock_payload,
    }

    client = LambdaClient(test_settings)
    with pytest.raises(SandboxExecutionError) as exc_info:
        await client.execute_in_sandbox(
            code="print(1)", test_suite="assert True", language="python"
        )
    assert "parse sandbox response JSON" in str(exc_info.value)

    # Payload is JSON but missing keys
    payload_data = {"stdout": "missing keys"}
    mock_payload = io.BytesIO(json.dumps(payload_data).encode("utf-8"))
    mock_boto_client.invoke.return_value = {
        "StatusCode": 200,
        "Payload": mock_payload,
    }
    with pytest.raises(SandboxExecutionError) as exc_info:
        await client.execute_in_sandbox(
            code="print(1)", test_suite="assert True", language="python"
        )
    assert "Missing required key" in str(exc_info.value)
