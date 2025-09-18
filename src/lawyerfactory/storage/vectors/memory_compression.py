"""
# Script Name: memory_compression.py
# Description: MCP Memory Server Integration for LawyerFactory Pneumonic memory compression system using Model Context Protocol for context management. Provides intelligent context compression, retrieval, and workflow state persistence.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: null
MCP Memory Server Integration for LawyerFactory
Pneumonic memory compression system using Model Context Protocol for context management.
Provides intelligent context compression, retrieval, and workflow state persistence.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memory stored in the MCP system"""

    CASE_CONTEXT = "case_context"
    WORKFLOW_STATE = "workflow_state"
    LEGAL_PRECEDENT = "legal_precedent"
    DOCUMENT_SUMMARY = "document_summary"
    AGENT_DECISION = "agent_decision"
    USER_PREFERENCE = "user_preference"
    COMPRESSED_CONVERSATION = "compressed_conversation"


class CompressionLevel(Enum):
    """Levels of memory compression"""

    NONE = 0.0
    LOW = 0.3
    MEDIUM = 0.6
    HIGH = 0.8
    EXTREME = 0.95


@dataclass
class MemoryEntry:
    """A memory entry with compression metadata"""

    id: str
    content: str
    memory_type: MemoryType
    compression_level: CompressionLevel
    timestamp: datetime
    relevance_score: float = 1.0
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    semantic_tags: List[str] = field(default_factory=list)
    relationships: Dict[str, str] = field(default_factory=dict)

    def update_access(self):
        """Update access tracking"""
        self.access_count += 1
        self.last_accessed = datetime.now()


class MCPMemoryManager:
    """Enhanced memory manager using MCP servers for pneumonic compression"""

    def __init__(self, mcp_tools=None):
        """
        Initialize MCP memory manager

        Args:
            mcp_tools: Dictionary of MCP tool functions for memory operations
        """
        self.mcp_tools = mcp_tools or {}
        self.compression_strategies = self._initialize_compression_strategies()
        self.memory_cache = {}  # Local cache for frequently accessed memories
        self.compression_queue = asyncio.Queue()  # Queue for background compression

    def _initialize_compression_strategies(self) -> Dict[MemoryType, Dict[str, Any]]:
        """Initialize compression strategies for different memory types"""
        return {
            MemoryType.CASE_CONTEXT: {
                "strategy": "semantic_summarization",
                "retention_days": 30,
                "max_entries": 100,
                "compression_threshold": 0.7,
            },
            MemoryType.WORKFLOW_STATE: {
                "strategy": "state_checkpointing",
                "retention_days": 7,
                "max_entries": 50,
                "compression_threshold": 0.5,
            },
            MemoryType.LEGAL_PRECEDENT: {
                "strategy": "citation_extraction",
                "retention_days": 365,
                "max_entries": 500,
                "compression_threshold": 0.8,
            },
            MemoryType.DOCUMENT_SUMMARY: {
                "strategy": "hierarchical_summarization",
                "retention_days": 90,
                "max_entries": 200,
                "compression_threshold": 0.6,
            },
            MemoryType.AGENT_DECISION: {
                "strategy": "decision_tree_compression",
                "retention_days": 14,
                "max_entries": 100,
                "compression_threshold": 0.7,
            },
            MemoryType.COMPRESSED_CONVERSATION: {
                "strategy": "dialogue_compression",
                "retention_days": 7,
                "max_entries": 50,
                "compression_threshold": 0.9,
            },
        }

    async def store_memory(
        self,
        content: str,
        memory_type: MemoryType,
        session_id: str,
        semantic_tags: Optional[List[str]] = None,
        relationships: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Store memory in MCP system with pneumonic compression

        Args:
            content: Memory content to store
            memory_type: Type of memory being stored
            session_id: Session identifier for context
            semantic_tags: Optional semantic tags for retrieval
            relationships: Optional relationships to other memories

        Returns:
            Memory ID for later retrieval
        """
        try:
            memory_id = f"{memory_type.value}_{session_id}_{datetime.now().isoformat()}"

            # Determine compression level based on content size and type
            compression_level = self._determine_compression_level(content, memory_type)

            # Apply compression if needed
            compressed_content = await self._compress_content(
                content, memory_type, compression_level
            )

            # Create memory entry
            memory_entry = MemoryEntry(
                id=memory_id,
                content=compressed_content,
                memory_type=memory_type,
                compression_level=compression_level,
                timestamp=datetime.now(),
                semantic_tags=semantic_tags or [],
                relationships=relationships or {},
            )

            # Store in MCP memory server
            await self._store_in_mcp(memory_entry, session_id)

            # Cache locally if frequently accessed type
            if memory_type in [MemoryType.CASE_CONTEXT, MemoryType.WORKFLOW_STATE]:
                self.memory_cache[memory_id] = memory_entry

            logger.info(
                f"Stored memory {memory_id} with compression {compression_level.name}"
            )
            return memory_id

        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise

    async def retrieve_memory(
        self, memory_id: str, decompress: bool = True
    ) -> Optional[MemoryEntry]:
        """
        Retrieve memory from MCP system with optional decompression

        Args:
            memory_id: Memory identifier
            decompress: Whether to decompress the content

        Returns:
            MemoryEntry if found, None otherwise
        """
        try:
            # Check local cache first
            if memory_id in self.memory_cache:
                memory = self.memory_cache[memory_id]
                memory.update_access()

                if decompress and memory.compression_level != CompressionLevel.NONE:
                    memory.content = await self._decompress_content(
                        memory.content, memory.memory_type
                    )

                return memory

            # Retrieve from MCP server
            memory_data = await self._retrieve_from_mcp(memory_id)
            if not memory_data:
                return None

            # Reconstruct memory entry
            memory = self._reconstruct_memory_entry(memory_data)
            memory.update_access()

            # Decompress if requested
            if decompress and memory.compression_level != CompressionLevel.NONE:
                memory.content = await self._decompress_content(
                    memory.content, memory.memory_type
                )

            # Update MCP with access tracking
            await self._update_memory_access(
                memory_id, memory.access_count, memory.last_accessed
            )

            return memory

        except Exception as e:
            logger.error(f"Failed to retrieve memory {memory_id}: {e}")
            return None

    async def search_memories(
        self,
        query: str,
        memory_types: Optional[List[MemoryType]] = None,
        session_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[MemoryEntry]:
        """
        Search memories using semantic similarity

        Args:
            query: Search query
            memory_types: Optional filter by memory types
            session_id: Optional filter by session
            limit: Maximum number of results

        Returns:
            List of relevant memory entries
        """
        try:
            # Use MCP search capabilities
            search_params = {"query": query, "limit": limit}

            if memory_types:
                search_params["types"] = [mt.value for mt in memory_types]

            if session_id:
                search_params["session_id"] = session_id

            # Execute search via MCP
            search_results = await self._search_mcp(search_params)

            # Convert results to memory entries
            memories = []
            for result in search_results:
                memory = self._reconstruct_memory_entry(result)
                if memory:
                    memories.append(memory)

            # Sort by relevance score
            memories.sort(key=lambda m: m.relevance_score, reverse=True)

            logger.info(f"Found {len(memories)} memories for query: {query[:50]}...")
            return memories[:limit]

        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []

    async def compress_session_context(
        self, session_id: str, compression_target: float = 0.7
    ) -> Dict[str, Any]:
        """
        Compress all context for a session using pneumonic techniques

        Args:
            session_id: Session to compress
            compression_target: Target compression ratio (0.0-1.0)

        Returns:
            Compression summary with statistics
        """
        try:
            # Retrieve all memories for session
            session_memories = await self._get_session_memories(session_id)

            if not session_memories:
                return {"status": "no_memories", "session_id": session_id}

            # Group memories by type
            memory_groups = {}
            for memory in session_memories:
                if memory.memory_type not in memory_groups:
                    memory_groups[memory.memory_type] = []
                memory_groups[memory.memory_type].append(memory)

            compression_stats = {
                "session_id": session_id,
                "original_count": len(session_memories),
                "compressed_count": 0,
                "compression_ratio": 0.0,
                "preserved_memories": [],
                "compressed_memories": [],
            }

            # Apply compression strategies by type
            for memory_type, memories in memory_groups.items():
                strategy = self.compression_strategies.get(memory_type, {})
                threshold = strategy.get("compression_threshold", 0.7)

                if len(memories) > strategy.get("max_entries", 100):
                    # Apply aggressive compression
                    compressed = await self._apply_pneumonic_compression(
                        memories, compression_target
                    )
                    compression_stats["compressed_memories"].extend(compressed)
                else:
                    # Preserve memories below threshold
                    compression_stats["preserved_memories"].extend(
                        [m.id for m in memories]
                    )

            # Calculate final statistics
            total_compressed = len(compression_stats["compressed_memories"])
            compression_stats["compressed_count"] = total_compressed
            compression_stats["compression_ratio"] = total_compressed / len(
                session_memories
            )

            # Store compression summary
            await self._store_compression_summary(session_id, compression_stats)

            logger.info(
                f"Compressed session {session_id}: {compression_stats['compression_ratio']:.2%} ratio"
            )
            return compression_stats

        except Exception as e:
            logger.error(f"Failed to compress session context: {e}")
            return {"status": "error", "error": str(e)}

    def _determine_compression_level(
        self, content: str, memory_type: MemoryType
    ) -> CompressionLevel:
        """Determine appropriate compression level for content"""
        content_size = len(content)

        # Size-based compression decisions
        if content_size < 500:
            return CompressionLevel.NONE
        elif content_size < 2000:
            return CompressionLevel.LOW
        elif content_size < 10000:
            return CompressionLevel.MEDIUM
        elif content_size < 50000:
            return CompressionLevel.HIGH
        else:
            return CompressionLevel.EXTREME

    async def _compress_content(
        self, content: str, memory_type: MemoryType, compression_level: CompressionLevel
    ) -> str:
        """Apply pneumonic compression to content"""
        if compression_level == CompressionLevel.NONE:
            return content

        # Apply compression strategy based on memory type
        strategy = self.compression_strategies.get(memory_type, {}).get(
            "strategy", "semantic_summarization"
        )

        if strategy == "semantic_summarization":
            return await self._semantic_summarization(content, compression_level)
        elif strategy == "state_checkpointing":
            return await self._state_checkpointing(content, compression_level)
        elif strategy == "citation_extraction":
            return await self._citation_extraction(content, compression_level)
        elif strategy == "hierarchical_summarization":
            return await self._hierarchical_summarization(content, compression_level)
        elif strategy == "decision_tree_compression":
            return await self._decision_tree_compression(content, compression_level)
        elif strategy == "dialogue_compression":
            return await self._dialogue_compression(content, compression_level)
        else:
            return await self._default_compression(content, compression_level)

    async def _semantic_summarization(
        self, content: str, level: CompressionLevel
    ) -> str:
        """Semantic summarization compression strategy"""
        if level == CompressionLevel.LOW:
            return content[: int(len(content) * 0.7)]
        elif level == CompressionLevel.MEDIUM:
            return content[: int(len(content) * 0.4)]
        elif level == CompressionLevel.HIGH:
            return content[: int(len(content) * 0.2)]
        else:  # EXTREME
            return content[: int(len(content) * 0.05)]

    async def _state_checkpointing(self, content: str, level: CompressionLevel) -> str:
        """State checkpointing compression for workflow states"""
        try:
            state_data = json.loads(content)

            if level in [CompressionLevel.LOW, CompressionLevel.MEDIUM]:
                # Keep essential state information
                compressed = {
                    "phase": state_data.get("phase"),
                    "status": state_data.get("status"),
                    "key_decisions": state_data.get("key_decisions", [])[:3],
                    "timestamp": state_data.get("timestamp"),
                }
            else:  # HIGH or EXTREME
                # Keep only critical checkpoint data
                compressed = {
                    "phase": state_data.get("phase"),
                    "status": state_data.get("status"),
                    "timestamp": state_data.get("timestamp"),
                }

            return json.dumps(compressed)
        except json.JSONDecodeError:
            return await self._default_compression(content, level)

    async def _citation_extraction(self, content: str, level: CompressionLevel) -> str:
        """Extract and compress legal citations and precedents"""
        # Simple citation extraction (would use more sophisticated NLP in production)
        lines = content.split("\n")
        citations = [
            line
            for line in lines
            if any(
                keyword in line.lower()
                for keyword in ["v.", "case", "court", "decision"]
            )
        ]

        if level == CompressionLevel.LOW:
            return "\n".join(citations[:10])
        elif level == CompressionLevel.MEDIUM:
            return "\n".join(citations[:5])
        else:
            return "\n".join(citations[:2])

    async def _hierarchical_summarization(
        self, content: str, level: CompressionLevel
    ) -> str:
        """Hierarchical summarization for documents"""
        paragraphs = content.split("\n\n")

        if level == CompressionLevel.LOW:
            return "\n\n".join(paragraphs[: len(paragraphs) // 2])
        elif level == CompressionLevel.MEDIUM:
            return "\n\n".join(paragraphs[: len(paragraphs) // 3])
        elif level == CompressionLevel.HIGH:
            return "\n\n".join(paragraphs[:3])
        else:  # EXTREME
            return paragraphs[0] if paragraphs else ""

    async def _decision_tree_compression(
        self, content: str, level: CompressionLevel
    ) -> str:
        """Compress agent decisions into decision trees"""
        # Simplified decision tree extraction
        decisions = [
            line
            for line in content.split("\n")
            if "decision:" in line.lower() or "chose" in line.lower()
        ]

        if level == CompressionLevel.LOW:
            return "\n".join(decisions[:5])
        elif level == CompressionLevel.MEDIUM:
            return "\n".join(decisions[:3])
        else:
            return decisions[0] if decisions else ""

    async def _dialogue_compression(self, content: str, level: CompressionLevel) -> str:
        """Compress conversation dialogues"""
        # Extract key exchanges
        lines = content.split("\n")
        key_lines = [
            line
            for line in lines
            if any(
                indicator in line.lower()
                for indicator in ["user:", "assistant:", "agent:", "system:"]
            )
        ]

        if level == CompressionLevel.LOW:
            return "\n".join(key_lines[:20])
        elif level == CompressionLevel.MEDIUM:
            return "\n".join(key_lines[:10])
        elif level == CompressionLevel.HIGH:
            return "\n".join(key_lines[:5])
        else:  # EXTREME
            return "\n".join(key_lines[:2])

    async def _default_compression(self, content: str, level: CompressionLevel) -> str:
        """Default compression strategy"""
        compression_ratios = {
            CompressionLevel.LOW: 0.7,
            CompressionLevel.MEDIUM: 0.4,
            CompressionLevel.HIGH: 0.2,
            CompressionLevel.EXTREME: 0.05,
        }

        ratio = compression_ratios.get(level, 1.0)
        target_length = int(len(content) * ratio)
        return content[:target_length]

    async def _decompress_content(self, content: str, memory_type: MemoryType) -> str:
        """Decompress content (placeholder for future implementation)"""
        # In a full implementation, this would reverse the compression
        # For now, return the compressed content as-is
        return content

    async def _store_in_mcp(self, memory_entry: MemoryEntry, session_id: str):
        """Store memory entry in MCP server"""
        if "create_entities" in self.mcp_tools:
            entity_data = {
                "name": memory_entry.id,
                "entityType": memory_entry.memory_type.value,
                "observations": [
                    memory_entry.content,
                    f"Compression: {memory_entry.compression_level.name}",
                    f"Timestamp: {memory_entry.timestamp.isoformat()}",
                    f"Session: {session_id}",
                ],
            }

            await self.mcp_tools["create_entities"]({"entities": [entity_data]})

    async def _retrieve_from_mcp(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve memory from MCP server"""
        if "open_nodes" in self.mcp_tools:
            results = await self.mcp_tools["open_nodes"]({"names": [memory_id]})
            return results[0] if results else None
        return None

    async def _search_mcp(self, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search MCP server for memories"""
        if "search_nodes" in self.mcp_tools:
            results = await self.mcp_tools["search_nodes"](
                {"query": search_params["query"]}
            )
            return results[: search_params.get("limit", 10)]
        return []

    async def _update_memory_access(
        self, memory_id: str, access_count: int, last_accessed: datetime
    ):
        """Update memory access statistics in MCP"""
        if "add_observations" in self.mcp_tools:
            observation = (
                f"Accessed {access_count} times, last: {last_accessed.isoformat()}"
            )
            await self.mcp_tools["add_observations"](
                {"observations": [{"entityName": memory_id, "contents": [observation]}]}
            )

    async def _get_session_memories(self, session_id: str) -> List[MemoryEntry]:
        """Get all memories for a session"""
        search_results = await self._search_mcp(
            {"query": f"Session: {session_id}", "limit": 1000}
        )
        memories = []

        for result in search_results:
            memory = self._reconstruct_memory_entry(result)
            if memory:
                memories.append(memory)

        return memories

    def _reconstruct_memory_entry(
        self, mcp_data: Dict[str, Any]
    ) -> Optional[MemoryEntry]:
        """Reconstruct MemoryEntry from MCP data"""
        try:
            observations = mcp_data.get("observations", [])
            if not observations:
                return None

            content = observations[0]
            compression_info = (
                observations[1] if len(observations) > 1 else "Compression: NONE"
            )
            timestamp_info = (
                observations[2]
                if len(observations) > 2
                else f"Timestamp: {datetime.now().isoformat()}"
            )

            # Parse compression level
            compression_name = compression_info.split(": ")[1]
            compression_level = CompressionLevel[compression_name]

            # Parse timestamp
            timestamp_str = timestamp_info.split(": ")[1]
            timestamp = datetime.fromisoformat(timestamp_str)

            # Parse memory type
            memory_type = MemoryType(mcp_data.get("entityType", "case_context"))

            return MemoryEntry(
                id=mcp_data["name"],
                content=content,
                memory_type=memory_type,
                compression_level=compression_level,
                timestamp=timestamp,
            )

        except Exception as e:
            logger.error(f"Failed to reconstruct memory entry: {e}")
            return None

    async def _apply_pneumonic_compression(
        self, memories: List[MemoryEntry], target_ratio: float
    ) -> List[str]:
        """Apply pneumonic compression techniques to memory groups"""
        # Sort memories by access patterns and relevance
        memories.sort(key=lambda m: (m.access_count, m.relevance_score), reverse=True)

        # Calculate how many to compress
        target_count = int(len(memories) * target_ratio)

        compressed_ids = []
        for i in range(target_count, len(memories)):
            memory = memories[i]

            # Apply higher compression to less accessed memories
            new_level = (
                CompressionLevel.HIGH
                if memory.access_count < 3
                else CompressionLevel.MEDIUM
            )

            # Compress content
            compressed_content = await self._compress_content(
                memory.content, memory.memory_type, new_level
            )

            # Update memory
            memory.content = compressed_content
            memory.compression_level = new_level

            # Update in MCP
            await self._store_in_mcp(memory, "compressed_session")
            compressed_ids.append(memory.id)

        return compressed_ids

    async def _store_compression_summary(self, session_id: str, stats: Dict[str, Any]):
        """Store compression summary in MCP"""
        if "create_entities" in self.mcp_tools:
            summary_id = (
                f"compression_summary_{session_id}_{datetime.now().isoformat()}"
            )
            entity_data = {
                "name": summary_id,
                "entityType": "compression_summary",
                "observations": [
                    json.dumps(stats),
                    f"Session: {session_id}",
                    f"Compression ratio: {stats.get('compression_ratio', 0):.2%}",
                ],
            }

            await self.mcp_tools["create_entities"]({"entities": [entity_data]})


class PneumonicMemoryIntegration:
    """Integration layer for MCP memory with LawyerFactory workflow"""

    def __init__(self, mcp_memory_manager: MCPMemoryManager):
        self.memory_manager = mcp_memory_manager
        self.workflow_contexts = {}  # session_id -> context

    async def capture_workflow_context(
        self, session_id: str, phase: str, context_data: Dict[str, Any]
    ) -> str:
        """Capture workflow context for pneumonic compression"""
        context_json = json.dumps(context_data, default=str)

        memory_id = await self.memory_manager.store_memory(
            content=context_json,
            memory_type=MemoryType.WORKFLOW_STATE,
            session_id=session_id,
            semantic_tags=[phase, "workflow", "context"],
            relationships={"phase": phase, "session": session_id},
        )

        self.workflow_contexts[session_id] = memory_id
        return memory_id

    async def compress_case_history(
        self, case_name: str, session_id: str
    ) -> Dict[str, Any]:
        """Compress all case-related memories"""
        return await self.memory_manager.compress_session_context(
            session_id=session_id, compression_target=0.7
        )

    async def retrieve_relevant_context(self, query: str, session_id: str) -> List[str]:
        """Retrieve relevant context for current workflow phase"""
        memories = await self.memory_manager.search_memories(
            query=query,
            memory_types=[MemoryType.CASE_CONTEXT, MemoryType.LEGAL_PRECEDENT],
            session_id=session_id,
            limit=5,
        )

        return [memory.content for memory in memories]

    async def store_agent_decision(
        self, session_id: str, agent_name: str, decision_data: Dict[str, Any]
    ) -> str:
        """Store agent decision for future reference"""
        decision_json = json.dumps(decision_data, default=str)

        return await self.memory_manager.store_memory(
            content=decision_json,
            memory_type=MemoryType.AGENT_DECISION,
            session_id=session_id,
            semantic_tags=[agent_name, "decision", "agent"],
            relationships={"agent": agent_name, "session": session_id},
        )
