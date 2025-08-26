"""
LLM Service Integration Module for LawyerFactory
Provides centralized LLM configuration and service abstraction.
"""

from .config import LLMConfigManager
from .service import LLMService
from .providers import OpenAIProvider, OllamaProvider, GeminiProvider

__all__ = [
    'LLMConfigManager',
    'LLMService',
    'OpenAIProvider',
    'OllamaProvider',
    'GeminiProvider'
]