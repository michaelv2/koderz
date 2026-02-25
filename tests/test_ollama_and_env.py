"""Tests for Ollama integration and API key environment variables for single model use.

Tests cover:
1. OllamaClient initialization and configuration
2. OllamaClient request building (chat endpoint, options, system prompts)
3. OllamaClient retry/error handling
4. ModelFactory provider routing and API key validation
5. Model registry provider detection (auto-detect Ollama via colon)
6. Environment variable loading for single-model configurations
7. Single-model use: same model across all phases
8. Live integration tests against real Ollama server at 192.168.1.74
"""

import os
import json
import pytest
from unittest.mock import patch, Mock, MagicMock

# Import project modules
from koderz.models.local import OllamaClient
from koderz.models.factory import ModelFactory
from koderz.models.registry import (
    get_provider,
    get_tier,
    get_model_info,
    MODEL_REGISTRY,
)
from koderz.utils.retry import MaxRetriesExceeded

# ── Constants ─────────────────────────────────────────────────────────────

OLLAMA_HOST = "http://192.168.1.74:11434"


# ── OllamaClient Initialization ──────────────────────────────────────────


class TestOllamaClientInit:
    """Test OllamaClient initialization and configuration."""

    def test_default_config(self):
        client = OllamaClient()
        assert client.host == "http://localhost:11434"
        assert client.timeout == 300
        assert client.max_retries == 3
        assert client.num_ctx == 5120
        assert client.seed is None
        assert client.temperature == 0.1

    def test_custom_host(self):
        client = OllamaClient(host="http://192.168.1.100:11434")
        assert client.host == "http://192.168.1.100:11434"

    def test_custom_timeout(self):
        client = OllamaClient(timeout=600)
        assert client.timeout == 600

    def test_custom_num_ctx(self):
        client = OllamaClient(num_ctx=8192)
        assert client.num_ctx == 8192

    def test_custom_seed(self):
        client = OllamaClient(seed=42)
        assert client.seed == 42

    def test_custom_temperature(self):
        client = OllamaClient(temperature=0.7)
        assert client.temperature == 0.7

    def test_full_custom_config(self):
        client = OllamaClient(
            host="http://gpu-server:11434",
            timeout=120,
            max_retries=5,
            num_ctx=16384,
            seed=123,
            temperature=0.5,
        )
        assert client.host == "http://gpu-server:11434"
        assert client.timeout == 120
        assert client.max_retries == 5
        assert client.num_ctx == 16384
        assert client.seed == 123
        assert client.temperature == 0.5


# ── OllamaClient Generate (Request Building) ─────────────────────────────


class TestOllamaClientGenerate:
    """Test OllamaClient.generate() request building and response parsing."""

    @patch("koderz.models.local.requests.post")
    def test_generate_basic_request(self, mock_post):
        """Verify chat endpoint URL, payload structure, and response extraction."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"content": "def hello(): return 'world'"}
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = OllamaClient(host="http://localhost:11434", timeout=300)
        result = client.generate("Write a hello function", model="codellama:70b")

        assert result == "def hello(): return 'world'"
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:11434/api/chat"
        payload = call_args[1]["json"]
        assert payload["model"] == "codellama:70b"
        assert payload["stream"] is False
        assert len(payload["messages"]) == 1
        assert payload["messages"][0]["role"] == "user"
        assert payload["messages"][0]["content"] == "Write a hello function"

    @patch("koderz.models.local.requests.post")
    def test_generate_with_system_prompt(self, mock_post):
        """Verify system prompt is prepended as system message."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"content": "result"}
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = OllamaClient()
        client.generate(
            "Write code",
            model="codellama:70b",
            system="You are a Python expert.",
        )

        payload = mock_post.call_args[1]["json"]
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][0]["content"] == "You are a Python expert."
        assert payload["messages"][1]["role"] == "user"
        assert payload["messages"][1]["content"] == "Write code"

    @patch("koderz.models.local.requests.post")
    def test_generate_without_system_prompt(self, mock_post):
        """Without system prompt, messages should have only user message."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "ok"}}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = OllamaClient()
        client.generate("Hello", model="codellama:70b")

        payload = mock_post.call_args[1]["json"]
        assert len(payload["messages"]) == 1
        assert payload["messages"][0]["role"] == "user"

    @patch("koderz.models.local.requests.post")
    def test_generate_options_include_num_ctx(self, mock_post):
        """Verify num_ctx is passed in options."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "ok"}}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = OllamaClient(num_ctx=8192)
        client.generate("test", model="codellama:70b")

        options = mock_post.call_args[1]["json"]["options"]
        assert options["num_ctx"] == 8192
        assert options["temperature"] == 0.1
        assert options["top_p"] == 0.9
        assert options["num_predict"] == 4096

    @patch("koderz.models.local.requests.post")
    def test_generate_with_seed(self, mock_post):
        """Verify seed is passed when set."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "ok"}}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = OllamaClient(seed=42)
        client.generate("test", model="codellama:70b")

        options = mock_post.call_args[1]["json"]["options"]
        assert options["seed"] == 42

    @patch("koderz.models.local.requests.post")
    def test_generate_without_seed(self, mock_post):
        """Verify seed is NOT in options when not set."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "ok"}}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = OllamaClient(seed=None)
        client.generate("test", model="codellama:70b")

        options = mock_post.call_args[1]["json"]["options"]
        assert "seed" not in options

    @patch("koderz.models.local.requests.post")
    def test_generate_uses_timeout(self, mock_post):
        """Verify timeout is passed to requests.post."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "ok"}}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = OllamaClient(timeout=120)
        client.generate("test", model="codellama:70b")

        assert mock_post.call_args[1]["timeout"] == 120


# ── OllamaClient Generate Spec ───────────────────────────────────────────


class TestOllamaClientGenerateSpec:
    """Test OllamaClient.generate_spec() method."""

    @patch("koderz.models.local.requests.post")
    def test_generate_spec_returns_dict(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"content": "Spec: parse integers from list"}
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = OllamaClient()
        result = client.generate_spec("Write a function to parse integers", model="gpt-oss:20b")

        assert isinstance(result, dict)
        assert "spec" in result
        assert "cost" in result
        assert result["spec"] == "Spec: parse integers from list"
        assert result["cost"] == 0.0  # Local models are free


# ── OllamaClient List Models ─────────────────────────────────────────────


class TestOllamaClientListModels:
    """Test OllamaClient.list_models() method."""

    @patch("koderz.models.local.requests.get")
    def test_list_models_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "codellama:70b", "size": 38000000000},
                {"name": "gpt-oss:20b", "size": 12000000000},
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = OllamaClient()
        models = client.list_models()

        assert len(models) == 2
        assert models[0]["name"] == "codellama:70b"
        mock_get.assert_called_once_with(
            "http://localhost:11434/api/tags", timeout=30
        )

    @patch("koderz.models.local.requests.get")
    def test_list_models_empty(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = OllamaClient()
        models = client.list_models()
        assert models == []


# ── OllamaClient Load Model ──────────────────────────────────────────────


class TestOllamaClientLoadModel:
    """Test OllamaClient.load_model() method."""

    @patch("koderz.models.local.requests.post")
    def test_load_model_calls_pull(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = OllamaClient()
        client.load_model("codellama:70b")

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:11434/api/pull"
        assert call_args[1]["json"] == {"name": "codellama:70b", "stream": False}
        assert call_args[1]["timeout"] == 600  # 10 minute timeout for downloads


# ── OllamaClient Error Handling / Retry ───────────────────────────────────


class TestOllamaClientRetry:
    """Test OllamaClient retry behavior on errors."""

    @patch("koderz.models.local.requests.post")
    def test_non_retryable_http_error_raises_immediately(self, mock_post):
        """Non-503/429 HTTP errors should not be retried."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = __import__(
            "requests"
        ).exceptions.HTTPError(response=mock_response)
        mock_post.return_value = mock_response

        client = OllamaClient(max_retries=3)
        with pytest.raises(__import__("requests").exceptions.HTTPError):
            client.generate("test", model="codellama:70b")

        # Should be called only once (no retries for 404)
        assert mock_post.call_count == 1

    @patch("time.sleep")  # Speed up retries
    @patch("koderz.models.local.requests.post")
    def test_503_triggers_retry(self, mock_post, mock_sleep):
        """503 errors should trigger exponential backoff retry."""
        import requests as req

        mock_error_response = Mock()
        mock_error_response.status_code = 503
        http_error = req.exceptions.HTTPError(response=mock_error_response)
        mock_error_response.raise_for_status.side_effect = http_error

        mock_success_response = Mock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {"message": {"content": "ok"}}
        mock_success_response.raise_for_status = Mock()

        # First call fails with 503, second succeeds
        mock_post.side_effect = [mock_error_response, mock_success_response]

        # Need to fix: raise_for_status on first call raises, second doesn't
        mock_error_response.raise_for_status.side_effect = http_error
        mock_success_response.raise_for_status.side_effect = None

        client = OllamaClient(max_retries=3)
        result = client.generate("test", model="codellama:70b")

        assert result == "ok"
        assert mock_post.call_count == 2

    @patch("time.sleep")
    @patch("koderz.models.local.requests.post")
    def test_max_retries_exceeded_on_repeated_503(self, mock_post, mock_sleep):
        """Repeated 503 errors should eventually raise MaxRetriesExceeded."""
        import requests as req

        mock_response = Mock()
        mock_response.status_code = 503
        http_error = req.exceptions.HTTPError(response=mock_response)
        mock_response.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_response

        client = OllamaClient(max_retries=2)
        with pytest.raises(MaxRetriesExceeded):
            client.generate("test", model="codellama:70b")

        # 1 initial + 2 retries = 3 total
        assert mock_post.call_count == 3

    @patch("time.sleep")
    @patch("koderz.models.local.requests.post")
    def test_timeout_triggers_retry(self, mock_post, mock_sleep):
        """ReadTimeout should trigger retry."""
        import requests as req

        mock_success = Mock()
        mock_success.status_code = 200
        mock_success.json.return_value = {"message": {"content": "recovered"}}
        mock_success.raise_for_status = Mock()

        mock_post.side_effect = [
            req.exceptions.ReadTimeout("timeout"),
            mock_success,
        ]

        client = OllamaClient(max_retries=3)
        result = client.generate("test", model="codellama:70b")
        assert result == "recovered"
        assert mock_post.call_count == 2


# ── Model Registry ────────────────────────────────────────────────────────


class TestModelRegistry:
    """Test model registry provider detection and metadata."""

    def test_known_ollama_models(self):
        assert get_provider("codellama:70b") == "ollama"
        assert get_provider("llama3.3:70b") == "ollama"

    def test_auto_detect_ollama_by_colon(self):
        """Any model with colon is auto-detected as Ollama."""
        assert get_provider("qwen2.5-coder:32b") == "ollama"
        assert get_provider("gpt-oss:20b") == "ollama"
        assert get_provider("custom-model:7b") == "ollama"
        assert get_provider("nemotron-3-nano:30b") == "ollama"

    def test_known_anthropic_models(self):
        assert get_provider("claude-opus-4-5") == "anthropic"
        assert get_provider("claude-sonnet-4-5") == "anthropic"
        assert get_provider("claude-haiku-4-5") == "anthropic"
        assert get_provider("claude-opus-4") == "anthropic"
        assert get_provider("claude-sonnet-4") == "anthropic"

    def test_known_openai_models(self):
        assert get_provider("gpt-4o") == "openai"
        assert get_provider("gpt-4o-mini") == "openai"
        assert get_provider("gpt-4.1") == "openai"
        assert get_provider("gpt-4.1-mini") == "openai"
        assert get_provider("gpt-4.1-nano") == "openai"
        assert get_provider("gpt-5-mini") == "openai"
        assert get_provider("gpt-5-nano") == "openai"

    def test_unknown_model_without_colon(self):
        assert get_provider("unknown-model") == "unknown"

    def test_ollama_tier_is_local(self):
        assert get_tier("codellama:70b") == "local"
        assert get_tier("gpt-oss:20b") == "local"  # auto-detected

    def test_small_frontier_tier(self):
        assert get_tier("gpt-4o-mini") == "small_frontier"
        assert get_tier("claude-haiku-4-5") == "small_frontier"

    def test_frontier_tier(self):
        assert get_tier("claude-opus-4-5") == "frontier"
        assert get_tier("gpt-4o") == "frontier"

    def test_ollama_models_are_free(self):
        info = get_model_info("codellama:70b")
        assert info["cost_per_1m_input"] == 0.0
        assert info["cost_per_1m_output"] == 0.0

    def test_auto_detected_ollama_is_free(self):
        info = get_model_info("some-random:model")
        assert info["cost_per_1m_input"] == 0.0
        assert info["cost_per_1m_output"] == 0.0
        assert info["provider"] == "ollama"


# ── ModelFactory Provider Routing ─────────────────────────────────────────


class TestModelFactoryRouting:
    """Test ModelFactory routes to correct client based on model name."""

    def test_ollama_model_returns_ollama_client(self):
        factory = ModelFactory(ollama_host="http://localhost:11434")
        client = factory.get_client("codellama:70b")
        assert isinstance(client, OllamaClient)

    def test_auto_detected_ollama_model(self):
        factory = ModelFactory()
        client = factory.get_client("qwen2.5-coder:32b")
        assert isinstance(client, OllamaClient)

    def test_ollama_client_uses_factory_config(self):
        factory = ModelFactory(
            ollama_host="http://gpu-box:11434",
            timeout=600,
            max_retries=5,
            num_ctx=16384,
            seed=99,
            temperature=0.3,
        )
        client = factory.get_client("codellama:70b")
        assert isinstance(client, OllamaClient)
        assert client.host == "http://gpu-box:11434"
        assert client.timeout == 600
        assert client.max_retries == 5
        assert client.num_ctx == 16384
        assert client.seed == 99
        assert client.temperature == 0.3

    def test_ollama_client_is_cached(self):
        factory = ModelFactory()
        client1 = factory.get_client("codellama:70b")
        client2 = factory.get_client("gpt-oss:20b")
        # Same OllamaClient instance reused for all Ollama models
        assert client1 is client2

    def test_anthropic_without_key_raises(self):
        factory = ModelFactory(anthropic_api_key=None)
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY required"):
            factory.get_client("claude-sonnet-4-5")

    def test_openai_without_key_raises(self):
        factory = ModelFactory(openai_api_key=None)
        with pytest.raises(ValueError, match="OPENAI_API_KEY required"):
            factory.get_client("gpt-4o")

    def test_unknown_provider_raises(self):
        factory = ModelFactory()
        with pytest.raises(ValueError, match="Unknown provider"):
            factory.get_client("totally-unknown-model")


# ── API Key Environment Variables ─────────────────────────────────────────


class TestAPIKeyEnvironmentVariables:
    """Test that environment variables are properly read for API keys."""

    @patch.dict(os.environ, {
        "OLLAMA_HOST": OLLAMA_HOST,
    }, clear=False)
    def test_ollama_host_from_env(self):
        """OLLAMA_HOST env var should configure Ollama client to 192.168.1.74."""
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        factory = ModelFactory(ollama_host=host)
        client = factory.get_client("codellama:70b")
        assert client.host == OLLAMA_HOST

    @patch.dict(os.environ, {}, clear=False)
    def test_ollama_host_default(self):
        """Missing OLLAMA_HOST should default to localhost:11434."""
        os.environ.pop("OLLAMA_HOST", None)
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        assert host == "http://localhost:11434"

    @patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "sk-ant-test-key-123",
    }, clear=False)
    def test_anthropic_key_from_env(self):
        """ANTHROPIC_API_KEY env var should be passed to ModelFactory."""
        key = os.getenv("ANTHROPIC_API_KEY")
        assert key == "sk-ant-test-key-123"
        factory = ModelFactory(anthropic_api_key=key)
        assert factory.anthropic_api_key == "sk-ant-test-key-123"

    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "sk-proj-test-key-456",
    }, clear=False)
    def test_openai_key_from_env(self):
        """OPENAI_API_KEY env var should be passed to ModelFactory."""
        key = os.getenv("OPENAI_API_KEY")
        assert key == "sk-proj-test-key-456"
        factory = ModelFactory(openai_api_key=key)
        assert factory.openai_api_key == "sk-proj-test-key-456"

    @patch.dict(os.environ, {}, clear=False)
    def test_missing_api_keys_are_none(self):
        """Missing API keys should result in None."""
        os.environ.pop("ANTHROPIC_API_KEY", None)
        os.environ.pop("OPENAI_API_KEY", None)
        assert os.getenv("ANTHROPIC_API_KEY") is None
        assert os.getenv("OPENAI_API_KEY") is None

    @patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "",
    }, clear=False)
    def test_empty_api_key_is_empty_string(self):
        """Empty string API key is truthy from getenv, but different from None."""
        key = os.getenv("ANTHROPIC_API_KEY")
        assert key == ""
        # ModelFactory treats empty string as a key (it's truthy-ish check may pass)
        # The actual API client will fail on auth, but factory won't block creation
        factory = ModelFactory(anthropic_api_key=key)
        assert factory.anthropic_api_key == ""


# ── Single Model Use ──────────────────────────────────────────────────────


class TestSingleModelUse:
    """Test using a single Ollama model for all phases (spec, iterations, checkpoints).

    In single-model use, the user specifies the same Ollama model for:
    - --frontier-spec-model (Phase 1: spec generation)
    - --local-model (Phase 2: iterative execution)
    - --frontier-checkpoint-model (Phase 3: checkpoint review)
    """

    def test_single_ollama_model_all_phases(self):
        """Same Ollama model can be used for all three phases."""
        model = "gpt-oss:20b"
        factory = ModelFactory(ollama_host=OLLAMA_HOST)

        # All three phases route to the same OllamaClient
        spec_client = factory.get_client(model)
        iter_client = factory.get_client(model)
        checkpoint_client = factory.get_client(model)

        assert isinstance(spec_client, OllamaClient)
        assert isinstance(iter_client, OllamaClient)
        assert isinstance(checkpoint_client, OllamaClient)
        # All the same cached instance
        assert spec_client is iter_client
        assert iter_client is checkpoint_client
        # Confirm host is the real server
        assert spec_client.host == OLLAMA_HOST

    def test_single_ollama_model_no_api_keys_needed(self):
        """When using only Ollama models, no API keys are required."""
        factory = ModelFactory(
            ollama_host=OLLAMA_HOST,
            anthropic_api_key=None,
            openai_api_key=None,
        )
        # Should succeed without any API keys
        client = factory.get_client("gpt-oss:20b")
        assert isinstance(client, OllamaClient)
        assert client.host == OLLAMA_HOST

    def test_different_ollama_models_same_client(self):
        """Different Ollama models share the same OllamaClient instance."""
        factory = ModelFactory()
        client_a = factory.get_client("gpt-oss:20b")
        client_b = factory.get_client("codellama:70b")
        client_c = factory.get_client("qwen2.5-coder:32b")
        assert client_a is client_b
        assert client_b is client_c

    @patch("koderz.models.local.requests.post")
    def test_single_model_spec_generation(self, mock_post):
        """Verify spec generation works with Ollama model."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"content": "Spec: The function should sort a list."}
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        factory = ModelFactory()
        client = factory.get_client("gpt-oss:20b")
        result = client.generate_spec("Write a sort function", model="gpt-oss:20b")

        assert result["cost"] == 0.0
        assert "sort" in result["spec"].lower()

    @patch("koderz.models.local.requests.post")
    def test_single_model_iteration_generation(self, mock_post):
        """Verify code generation works with Ollama model."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"content": "def sort_list(lst):\n    return sorted(lst)"}
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        factory = ModelFactory()
        client = factory.get_client("gpt-oss:20b")
        result = client.generate(
            "Implement the sort function",
            model="gpt-oss:20b",
            system="You are a coding assistant.",
        )

        assert "sorted" in result
        # Verify system prompt was sent
        payload = mock_post.call_args[1]["json"]
        assert payload["messages"][0]["role"] == "system"

    @patch.dict(os.environ, {
        "OLLAMA_HOST": OLLAMA_HOST,
    }, clear=False)
    def test_single_model_env_config(self):
        """Single Ollama model use with env-configured host at 192.168.1.74."""
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        factory = ModelFactory(
            ollama_host=host,
            anthropic_api_key=None,
            openai_api_key=None,
        )
        client = factory.get_client("gpt-oss:20b")
        assert isinstance(client, OllamaClient)
        assert client.host == OLLAMA_HOST


# ── CLI Environment Variable Integration ──────────────────────────────────


class TestCLIEnvironmentIntegration:
    """Test that the CLI pattern for loading env vars works correctly."""

    @patch.dict(os.environ, {
        "OLLAMA_HOST": OLLAMA_HOST,
        "ANTHROPIC_API_KEY": "sk-ant-test",
        "OPENAI_API_KEY": "sk-proj-test",
    }, clear=False)
    def test_cli_pattern_all_keys(self):
        """Simulate CLI initialization with all env vars set (host=192.168.1.74)."""
        factory = ModelFactory(
            ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )
        assert factory.ollama_host == OLLAMA_HOST
        assert factory.anthropic_api_key == "sk-ant-test"
        assert factory.openai_api_key == "sk-proj-test"

    @patch.dict(os.environ, {}, clear=False)
    def test_cli_pattern_ollama_only(self):
        """Simulate CLI initialization with only Ollama (no API keys)."""
        os.environ.pop("ANTHROPIC_API_KEY", None)
        os.environ.pop("OPENAI_API_KEY", None)
        os.environ.pop("OLLAMA_HOST", None)

        factory = ModelFactory(
            ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )
        assert factory.ollama_host == "http://localhost:11434"
        assert factory.anthropic_api_key is None
        assert factory.openai_api_key is None

        # Ollama models work fine
        client = factory.get_client("gpt-oss:20b")
        assert isinstance(client, OllamaClient)

        # Frontier models fail gracefully
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY required"):
            factory.get_client("claude-sonnet-4-5")
        with pytest.raises(ValueError, match="OPENAI_API_KEY required"):
            factory.get_client("gpt-4o")

    @patch.dict(os.environ, {
        "OLLAMA_HOST": OLLAMA_HOST,
    }, clear=False)
    def test_cli_pattern_custom_ollama_host(self):
        """Simulate using the remote Ollama server at 192.168.1.74."""
        factory = ModelFactory(
            ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            anthropic_api_key=None,
            openai_api_key=None,
        )
        client = factory.get_client("codellama:70b")
        assert client.host == OLLAMA_HOST


# ── Retry Utility ─────────────────────────────────────────────────────────


class TestRetryUtility:
    """Test the retry_with_backoff utility used by OllamaClient."""

    def test_is_ollama_overloaded_503(self):
        from koderz.utils.retry import is_ollama_overloaded
        import requests as req

        mock_response = Mock()
        mock_response.status_code = 503
        error = req.exceptions.HTTPError(response=mock_response)
        assert is_ollama_overloaded(error) is True

    def test_is_ollama_overloaded_429(self):
        from koderz.utils.retry import is_ollama_overloaded
        import requests as req

        mock_response = Mock()
        mock_response.status_code = 429
        error = req.exceptions.HTTPError(response=mock_response)
        assert is_ollama_overloaded(error) is True

    def test_is_ollama_overloaded_timeout(self):
        from koderz.utils.retry import is_ollama_overloaded
        import requests as req

        error = req.exceptions.ReadTimeout("timeout")
        assert is_ollama_overloaded(error) is True

    def test_is_ollama_overloaded_other_error(self):
        from koderz.utils.retry import is_ollama_overloaded

        error = ValueError("not overloaded")
        assert is_ollama_overloaded(error) is False

    def test_is_ollama_overloaded_404(self):
        from koderz.utils.retry import is_ollama_overloaded
        import requests as req

        mock_response = Mock()
        mock_response.status_code = 404
        error = req.exceptions.HTTPError(response=mock_response)
        assert is_ollama_overloaded(error) is False


# ── Live Integration Tests (192.168.1.74) ─────────────────────────────────


class TestLiveOllamaServer:
    """Live integration tests against Ollama at 192.168.1.74:11434.

    These tests make real HTTP requests to the Ollama server.
    They verify end-to-end connectivity, model listing, and generation.
    """

    def test_live_server_connectivity(self):
        """Verify Ollama server at 192.168.1.74 is reachable."""
        import requests
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        print(f"\n  Server online, {len(data['models'])} models available")

    def test_live_list_models(self):
        """List models from real server via OllamaClient."""
        client = OllamaClient(host=OLLAMA_HOST)
        models = client.list_models()
        assert len(models) > 0
        model_names = [m["name"] for m in models]
        print(f"\n  Available models: {model_names}")
        # Verify at least one expected model is present
        assert any("gpt-oss" in name for name in model_names), \
            f"Expected gpt-oss model in {model_names}"

    def test_live_factory_creates_client_with_real_host(self):
        """ModelFactory creates OllamaClient pointing to 192.168.1.74."""
        factory = ModelFactory(
            ollama_host=OLLAMA_HOST,
            anthropic_api_key=None,
            openai_api_key=None,
        )
        client = factory.get_client("gpt-oss:20b")
        assert isinstance(client, OllamaClient)
        assert client.host == OLLAMA_HOST
        # Verify it can actually reach the server
        models = client.list_models()
        assert len(models) > 0

    @patch.dict(os.environ, {"OLLAMA_HOST": OLLAMA_HOST}, clear=False)
    def test_live_env_var_to_factory_to_server(self):
        """Full pipeline: env var -> ModelFactory -> OllamaClient -> real server."""
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        assert host == OLLAMA_HOST

        factory = ModelFactory(
            ollama_host=host,
            anthropic_api_key=None,
            openai_api_key=None,
        )
        client = factory.get_client("gpt-oss:20b")
        assert client.host == OLLAMA_HOST

        # Actually hit the server
        models = client.list_models()
        model_names = [m["name"] for m in models]
        assert "gpt-oss:20b" in model_names, \
            f"gpt-oss:20b not found in {model_names}"

    def test_live_generate_with_gpt_oss(self):
        """Live generation test: send a simple prompt to gpt-oss:20b."""
        client = OllamaClient(host=OLLAMA_HOST, timeout=120)
        result = client.generate(
            prompt="Return only the number 42. No explanation.",
            model="gpt-oss:20b",
        )
        assert isinstance(result, str)
        assert len(result) > 0
        assert "42" in result
        print(f"\n  gpt-oss:20b response: {result[:100]}")

    def test_live_generate_with_system_prompt(self):
        """Live generation with system prompt on real server."""
        client = OllamaClient(host=OLLAMA_HOST, timeout=120)
        result = client.generate(
            prompt="What is 2+2?",
            model="gpt-oss:20b",
            system="You are a math tutor. Answer with just the number.",
        )
        assert isinstance(result, str)
        assert "4" in result
        print(f"\n  System prompt response: {result[:100]}")

    def test_live_generate_spec(self):
        """Live spec generation with gpt-oss:20b on real server."""
        client = OllamaClient(host=OLLAMA_HOST, timeout=120)
        result = client.generate_spec(
            problem="Write a function has_close_elements that checks if any two numbers in a list are closer than a given threshold.",
            model="gpt-oss:20b",
        )
        assert isinstance(result, dict)
        assert "spec" in result
        assert "cost" in result
        assert result["cost"] == 0.0
        assert len(result["spec"]) > 50  # Should be a meaningful spec
        print(f"\n  Spec length: {len(result['spec'])} chars")
        print(f"  Spec preview: {result['spec'][:150]}...")

    def test_live_single_model_all_phases_end_to_end(self):
        """End-to-end: single gpt-oss:20b model for spec + iteration via factory."""
        factory = ModelFactory(
            ollama_host=OLLAMA_HOST,
            anthropic_api_key=None,
            openai_api_key=None,
        )

        model = "gpt-oss:20b"

        # Phase 1: Spec generation
        spec_client = factory.get_client(model)
        spec_result = spec_client.generate_spec(
            problem="Write a function that returns the sum of a list of integers.",
            model=model,
        )
        assert spec_result["cost"] == 0.0
        assert len(spec_result["spec"]) > 20

        # Phase 2: Code iteration
        iter_client = factory.get_client(model)
        assert iter_client is spec_client  # Same cached instance
        code_result = iter_client.generate(
            prompt=f"Based on this spec:\n{spec_result['spec']}\n\nWrite the Python function:",
            model=model,
            system="You are an expert Python programmer. Write only the function code.",
        )
        assert isinstance(code_result, str)
        assert len(code_result) > 10

        # Phase 3: Checkpoint (review-like generation)
        checkpoint_client = factory.get_client(model)
        assert checkpoint_client is spec_client  # Same cached instance
        review = checkpoint_client.generate(
            prompt=f"Review this code and suggest one improvement:\n```python\n{code_result}\n```",
            model=model,
        )
        assert isinstance(review, str)
        assert len(review) > 10

        print(f"\n  Spec: {spec_result['spec'][:80]}...")
        print(f"  Code: {code_result[:80]}...")
        print(f"  Review: {review[:80]}...")
