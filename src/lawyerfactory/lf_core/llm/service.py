"""
LLM Service for LawyerFactory
Main service layer that integrates with different LLM providers.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from .config import LLMConfigManager

logger = logging.getLogger(__name__)


class LLMService:
    """
    Main LLM service that provides a unified interface to different providers
    """

    def __init__(self, config_manager: Optional[LLMConfigManager] = None):
        self.config_manager = config_manager or LLMConfigManager()
        self._providers = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize provider instances"""
        try:
            from .providers import OpenAIProvider, OllamaProvider, GeminiProvider

            self._providers = {
                "openai": OpenAIProvider(self.config_manager),
                "ollama": OllamaProvider(self.config_manager),
                "gemini": GeminiProvider(self.config_manager),
            }
        except ImportError as e:
            logger.error(f"Failed to import providers: {e}")

    def get_current_provider(self) -> Optional[Any]:
        """Get the currently active provider instance"""
        current_provider_name = self.config_manager.get_current_provider()
        return self._providers.get(current_provider_name)

    def get_provider(self, provider_name: str) -> Optional[Any]:
        """Get a specific provider instance"""
        return self._providers.get(provider_name)

    async def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate text using the current provider"""
        provider = self.get_current_provider()
        if not provider:
            return {"success": False, "error": "No active LLM provider configured"}

        try:
            return await provider.generate_text(prompt, **kwargs)
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return {"success": False, "error": str(e)}

    async def classify_evidence(
        self, content: str, filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """Classify evidence as primary/secondary with detailed categorization"""
        provider = self.get_current_provider()
        if not provider:
            return {"success": False, "error": "No active LLM provider configured"}

        try:
            return await provider.classify_evidence(content, filename)
        except Exception as e:
            logger.error(f"Evidence classification failed: {e}")
            return {"success": False, "error": str(e)}

    async def extract_metadata(
        self, content: str, doc_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract metadata from document content"""
        provider = self.get_current_provider()
        if not provider:
            return {"success": False, "error": "No active LLM provider configured"}

        try:
            return await provider.extract_metadata(content, doc_type)
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            return {"success": False, "error": str(e)}

    async def summarize_text(
        self, content: str, max_length: int = 200
    ) -> Dict[str, Any]:
        """Summarize text content"""
        provider = self.get_current_provider()
        if not provider:
            return {"success": False, "error": "No active LLM provider configured"}

        try:
            return await provider.summarize_text(content, max_length)
        except Exception as e:
            logger.error(f"Text summarization failed: {e}")
            return {"success": False, "error": str(e)}

    def test_connection(self, provider_name: Optional[str] = None) -> Dict[str, Any]:
        """Test connection to a provider"""
        if provider_name:
            provider = self.get_provider(provider_name)
        else:
            provider = self.get_current_provider()

        if not provider:
            return {
                "success": False,
                "error": f"Provider {provider_name or 'current'} not available",
            }

        try:
            return provider.test_connection()
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {"success": False, "error": str(e)}

    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        return list(self._providers.keys())

    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        status = {}
        for name, provider in self._providers.items():
            try:
                config = self.config_manager.get_provider_config(name)
                validation = self.config_manager.validate_provider_config(name)
                status[name] = {
                    "enabled": config.get("enabled", False),
                    "valid": validation["valid"],
                    "issues": validation["issues"],
                }
            except Exception as e:
                status[name] = {"enabled": False, "valid": False, "issues": [str(e)]}

        current_provider = self.config_manager.get_current_provider()
        status["current_provider"] = current_provider

        return status

    async def batch_process(
        self, items: List[Dict[str, Any]], operation: str = "generate_text"
    ) -> List[Dict[str, Any]]:
        """Process multiple items in batch"""
        provider = self.get_current_provider()
        if not provider:
            return [
                {"success": False, "error": "No active LLM provider configured"}
                for _ in items
            ]

        try:
            return await provider.batch_process(items, operation)
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            return [{"success": False, "error": str(e)} for _ in items]

    def switch_provider(self, provider_name: str) -> bool:
        """Switch to a different provider"""
        if provider_name not in self._providers:
            logger.error(f"Provider {provider_name} not available")
            return False

        # Validate the provider configuration
        validation = self.config_manager.validate_provider_config(provider_name)
        if not validation["valid"]:
            logger.error(
                f"Provider {provider_name} configuration invalid: {validation['issues']}"
            )
            return False

        # Set as current provider
        success = self.config_manager.set_current_provider(provider_name)
        if success:
            logger.info(f"Switched to provider: {provider_name}")
        else:
            logger.error(f"Failed to switch to provider: {provider_name}")

        return success

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all providers"""
        results = {}
        for name, provider in self._providers.items():
            try:
                results[name] = await provider.health_check()
            except Exception as e:
                results[name] = {"healthy": False, "error": str(e)}

        current_provider = self.config_manager.get_current_provider()
        overall_healthy = results.get(current_provider, {}).get("healthy", False)

        return {
            "overall_healthy": overall_healthy,
            "current_provider": current_provider,
            "providers": results,
        }
