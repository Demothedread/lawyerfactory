"""
Bartleby AI Legal Clerk - Chat Handler

This module provides the backend chat functionality for the Bartleby chatbot,
including:
- Natural language understanding for legal queries
- Integration with enhanced vector store for evidence search
- Context-aware responses based on case state
- Action execution for document modifications
- Support for multiple LLM providers (OpenAI, Anthropic, GitHub Copilot, Ollama)

Named after the literary clerk Bartleby, but infinitely more helpful.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import anthropic
import openai
import requests
from flask import jsonify, request, Response, stream_with_context

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GITHUB_COPILOT = "github-copilot"
    OLLAMA = "ollama"


class ActionType(Enum):
    """Types of actions Bartleby can execute"""
    MODIFY_OUTLINE = "modify_outline"
    UPDATE_EVIDENCE = "update_evidence"
    ADJUST_RESEARCH = "adjust_research"
    SEARCH_VECTORS = "search_vectors"
    ADD_CLAIM = "add_claim"
    EDIT_FACT = "edit_fact"


@dataclass
class ChatMessage:
    """Chat message structure"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    cost: Optional[float] = None


@dataclass
class ChatContext:
    """Context information for chat responses"""
    case_id: Optional[str] = None
    skeletal_outline: Optional[Dict] = None
    evidence_data: Optional[List[Dict]] = None
    phase_statuses: Optional[Dict] = None
    attached_context: List[Dict] = field(default_factory=list)


class BartlebyChatHandler:
    """
    Handles chat interactions with Bartleby AI Legal Clerk
    """

    def __init__(self, vector_store_manager=None, evidence_table=None):
        """
        Initialize Bartleby chat handler

        Args:
            vector_store_manager: EnhancedVectorStoreManager instance
            evidence_table: Evidence table API instance
        """
        self.vector_store = vector_store_manager
        self.evidence_table = evidence_table

        # Initialize LLM clients
        self.openai_client = None
        self.anthropic_client = None
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        # Load API keys
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.openai_client = openai.OpenAI(api_key=openai_key)

        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)

        # System prompt for Bartleby
        self.system_prompt = """You are Bartleby, an AI legal clerk assistant for LawyerFactory.

Your role is to help attorneys with:
- Legal research and evidence analysis
- Modifying case documents (skeletal outlines, evidence tables)
- Answering questions about case law and statutes
- Providing strategic litigation advice
- Adjusting research parameters

You have access to:
- Enhanced vector store with case evidence
- Evidence table with PRIMARY and SECONDARY classifications
- Skeletal outline structure
- Current phase workflow status

Personality:
- Professional but approachable
- Detail-oriented and precise
- Proactive in suggesting improvements
- Always cite sources when providing legal information

When suggesting actions:
- Return structured action objects in JSON format
- Be specific about what changes to make
- Explain why the changes would be beneficial
- Ask for confirmation on major modifications

Format your responses in Markdown for clarity.
"""

    def get_llm_client(self, provider: str, model: str):
        """
        Get appropriate LLM client based on provider

        Args:
            provider: LLM provider name
            model: Model name

        Returns:
            Tuple of (client, model_name)
        """
        provider_enum = LLMProvider(provider)

        if provider_enum == LLMProvider.OPENAI:
            if not self.openai_client:
                raise ValueError("OpenAI API key not configured")
            return (self.openai_client, model)

        elif provider_enum == LLMProvider.ANTHROPIC:
            if not self.anthropic_client:
                raise ValueError("Anthropic API key not configured")
            return (self.anthropic_client, model)

        elif provider_enum == LLMProvider.GITHUB_COPILOT:
            # GitHub Copilot uses OpenAI client with special endpoint
            github_token = os.getenv("GITHUB_TOKEN")
            if not github_token:
                raise ValueError("GitHub token not configured")
            # Simplified - would need actual GitHub Copilot API integration
            return (self.openai_client, model)

        elif provider_enum == LLMProvider.OLLAMA:
            # Ollama uses local HTTP endpoint
            return (None, model)

        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def calculate_cost(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate API cost for LLM call

        Args:
            provider: LLM provider
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        # Pricing rates per 1K tokens (as of October 2025)
        pricing = {
            "openai": {
                "gpt-5": {"input": 0.03, "output": 0.12},
                "gpt-5-mini": {"input": 0.015, "output": 0.06},
                "gpt-5-nano": {"input": 0.005, "output": 0.02},
                "gpt-4o": {"input": 0.005, "output": 0.015},
                "gpt-o1": {"input": 0.015, "output": 0.06},
                "gpt-o3": {"input": 0.01, "output": 0.04},
            },
            "anthropic": {
                "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
                "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
                "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
            },
            "github-copilot": {
                "default": {"input": 0.0, "output": 0.0}  # Subscription-based
            },
            "ollama": {
                "default": {"input": 0.0, "output": 0.0}  # Free localhost
            },
        }

        provider_pricing = pricing.get(provider, {})
        model_pricing = provider_pricing.get(model, provider_pricing.get("default", {"input": 0, "output": 0}))

        input_cost = (input_tokens / 1000.0) * model_pricing["input"]
        output_cost = (output_tokens / 1000.0) * model_pricing["output"]

        return input_cost + output_cost

    def build_context_prompt(self, context: ChatContext) -> str:
        """
        Build context prompt from current case state

        Args:
            context: Chat context object

        Returns:
            Formatted context string
        """
        context_parts = []

        if context.case_id:
            context_parts.append(f"**Current Case ID**: {context.case_id}")

        if context.skeletal_outline:
            context_parts.append(f"**Skeletal Outline**:\n```json\n{json.dumps(context.skeletal_outline, indent=2)}\n```")

        if context.evidence_data:
            evidence_count = len(context.evidence_data)
            primary_count = sum(1 for e in context.evidence_data if e.get('evidence_source') == 'PRIMARY')
            secondary_count = sum(1 for e in context.evidence_data if e.get('evidence_source') == 'SECONDARY')
            context_parts.append(f"**Evidence Summary**: {evidence_count} total ({primary_count} PRIMARY, {secondary_count} SECONDARY)")

        if context.phase_statuses:
            active_phases = [k for k, v in context.phase_statuses.items() if v.get('status') in ['active', 'in_progress']]
            completed_phases = [k for k, v in context.phase_statuses.items() if v.get('status') == 'completed']
            context_parts.append(f"**Workflow Status**: {len(completed_phases)} phases completed, {len(active_phases)} active")

        if context.attached_context:
            context_parts.append(f"**Attached Context**: {', '.join(c.get('type', 'unknown') for c in context.attached_context)}")

        return "\n\n".join(context_parts)

    async def send_message(self, message: str, context: ChatContext, settings: Dict) -> ChatMessage:
        """
        Process a chat message and generate response

        Args:
            message: User message
            context: Current case context
            settings: LLM settings (model, temperature, etc.)

        Returns:
            ChatMessage with response and actions
        """
        provider = settings.get("provider", "openai")
        model = settings.get("model", "gpt-5")
        temperature = settings.get("temperature", 0.7)
        max_tokens = settings.get("maxTokens", 4096)

        # Build full prompt with context
        context_prompt = self.build_context_prompt(context)
        full_prompt = f"{context_prompt}\n\n**User Query**: {message}"

        try:
            client, model_name = self.get_llm_client(provider, model)

            if provider == "openai":
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": full_prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                response_text = response.choices[0].message.content
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens

            elif provider == "anthropic":
                response = client.messages.create(
                    model=model_name,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=self.system_prompt,
                    messages=[
                        {"role": "user", "content": full_prompt}
                    ]
                )

                response_text = response.content[0].text
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens

            elif provider == "ollama":
                # Ollama local API call
                ollama_response = requests.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": f"{self.system_prompt}\n\n{full_prompt}",
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                        }
                    }
                )
                ollama_data = ollama_response.json()
                response_text = ollama_data.get("response", "")
                input_tokens = 0  # Ollama doesn't provide token counts
                output_tokens = 0

            else:
                response_text = "Error: Unsupported LLM provider"
                input_tokens = 0
                output_tokens = 0

            # Calculate cost
            cost = self.calculate_cost(provider, model, input_tokens, output_tokens)

            # Extract actions from response (if any)
            actions = self.extract_actions(response_text)

            # Create response message
            return ChatMessage(
                role="assistant",
                content=response_text,
                actions=actions,
                cost=cost
            )

        except Exception as e:
            logger.error(f"Chat error: {e}")
            return ChatMessage(
                role="assistant",
                content=f"⚠️ Error processing your request: {str(e)}",
                cost=0.0
            )

    def extract_actions(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Extract structured actions from LLM response

        Looks for JSON blocks with action specifications

        Args:
            response_text: LLM response text

        Returns:
            List of action dictionaries
        """
        actions = []

        # Simple JSON extraction (would be more sophisticated in production)
        if "```json" in response_text:
            try:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
                action_data = json.loads(json_text)

                if isinstance(action_data, dict) and "actions" in action_data:
                    actions = action_data["actions"]
                elif isinstance(action_data, list):
                    actions = action_data

            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON actions from response")

        return actions

    async def execute_action(self, action: Dict[str, Any], case_id: str) -> Dict[str, Any]:
        """
        Execute a suggested action

        Args:
            action: Action dictionary
            case_id: Current case ID

        Returns:
            Execution result
        """
        action_type = action.get("type")
        action_data = action.get("data", {})

        try:
            if action_type == ActionType.MODIFY_OUTLINE.value:
                # Modify skeletal outline
                result = await self._modify_outline(case_id, action_data)

            elif action_type == ActionType.UPDATE_EVIDENCE.value:
                # Update evidence table
                result = await self._update_evidence(case_id, action_data)

            elif action_type == ActionType.ADJUST_RESEARCH.value:
                # Adjust research parameters
                result = await self._adjust_research(case_id, action_data)

            elif action_type == ActionType.SEARCH_VECTORS.value:
                # Search vector store
                result = await self._search_vectors(case_id, action_data)

            else:
                result = {"success": False, "error": f"Unknown action type: {action_type}"}

            return result

        except Exception as e:
            logger.error(f"Action execution error: {e}")
            return {"success": False, "error": str(e)}

    async def _modify_outline(self, case_id: str, data: Dict) -> Dict:
        """Modify skeletal outline"""
        # Would integrate with SkeletalOutlineSystem
        logger.info(f"Modifying outline for case {case_id}: {data}")
        return {"success": True, "message": "Outline modified"}

    async def _update_evidence(self, case_id: str, data: Dict) -> Dict:
        """Update evidence table"""
        # Would integrate with evidence table API
        logger.info(f"Updating evidence for case {case_id}: {data}")
        return {"success": True, "message": "Evidence updated"}

    async def _adjust_research(self, case_id: str, data: Dict) -> Dict:
        """Adjust research parameters"""
        # Would integrate with PhaseA02Research
        logger.info(f"Adjusting research for case {case_id}: {data}")
        return {"success": True, "message": "Research parameters adjusted"}

    async def _search_vectors(self, case_id: str, data: Dict) -> Dict:
        """Search vector store"""
        if not self.vector_store:
            return {"success": False, "error": "Vector store not available"}

        query = data.get("query", "")
        filters = data.get("filters", {})

        try:
            # Perform vector search
            results = await self.vector_store.search(
                query=query,
                filters=filters,
                limit=data.get("limit", 10)
            )

            return {
                "success": True,
                "results": results,
                "count": len(results)
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def add_system_message(self, case_id: str, message: str, metadata: Dict[str, Any] = None):
        """
        Add a system message to Bartleby's chat history.
        Used for phase narration and automated updates.
        
        Args:
            case_id: Case identifier
            message: System message text
            metadata: Optional metadata (phase, event, progress, etc.)
        """
        try:
            # For now, just log it. In production, would store in database
            logger.info(f"[Bartleby System] Case {case_id}: {message}")
            if metadata:
                logger.debug(f"[Bartleby System] Metadata: {json.dumps(metadata)}")
            return True
        except Exception as e:
            logger.error(f"Failed to add system message: {e}")
            return False

    def handle_intervention(
        self,
        case_id: str,
        phase: str,
        intervention_type: str,
        message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle user intervention during phase execution.
        Processes questions, modification requests, or additional guidance.
        
        Args:
            case_id: Case identifier
            phase: Current phase (e.g., "phaseA01", "phaseB02")
            intervention_type: Type of intervention ("question", "modification", "addition")
            message: User's message
            context: Additional context from current phase state
            
        Returns:
            Dict with response and any actions to take
        """
        try:
            logger.info(f"Processing intervention: {intervention_type} in {phase}")
            
            # Build enhanced context for intervention
            intervention_context = ChatContext(
                case_id=case_id,
                phase_statuses={phase: context.get("status")},
                attached_context=[{
                    "type": "phase_state",
                    "phase": phase,
                    "data": context
                }]
            )
            
            # Create prompt based on intervention type
            if intervention_type == "question":
                prompt = f"""The user has a question during {phase}:

Question: {message}

Current phase context: {json.dumps(context, indent=2)}

Provide a clear, helpful answer that assists the user in understanding what's happening."""
            
            elif intervention_type == "modification":
                prompt = f"""The user wants to make a modification during {phase}:

Request: {message}

Current phase context: {json.dumps(context, indent=2)}

Analyze this request and provide:
1. Whether the modification is possible at this stage
2. What specific changes need to be made
3. Any potential impacts on the workflow"""
            
            elif intervention_type == "addition":
                prompt = f"""The user wants to add something during {phase}:

Addition: {message}

Current phase context: {json.dumps(context, indent=2)}

Evaluate this addition request and provide:
1. How this can be incorporated
2. Where it should be added
3. Any adjustments needed to existing content"""
            
            else:
                prompt = f"""User intervention in {phase}: {message}

Context: {json.dumps(context, indent=2)}

Provide helpful guidance."""
            
            # Get LLM response
            # Use default settings for interventions
            settings = {
                "llmProvider": os.getenv("LLM_PROVIDER", "openai"),
                "aiModel": os.getenv("LLM_MODEL", "gpt-4"),
                "temperature": 0.3,  # Lower temperature for intervention responses
                "maxTokens": 1500
            }
            
            # Use synchronous version for simplicity in intervention handling
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response_message = loop.run_until_complete(
                self.send_message(prompt, intervention_context, settings)
            )
            loop.close()
            
            return {
                "success": True,
                "response": response_message.content,
                "actions": response_message.actions,
                "cost": response_message.cost,
                "intervention_type": intervention_type
            }
            
        except Exception as e:
            logger.error(f"Error handling intervention: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "I encountered an error processing your request. Please try again or rephrase your question."
            }


# Flask route handlers

def register_chat_routes(app, chat_handler: BartlebyChatHandler):
    """
    Register Bartleby chat routes with Flask app

    Args:
        app: Flask application
        chat_handler: BartlebyChatHandler instance
    """

    @app.route('/api/chat/message', methods=['POST'])
    async def chat_message():
        """Handle chat message"""
        data = request.json
        message = data.get('message', '')
        case_id = data.get('case_id')
        context_data = data.get('context', {})
        settings = data.get('settings', {})

        # Build context
        context = ChatContext(
            case_id=case_id,
            skeletal_outline=context_data.get('outline'),
            evidence_data=context_data.get('evidence'),
            phase_statuses=context_data.get('phases'),
            attached_context=context_data.get('attached', [])
        )

        # Get response
        response_message = await chat_handler.send_message(message, context, settings)

        return jsonify({
            "success": True,
            "message": response_message.content,
            "actions": response_message.actions,
            "cost": response_message.cost,
            "timestamp": response_message.timestamp.isoformat()
        })

    @app.route('/api/chat/modify-outline', methods=['POST'])
    async def modify_outline():
        """Modify skeletal outline via chat"""
        data = request.json
        case_id = data.get('case_id')
        modifications = data.get('modifications')

        result = await chat_handler.execute_action({
            "type": ActionType.MODIFY_OUTLINE.value,
            "data": modifications
        }, case_id)

        return jsonify(result)

    @app.route('/api/chat/update-evidence', methods=['POST'])
    async def update_evidence():
        """Update evidence via chat"""
        data = request.json
        case_id = data.get('case_id')
        update = data.get('update')

        result = await chat_handler.execute_action({
            "type": ActionType.UPDATE_EVIDENCE.value,
            "data": update
        }, case_id)

        return jsonify(result)

    @app.route('/api/chat/adjust-research', methods=['POST'])
    async def adjust_research():
        """Adjust research parameters via chat"""
        data = request.json
        case_id = data.get('case_id')
        parameters = data.get('parameters')

        result = await chat_handler.execute_action({
            "type": ActionType.ADJUST_RESEARCH.value,
            "data": parameters
        }, case_id)

        return jsonify(result)

    @app.route('/api/chat/vector-search', methods=['POST'])
    async def vector_search():
        """Search vector store via chat"""
        data = request.json
        case_id = data.get('case_id')
        query = data.get('query')
        filters = data.get('filters', {})

        result = await chat_handler.execute_action({
            "type": ActionType.SEARCH_VECTORS.value,
            "data": {"query": query, "filters": filters}
        }, case_id)

        return jsonify(result)
