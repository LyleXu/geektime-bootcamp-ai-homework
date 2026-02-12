"""Enhanced tests for result validator."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import openai

from pg_mcp_server.core.result_validator import ResultValidator
from pg_mcp_server.config.settings import OpenAIConfig
from pydantic import SecretStr


@pytest.fixture
def openai_config():
    """Create test OpenAI configuration."""
    return OpenAIConfig(
        api_key=SecretStr("test-api-key"),
        model="gpt-4",
        api_base="https://api.openai.com/v1",
        timeout=30,
        use_azure=False,
    )


@pytest.fixture
def azure_openai_config():
    """Create test Azure OpenAI configuration."""
    return OpenAIConfig(
        api_key=SecretStr("test-azure-key"),
        model="gpt-4",
        azure_endpoint="https://test.openai.azure.com",
        azure_deployment="gpt-4-deployment",
        api_version="2023-05-15",
        timeout=30,
        use_azure=True,
    )


class TestResultValidatorInitialization:
    """Test ResultValidator initialization."""

    def test_initialization_with_openai(self, openai_config):
        """Test initialization with standard OpenAI."""
        with patch("openai.AsyncOpenAI") as mock_openai:
            validator = ResultValidator(openai_config)
            
            assert validator.config == openai_config
            assert validator.model_name == "gpt-4"
            mock_openai.assert_called_once_with(
                api_key="test-api-key",
                base_url="https://api.openai.com/v1",
                timeout=30,
            )

    def test_initialization_with_azure_openai(self, azure_openai_config):
        """Test initialization with Azure OpenAI."""
        with patch("openai.AsyncAzureOpenAI") as mock_azure:
            validator = ResultValidator(azure_openai_config)
            
            assert validator.config == azure_openai_config
            assert validator.model_name == "gpt-4-deployment"
            mock_azure.assert_called_once_with(
                api_key="test-azure-key",
                azure_endpoint="https://test.openai.azure.com",
                api_version="2023-05-15",
                timeout=30,
            )

    def test_initialization_azure_missing_endpoint(self):
        """Test initialization fails when Azure endpoint missing."""
        config = OpenAIConfig(
            api_key=SecretStr("test-key"),
            model="gpt-4",
            use_azure=True,
            azure_deployment="deployment",
            # Missing azure_endpoint
        )
        
        with pytest.raises(ValueError, match="azure_endpoint and azure_deployment are required"):
            ResultValidator(config)

    def test_initialization_azure_missing_deployment(self):
        """Test initialization fails when Azure deployment missing."""
        config = OpenAIConfig(
            api_key=SecretStr("test-key"),
            model="gpt-4",
            use_azure=True,
            azure_endpoint="https://test.openai.azure.com",
            # Missing azure_deployment
        )
        
        with pytest.raises(ValueError, match="azure_endpoint and azure_deployment are required"):
            ResultValidator(config)


class TestValidateResults:
    """Test validate_results method."""

    @pytest.mark.asyncio
    async def test_validate_results_empty_results(self, openai_config):
        """Test validation with empty results."""
        with patch("openai.AsyncOpenAI"):
            validator = ResultValidator(openai_config)
            
            is_valid, error = await validator.validate_results(
                original_query="Get all users",
                sql="SELECT * FROM users",
                results=[],
            )
            
            assert is_valid is True
            assert error is None

    @pytest.mark.asyncio
    async def test_validate_results_valid_response(self, openai_config):
        """Test validation with VALID response from OpenAI."""
        with patch("openai.AsyncOpenAI") as mock_openai_class:
            # Mock the client and its methods
            mock_client = AsyncMock()
            mock_openai_class.return_value = mock_client
            
            # Mock the chat completion response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "VALID"
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            
            validator = ResultValidator(openai_config)
            
            is_valid, error = await validator.validate_results(
                original_query="Get all active users",
                sql="SELECT * FROM users WHERE active = true",
                results=[{"id": 1, "name": "Alice", "active": True}],
            )
            
            assert is_valid is True
            assert error is None
            
            # Verify API was called correctly
            mock_client.chat.completions.create.assert_called_once()
            call_kwargs = mock_client.chat.completions.create.call_args.kwargs
            assert call_kwargs["model"] == "gpt-4"
            assert call_kwargs["temperature"] == 0.1
            assert len(call_kwargs["messages"]) == 2

    @pytest.mark.asyncio
    async def test_validate_results_invalid_response(self, openai_config):
        """Test validation with INVALID response from OpenAI."""
        with patch("openai.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_openai_class.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "INVALID: Query returns wrong columns"
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            
            validator = ResultValidator(openai_config)
            
            is_valid, error = await validator.validate_results(
                original_query="Get user names",
                sql="SELECT * FROM users",
                results=[{"id": 1, "name": "Alice", "email": "alice@example.com"}],
            )
            
            assert is_valid is False
            assert error == "query returns wrong columns"

    @pytest.mark.asyncio
    async def test_validate_results_uncertain_response(self, openai_config):
        """Test validation with uncertain response from OpenAI."""
        with patch("openai.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_openai_class.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Uncertain: Need more context"
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            
            validator = ResultValidator(openai_config)
            
            is_valid, error = await validator.validate_results(
                original_query="Get data",
                sql="SELECT * FROM table",
                results=[{"col": "value"}],
            )
            
            # Conservative strategy: pass validation when uncertain
            assert is_valid is True
            assert error is None

    @pytest.mark.asyncio
    async def test_validate_results_empty_content(self, openai_config):
        """Test validation when OpenAI returns empty content."""
        with patch("openai.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_openai_class.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = None
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            
            validator = ResultValidator(openai_config)
            
            is_valid, error = await validator.validate_results(
                original_query="Get users",
                sql="SELECT * FROM users",
                results=[{"id": 1}],
            )
            
            # Conservative strategy: pass validation when empty response
            assert is_valid is True
            assert error is None

    @pytest.mark.asyncio
    async def test_validate_results_api_error(self, openai_config):
        """Test validation when API call fails."""
        with patch("openai.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_openai_class.return_value = mock_client
            
            # Create proper APIError with required request parameter
            mock_request = MagicMock()
            mock_request.url = "https://api.openai.com/v1/chat/completions"
            api_error = openai.APIError("API Error", request=mock_request, body=None)
            mock_client.chat.completions.create = AsyncMock(side_effect=api_error)
            
            validator = ResultValidator(openai_config)
            
            is_valid, error = await validator.validate_results(
                original_query="Get users",
                sql="SELECT * FROM users",
                results=[{"id": 1}],
            )
            
            # Conservative strategy: pass validation on error
            assert is_valid is True
            assert error is None

    @pytest.mark.asyncio
    async def test_validate_results_max_rows_limit(self, openai_config):
        """Test that only max_rows_to_check rows are sent to API."""
        with patch("openai.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_openai_class.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "VALID"
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            
            validator = ResultValidator(openai_config)
            
            # Create 10 rows
            results = [{"id": i, "name": f"User{i}"} for i in range(10)]
            
            await validator.validate_results(
                original_query="Get users",
                sql="SELECT * FROM users",
                results=results,
                max_rows_to_check=3,
            )
            
            # Check that user prompt only contains 3 rows
            call_kwargs = mock_client.chat.completions.create.call_args.kwargs
            user_message = call_kwargs["messages"][1]["content"]
            assert "(first 3 rows)" in user_message


class TestPromptBuilding:
    """Test prompt building methods."""

    def test_build_validation_system_prompt(self, openai_config):
        """Test system prompt building."""
        with patch("openai.AsyncOpenAI"):
            validator = ResultValidator(openai_config)
            
            prompt = validator._build_validation_system_prompt()
            
            assert "SQL query validator" in prompt
            assert "VALID" in prompt
            assert "INVALID" in prompt

    def test_build_validation_user_prompt(self, openai_config):
        """Test user prompt building."""
        with patch("openai.AsyncOpenAI"):
            validator = ResultValidator(openai_config)
            
            results = [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ]
            
            prompt = validator._build_validation_user_prompt(
                original_query="Get all users",
                sql="SELECT id, name FROM users",
                sample_results=results,
            )
            
            assert "Get all users" in prompt
            assert "SELECT id, name FROM users" in prompt
            assert "Alice" in prompt
            assert "Bob" in prompt
            assert "(first 2 rows)" in prompt

    def test_format_results_for_prompt_empty(self, openai_config):
        """Test formatting empty results."""
        with patch("openai.AsyncOpenAI"):
            validator = ResultValidator(openai_config)
            
            formatted = validator._format_results_for_prompt([])
            
            assert formatted == "No results"

    def test_format_results_for_prompt_with_data(self, openai_config):
        """Test formatting results with data."""
        with patch("openai.AsyncOpenAI"):
            validator = ResultValidator(openai_config)
            
            results = [
                {"id": 1, "name": "Alice", "active": True},
                {"id": 2, "name": "Bob", "active": False},
            ]
            
            formatted = validator._format_results_for_prompt(results)
            
            # Check table format
            assert "id | name | active" in formatted
            assert "---" in formatted
            assert "1 | Alice | True" in formatted
            assert "2 | Bob | False" in formatted

    def test_format_results_for_prompt_missing_values(self, openai_config):
        """Test formatting results with missing values."""
        with patch("openai.AsyncOpenAI"):
            validator = ResultValidator(openai_config)
            
            results = [
                {"id": 1, "name": "Alice"},
                {"id": 2},  # Missing 'name'
            ]
            
            formatted = validator._format_results_for_prompt(results)
            
            # Check missing value is handled
            assert "2 | " in formatted or "2 |" in formatted
