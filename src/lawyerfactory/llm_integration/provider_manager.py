"""
LLM Provider Integration Module - Backend standardization for LawyerFactory
Provides unified LLM provider management across all agents and phases
"""

from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass
from enum import Enum
import logging
import os
from typing import Any, Dict, List, Optional, Union

import aiohttp
from anthropic import Anthropic
import openai

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    AZURE = "azure"
    LOCAL = "local"


@dataclass
class LLMConfig:
    """Configuration for LLM provider"""

    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4000
    custom_endpoint: Optional[str] = None
    timeout: int = 30
    retry_attempts: int = 3


@dataclass
class LLMResponse:
    """Response from LLM provider"""

    content: str
    provider: LLMProvider
    model: str
    usage: Optional[Dict[str, Any]] = None
    cost_estimate: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class LLMProviderBase(ABC):
    """Abstract base class for LLM providers"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = None
        self._initialize_client()

    @abstractmethod
    def _initialize_client(self):
        """Initialize the provider-specific client"""
        pass

    @abstractmethod
    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Generate response from the LLM"""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connection to the LLM provider"""
        pass


class OpenAIProvider(LLMProviderBase):
    """OpenAI LLM provider implementation"""

    MODELS = {
        "gpt-4o": {"input_cost": 0.005, "output_cost": 0.015},
        "gpt-4-turbo": {"input_cost": 0.01, "output_cost": 0.03},
        "gpt-3.5-turbo": {"input_cost": 0.0015, "output_cost": 0.002},
    }

    def _initialize_client(self):
        """Initialize OpenAI client"""
        if not self.config.api_key:
            self.config.api_key = os.getenv("OPENAI_API_KEY")

        if not self.config.api_key:
            raise ValueError("OpenAI API key is required")

        self.client = openai.AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.custom_endpoint,
            timeout=self.config.timeout,
        )

    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Generate response using OpenAI API"""
        try:
            # Prepare request parameters
            request_params = {
                "model": self.config.model,
                "messages": messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                **kwargs,
            }

            # Make API call with retry logic
            for attempt in range(self.config.retry_attempts):
                try:
                    response = await self.client.chat.completions.create(**request_params)

                    # Calculate cost estimate
                    usage = response.usage
                    cost_estimate = 0.0
                    if usage and self.config.model in self.MODELS:
                        model_pricing = self.MODELS[self.config.model]
                        cost_estimate = (
                            usage.prompt_tokens * model_pricing["input_cost"] / 1000
                            + usage.completion_tokens * model_pricing["output_cost"] / 1000
                        )

                    return LLMResponse(
                        content=response.choices[0].message.content,
                        provider=LLMProvider.OPENAI,
                        model=self.config.model,
                        usage=usage.model_dump() if usage else None,
                        cost_estimate=cost_estimate,
                        metadata={
                            "finish_reason": response.choices[0].finish_reason,
                            "response_id": response.id,
                        },
                    )

                except Exception as e:
                    if attempt == self.config.retry_attempts - 1:
                        raise
                    logger.warning(f"OpenAI API attempt {attempt + 1} failed: {e}")
                    await asyncio.sleep(2**attempt)  # Exponential backoff

        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise

    async def test_connection(self) -> bool:
        """Test OpenAI API connection"""
        try:
            test_messages = [{"role": "user", "content": "Hello"}]
            response = await self.client.chat.completions.create(
                model=self.config.model, messages=test_messages, max_tokens=5
            )
            return bool(response.choices)
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False


class AnthropicProvider(LLMProviderBase):
    """Anthropic LLM provider implementation"""

    MODELS = {
        "claude-3-opus-20240229": {"input_cost": 0.015, "output_cost": 0.075},
        "claude-3-sonnet-20240229": {"input_cost": 0.003, "output_cost": 0.015},
        "claude-3-haiku-20240307": {"input_cost": 0.00025, "output_cost": 0.00125},
    }

    def _initialize_client(self):
        """Initialize Anthropic client"""
        if not self.config.api_key:
            self.config.api_key = os.getenv("ANTHROPIC_API_KEY")

        if not self.config.api_key:
            raise ValueError("Anthropic API key is required")

        self.client = Anthropic(
            api_key=self.config.api_key,
            base_url=self.config.custom_endpoint,
            timeout=self.config.timeout,
        )

    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Generate response using Anthropic API"""
        try:
            # Convert messages format for Anthropic
            system_message = ""
            anthropic_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    anthropic_messages.append(msg)

            # Prepare request parameters
            request_params = {
                "model": self.config.model,
                "messages": anthropic_messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                **kwargs,
            }

            if system_message:
                request_params["system"] = system_message

            # Make API call with retry logic
            for attempt in range(self.config.retry_attempts):
                try:
                    response = await self.client.messages.create(**request_params)

                    # Calculate cost estimate
                    cost_estimate = 0.0
                    if response.usage and self.config.model in self.MODELS:
                        model_pricing = self.MODELS[self.config.model]
                        cost_estimate = (
                            response.usage.input_tokens * model_pricing["input_cost"] / 1000
                            + response.usage.output_tokens * model_pricing["output_cost"] / 1000
                        )

                    return LLMResponse(
                        content=response.content[0].text,
                        provider=LLMProvider.ANTHROPIC,
                        model=self.config.model,
                        usage=(
                            {
                                "input_tokens": response.usage.input_tokens,
                                "output_tokens": response.usage.output_tokens,
                            }
                            if response.usage
                            else None
                        ),
                        cost_estimate=cost_estimate,
                        metadata={"stop_reason": response.stop_reason, "response_id": response.id},
                    )

                except Exception as e:
                    if attempt == self.config.retry_attempts - 1:
                        raise
                    logger.warning(f"Anthropic API attempt {attempt + 1} failed: {e}")
                    await asyncio.sleep(2**attempt)

        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise

    async def test_connection(self) -> bool:
        """Test Anthropic API connection"""
        try:
            test_messages = [{"role": "user", "content": "Hello"}]
            response = await self.client.messages.create(
                model=self.config.model, messages=test_messages, max_tokens=5
            )
            return bool(response.content)
        except Exception as e:
            logger.error(f"Anthropic connection test failed: {e}")
            return False


class GroqProvider(LLMProviderBase):
    """Groq LLM provider implementation"""

    MODELS = {
        "llama3-8b-8192": {"input_cost": 0.0001, "output_cost": 0.0001},
        "llama3-70b-8192": {"input_cost": 0.0006, "output_cost": 0.0006},
        "mixtral-8x7b-32768": {"input_cost": 0.0002, "output_cost": 0.0002},
    }

    def _initialize_client(self):
        """Initialize Groq client"""
        if not self.config.api_key:
            self.config.api_key = os.getenv("GROQ_API_KEY")

        if not self.config.api_key:
            raise ValueError("Groq API key is required")

        # Groq uses OpenAI-compatible API
        self.client = openai.AsyncOpenAI(
            api_key=self.config.api_key,
            base_url="https://api.groq.com/openai/v1",
            timeout=self.config.timeout,
        )

    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Generate response using Groq API"""
        try:
            request_params = {
                "model": self.config.model,
                "messages": messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                **kwargs,
            }

            # Make API call with retry logic
            for attempt in range(self.config.retry_attempts):
                try:
                    response = await self.client.chat.completions.create(**request_params)

                    # Calculate cost estimate
                    usage = response.usage
                    cost_estimate = 0.0
                    if usage and self.config.model in self.MODELS:
                        model_pricing = self.MODELS[self.config.model]
                        cost_estimate = (
                            usage.prompt_tokens * model_pricing["input_cost"] / 1000
                            + usage.completion_tokens * model_pricing["output_cost"] / 1000
                        )

                    return LLMResponse(
                        content=response.choices[0].message.content,
                        provider=LLMProvider.GROQ,
                        model=self.config.model,
                        usage=usage.model_dump() if usage else None,
                        cost_estimate=cost_estimate,
                        metadata={
                            "finish_reason": response.choices[0].finish_reason,
                            "response_id": response.id,
                        },
                    )

                except Exception as e:
                    if attempt == self.config.retry_attempts - 1:
                        raise
                    logger.warning(f"Groq API attempt {attempt + 1} failed: {e}")
                    await asyncio.sleep(2**attempt)

        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise

    async def test_connection(self) -> bool:
        """Test Groq API connection"""
        try:
            test_messages = [{"role": "user", "content": "Hello"}]
            response = await self.client.chat.completions.create(
                model=self.config.model, messages=test_messages, max_tokens=5
            )
            return bool(response.choices)
        except Exception as e:
            logger.error(f"Groq connection test failed: {e}")
            return False


class LocalProvider(LLMProviderBase):
    """Local LLM provider implementation (Ollama/etc)"""

    def _initialize_client(self):
        """Initialize local LLM client"""
        if not self.config.custom_endpoint:
            self.config.custom_endpoint = "http://localhost:11434"

    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Generate response using local LLM"""
        try:
            # Prepare request for Ollama-style API
            prompt = self._convert_messages_to_prompt(messages)

            request_data = {
                "model": self.config.model,
                "prompt": prompt,
                "options": {
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens,
                },
            }

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as session:
                async with session.post(
                    f"{self.config.custom_endpoint}/api/generate", json=request_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()

                        return LLMResponse(
                            content=result.get("response", ""),
                            provider=LLMProvider.LOCAL,
                            model=self.config.model,
                            usage=None,  # Local models don't track usage
                            cost_estimate=0.0,  # No cost for local models
                            metadata={
                                "total_duration": result.get("total_duration"),
                                "load_duration": result.get("load_duration"),
                                "prompt_eval_count": result.get("prompt_eval_count"),
                                "eval_count": result.get("eval_count"),
                            },
                        )
                    else:
                        raise Exception(f"Local LLM API returned status {response.status}")

        except Exception as e:
            logger.error(f"Local LLM API call failed: {e}")
            raise

    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert OpenAI-style messages to single prompt"""
        prompt_parts = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)

    async def test_connection(self) -> bool:
        """Test local LLM connection"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.config.custom_endpoint}/api/tags") as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Local LLM connection test failed: {e}")
            return False


class LLMManager:
    """Unified LLM provider management"""

    PROVIDER_CLASSES = {
        LLMProvider.OPENAI: OpenAIProvider,
        LLMProvider.ANTHROPIC: AnthropicProvider,
        LLMProvider.GROQ: GroqProvider,
        LLMProvider.LOCAL: LocalProvider,
    }

    def __init__(self):
        self.providers = {}
        self.default_config = None
        self._load_environment_config()

    def _load_environment_config(self):
        """Load default configuration from environment variables"""
        # Determine default provider based on available API keys
        default_provider = LLMProvider.OPENAI

        if os.getenv("ANTHROPIC_API_KEY"):
            default_provider = LLMProvider.ANTHROPIC
        elif os.getenv("GROQ_API_KEY"):
            default_provider = LLMProvider.GROQ
        elif os.getenv("OPENAI_API_KEY"):
            default_provider = LLMProvider.OPENAI

        self.default_config = LLMConfig(
            provider=default_provider,
            model=self._get_default_model(default_provider),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4000")),
            timeout=int(os.getenv("LLM_TIMEOUT", "30")),
        )

    def _get_default_model(self, provider: LLMProvider) -> str:
        """Get default model for provider"""
        defaults = {
            LLMProvider.OPENAI: "gpt-4o",
            LLMProvider.ANTHROPIC: "claude-3-sonnet-20240229",
            LLMProvider.GROQ: "llama3-8b-8192",
            LLMProvider.LOCAL: "llama2",
        }
        return defaults.get(provider, "gpt-4o")

    def create_provider(self, config: Optional[LLMConfig] = None) -> LLMProviderBase:
        """Create LLM provider instance"""
        if config is None:
            config = self.default_config

        if config.provider not in self.PROVIDER_CLASSES:
            raise ValueError(f"Unsupported provider: {config.provider}")

        provider_class = self.PROVIDER_CLASSES[config.provider]
        return provider_class(config)

    def get_or_create_provider(self, config: Optional[LLMConfig] = None) -> LLMProviderBase:
        """Get cached provider or create new one"""
        if config is None:
            config = self.default_config

        cache_key = f"{config.provider}_{config.model}_{config.api_key or 'default'}"

        if cache_key not in self.providers:
            self.providers[cache_key] = self.create_provider(config)

        return self.providers[cache_key]

    async def generate_response(
        self, messages: List[Dict[str, str]], config: Optional[LLMConfig] = None, **kwargs
    ) -> LLMResponse:
        """Generate response using specified or default provider"""
        provider = self.get_or_create_provider(config)
        return await provider.generate_response(messages, **kwargs)

    async def test_all_providers(self) -> Dict[LLMProvider, bool]:
        """Test all configured providers"""
        results = {}

        for provider_enum in LLMProvider:
            try:
                config = LLMConfig(
                    provider=provider_enum, model=self._get_default_model(provider_enum)
                )
                provider = self.create_provider(config)
                results[provider_enum] = await provider.test_connection()
            except Exception as e:
                logger.error(f"Failed to test {provider_enum}: {e}")
                results[provider_enum] = False

        return results

    def get_available_models(self, provider: LLMProvider) -> List[str]:
        """Get available models for provider"""
        model_maps = {
            LLMProvider.OPENAI: list(OpenAIProvider.MODELS.keys()),
            LLMProvider.ANTHROPIC: list(AnthropicProvider.MODELS.keys()),
            LLMProvider.GROQ: list(GroqProvider.MODELS.keys()),
            LLMProvider.LOCAL: ["llama2", "codellama", "mistral", "phi"],
        }
        return model_maps.get(provider, [])


# Global LLM manager instance
llm_manager = LLMManager()


# Convenience functions for easy usage
async def generate_llm_response(
    messages: List[Dict[str, str]],
    provider: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs,
) -> LLMResponse:
    """
    Generate LLM response with simplified interface

    Args:
        messages: List of message dictionaries with 'role' and 'content'
        provider: Provider name ('openai', 'anthropic', 'groq', 'local')
        model: Model name (optional, uses default for provider)
        **kwargs: Additional parameters passed to provider

    Returns:
        LLMResponse object with generated content
    """
    config = None
    if provider:
        provider_enum = LLMProvider(provider)
        config = LLMConfig(
            provider=provider_enum, model=model or llm_manager._get_default_model(provider_enum)
        )

    return await llm_manager.generate_response(messages, config, **kwargs)


async def test_llm_providers() -> Dict[str, bool]:
    """Test all LLM providers and return availability status"""
    results = await llm_manager.test_all_providers()
    return {provider.value: status for provider, status in results.items()}


def get_llm_config(provider: str, model: Optional[str] = None, **kwargs) -> LLMConfig:
    """Create LLM configuration with validation"""
    provider_enum = LLMProvider(provider)

    config = LLMConfig(
        provider=provider_enum,
        model=model or llm_manager._get_default_model(provider_enum),
        **kwargs,
    )

    return config


# Export for agent integration
__all__ = [
    "LLMProvider",
    "LLMConfig",
    "LLMResponse",
    "LLMManager",
    "llm_manager",
    "generate_llm_response",
    "test_llm_providers",
    "get_llm_config",
]
