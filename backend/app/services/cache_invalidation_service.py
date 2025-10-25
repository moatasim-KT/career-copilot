"""
Cache Invalidation Service for managing cache invalidation strategies.
Provides intelligent cache invalidation based on data changes and business rules.
"""

import asyncio
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass

from .cache_service import get_cache_service, get_document_cache, get_vector_cache
from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()
cache_service = get_cache_service()
document_cache = get_document_cache()
vector_cache = get_vector_cache()


class InvalidationStrategy(Enum):
    """Cache invalidation strategies."""
    IMMEDIATE = "immediate"  # Invalidate immediately
    DELAYED = "delayed"      # Invalidate after a delay
    SCHEDULED = "scheduled"  # Invalidate at scheduled times
    CONDITIONAL = "conditional"  # Invalidate based on conditions
    CASCADE = "cascade"      # Invalidate related cache entries


class InvalidationTrigger(Enum):
    """Cache invalidation triggers."""
    DATA_UPDATE = "data_update"
    USER_ACTION = "user_action"
    TIME_BASED = "time_based"
    DEPENDENCY_CHANGE = "dependency_change"
    MANUAL = "manual"
    SYSTEM_EVENT = "system_event"


@dataclass
class InvalidationRule:
    """Cache invalidation rule."""
    rule_id: str
    name: str
    description: str
    strategy: InvalidationStrategy
    trigger: InvalidationTrigger
    cache_patterns: List[str]
    conditions: Dict[str, Any]
    delay_seconds: int = 0
    enabled: bool = True
    created_at: datetime = None
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0


@dataclass
class InvalidationEvent:
    """Cache invalidation event."""
    event_id: str
    rule_id: str
    trigger: InvalidationTrigger
    cache_patterns: List[str]
    metadata: Dict[str, Any]
    timestamp: datetime
    processed: bool = False
    processed_at: Optional[datetime] = None
    invalidated_keys: List[str] = None
    error: Optional[str] = None


class CacheInvalidationService:
    """Service for managing cache invalidation strategies and rules."""
    
    def __init__(self):
        """Initialize cache invalidation service."""
        self.invalidation_rules: Dict[str, InvalidationRule] = {}
        self.pending_events: List[InvalidationEvent] = []
        self.processed_events: List[InvalidationEvent] = []
        self.dependency_graph: Dict[str, Set[str]] = {}
        
        # Event handlers
        self.event_handlers: Dict[InvalidationTrigger, List[Callable]] = {
            trigger: [] for trigger in InvalidationTrigger
        }
        
        # Initialize default rules
        self._initialize_default_rules()
        
        logger.info("Cache invalidation service initialized")
    
    def _initialize_default_rules(self):
        """Initialize default invalidation rules."""
        # User data update rule
        self.add_rule(InvalidationRule(
            rule_id="user_data_update",
            name="User Data Update",
            description="Invalidate user-related caches when user data is updated",
            strategy=InvalidationStrategy.IMMEDIATE,
            trigger=InvalidationTrigger.DATA_UPDATE,
            cache_patterns=["session:*", "user_settings:*", "user_sessions:*"],
            conditions={"entity_type": "user"}
        ))
        
        # Contract analysis update rule
        self.add_rule(InvalidationRule(
            rule_id="contract_analysis_update",
            name="Contract Analysis Update",
            description="Invalidate analysis caches when contract data is updated",
            strategy=InvalidationStrategy.CASCADE,
            trigger=InvalidationTrigger.DATA_UPDATE,
            cache_patterns=["analysis:*", "document_text:*", "ai_response:*"],
            conditions={"entity_type": "contract"}
        ))
        
        # AI model change rule
        self.add_rule(InvalidationRule(
            rule_id="ai_model_change",
            name="AI Model Change",
            description="Invalidate AI response caches when model configuration changes",
            strategy=InvalidationStrategy.IMMEDIATE,
            trigger=InvalidationTrigger.SYSTEM_EVENT,
            cache_patterns=["ai_response:*"],
            conditions={"event_type": "ai_model_change"}
        ))
        
        # Scheduled cleanup rule
        self.add_rule(InvalidationRule(
            rule_id="scheduled_cleanup",
            name="Scheduled Cleanup",
            description="Periodic cleanup of expired cache entries",
            strategy=InvalidationStrategy.SCHEDULED,
            trigger=InvalidationTrigger.TIME_BASED,
            cache_patterns=["*"],
            conditions={"schedule": "0 2 * * *"},  # Daily at 2 AM
            delay_seconds=0
        ))
        
        # Vector database update rule
        self.add_rule(InvalidationRule(
            rule_id="vector_db_update",
            name="Vector Database Update",
            description="Invalidate vector caches when precedent data is updated",
            strategy=InvalidationStrategy.DELAYED,
            trigger=InvalidationTrigger.DATA_UPDATE,
            cache_patterns=["vector_similar:*", "precedents:*"],
            conditions={"entity_type": "precedent"},
            delay_seconds=300  # 5 minutes delay
        ))
    
    def add_rule(self, rule: InvalidationRule) -> bool:
        """
        Add a cache invalidation rule.
        
        Args:
            rule: Invalidation rule to add
            
        Returns:
            True if added successfully, False otherwise
        """
        try:
            if rule.created_at is None:
                rule.created_at = datetime.utcnow()
            
            self.invalidation_rules[rule.rule_id] = rule
            logger.info(f"Added invalidation rule: {rule.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding invalidation rule: {e}")
            return False
    
    def remove_rule(self, rule_id: str) -> bool:
        """
        Remove a cache invalidation rule.
        
        Args:
            rule_id: ID of the rule to remove
            
        Returns:
            True if removed successfully, False otherwise
        """
        if rule_id in self.invalidation_rules:
            del self.invalidation_rules[rule_id]
            logger.info(f"Removed invalidation rule: {rule_id}")
            return True
        return False
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable an invalidation rule."""
        if rule_id in self.invalidation_rules:
            self.invalidation_rules[rule_id].enabled = True
            logger.info(f"Enabled invalidation rule: {rule_id}")
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable an invalidation rule."""
        if rule_id in self.invalidation_rules:
            self.invalidation_rules[rule_id].enabled = False
            logger.info(f"Disabled invalidation rule: {rule_id}")
            return True
        return False
    
    async def trigger_invalidation(
        self,
        trigger: InvalidationTrigger,
        metadata: Dict[str, Any],
        force: bool = False
    ) -> List[str]:
        """
        Trigger cache invalidation based on an event.
        
        Args:
            trigger: Type of trigger
            metadata: Event metadata
            force: Force invalidation even if conditions don't match
            
        Returns:
            List of event IDs created
        """
        event_ids = []
        
        # Find matching rules
        matching_rules = self._find_matching_rules(trigger, metadata, force)
        
        for rule in matching_rules:
            # Create invalidation event
            event = InvalidationEvent(
                event_id=f"{rule.rule_id}_{int(time.time())}_{len(self.pending_events)}",
                rule_id=rule.rule_id,
                trigger=trigger,
                cache_patterns=rule.cache_patterns.copy(),
                metadata=metadata.copy(),
                timestamp=datetime.utcnow()
            )
            
            # Process based on strategy
            if rule.strategy == InvalidationStrategy.IMMEDIATE:
                await self._process_immediate_invalidation(event, rule)
            elif rule.strategy == InvalidationStrategy.DELAYED:
                await self._schedule_delayed_invalidation(event, rule)
            elif rule.strategy == InvalidationStrategy.CASCADE:
                await self._process_cascade_invalidation(event, rule)
            else:
                # Add to pending events for later processing
                self.pending_events.append(event)
            
            event_ids.append(event.event_id)
            
            # Update rule statistics
            rule.last_triggered = datetime.utcnow()
            rule.trigger_count += 1
        
        return event_ids
    
    def _find_matching_rules(
        self,
        trigger: InvalidationTrigger,
        metadata: Dict[str, Any],
        force: bool = False
    ) -> List[InvalidationRule]:
        """Find invalidation rules that match the trigger and conditions."""
        matching_rules = []
        
        for rule in self.invalidation_rules.values():
            if not rule.enabled and not force:
                continue
            
            if rule.trigger != trigger:
                continue
            
            # Check conditions
            if not force and not self._check_conditions(rule.conditions, metadata):
                continue
            
            matching_rules.append(rule)
        
        return matching_rules
    
    def _check_conditions(self, conditions: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
        """Check if metadata matches rule conditions."""
        for key, expected_value in conditions.items():
            if key not in metadata:
                return False
            
            actual_value = metadata[key]
            
            # Handle different condition types
            if isinstance(expected_value, list):
                if actual_value not in expected_value:
                    return False
            elif isinstance(expected_value, dict):
                # Handle complex conditions (e.g., ranges, patterns)
                if "pattern" in expected_value:
                    import fnmatch
                    if not fnmatch.fnmatch(str(actual_value), expected_value["pattern"]):
                        return False
                elif "range" in expected_value:
                    range_val = expected_value["range"]
                    if not (range_val.get("min", float('-inf')) <= actual_value <= range_val.get("max", float('inf'))):
                        return False
            else:
                if actual_value != expected_value:
                    return False
        
        return True
    
    async def _process_immediate_invalidation(self, event: InvalidationEvent, rule: InvalidationRule):
        """Process immediate cache invalidation."""
        try:
            invalidated_keys = []
            
            for pattern in event.cache_patterns:
                if "*" in pattern:
                    # Pattern-based invalidation
                    count = cache_service.invalidate_pattern(pattern)
                    invalidated_keys.append(f"{pattern} ({count} keys)")
                else:
                    # Direct key invalidation
                    success = cache_service.delete(pattern)
                    if success:
                        invalidated_keys.append(pattern)
            
            event.processed = True
            event.processed_at = datetime.utcnow()
            event.invalidated_keys = invalidated_keys
            
            self.processed_events.append(event)
            logger.info(f"Immediate invalidation completed for rule {rule.rule_id}: {len(invalidated_keys)} patterns")
            
        except Exception as e:
            event.error = str(e)
            logger.error(f"Error in immediate invalidation: {e}")
    
    async def _schedule_delayed_invalidation(self, event: InvalidationEvent, rule: InvalidationRule):
        """Schedule delayed cache invalidation."""
        async def delayed_invalidation():
            await asyncio.sleep(rule.delay_seconds)
            await self._process_immediate_invalidation(event, rule)
        
        # Schedule the invalidation
        asyncio.create_task(delayed_invalidation())
        logger.info(f"Scheduled delayed invalidation for rule {rule.rule_id} in {rule.delay_seconds} seconds")
    
    async def _process_cascade_invalidation(self, event: InvalidationEvent, rule: InvalidationRule):
        """Process cascade cache invalidation with dependency resolution."""
        try:
            invalidated_keys = []
            
            # First, invalidate direct patterns
            for pattern in event.cache_patterns:
                if "*" in pattern:
                    count = cache_service.invalidate_pattern(pattern)
                    invalidated_keys.append(f"{pattern} ({count} keys)")
                else:
                    success = cache_service.delete(pattern)
                    if success:
                        invalidated_keys.append(pattern)
            
            # Then, invalidate dependent caches
            dependent_patterns = self._get_dependent_patterns(event.cache_patterns)
            for pattern in dependent_patterns:
                if "*" in pattern:
                    count = cache_service.invalidate_pattern(pattern)
                    invalidated_keys.append(f"dependent:{pattern} ({count} keys)")
                else:
                    success = cache_service.delete(pattern)
                    if success:
                        invalidated_keys.append(f"dependent:{pattern}")
            
            event.processed = True
            event.processed_at = datetime.utcnow()
            event.invalidated_keys = invalidated_keys
            
            self.processed_events.append(event)
            logger.info(f"Cascade invalidation completed for rule {rule.rule_id}: {len(invalidated_keys)} patterns")
            
        except Exception as e:
            event.error = str(e)
            logger.error(f"Error in cascade invalidation: {e}")
    
    def _get_dependent_patterns(self, patterns: List[str]) -> List[str]:
        """Get cache patterns that depend on the given patterns."""
        dependent_patterns = set()
        
        for pattern in patterns:
            if pattern in self.dependency_graph:
                dependent_patterns.update(self.dependency_graph[pattern])
        
        return list(dependent_patterns)
    
    def add_dependency(self, source_pattern: str, dependent_pattern: str):
        """Add a cache dependency relationship."""
        if source_pattern not in self.dependency_graph:
            self.dependency_graph[source_pattern] = set()
        
        self.dependency_graph[source_pattern].add(dependent_pattern)
        logger.debug(f"Added cache dependency: {source_pattern} -> {dependent_pattern}")
    
    def remove_dependency(self, source_pattern: str, dependent_pattern: str):
        """Remove a cache dependency relationship."""
        if source_pattern in self.dependency_graph:
            self.dependency_graph[source_pattern].discard(dependent_pattern)
            
            # Clean up empty dependency sets
            if not self.dependency_graph[source_pattern]:
                del self.dependency_graph[source_pattern]
    
    async def invalidate_user_caches(self, user_id: str) -> int:
        """Invalidate all caches related to a specific user."""
        patterns = [
            f"session:*{user_id}*",
            f"user_settings:{user_id}",
            f"user_sessions:{user_id}",
            f"analysis:*:{user_id}:*"
        ]
        
        total_invalidated = 0
        for pattern in patterns:
            count = cache_service.invalidate_pattern(pattern)
            total_invalidated += count
        
        logger.info(f"Invalidated {total_invalidated} cache entries for user {user_id}")
        return total_invalidated
    
    async def invalidate_contract_caches(self, contract_hash: str) -> int:
        """Invalidate all caches related to a specific contract."""
        patterns = [
            f"document_text:{contract_hash}",
            f"analysis:*:{contract_hash}",
            f"ai_response:*:{contract_hash}*",
            f"precedents:{contract_hash}"
        ]
        
        total_invalidated = 0
        for pattern in patterns:
            count = cache_service.invalidate_pattern(pattern)
            total_invalidated += count
        
        logger.info(f"Invalidated {total_invalidated} cache entries for contract {contract_hash}")
        return total_invalidated
    
    async def invalidate_ai_caches(self, model_type: Optional[str] = None) -> int:
        """Invalidate AI response caches, optionally filtered by model type."""
        if model_type:
            pattern = f"ai_response:{model_type}:*"
        else:
            pattern = "ai_response:*"
        
        count = cache_service.invalidate_pattern(pattern)
        logger.info(f"Invalidated {count} AI response cache entries")
        return count
    
    def get_invalidation_stats(self) -> Dict[str, Any]:
        """Get cache invalidation statistics."""
        total_rules = len(self.invalidation_rules)
        enabled_rules = sum(1 for rule in self.invalidation_rules.values() if rule.enabled)
        pending_events = len(self.pending_events)
        processed_events = len(self.processed_events)
        
        # Calculate trigger statistics
        trigger_stats = {}
        for rule in self.invalidation_rules.values():
            trigger_type = rule.trigger.value
            if trigger_type not in trigger_stats:
                trigger_stats[trigger_type] = {"count": 0, "total_triggers": 0}
            trigger_stats[trigger_type]["count"] += 1
            trigger_stats[trigger_type]["total_triggers"] += rule.trigger_count
        
        return {
            "total_rules": total_rules,
            "enabled_rules": enabled_rules,
            "pending_events": pending_events,
            "processed_events": processed_events,
            "trigger_statistics": trigger_stats,
            "dependency_relationships": len(self.dependency_graph)
        }
    
    def get_rules(self) -> List[InvalidationRule]:
        """Get all invalidation rules."""
        return list(self.invalidation_rules.values())
    
    def get_recent_events(self, hours: int = 24) -> List[InvalidationEvent]:
        """Get recent invalidation events."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [
            event for event in self.processed_events 
            if event.timestamp >= cutoff_time
        ]


# Global instance
_cache_invalidation_service = None


def get_cache_invalidation_service() -> CacheInvalidationService:
    """Get global cache invalidation service instance."""
    global _cache_invalidation_service
    if _cache_invalidation_service is None:
        _cache_invalidation_service = CacheInvalidationService()
    return _cache_invalidation_service
