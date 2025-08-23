"""
# Script Name: models_shared.py
# Description: Centralized LLM configuration and shared models for LawyerFactory system.
# Relationships:
#   - Entity Type: Data Model
#   - Directory Group: Core
#   - Group Tags: llm, configuration, shared
"""

import os
import json
import logging
import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# ===== LLM PROVIDER ENUMS =====

class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    OLLAMA = "ollama"
    GOOGLE_GEMINI = "google_gemini"


class ModelCapability(Enum):
    """LLM model capabilities"""
    TEXT_GENERATION = "text_generation"
    EMBEDDINGS = "embeddings"
    VISION = "vision"
    FUNCTION_CALLING = "function_calling"


# ===== LLM CONFIGURATION =====

@dataclass
class LLMConfig:
    """Centralized LLM configuration"""
    provider: LLMProvider = LLMProvider.OPENAI
    model_name: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4000
    embedding_model: str = "text-embedding-3-small"
    vector_store_enabled: bool = True
    capabilities: List[ModelCapability] = field(default_factory=lambda: [ModelCapability.TEXT_GENERATION])

    # Provider-specific settings
    openai_settings: Dict[str, Any] = field(default_factory=dict)
    ollama_settings: Dict[str, Any] = field(default_factory=dict)
    gemini_settings: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_environment(cls) -> 'LLMConfig':
        """Create configuration from environment variables"""
        return cls(
            provider=LLMProvider(os.getenv('LAWYERFACTORY_LLM_PROVIDER', 'openai')),
            model_name=os.getenv('LAWYERFACTORY_LLM_MODEL', 'gpt-4o-mini'),
            api_key=os.getenv('LAWYERFACTORY_LLM_API_KEY') or os.getenv('OPENAI_API_KEY'),
            base_url=os.getenv('LAWYERFACTORY_LLM_BASE_URL'),
            temperature=float(os.getenv('LAWYERFACTORY_LLM_TEMPERATURE', '0.7')),
            max_tokens=int(os.getenv('LAWYERFACTORY_LLM_MAX_TOKENS', '4000')),
            embedding_model=os.getenv('LAWYERFACTORY_EMBEDDING_MODEL', 'text-embedding-3-small'),
            vector_store_enabled=os.getenv('LAWYERFACTORY_VECTOR_STORE_ENABLED', 'true').lower() == 'true'
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'provider': self.provider.value,
            'model_name': self.model_name,
            'base_url': self.base_url,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'embedding_model': self.embedding_model,
            'vector_store_enabled': self.vector_store_enabled,
            'capabilities': [cap.value for cap in self.capabilities],
            'openai_settings': self.openai_settings,
            'ollama_settings': self.ollama_settings,
            'gemini_settings': self.gemini_settings
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMConfig':
        """Create from dictionary"""
        config = cls()
        config.provider = LLMProvider(data.get('provider', 'openai'))
        config.model_name = data.get('model_name', 'gpt-4o-mini')
        config.base_url = data.get('base_url')
        config.temperature = data.get('temperature', 0.7)
        config.max_tokens = data.get('max_tokens', 4000)
        config.embedding_model = data.get('embedding_model', 'text-embedding-3-small')
        config.vector_store_enabled = data.get('vector_store_enabled', True)
        config.capabilities = [ModelCapability(cap) for cap in data.get('capabilities', ['text_generation'])]
        config.openai_settings = data.get('openai_settings', {})
        config.ollama_settings = data.get('ollama_settings', {})
        config.gemini_settings = data.get('gemini_settings', {})
        return config


# ===== LLM SERVICE ABSTRACTION =====

class LLMServiceInterface(ABC):
    """Abstract interface for LLM services"""

    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt"""
        pass

    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if service is available"""
        pass

    @abstractmethod
    async def get_capabilities(self) -> List[ModelCapability]:
        """Get service capabilities"""
        pass


class OpenAIService(LLMServiceInterface):
    """OpenAI LLM service implementation"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize OpenAI client"""
        try:
            import openai
            self.client = openai.AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url
            )
        except ImportError:
            logger.warning("OpenAI library not available")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using OpenAI"""
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")

        try:
            response = await self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get('temperature', self.config.temperature),
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens)
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI text generation failed: {e}")
            raise

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI"""
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")

        try:
            response = await self.client.embeddings.create(
                model=self.config.embedding_model,
                input=texts
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            logger.error(f"OpenAI embedding generation failed: {e}")
            raise

    async def is_available(self) -> bool:
        """Check if OpenAI service is available"""
        if not self.client or not self.config.api_key:
            return False

        try:
            # Simple availability check
            await self.client.models.list()
            return True
        except Exception:
            return False

    async def get_capabilities(self) -> List[ModelCapability]:
        """Get OpenAI capabilities"""
        return [ModelCapability.TEXT_GENERATION, ModelCapability.EMBEDDINGS]


class OllamaService(LLMServiceInterface):
    """Ollama local LLM service implementation"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.base_url = config.base_url or "http://localhost:11434"

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using Ollama"""
        import aiohttp

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.config.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": kwargs.get('temperature', self.config.temperature),
                        "num_predict": kwargs.get('max_tokens', self.config.max_tokens)
                    }
                }

                async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('response', '')
                    else:
                        raise RuntimeError(f"Ollama API error: {response.status}")
        except Exception as e:
            logger.error(f"Ollama text generation failed: {e}")
            raise

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Ollama"""
        # Ollama doesn't have built-in embeddings, return zeros
        logger.warning("Ollama embeddings not implemented, returning zero vectors")
        return [[0.0] * 384 for _ in texts]  # Common embedding dimension

    async def is_available(self) -> bool:
        """Check if Ollama service is available"""
        import aiohttp

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    return response.status == 200
        except Exception:
            return False

    async def get_capabilities(self) -> List[ModelCapability]:
        """Get Ollama capabilities"""
        return [ModelCapability.TEXT_GENERATION]  # No embeddings support


class GoogleGeminiService(LLMServiceInterface):
    """Google Gemini LLM service implementation"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Google Gemini client"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.config.api_key)
            self.client = genai.GenerativeModel(self.config.model_name)
        except ImportError:
            logger.warning("Google Generative AI library not available")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using Google Gemini"""
        if not self.client:
            raise RuntimeError("Gemini client not initialized")

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.generate_content(prompt).text
            )
            return response
        except Exception as e:
            logger.error(f"Gemini text generation failed: {e}")
            raise

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Google Gemini"""
        # Gemini doesn't have dedicated embedding model, return zeros
        logger.warning("Gemini embeddings not implemented, returning zero vectors")
        return [[0.0] * 768 for _ in texts]  # Gemini embedding dimension

    async def is_available(self) -> bool:
        """Check if Gemini service is available"""
        if not self.client or not self.config.api_key:
            return False

        try:
            # Simple availability check
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.generate_content("Hello").text
            )
            return True
        except Exception:
            return False

    async def get_capabilities(self) -> List[ModelCapability]:
        """Get Gemini capabilities"""
        return [ModelCapability.TEXT_GENERATION, ModelCapability.VISION]


# ===== LLM SERVICE FACTORY =====

class LLMServiceFactory:
    """Factory for creating LLM services"""

    @staticmethod
    def create_service(config: LLMConfig) -> LLMServiceInterface:
        """Create LLM service based on configuration"""
        if config.provider == LLMProvider.OPENAI:
            return OpenAIService(config)
        elif config.provider == LLMProvider.OLLAMA:
            return OllamaService(config)
        elif config.provider == LLMProvider.GOOGLE_GEMINI:
            return GoogleGeminiService(config)
        else:
            raise ValueError(f"Unsupported LLM provider: {config.provider}")


# ===== LLM CONFIGURATION MANAGER =====

class LLMConfigurationManager:
    """Centralized LLM configuration management"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path or "llm_config.json")
        self.current_config = LLMConfig.from_environment()
        self.service: Optional[LLMServiceInterface] = None
        self._load_config()

    def _load_config(self):
        """Load configuration from file"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    self.current_config = LLMConfig.from_dict(data)
            except Exception as e:
                logger.warning(f"Failed to load LLM config: {e}")

    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.current_config.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save LLM config: {e}")

    def update_config(self, **kwargs):
        """Update configuration parameters"""
        for key, value in kwargs.items():
            if hasattr(self.current_config, key):
                setattr(self.current_config, key, value)

        # Recreate service with new config
        self.service = None
        self.save_config()

    def get_service(self) -> LLMServiceInterface:
        """Get or create LLM service"""
        if not self.service:
            self.service = LLMServiceFactory.create_service(self.current_config)
        return self.service

    async def validate_config(self) -> Dict[str, Any]:
        """Validate current configuration"""
        results = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'capabilities': []
        }

        try:
            service = self.get_service()
            results['valid'] = await service.is_available()
            results['capabilities'] = [cap.value for cap in await service.get_capabilities()]

            if not results['valid']:
                results['errors'].append(f"{self.current_config.provider.value} service not available")

            if not self.current_config.api_key and self.current_config.provider != LLMProvider.OLLAMA:
                results['errors'].append("API key required for this provider")

        except Exception as e:
            results['errors'].append(f"Configuration validation failed: {e}")

        return results

    def get_available_providers(self) -> List[Dict[str, Any]]:
        """Get list of available providers with their capabilities"""
        providers = []

        for provider in LLMProvider:
            config = LLMConfig(provider=provider)
            service = LLMServiceFactory.create_service(config)

            providers.append({
                'name': provider.value,
                'display_name': provider.value.replace('_', ' ').title(),
                'available': asyncio.run(service.is_available()),
                'capabilities': [cap.value for cap in asyncio.run(service.get_capabilities())]
            })

        return providers


# ===== BACKWARD COMPATIBILITY =====

# Keep existing Stage and Task classes for backward compatibility
class Stage(Enum):
    PREPRODUCTION_PLANNING = "Preproduction Planning"
    RESEARCH_AND_DEVELOPMENT = "Research and Development"
    ORGANIZATION_DATABASE_BUILDING = "Organization / Database Building"
    FIRST_PASS = "1st Pass All Parts"
    COMBINING = "Combining"
    EDITING = "Editing"
    SECOND_PASS = "2nd Pass"
    HUMAN_FEEDBACK = "Human Feedback"
    FINAL_DRAFT = "Final Draft"


STAGE_SEQUENCE = [
    Stage.PREPRODUCTION_PLANNING,
    Stage.RESEARCH_AND_DEVELOPMENT,
    Stage.ORGANIZATION_DATABASE_BUILDING,
    Stage.FIRST_PASS,
    Stage.COMBINING,
    Stage.EDITING,
    Stage.SECOND_PASS,
    Stage.HUMAN_FEEDBACK,
    Stage.FINAL_DRAFT,
]


@dataclass
class Task:
    id: int
    title: str
    stage: Stage = Stage.PREPRODUCTION_PLANNING
    description: str = ""
    assignee: str | None = None

    def assign(self, agent: str) -> None:
        """Assign this task to an agent."""
        self.assignee = agent

    def advance(self) -> None:
        """Advance the task to the next stage."""
        current_index = STAGE_SEQUENCE.index(self.stage)
        if current_index < len(STAGE_SEQUENCE) - 1:
            self.stage = STAGE_SEQUENCE[current_index + 1]


# ===== GLOBAL LLM MANAGER INSTANCE =====

# Global instance for easy access
llm_manager = LLMConfigurationManager()

def get_llm_service() -> LLMServiceInterface:
    """Get the global LLM service instance"""
    return llm_manager.get_service()

def update_llm_config(**kwargs):
    """Update global LLM configuration"""
    llm_manager.update_config(**kwargs)

def get_llm_config() -> LLMConfig:
    """Get current LLM configuration"""
    return llm_manager.current_config