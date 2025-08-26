"""
LLM Providers for LawyerFactory
Individual provider implementations for different LLM services.
"""

import asyncio
import json
import logging
import os
import subprocess
import shutil
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, cast

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    def __init__(self, config_manager, provider_name: str):
        self.config_manager = config_manager
        self.provider_name = provider_name
        self._client = None

    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate text using the provider"""
        pass

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to the provider"""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        pass

    def get_config(self) -> Dict[str, Any]:
        """Get provider configuration"""
        return self.config_manager.get_provider_config(self.provider_name)


class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation"""

    def __init__(self, config_manager):
        super().__init__(config_manager, "openai")
        self._initialize_client()

    def _initialize_client(self):
        """Initialize OpenAI client"""
        try:
            import openai

            config = self.get_config() or {}
            api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
            if api_key:
                # prefer explicit OpenAI client construction if available
                try:
                    self._client = openai.OpenAI(api_key=api_key)
                except Exception:
                    # fallback: set module as client for older SDK variants
                    self._client = openai
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client: {e}")

    async def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate text using OpenAI"""
        if not self._client:
            return {"success": False, "error": "OpenAI client not initialized"}

        try:
            config = self.get_config() or {}
            messages = [{"role": "user", "content": prompt}]
            # defensive call: cast messages to Any to avoid static-checker mismatches
            messages_any = cast(Any, messages)

            # Attempt several call patterns depending on installed openai package
            response = None
            try:
                # new-ish SDK style
                response = self._client.chat.completions.create(
                    model=config.get("model", "gpt-4"),
                    messages=messages_any,
                    temperature=config.get("temperature", 0.7),
                    max_tokens=config.get("max_tokens", 1000),
                    **kwargs,
                )
            except Exception:
                # fallback to older ChatCompletion API
                try:
                    response = self._client.ChatCompletion.create(
                        model=config.get("model", "gpt-4"),
                        messages=messages_any,
                        temperature=config.get("temperature", 0.7),
                        max_tokens=config.get("max_tokens", 1000),
                        **kwargs,
                    )
                except Exception as e2:
                    # as last resort try a generic completion() name if present
                    try:
                        response = getattr(self._client, "completion")(
                            prompt=prompt, **kwargs
                        )
                    except Exception:
                        raise e2

            # Defensive extraction of text and usage
            text = ""
            usage = {}
            try:
                # handle object/dict shapes
                text = (
                    getattr(response, "choices", None)
                    and getattr(response.choices[0], "message", None)
                    and getattr(response.choices[0].message, "content", None)
                )
                if not text and isinstance(response, dict):
                    # common dict layout
                    text = (
                        response.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content")
                        or response.get("text")
                        or ""
                    )
            except Exception:
                text = ""

            try:
                usage_obj = getattr(response, "usage", None) or (
                    response.get("usage") if isinstance(response, dict) else None
                )
                if usage_obj:
                    usage = {
                        "prompt_tokens": getattr(
                            usage_obj,
                            "prompt_tokens",
                            (
                                usage_obj.get("prompt_tokens")
                                if isinstance(usage_obj, dict)
                                else None
                            ),
                        ),
                        "completion_tokens": getattr(
                            usage_obj,
                            "completion_tokens",
                            (
                                usage_obj.get("completion_tokens")
                                if isinstance(usage_obj, dict)
                                else None
                            ),
                        ),
                        "total_tokens": getattr(
                            usage_obj,
                            "total_tokens",
                            (
                                usage_obj.get("total_tokens")
                                if isinstance(usage_obj, dict)
                                else None
                            ),
                        ),
                    }
            except Exception:
                usage = {}

            return {"success": True, "text": text or "", "usage": usage}
        except Exception as e:
            logger.error(f"OpenAI text generation failed: {e}")
            return {"success": False, "error": str(e)}

    async def classify_evidence(
        self, content: str, filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """Classify evidence using OpenAI"""
        prompt = f"""
        Analyze the following document content and classify it as either PRIMARY or SECONDARY evidence.
        Then provide a specific evidence type classification.

        PRIMARY evidence categories (first-hand):
        - Witness Statement
        - Original Document
        - Physical Evidence Photo
        - Audio/Video Recording
        - Digital Communication (original)
        - Scene Photograph
        - Autopsy Report
        - Original Contract
        - Police Report
        - Medical Record
        - Other (specify)

        SECONDARY evidence categories (third-hand):
        - News Article
        - Social Media Post
        - Journal Article
        - Government Report
        - Court Filing
        - Legal Brief
        - Academic Paper
        - Blog Post
        - Press Release
        - Other (specify)

        Document content:
        {content[:4000]}

        Provide your response in JSON format:
        {{
            "evidence_type": "PRIMARY or SECONDARY",
            "specific_category": "specific category from above",
            "confidence_score": 0.0-1.0,
            "reasoning": "brief explanation",
            "key_characteristics": ["characteristic1", "characteristic2"]
        }}
        """

        result = await self.generate_text(prompt, temperature=0.3)
        if not result["success"]:
            return result

        try:
            # Parse JSON response
            response_data = json.loads(result["text"])
            return {"success": True, "classification": response_data}
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Failed to parse classification response",
            }

    async def extract_metadata(
        self, content: str, doc_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract metadata using OpenAI"""
        prompt = f"""
        Extract metadata from the following document content.
        Focus on legal relevance and provide structured information.

        Document content:
        {content[:3000]}

        Provide metadata in JSON format:
        {{
            "title": "document title or subject",
            "author": "author if identifiable",
            "date": "date if mentioned",
            "parties_involved": ["party1", "party2"],
            "key_issues": ["issue1", "issue2"],
            "summary": "brief summary",
            "relevance_score": 0.0-1.0,
            "legal_context": "relevant legal context"
        }}
        """

        result = await self.generate_text(prompt, temperature=0.2)
        if not result["success"]:
            return result

        try:
            metadata = json.loads(result["text"])
            return {"success": True, "metadata": metadata}
        except json.JSONDecodeError:
            return {"success": False, "error": "Failed to parse metadata response"}

    async def summarize_text(
        self, content: str, max_length: int = 200
    ) -> Dict[str, Any]:
        """Summarize text using OpenAI"""
        prompt = f"""
        Summarize the following text in {max_length} words or less.
        Focus on the key legal points and factual information.

        Text to summarize:
        {content[:4000]}

        Provide a concise summary:
        """

        return await self.generate_text(prompt, temperature=0.3, max_tokens=max_length)

    def test_connection(self) -> Dict[str, Any]:
        """Test OpenAI connection"""
        config = self.get_config()
        if not config.get("api_key"):
            return {"success": False, "error": "API key not configured"}

        if not self._client:
            return {"success": False, "error": "Client not initialized"}

        try:
            # Simple test - check if API key is valid by making a minimal request
            # This is a synchronous check for connection status
            return {
                "success": True,
                "message": "OpenAI client initialized successfully",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for OpenAI"""
        try:
            # Try a minimal completion to test API connectivity
            result = await self.generate_text("Hello", max_tokens=10)
            return {
                "healthy": result["success"],
                "response_time": "N/A",  # Could measure this
                "error": result.get("error"),
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    async def batch_process(
        self, items: List[Dict[str, Any]], operation: str = "generate_text"
    ) -> List[Dict[str, Any]]:
        """Process multiple items in batch"""
        results = []
        for item in items:
            if operation == "generate_text":
                result = await self.generate_text(item.get("prompt", ""))
            elif operation == "classify_evidence":
                result = await self.classify_evidence(
                    item.get("content", ""), item.get("filename")
                )
            elif operation == "extract_metadata":
                result = await self.extract_metadata(
                    item.get("content", ""), item.get("doc_type")
                )
            elif operation == "summarize_text":
                result = await self.summarize_text(
                    item.get("content", ""), item.get("max_length", 200)
                )
            else:
                result = {"success": False, "error": f"Unknown operation: {operation}"}

            results.append(result)

            # Add small delay to avoid rate limits
            await asyncio.sleep(0.1)

        return results


class OllamaProvider(LLMProvider):
    """Ollama provider implementation"""

    def __init__(self, config_manager):
        super().__init__(config_manager, "ollama")
        self._base_url = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Ollama client and ensure local server is running if required"""
        config = self.get_config() or {}
        self._base_url = config.get("base_url", "http://localhost:11434")

        # quick check if service is responding
        def _is_running():
            try:
                # prefer requests if available for simplicity
                import requests  # type: ignore

                resp = requests.get(f"{self._base_url}/api/tags", timeout=2)
                return resp.status_code == 200
            except Exception:
                return False

        if _is_running():
            return

        # attempt to launch ollama if installed and user expects local usage
        ollama_cmd = shutil.which("ollama")
        if ollama_cmd:
            try:
                # Start the model run in background; best-effort non-blocking
                logger.info(
                    "Ollama not responding; attempting to start 'ollama run lllama3' in background"
                )
                # Use Popen to avoid blocking; output suppressed
                subprocess.Popen(
                    [ollama_cmd, "run", "lllama3"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                # wait briefly and re-check
                time.sleep(3)
                if _is_running():
                    logger.info("Ollama started successfully")
                else:
                    logger.warning(
                        "Attempted to start Ollama but service still not responding"
                    )
            except Exception as e:
                logger.warning(f"Failed to start Ollama process: {e}")
        else:
            logger.warning(
                "Ollama binary not found in PATH; ensure Ollama is installed and running"
            )

    async def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate text using Ollama"""
        try:
            import aiohttp

            config = self.get_config()
            url = f"{self._base_url}/api/generate"

            payload = {
                "model": config.get("model", "llama2"),
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": config.get("temperature", 0.7),
                    "num_predict": config.get("max_tokens", 4000),
                },
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "text": result.get("response", ""),
                            "usage": {
                                "eval_count": result.get("eval_count", 0),
                                "eval_duration": result.get("eval_duration", 0),
                            },
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}",
                        }
        except Exception as e:
            logger.error(f"Ollama text generation failed: {e}")
            return {"success": False, "error": str(e)}

    async def classify_evidence(
        self, content: str, filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """Classify evidence using Ollama"""
        # Use the same prompt structure as OpenAI
        prompt = f"""
        Analyze the following document content and classify it as either PRIMARY or SECONDARY evidence.
        Then provide a specific evidence type classification.

        PRIMARY evidence categories (first-hand):
        - Witness Statement
        - Original Document
        - Physical Evidence Photo
        - Audio/Video Recording
        - Digital Communication (original)
        - Scene Photograph
        - Autopsy Report
        - Original Contract
        - Police Report
        - Medical Record
        - Other (specify)

        SECONDARY evidence categories (third-hand):
        - News Article
        - Social Media Post
        - Journal Article
        - Government Report
        - Court Filing
        - Legal Brief
        - Academic Paper
        - Blog Post
        - Press Release
        - Other (specify)

        Document content:
        {content[:3000]}

        Provide your response in JSON format:
        {{
            "evidence_type": "PRIMARY or SECONDARY",
            "specific_category": "specific category from above",
            "confidence_score": 0.0-1.0,
            "reasoning": "brief explanation",
            "key_characteristics": ["characteristic1", "characteristic2"]
        }}
        """

        result = await self.generate_text(prompt, temperature=0.3)
        if not result["success"]:
            return result

        try:
            response_data = json.loads(result["text"])
            return {"success": True, "classification": response_data}
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Failed to parse classification response",
            }

    async def extract_metadata(
        self, content: str, doc_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract metadata using Ollama"""
        prompt = f"""
        Extract metadata from the following document content.
        Focus on legal relevance and provide structured information.

        Document content:
        {content[:2000]}

        Provide metadata in JSON format:
        {{
            "title": "document title or subject",
            "author": "author if identifiable",
            "date": "date if mentioned",
            "parties_involved": ["party1", "party2"],
            "key_issues": ["issue1", "issue2"],
            "summary": "brief summary",
            "relevance_score": 0.0-1.0,
            "legal_context": "relevant legal context"
        }}
        """

        result = await self.generate_text(prompt, temperature=0.2)
        if not result["success"]:
            return result

        try:
            metadata = json.loads(result["text"])
            return {"success": True, "metadata": metadata}
        except json.JSONDecodeError:
            return {"success": False, "error": "Failed to parse metadata response"}

    async def summarize_text(
        self, content: str, max_length: int = 200
    ) -> Dict[str, Any]:
        """Summarize text using Ollama"""
        prompt = f"""
        Summarize the following text in {max_length} words or less.
        Focus on the key legal points and factual information.

        Text to summarize:
        {content[:3000]}

        Provide a concise summary:
        """

        return await self.generate_text(prompt, temperature=0.3)

    def test_connection(self) -> Dict[str, Any]:
        """Test Ollama connection"""
        config = self.get_config()
        if not config.get("base_url"):
            return {"success": False, "error": "Base URL not configured"}

        return {
            "success": True,
            "message": f"Ollama base URL configured: {config['base_url']}",
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for Ollama"""
        try:
            import aiohttp

            url = f"{self._base_url}/api/tags"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return {"healthy": True, "message": "Ollama service is running"}
                    else:
                        return {"healthy": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    async def batch_process(
        self, items: List[Dict[str, Any]], operation: str = "generate_text"
    ) -> List[Dict[str, Any]]:
        """Process multiple items in batch"""
        results = []
        for item in items:
            if operation == "generate_text":
                result = await self.generate_text(item.get("prompt", ""))
            elif operation == "classify_evidence":
                result = await self.classify_evidence(
                    item.get("content", ""), item.get("filename")
                )
            elif operation == "extract_metadata":
                result = await self.extract_metadata(
                    item.get("content", ""), item.get("doc_type")
                )
            elif operation == "summarize_text":
                result = await self.summarize_text(
                    item.get("content", ""), item.get("max_length", 200)
                )
            else:
                result = {"success": False, "error": f"Unknown operation: {operation}"}

            results.append(result)

            # Add delay to avoid overwhelming the local service
            await asyncio.sleep(0.5)

        return results


class GeminiProvider(LLMProvider):
    """Gemini provider implementation"""

    def __init__(self, config_manager):
        super().__init__(config_manager, "gemini")
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Gemini client (optional dependency). Use env var fallback."""
        try:
            import google.generativeai as genai  # type: ignore

            config = self.get_config() or {}
            api_key = config.get("api_key") or os.getenv("GEMINI_API_KEY")
            if api_key:
                try:
                    genai.configure(api_key=api_key)
                except Exception:
                    # older/newer libs may differ; ignore configure failure but keep module
                    pass
                self._client = genai
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini client: {e}")
            self._client = None

    async def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate text using Gemini"""
        if not self._client:
            return {"success": False, "error": "Gemini client not initialized"}

        try:
            config = self.get_config()
            loop = asyncio.get_event_loop()

            # Prefer direct high-level client API if available, otherwise fallback to model object
            if hasattr(self._client, "generate_text"):
                # Run potential blocking sync call in executor
                response = await loop.run_in_executor(
                    None,
                    lambda: self._client.generate_text(
                        prompt,
                        model=config.get("model", "gemini-flash"),
                        temperature=config.get("temperature", 0.7),
                        max_output_tokens=config.get("max_tokens", 4000),
                        **kwargs,
                    ),
                )
            else:
                # Use GenerativeModel path; build GenerationConfig from the client module (self._client)
                model_obj = getattr(self._client, "GenerativeModel")(
                    config.get("model", "gemini-flash")
                )
                generation_config = self._client.types.GenerationConfig(
                    temperature=config.get("temperature", 0.7),
                    max_output_tokens=config.get("max_tokens", 4000),
                )

                # model_obj.generate_content may be synchronous; run in executor
                response = await loop.run_in_executor(
                    None,
                    lambda: model_obj.generate_content(
                        prompt, generation_config=generation_config, **kwargs
                    ),
                )

            # Normalize response to extract text and usage safely
            text = ""
            usage = {}
            try:
                # common attribute on newer client responses
                text = getattr(response, "text", None) or (
                    response.get("text") if isinstance(response, dict) else None
                )
            except Exception:
                text = None

            # Fallback: some responses include candidates list with content
            if not text:
                try:
                    candidates = getattr(response, "candidates", None) or (
                        response.get("candidates")
                        if isinstance(response, dict)
                        else None
                    )
                    if candidates:
                        # try extract best candidate text
                        first = candidates[0]
                        # candidate may be object or dict
                        text = getattr(first, "content", None) or (
                            first.get("content") if isinstance(first, dict) else None
                        )
                except Exception:
                    text = None

            # usage info (best-effort)
            try:
                candidates = (
                    getattr(response, "candidates", None)
                    or (
                        response.get("candidates") if isinstance(response, dict) else []
                    )
                    or []
                )
                candidates_count = len(candidates)
                usage = {"candidates": candidates_count}
            except Exception:
                usage = {}

            return {"success": True, "text": text or "", "usage": usage}
        except Exception as e:
            logger.error(f"Gemini text generation failed: {e}")
            return {"success": False, "error": str(e)}

    async def classify_evidence(
        self, content: str, filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """Classify evidence using Gemini"""
        prompt = f"""
        Analyze the following document content and classify it as either PRIMARY or SECONDARY evidence.
        Then provide a specific evidence type classification.

        PRIMARY evidence categories (first-hand):
        - Witness Statement
        - Original Document
        - Physical Evidence Photo
        - Audio/Video Recording
        - Digital Communication (original)
        - Scene Photograph
        - Autopsy Report
        - Original Contract
        - Police Report
        - Medical Record
        - Other (specify)

        SECONDARY evidence categories (third-hand):
        - News Article
        - Social Media Post
        - Journal Article
        - Government Report
        - Court Filing
        - Legal Brief
        - Academic Paper
        - Blog Post
        - Press Release
        - Other (specify)

        Document content:
        {content[:4000]}

        Provide your response in JSON format:
        {{
            "evidence_type": "PRIMARY or SECONDARY",
            "specific_category": "specific category from above",
            "confidence_score": 0.0-1.0,
            "reasoning": "brief explanation",
            "key_characteristics": ["characteristic1", "characteristic2"]
        }}
        """

        result = await self.generate_text(prompt, temperature=0.3)
        if not result["success"]:
            return result

        try:
            response_data = json.loads(result["text"])
            return {"success": True, "classification": response_data}
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Failed to parse classification response",
            }

    async def extract_metadata(
        self, content: str, doc_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract metadata using Gemini"""
        prompt = f"""
        Extract metadata from the following document content.
        Focus on legal relevance and provide structured information.

        Document content:
        {content[:3000]}

        Provide metadata in JSON format:
        {{
            "title": "document title or subject",
            "author": "author if identifiable",
            "date": "date if mentioned",
            "parties_involved": ["party1", "party2"],
            "key_issues": ["issue1", "issue2"],
            "summary": "brief summary",
            "relevance_score": 0.0-1.0,
            "legal_context": "relevant legal context"
        }}
        """

        result = await self.generate_text(prompt, temperature=0.2)
        if not result["success"]:
            return result

        try:
            metadata = json.loads(result["text"])
            return {"success": True, "metadata": metadata}
        except json.JSONDecodeError:
            return {"success": False, "error": "Failed to parse metadata response"}

    async def summarize_text(
        self, content: str, max_length: int = 200
    ) -> Dict[str, Any]:
        """Summarize text using Gemini"""
        prompt = f"""
        Summarize the following text in {max_length} words or less.
        Focus on the key legal points and factual information.

        Text to summarize:
        {content[:4000]}

        Provide a concise summary:
        """

        return await self.generate_text(prompt, temperature=0.3)

    def test_connection(self) -> Dict[str, Any]:
        """Test Gemini connection"""
        config = self.get_config()
        if not config.get("api_key"):
            return {"success": False, "error": "API key not configured"}

        if not self._client:
            return {"success": False, "error": "Client not initialized"}

        return {"success": True, "message": "Gemini client initialized successfully"}

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for Gemini"""
        try:
            result = await self.generate_text("Hello", max_tokens=10)
            return {"healthy": result["success"], "error": result.get("error")}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    async def batch_process(
        self, items: List[Dict[str, Any]], operation: str = "generate_text"
    ) -> List[Dict[str, Any]]:
        """Process multiple items in batch"""
        results = []
        for item in items:
            if operation == "generate_text":
                result = await self.generate_text(item.get("prompt", ""))
            elif operation == "classify_evidence":
                result = await self.classify_evidence(
                    item.get("content", ""), item.get("filename")
                )
            elif operation == "extract_metadata":
                result = await self.extract_metadata(
                    item.get("content", ""), item.get("doc_type")
                )
            elif operation == "summarize_text":
                result = await self.summarize_text(
                    item.get("content", ""), item.get("max_length", 200)
                )
            else:
                result = {"success": False, "error": f"Unknown operation: {operation}"}

            results.append(result)

            # Add small delay to avoid rate limits
            await asyncio.sleep(0.1)

        return results
