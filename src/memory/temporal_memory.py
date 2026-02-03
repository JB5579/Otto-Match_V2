"""
Temporal Memory Manager for Otto.AI
Manages hierarchical memory with consolidation, retrieval, and decay
"""

import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import asyncio
from enum import Enum

from src.memory.zep_client import ZepClient, ConversationContext, Message

# Configure logging
logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memory in the hierarchy"""
    WORKING = "working"      # Last 10 turns
    EPISODIC = "episodic"    # Key decisions and moments
    SEMANTIC = "semantic"    # Generalized preferences


@dataclass
class MemoryFragment:
    """A piece of memory with metadata"""
    content: str
    memory_type: MemoryType
    importance: float  # 0.0 to 1.0
    timestamp: datetime
    decay_factor: float  # How quickly importance decays
    associated_preferences: List[Dict[str, Any]]
    access_count: int = 0
    last_accessed: Optional[datetime] = None


@dataclass
class ConsolidatedMemory:
    """Consolidated memory ready for long-term storage"""
    user_id: str
    preferences: Dict[str, Any]
    key_decisions: List[Dict[str, Any]]
    conversation_summary: str
    confidence_scores: Dict[str, float]
    last_updated: datetime
    version: int = 1


class TemporalMemoryManager:
    """Manages Otto's hierarchical memory system"""

    def __init__(
        self,
        zep_client: ZepClient,
        consolidation_threshold: int = 20,  # Consolidate after 20 turns
        working_memory_size: int = 10
    ):
        self.zep_client = zep_client
        self.consolidation_threshold = consolidation_threshold
        self.working_memory_size = working_memory_size
        self.memory_cache: Dict[str, List[MemoryFragment]] = {}
        self.initialized = False

        # Decay parameters
        self.decay_halflife = timedelta(days=7)  # Importance halves every week
        self.min_importance = 0.1  # Minimum importance before memory is forgotten

    async def initialize(self) -> bool:
        """Initialize the temporal memory manager"""
        try:
            if not self.zep_client.initialized:
                logger.error("Zep client not initialized")
                return False

            self.initialized = True
            logger.info("Temporal memory manager initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize temporal memory manager: {e}")
            return False

    async def add_memory_fragment(
        self,
        user_id: str,
        content: str,
        memory_type: MemoryType,
        importance: float = 0.5,
        associated_preferences: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Add a new memory fragment to the hierarchy"""
        if not self.initialized:
            logger.error("Temporal memory manager not initialized")
            return False

        try:
            # Create memory fragment
            fragment = MemoryFragment(
                content=content,
                memory_type=memory_type,
                importance=importance,
                timestamp=datetime.now(),
                decay_factor=self._calculate_decay_factor(memory_type),
                associated_preferences=associated_preferences or [],
                access_count=0,
                last_accessed=datetime.now()
            )

            # Add to appropriate memory store
            if user_id not in self.memory_cache:
                self.memory_cache[user_id] = []

            self.memory_cache[user_id].append(fragment)

            # Check if consolidation is needed
            await self._check_consolidation_needed(user_id)

            logger.debug(f"Added {memory_type.value} memory fragment for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add memory fragment: {e}")
            return False

    async def get_contextual_memory(
        self,
        user_id: str,
        current_query: str,
        max_memories: int = 50
    ) -> ConversationContext:
        """Retrieve relevant memory based on conversation context"""
        if not self.initialized:
            return ConversationContext(
                working_memory=[],
                episodic_memory=[],
                semantic_memory={},
                user_preferences={}
            )

        try:
            # Get working memory (recent turns)
            working_memory = await self._get_working_memory(user_id)

            # Get episodic memory (key decisions)
            episodic_memory = await self._get_episodic_memory(
                user_id, current_query, max_memories
            )

            # Get semantic memory (generalized preferences)
            semantic_memory = await self._get_semantic_memory(user_id)

            # Extract user preferences
            user_preferences = await self._extract_user_preferences(user_id)

            return ConversationContext(
                working_memory=working_memory,
                episodic_memory=episodic_memory,
                semantic_memory=semantic_memory,
                user_preferences=user_preferences
            )

        except Exception as e:
            logger.error(f"Failed to get contextual memory: {e}")
            return ConversationContext(
                working_memory=[],
                episodic_memory=[],
                semantic_memory={},
                user_preferences={}
            )

    async def update_preference_strength(
        self,
        user_id: str,
        preference_key: str,
        delta: float,
        source: str = "interaction"
    ) -> bool:
        """Update the strength of a preference based on user interaction"""
        if not self.initialized:
            return False

        try:
            # Get current consolidated memory
            consolidated = await self._get_consolidated_memory(user_id)
            if not consolidated:
                return False

            # Update preference strength
            if "preferences" not in consolidated.preferences:
                consolidated.preferences["preferences"] = {}

            if preference_key not in consolidated.preferences["preferences"]:
                consolidated.preferences["preferences"][preference_key] = {
                    "value": None,
                    "strength": 0.5,
                    "confidence": 0.5,
                    "source": source,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }

            pref = consolidated.preferences["preferences"][preference_key]
            pref["strength"] = max(0.0, min(1.0, pref["strength"] + delta))
            pref["updated_at"] = datetime.now().isoformat()
            pref["source"] = source

            # Update confidence based on multiple interactions
            if "interaction_count" not in pref:
                pref["interaction_count"] = 0
            pref["interaction_count"] += 1
            pref["confidence"] = min(1.0, pref["confidence"] + 0.1)

            # Save updated memory
            await self._save_consolidated_memory(user_id, consolidated)

            logger.debug(f"Updated preference {preference_key} strength to {pref['strength']}")
            return True

        except Exception as e:
            logger.error(f"Failed to update preference strength: {e}")
            return False

    async def cross_session_context_reconstruction(
        self,
        user_id: str,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """Reconstruct context from previous sessions"""
        if not self.initialized:
            return {}

        try:
            # Get conversation history from Zep
            cutoff_date = datetime.now() - timedelta(days=days_back)
            conversations = await self.zep_client.search_conversations(
                user_id=user_id,
                query="",
                limit=100,
                metadata_filter={"date_gte": cutoff_date.isoformat()}
            )

            # Extract key themes and preferences
            themes = {}
            preferences = {}
            brands_mentioned = {}
            vehicle_types = {}

            for conv in conversations:
                # Analyze content for themes
                if isinstance(conv, dict) and 'content' in conv:
                    content = conv['content'].lower()

                    # Extract vehicle types
                    if 'suv' in content:
                        vehicle_types['suv'] = vehicle_types.get('suv', 0) + 1
                    if 'truck' in content:
                        vehicle_types['truck'] = vehicle_types.get('truck', 0) + 1
                    if 'sedan' in content:
                        vehicle_types['sedan'] = vehicle_types.get('sedan', 0) + 1
                    if 'electric' in content or 'ev' in content:
                        vehicle_types['electric'] = vehicle_types.get('electric', 0) + 1

                    # Extract brands
                    brands = ['toyota', 'honda', 'ford', 'tesla', 'bmw', 'mercedes', 'audi', 'volkswagen']
                    for brand in brands:
                        if brand in content:
                            brands_mentioned[brand] = brands_mentioned.get(brand, 0) + 1

            # Construct context summary
            context = {
                "last_seen": conversations[-1].get('created_at') if conversations else None,
                "session_count": len(set(c.get('session_id') for c in conversations if isinstance(c, dict))),
                "preferred_vehicle_types": sorted(vehicle_types.items(), key=lambda x: x[1], reverse=True)[:3],
                "mentioned_brands": sorted(brands_mentioned.items(), key=lambda x: x[1], reverse=True)[:5],
                "total_interactions": len(conversations),
                "summary": f"User has had {len(set(c.get('session_id') for c in conversations if isinstance(c, dict)))} conversations in the last {days_back} days"
            }

            return context

        except Exception as e:
            logger.error(f"Failed to reconstruct cross-session context: {e}")
            return {}

    def _calculate_decay_factor(self, memory_type: MemoryType) -> float:
        """Calculate decay factor based on memory type"""
        decay_factors = {
            MemoryType.WORKING: 0.9,    # Retains 90% per day
            MemoryType.EPISODIC: 0.95,  # Retains 95% per day
            MemoryType.SEMANTIC: 0.98   # Retains 98% per day
        }
        return decay_factors.get(memory_type, 0.95)

    async def _get_working_memory(self, user_id: str) -> List[Message]:
        """Get recent conversation turns for working memory"""
        try:
            # Get recent messages from Zep
            history = await self.zep_client.get_conversation_history(
                user_id=user_id,
                limit=self.working_memory_size
            )
            return history
        except Exception as e:
            logger.error(f"Failed to get working memory: {e}")
            return []

    async def _get_episodic_memory(
        self,
        user_id: str,
        current_query: str,
        max_memories: int
    ) -> List[Dict[str, Any]]:
        """Get key episodic memories relevant to current context"""
        if user_id not in self.memory_cache:
            return []

        # Filter and rank episodic memories
        episodic_memories = [
            m for m in self.memory_cache[user_id]
            if m.memory_type == MemoryType.EPISODIC and m.importance > self.min_importance
        ]

        # Apply time decay
        for memory in episodic_memories:
            memory.importance = self._apply_time_decay(memory)

        # Sort by importance
        episodic_memories.sort(key=lambda m: m.importance, reverse=True)

        # Return as dictionaries
        return [
            {
                "content": m.content,
                "importance": m.importance,
                "timestamp": m.timestamp.isoformat(),
                "preferences": m.associated_preferences
            }
            for m in episodic_memories[:max_memories]
        ]

    async def _get_semantic_memory(self, user_id: str) -> Dict[str, Any]:
        """Get generalized semantic memory (preferences and patterns)"""
        if user_id not in self.memory_cache:
            return {}

        # Collect semantic memories
        semantic_memories = [
            m for m in self.memory_cache[user_id]
            if m.memory_type == MemoryType.SEMANTIC
        ]

        # Aggregate into patterns
        patterns = {}
        for memory in semantic_memories:
            memory.importance = self._apply_time_decay(memory)
            if memory.importance > self.min_importance:
                patterns[memory.content] = {
                    "importance": memory.importance,
                    "confidence": min(1.0, memory.access_count / 10),
                    "last_updated": memory.timestamp.isoformat()
                }

        return patterns

    async def _extract_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Extract structured user preferences from memory"""
        consolidated = await self._get_consolidated_memory(user_id)
        if consolidated:
            return consolidated.preferences
        return {}

    async def _check_consolidation_needed(self, user_id: str):
        """Check if memory consolidation is needed"""
        if user_id not in self.memory_cache:
            return

        total_memories = len(self.memory_cache[user_id])
        if total_memories >= self.consolidation_threshold:
            await self._consolidate_memories(user_id)

    async def _consolidate_memories(self, user_id: str):
        """Consolidate memories into long-term storage"""
        if user_id not in self.memory_cache:
            return

        try:
            memories = self.memory_cache[user_id]

            # Identify important memories
            important_memories = [
                m for m in memories
                if self._apply_time_decay(m) > self.min_importance
            ]

            # Group by type
            working = [m for m in important_memories if m.memory_type == MemoryType.WORKING]
            episodic = [m for m in important_memories if m.memory_type == MemoryType.EPISODIC]
            semantic = [m for m in important_memories if m.memory_type == MemoryType.SEMANTIC]

            # Extract preferences
            all_preferences = []
            for m in important_memories:
                all_preferences.extend(m.associated_preferences)

            # Create consolidated memory
            consolidated = ConsolidatedMemory(
                user_id=user_id,
                preferences=self._aggregate_preferences(all_preferences),
                key_decisions=[
                    {
                        "content": m.content,
                        "importance": m.importance,
                        "timestamp": m.timestamp.isoformat()
                    }
                    for m in episodic[:10]  # Top 10 key decisions
                ],
                conversation_summary=self._generate_summary(working),
                confidence_scores=self._calculate_confidence_scores(semantic),
                last_updated=datetime.now(),
                version=1
            )

            # Save consolidated memory
            await self._save_consolidated_memory(user_id, consolidated)

            # Clear old memories (keep recent working memories)
            self.memory_cache[user_id] = working[-self.working_memory_size:]

            logger.info(f"Consolidated {total_memories} memories for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to consolidate memories: {e}")

    def _apply_time_decay(self, memory: MemoryFragment) -> float:
        """Apply time decay to memory importance"""
        days_elapsed = (datetime.now() - memory.timestamp).days
        decayed_importance = memory.importance * (memory.decay_factor ** days_elapsed)
        return max(0.0, decayed_importance)

    def _aggregate_preferences(self, all_preferences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate and deduplicate preferences"""
        aggregated = {}

        for pref in all_preferences:
            key = pref.get("key")
            if not key:
                continue

            if key not in aggregated:
                aggregated[key] = {
                    "value": pref.get("value"),
                    "strength": 0.0,
                    "confidence": 0.0,
                    "sources": []
                }

            # Weight by confidence
            weight = pref.get("confidence", 0.5)
            aggregated[key]["strength"] += pref.get("strength", 0.5) * weight
            aggregated[key]["confidence"] += weight
            aggregated[key]["sources"].append(pref.get("source", "unknown"))

        # Normalize strengths
        for key, pref in aggregated.items():
            if pref["confidence"] > 0:
                pref["strength"] /= pref["confidence"]
                pref["confidence"] = min(1.0, pref["confidence"] / 5)  # Average of up to 5 sources

        return aggregated

    def _generate_summary(self, working_memories: List[MemoryFragment]) -> str:
        """Generate a summary of working memories"""
        if not working_memories:
            return ""

        # Simple extractive summarization
        important_memories = sorted(
            working_memories,
            key=lambda m: m.importance,
            reverse=True
        )[:5]

        return " | ".join([m.content for m in important_memories])

    def _calculate_confidence_scores(self, semantic_memories: List[MemoryFragment]) -> Dict[str, float]:
        """Calculate confidence scores for semantic memories"""
        scores = {}
        for memory in semantic_memories:
            confidence = min(1.0, memory.access_count / 10) * memory.importance
            scores[memory.content] = confidence
        return scores

    async def _save_consolidated_memory(self, user_id: str, consolidated: ConsolidatedMemory):
        """Save consolidated memory to persistent storage"""
        # In a real implementation, this would save to a database
        # For now, we'll store in Zep metadata
        try:
            metadata = {
                "type": "consolidated_memory",
                "version": consolidated.version,
                "data": asdict(consolidated)
            }

            # Store as user metadata in Zep
            await self.zep_client.update_user_metadata(user_id, metadata)

        except Exception as e:
            logger.error(f"Failed to save consolidated memory: {e}")

    async def _get_consolidated_memory(self, user_id: str) -> Optional[ConsolidatedMemory]:
        """Retrieve consolidated memory from storage"""
        try:
            # Get from Zep metadata
            metadata = await self.zep_client.get_user_metadata(user_id)
            if not metadata or metadata.get("type") != "consolidated_memory":
                return None

            data = metadata.get("data", {})
            return ConsolidatedMemory(
                user_id=data.get("user_id", user_id),
                preferences=data.get("preferences", {}),
                key_decisions=data.get("key_decisions", []),
                conversation_summary=data.get("conversation_summary", ""),
                confidence_scores=data.get("confidence_scores", {}),
                last_updated=datetime.fromisoformat(data.get("last_updated", datetime.now().isoformat())),
                version=data.get("version", 1)
            )

        except Exception as e:
            logger.error(f"Failed to get consolidated memory: {e}")
            return None