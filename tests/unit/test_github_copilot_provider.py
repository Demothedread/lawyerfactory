"""
Unit tests for GitHub Copilot / GitHub Models LLM provider integration.
Tests both the lf_core/llm layer (GitHubCopilotProvider) and the
llm_integration layer (GitHubCopilotProvider in provider_manager).
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import asyncio
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# aiohttp may not be installed in the test environment; stub it so that
# provider_manager (which has a top-level `import aiohttp`) can be imported.
if "aiohttp" not in sys.modules:
    sys.modules["aiohttp"] = MagicMock()

# anthropic may not be installed either
if "anthropic" not in sys.modules:
    _anthropic_stub = MagicMock()
    _anthropic_stub.Anthropic = MagicMock()
    sys.modules["anthropic"] = _anthropic_stub

# openai may not be installed in the bare test environment
if "openai" not in sys.modules:
    _openai_stub = MagicMock()
    _openai_stub.AsyncOpenAI = MagicMock()
    _openai_stub.OpenAI = MagicMock()
    sys.modules["openai"] = _openai_stub


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# Tests: models_shared.py – LLMProvider enum & GitHubCopilotService
# ---------------------------------------------------------------------------

class TestModelsSharedGitHubCopilot:
    """Tests for GitHub Copilot additions in lf_core/models_shared.py"""

    def test_llm_provider_enum_has_github_copilot(self):
        from lawyerfactory.lf_core.models_shared import LLMProvider
        assert LLMProvider.GITHUB_COPILOT.value == "github_copilot"

    def test_llm_config_has_github_copilot_settings_field(self):
        from lawyerfactory.lf_core.models_shared import LLMConfig
        cfg = LLMConfig()
        assert hasattr(cfg, "github_copilot_settings")
        assert isinstance(cfg.github_copilot_settings, dict)

    def test_llm_config_to_dict_includes_github_copilot_settings(self):
        from lawyerfactory.lf_core.models_shared import LLMConfig, LLMProvider
        cfg = LLMConfig(
            provider=LLMProvider.GITHUB_COPILOT,
            github_copilot_settings={"base_url": "https://models.inference.ai.azure.com"},
        )
        d = cfg.to_dict()
        assert d["provider"] == "github_copilot"
        assert "github_copilot_settings" in d
        assert d["github_copilot_settings"]["base_url"] == "https://models.inference.ai.azure.com"

    def test_llm_config_from_dict_round_trips(self):
        from lawyerfactory.lf_core.models_shared import LLMConfig, LLMProvider
        original = LLMConfig(
            provider=LLMProvider.GITHUB_COPILOT,
            model_name="gpt-4o",
            github_copilot_settings={"custom": True},
        )
        restored = LLMConfig.from_dict(original.to_dict())
        assert restored.provider == LLMProvider.GITHUB_COPILOT
        assert restored.model_name == "gpt-4o"
        assert restored.github_copilot_settings == {"custom": True}

    def test_llm_service_factory_creates_github_copilot_service(self):
        from lawyerfactory.lf_core.models_shared import (
            GitHubCopilotService,
            LLMConfig,
            LLMProvider,
            LLMServiceFactory,
        )
        cfg = LLMConfig(provider=LLMProvider.GITHUB_COPILOT)
        svc = LLMServiceFactory.create_service(cfg)
        assert isinstance(svc, GitHubCopilotService)

    def test_github_copilot_service_is_unavailable_without_token(self):
        from lawyerfactory.lf_core.models_shared import GitHubCopilotService, LLMConfig, LLMProvider

        cfg = LLMConfig(provider=LLMProvider.GITHUB_COPILOT, api_key=None)
        with patch.dict(os.environ, {}, clear=True):
            # Remove any token env vars that might be set in CI
            env_clean = {
                k: v for k, v in os.environ.items()
                if k not in ("GITHUB_TOKEN", "GH_TOKEN")
            }
            with patch.dict(os.environ, env_clean, clear=True):
                svc = GitHubCopilotService(cfg)
                available = run_async(svc.is_available())
                assert available is False

    def test_github_copilot_service_initializes_with_token(self):
        from lawyerfactory.lf_core.models_shared import GitHubCopilotService, LLMConfig, LLMProvider

        mock_openai = MagicMock()
        mock_client = MagicMock()
        mock_openai.AsyncOpenAI.return_value = mock_client

        cfg = LLMConfig(
            provider=LLMProvider.GITHUB_COPILOT,
            api_key="ghp_test_token",
            model_name="gpt-4o-mini",
        )
        with patch("lawyerfactory.lf_core.models_shared.openai", mock_openai, create=True):
            # Patch the openai import inside the module
            with patch.dict("sys.modules", {"openai": mock_openai}):
                svc = GitHubCopilotService(cfg)
                # The client initialization may use the real openai import path,
                # so just verify the service was constructed without error
                assert svc is not None

    def test_github_copilot_service_get_capabilities(self):
        from lawyerfactory.lf_core.models_shared import (
            GitHubCopilotService,
            LLMConfig,
            LLMProvider,
            ModelCapability,
        )
        cfg = LLMConfig(provider=LLMProvider.GITHUB_COPILOT)
        svc = GitHubCopilotService(cfg)
        caps = run_async(svc.get_capabilities())
        assert ModelCapability.TEXT_GENERATION in caps
        assert ModelCapability.EMBEDDINGS in caps

    def test_validate_config_github_copilot_missing_token(self):
        """validate_config should report error when no GitHub token is present."""
        from lawyerfactory.lf_core.models_shared import (
            LLMConfig,
            LLMConfigurationManager,
            LLMProvider,
        )

        env_clean = {
            k: v for k, v in os.environ.items()
            if k not in ("GITHUB_TOKEN", "GH_TOKEN")
        }
        with patch.dict(os.environ, env_clean, clear=True):
            mgr = LLMConfigurationManager.__new__(LLMConfigurationManager)
            mgr.current_config = LLMConfig(
                provider=LLMProvider.GITHUB_COPILOT, api_key=None
            )
            mgr.service = None
            result = run_async(mgr.validate_config())
        # Should report at least one error about the missing token
        assert len(result["errors"]) > 0
        assert any("token" in e.lower() or "github" in e.lower() for e in result["errors"])


# ---------------------------------------------------------------------------
# Tests: lf_core/llm/providers.py – GitHubCopilotProvider
# ---------------------------------------------------------------------------

class TestLfCoreLLMGitHubCopilotProvider:
    """Tests for GitHubCopilotProvider in lf_core/llm/providers.py"""

    def _make_provider(self, token=None):
        from lawyerfactory.lf_core.llm.providers import GitHubCopilotProvider

        mock_config_manager = MagicMock()
        mock_config_manager.get_provider_config.return_value = {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 1000,
            "enabled": True,
            "token": token or "",
        }
        with patch.dict(os.environ, {"GITHUB_TOKEN": token or ""}, clear=False):
            provider = GitHubCopilotProvider(mock_config_manager)
        return provider

    def test_provider_name(self):
        provider = self._make_provider()
        assert provider.provider_name == "github_copilot"

    def test_test_connection_no_token(self):
        from lawyerfactory.lf_core.llm.providers import GitHubCopilotProvider

        mock_config_manager = MagicMock()
        mock_config_manager.get_provider_config.return_value = {
            "model": "gpt-4o-mini",
            "enabled": True,
            "token": "",
            "api_key": "",
        }
        env_clean = {
            k: v for k, v in os.environ.items()
            if k not in ("GITHUB_TOKEN", "GH_TOKEN")
        }
        with patch.dict(os.environ, env_clean, clear=True):
            provider = GitHubCopilotProvider(mock_config_manager)
            result = provider.test_connection()
        assert result["success"] is False
        assert "token" in result["error"].lower() or "github" in result["error"].lower()

    def test_test_connection_with_token_no_client(self):
        """When token present but client init fails, test_connection reports failure."""
        from lawyerfactory.lf_core.llm.providers import GitHubCopilotProvider

        mock_config_manager = MagicMock()
        mock_config_manager.get_provider_config.return_value = {
            "model": "gpt-4o-mini",
            "enabled": True,
            "token": "ghp_test_token",
        }
        # Simulate failed openai import
        with patch.dict("sys.modules", {"openai": None}):
            provider = GitHubCopilotProvider.__new__(GitHubCopilotProvider)
            provider.config_manager = mock_config_manager
            provider.provider_name = "github_copilot"
            provider._client = None
        result = provider.test_connection()
        assert result["success"] is False

    def test_generate_text_no_client(self):
        from lawyerfactory.lf_core.llm.providers import GitHubCopilotProvider

        mock_config_manager = MagicMock()
        mock_config_manager.get_provider_config.return_value = {"model": "gpt-4o-mini"}

        provider = GitHubCopilotProvider.__new__(GitHubCopilotProvider)
        provider.config_manager = mock_config_manager
        provider.provider_name = "github_copilot"
        provider._client = None

        result = run_async(provider.generate_text("Hello"))
        assert result["success"] is False
        assert "not initialized" in result["error"].lower()

    def test_generate_text_success(self):
        from lawyerfactory.lf_core.llm.providers import GitHubCopilotProvider

        mock_config_manager = MagicMock()
        mock_config_manager.get_provider_config.return_value = {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 100,
        }

        # Build a mock response matching the openai SDK shape
        mock_message = MagicMock()
        mock_message.content = "Test response from GitHub Copilot"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 5
        mock_usage.completion_tokens = 8
        mock_usage.total_tokens = 13
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        provider = GitHubCopilotProvider.__new__(GitHubCopilotProvider)
        provider.config_manager = mock_config_manager
        provider.provider_name = "github_copilot"
        provider._client = mock_client

        result = run_async(provider.generate_text("Hello"))
        assert result["success"] is True
        assert result["text"] == "Test response from GitHub Copilot"
        assert result["usage"]["total_tokens"] == 13

    def test_health_check_success(self):
        from lawyerfactory.lf_core.llm.providers import GitHubCopilotProvider

        mock_config_manager = MagicMock()
        mock_config_manager.get_provider_config.return_value = {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 100,
        }

        mock_message = MagicMock()
        mock_message.content = "Hi"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = None

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        provider = GitHubCopilotProvider.__new__(GitHubCopilotProvider)
        provider.config_manager = mock_config_manager
        provider.provider_name = "github_copilot"
        provider._client = mock_client

        result = run_async(provider.health_check())
        assert result["healthy"] is True


# ---------------------------------------------------------------------------
# Tests: lf_core/llm/service.py – LLMService registers github_copilot
# ---------------------------------------------------------------------------

class TestLLMServiceRegistersGitHubCopilot:
    """Tests that LLMService registers the github_copilot provider."""

    def test_service_includes_github_copilot_in_available_providers(self):
        from lawyerfactory.lf_core.llm.service import LLMService

        service = LLMService()
        providers = service.get_available_providers()
        assert "github_copilot" in providers

    def test_service_get_provider_returns_github_copilot_instance(self):
        from lawyerfactory.lf_core.llm.providers import GitHubCopilotProvider
        from lawyerfactory.lf_core.llm.service import LLMService

        service = LLMService()
        provider = service.get_provider("github_copilot")
        assert provider is not None
        assert isinstance(provider, GitHubCopilotProvider)


# ---------------------------------------------------------------------------
# Tests: lf_core/llm/config.py – LLMConfigManager knows github_copilot
# ---------------------------------------------------------------------------

class TestLLMConfigManagerGitHubCopilot:
    """Tests that LLMConfigManager handles github_copilot provider."""

    def test_default_config_has_github_copilot_provider(self):
        from lawyerfactory.lf_core.llm.config import LLMConfigManager

        mgr = LLMConfigManager()
        cfg = mgr._get_default_config()
        assert "github_copilot" in cfg["providers"]
        gcp = cfg["providers"]["github_copilot"]
        assert "model" in gcp
        assert gcp["model"] == "gpt-4o-mini"
        assert "base_url" in gcp

    def test_validate_github_copilot_disabled_reports_issue(self):
        from lawyerfactory.lf_core.llm.config import LLMConfigManager

        mgr = LLMConfigManager()
        # Patch config to return github_copilot as disabled with no token
        mgr._config_cache = {
            "providers": {
                "github_copilot": {
                    "token": "",
                    "api_key": "",
                    "model": "gpt-4o-mini",
                    "enabled": False,
                }
            }
        }
        env_clean = {
            k: v for k, v in os.environ.items()
            if k not in ("GITHUB_TOKEN", "GH_TOKEN")
        }
        with patch.dict(os.environ, env_clean, clear=True):
            result = mgr.validate_provider_config("github_copilot")
        assert result["valid"] is False
        assert len(result["issues"]) > 0

    def test_validate_github_copilot_with_token_enabled(self):
        from lawyerfactory.lf_core.llm.config import LLMConfigManager

        mgr = LLMConfigManager()
        # Mock _load_config to return config with github_copilot enabled + token
        mgr._load_config = lambda: {
            "providers": {
                "github_copilot": {
                    "token": "ghp_test_token",
                    "model": "gpt-4o-mini",
                    "base_url": "https://models.inference.ai.azure.com",
                    "enabled": True,
                }
            }
        }
        result = mgr.validate_provider_config("github_copilot")
        assert result["valid"] is True
        assert result["issues"] == []


# ---------------------------------------------------------------------------
# Tests: llm_integration/provider_manager.py – GitHubCopilotProvider
# ---------------------------------------------------------------------------

class TestProviderManagerGitHubCopilot:
    """Tests for GitHubCopilotProvider in llm_integration/provider_manager.py"""

    def test_llm_provider_enum_includes_github_copilot(self):
        from lawyerfactory.llm_integration.provider_manager import LLMProvider
        assert LLMProvider.GITHUB_COPILOT.value == "github_copilot"

    def test_github_copilot_models_list_is_non_empty(self):
        from lawyerfactory.llm_integration.provider_manager import GITHUB_COPILOT_MODELS
        assert len(GITHUB_COPILOT_MODELS) > 0
        assert "gpt-4o-mini" in GITHUB_COPILOT_MODELS

    def test_llm_manager_default_model_for_github_copilot(self):
        from lawyerfactory.llm_integration.provider_manager import LLMManager, LLMProvider
        mgr = LLMManager.__new__(LLMManager)
        model = mgr._get_default_model(LLMProvider.GITHUB_COPILOT)
        assert model == "gpt-4o-mini"

    def test_llm_manager_available_models_for_github_copilot(self):
        from lawyerfactory.llm_integration.provider_manager import (
            GITHUB_COPILOT_MODELS,
            LLMManager,
            LLMProvider,
        )
        mgr = LLMManager.__new__(LLMManager)
        models = mgr.get_available_models(LLMProvider.GITHUB_COPILOT)
        assert models == GITHUB_COPILOT_MODELS

    def test_llm_manager_provider_classes_has_github_copilot(self):
        from lawyerfactory.llm_integration.provider_manager import (
            GitHubCopilotProvider,
            LLMManager,
            LLMProvider,
        )
        assert LLMProvider.GITHUB_COPILOT in LLMManager.PROVIDER_CLASSES
        assert LLMManager.PROVIDER_CLASSES[LLMProvider.GITHUB_COPILOT] is GitHubCopilotProvider

    def test_github_copilot_provider_raises_without_token(self):
        from lawyerfactory.llm_integration.provider_manager import (
            GitHubCopilotProvider,
            LLMConfig,
            LLMProvider,
        )
        cfg = LLMConfig(
            provider=LLMProvider.GITHUB_COPILOT,
            model="gpt-4o-mini",
            api_key=None,
        )
        env_clean = {
            k: v for k, v in os.environ.items()
            if k not in ("GITHUB_TOKEN", "GH_TOKEN")
        }
        with patch.dict(os.environ, env_clean, clear=True):
            with pytest.raises(ValueError, match="GitHub token"):
                GitHubCopilotProvider(cfg)

    def test_github_copilot_provider_initializes_with_token(self):
        from lawyerfactory.llm_integration.provider_manager import (
            GitHubCopilotProvider,
            LLMConfig,
            LLMProvider,
        )

        mock_openai_module = MagicMock()
        mock_async_client = MagicMock()
        mock_openai_module.AsyncOpenAI.return_value = mock_async_client

        cfg = LLMConfig(
            provider=LLMProvider.GITHUB_COPILOT,
            model="gpt-4o-mini",
            api_key="ghp_test_token_abc123",
        )

        with patch.dict("sys.modules", {"openai": mock_openai_module}):
            with patch(
                "lawyerfactory.llm_integration.provider_manager.openai",
                mock_openai_module,
            ):
                provider = GitHubCopilotProvider(cfg)
                assert provider.client is not None

    def test_github_copilot_provider_test_connection_success(self):
        from lawyerfactory.llm_integration.provider_manager import (
            GitHubCopilotProvider,
            LLMConfig,
            LLMProvider,
        )

        mock_message = MagicMock()
        mock_message.content = "Hi"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        cfg = LLMConfig(
            provider=LLMProvider.GITHUB_COPILOT,
            model="gpt-4o-mini",
            api_key="ghp_test",
        )
        provider = GitHubCopilotProvider.__new__(GitHubCopilotProvider)
        provider.config = cfg
        provider.client = mock_client

        result = run_async(provider.test_connection())
        assert result is True

    def test_github_copilot_provider_generate_response(self):
        from lawyerfactory.llm_integration.provider_manager import (
            GitHubCopilotProvider,
            LLMConfig,
            LLMProvider,
        )

        mock_usage = MagicMock()
        mock_usage.model_dump.return_value = {"prompt_tokens": 5, "completion_tokens": 10}
        mock_message = MagicMock()
        mock_message.content = "Legal analysis complete."
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        mock_response.id = "test-id-001"

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        cfg = LLMConfig(
            provider=LLMProvider.GITHUB_COPILOT,
            model="gpt-4o-mini",
            api_key="ghp_test",
        )
        provider = GitHubCopilotProvider.__new__(GitHubCopilotProvider)
        provider.config = cfg
        provider.client = mock_client

        messages = [{"role": "user", "content": "Analyze this case."}]
        response = run_async(provider.generate_response(messages))

        assert response.content == "Legal analysis complete."
        assert response.provider == LLMProvider.GITHUB_COPILOT
        assert response.model == "gpt-4o-mini"
        assert response.cost_estimate == 0.0  # Covered by subscription

    def test_get_llm_config_github_copilot(self):
        from lawyerfactory.llm_integration.provider_manager import (
            LLMProvider,
            get_llm_config,
        )
        cfg = get_llm_config("github_copilot", model="gpt-4o")
        assert cfg.provider == LLMProvider.GITHUB_COPILOT
        assert cfg.model == "gpt-4o"
