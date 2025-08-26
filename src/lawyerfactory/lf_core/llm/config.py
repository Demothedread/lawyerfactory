"""
LLM Configuration Manager for LawyerFactory
Integrates with the existing models_shared.py system for centralized configuration.
"""

import json
import logging
import os
import inspect
from pathlib import Path
from typing import Any, Dict, Optional

from ..models_shared import get_llm_config, update_llm_config

logger = logging.getLogger(__name__)


class LLMConfigManager:
    """
    Centralized LLM configuration manager that integrates with models_shared.py
    """

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "llm_config.json"
        self._config_cache = None
        self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from models_shared.py system"""
        try:
            # Try to get config from the centralized system
            raw = get_llm_config()
            # Normalize to plain dict
            if isinstance(raw, dict):
                config = raw
            else:
                # try common conversions
                if hasattr(raw, "to_dict"):
                    config = raw.to_dict()
                elif hasattr(raw, "__dict__"):
                    config = vars(raw)
                else:
                    # final attempt: serialize -> deserialize
                    try:
                        config = json.loads(json.dumps(raw))
                    except Exception:
                        config = {}
            self._config_cache = config
            return config
        except Exception as e:
            logger.warning(f"Failed to load config from models_shared: {e}")
            # Fallback to default configuration
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default LLM configuration"""
        return {
            "current_provider": "openai",
            "providers": {
                "openai": {
                    "api_key": os.getenv("OPENAI_API_KEY", ""),
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 4000,
                    "enabled": True,
                },
                "ollama": {
                    "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                    "model": "llama2",
                    "temperature": 0.7,
                    "max_tokens": 4000,
                    "enabled": False,
                },
                "gemini": {
                    "api_key": os.getenv("GEMINI_API_KEY", ""),
                    "model": "gemini-pro",
                    "temperature": 0.7,
                    "max_tokens": 4000,
                    "enabled": False,
                },
            },
        }

    def get_current_provider(self) -> str:
        """Get the currently active LLM provider"""
        config = self._load_config()
        return config.get("current_provider", "openai")

    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get configuration for a specific provider"""
        config = self._load_config()
        providers = config.get("providers", {})
        return providers.get(provider, {})

    def get_current_provider_config(self) -> Dict[str, Any]:
        """Get configuration for the currently active provider"""
        current_provider = self.get_current_provider()
        return self.get_provider_config(current_provider)

    def _call_update(self, *args, **kwargs) -> Any:
        """
        Flexibly call update_llm_config depending on its signature.
        Supports functions that expect (provider, config) or no args or single arg.
        """
        try:
            sig = inspect.signature(update_llm_config)
            params = sig.parameters
            # if takes two params, call with provider, config as passed
            if len(params) == 2:
                return update_llm_config(*args)
            # if zero-arg function, call without arguments (it may do global reload)
            if len(params) == 0:
                return update_llm_config()
            # if single-arg, call with the first arg if present
            if len(params) == 1:
                return update_llm_config(args[0] if args else None)
            # fallback: attempt direct call
            return update_llm_config(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Failed to call update_llm_config dynamically: {e}")
            # as a last resort, return False to indicate no update
            return False

    def update_provider_config(self, provider: str, config: Dict[str, Any]) -> bool:
        """Update configuration for a specific provider"""
        try:
            # Use the centralized update function flexibly
            success = self._call_update(provider, config)
            # If the centralized function returns None, interpret as True if no exception
            if success is None:
                success = True
            if success:
                self._config_cache = None  # Invalidate cache
            return bool(success)
        except Exception as e:
            logger.error(f"Failed to update provider config: {e}")
            return False

    def set_current_provider(self, provider: str) -> bool:
        """Set the currently active provider"""
        try:
            config = self._load_config()
            config["current_provider"] = provider
            # Try to call update function flexibly
            result = self._call_update("current_provider", provider)
            if result is None:
                return True
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to set current provider: {e}")
            return False

    def validate_provider_config(self, provider: str) -> Dict[str, Any]:
        """Validate configuration for a provider"""
        config = self.get_provider_config(provider)
        issues = []

        if not config.get("enabled", False):
            issues.append("Provider is disabled")

        if provider == "openai":
            if not config.get("api_key"):
                issues.append("API key is required")
        elif provider == "gemini":
            if not config.get("api_key"):
                issues.append("API key is required")
        elif provider == "ollama":
            if not config.get("base_url"):
                issues.append("Base URL is required")

        return {"valid": len(issues) == 0, "issues": issues}

    def get_available_providers(self) -> list:
        """Get list of available providers"""
        config = self._load_config()
        providers = config.get("providers", {})
        return [name for name, cfg in providers.items() if cfg.get("enabled", False)]

    def test_provider_connection(self, provider: str) -> Dict[str, Any]:
        """Test connection to a provider"""
        validation = self.validate_provider_config(provider)
        if not validation["valid"]:
            return {"success": False, "error": "; ".join(validation["issues"])}

        try:
            # Import here to avoid circular imports
            from .service import LLMService

            service = LLMService()
            return service.test_connection(provider)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def save_config_to_file(self, file_path: str) -> bool:
        """Save current configuration to a file"""
        try:
            config = self._load_config()
            with open(file_path, "w") as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save config to file: {e}")
            return False

    def load_config_from_file(self, file_path: str) -> bool:
        """Load configuration from a file"""
        try:
            with open(file_path, "r") as f:
                config = json.load(f)

            # Update the centralized config using flexible caller
            for provider, provider_config in config.get("providers", {}).items():
                try:
                    self._call_update(provider, provider_config)
                except Exception:
                    logger.warning(
                        f"Could not update provider {provider} via centralized API"
                    )

            if "current_provider" in config:
                try:
                    self._call_update("current_provider", config["current_provider"])
                except Exception:
                    logger.warning(
                        "Could not update current_provider via centralized API"
                    )

            self._config_cache = None  # Invalidate cache
            return True
        except Exception as e:
            logger.error(f"Failed to load config from file: {e}")
            return False
