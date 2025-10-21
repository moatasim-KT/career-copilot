"""
Cost tracking system for LLM requests with budget limits and monitoring.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from decimal import Decimal, ROUND_HALF_UP
import json

from ..core.logging import get_logger
from ..core.caching import get_cache_manager

logger = get_logger(__name__)
cache_manager = get_cache_manager()


class BudgetPeriod(Enum):
    """Budget period types."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class CostCategory(Enum):
    """Cost categories for tracking."""
    CONTRACT_ANALYSIS = "contract_analysis"
    NEGOTIATION = "negotiation"
    COMMUNICATION = "communication"
    RISK_ASSESSMENT = "risk_assessment"
    LEGAL_PRECEDENT = "legal_precedent"
    GENERAL = "general"


@dataclass
class CostEntry:
    """Individual cost entry for tracking."""
    timestamp: datetime
    provider: str
    model: str
    category: CostCategory
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: Decimal
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "provider": self.provider,
            "model": self.model,
            "category": self.category.value,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost": str(self.cost),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CostEntry":
        """Create from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            provider=data["provider"],
            model=data["model"],
            category=CostCategory(data["category"]),
            prompt_tokens=data["prompt_tokens"],
            completion_tokens=data["completion_tokens"],
            total_tokens=data["total_tokens"],
            cost=Decimal(data["cost"]),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            request_id=data.get("request_id"),
            metadata=data.get("metadata", {})
        )


@dataclass
class BudgetLimit:
    """Budget limit configuration."""
    category: Optional[CostCategory]
    period: BudgetPeriod
    limit: Decimal
    user_id: Optional[str] = None
    alert_threshold: float = 0.8  # Alert at 80% of limit
    hard_limit: bool = True  # Enforce hard limit vs soft warning
    
    def get_cache_key(self) -> str:
        """Get cache key for this budget limit."""
        user_part = f"user:{self.user_id}" if self.user_id else "global"
        category_part = f"cat:{self.category.value}" if self.category else "all"
        return f"budget:{user_part}:{category_part}:{self.period.value}"


@dataclass
class BudgetStatus:
    """Current budget status."""
    limit: BudgetLimit
    current_spend: Decimal
    remaining: Decimal
    percentage_used: float
    period_start: datetime
    period_end: datetime
    alert_triggered: bool
    limit_exceeded: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "category": self.limit.category.value if self.limit.category else None,
            "period": self.limit.period.value,
            "limit": str(self.limit.limit),
            "current_spend": str(self.current_spend),
            "remaining": str(self.remaining),
            "percentage_used": self.percentage_used,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "alert_triggered": self.alert_triggered,
            "limit_exceeded": self.limit_exceeded
        }


class CostTracker:
    """Tracks LLM costs and enforces budget limits."""
    
    def __init__(self):
        """Initialize cost tracker."""
        self.cost_entries: List[CostEntry] = []
        self.budget_limits: List[BudgetLimit] = []
        self.cache_ttl = 300  # 5 minutes
        self._load_default_budgets()
    
    def _load_default_budgets(self):
        """Load default budget limits."""
        # Default daily budgets
        self.budget_limits = [
            # Global daily limit
            BudgetLimit(
                category=None,
                period=BudgetPeriod.DAILY,
                limit=Decimal("50.00"),
                alert_threshold=0.8,
                hard_limit=True
            ),
            # Per-category daily limits
            BudgetLimit(
                category=CostCategory.CONTRACT_ANALYSIS,
                period=BudgetPeriod.DAILY,
                limit=Decimal("30.00"),
                alert_threshold=0.8,
                hard_limit=True
            ),
            BudgetLimit(
                category=CostCategory.NEGOTIATION,
                period=BudgetPeriod.DAILY,
                limit=Decimal("10.00"),
                alert_threshold=0.8,
                hard_limit=False
            ),
            BudgetLimit(
                category=CostCategory.COMMUNICATION,
                period=BudgetPeriod.DAILY,
                limit=Decimal("5.00"),
                alert_threshold=0.8,
                hard_limit=False
            ),
            # Monthly limits
            BudgetLimit(
                category=None,
                period=BudgetPeriod.MONTHLY,
                limit=Decimal("1000.00"),
                alert_threshold=0.9,
                hard_limit=True
            )
        ]
    
    async def record_cost(
        self,
        provider: str,
        model: str,
        category: CostCategory,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CostEntry:
        """
        Record a cost entry.
        
        Args:
            provider: LLM provider name
            model: Model name
            category: Cost category
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            cost: Cost in USD
            user_id: Optional user ID
            session_id: Optional session ID
            request_id: Optional request ID
            metadata: Optional metadata
            
        Returns:
            Created cost entry
        """
        cost_entry = CostEntry(
            timestamp=datetime.utcnow(),
            provider=provider,
            model=model,
            category=category,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost=Decimal(str(cost)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP),
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            metadata=metadata or {}
        )
        
        # Store in memory (in production, this would go to a database)
        self.cost_entries.append(cost_entry)
        
        # Cache recent entries for quick access
        await self._cache_cost_entry(cost_entry)
        
        logger.info(
            f"Recorded cost: {cost_entry.provider}:{cost_entry.model} "
            f"${cost_entry.cost} ({cost_entry.total_tokens} tokens)"
        )
        
        return cost_entry
    
    async def _cache_cost_entry(self, entry: CostEntry):
        """Cache cost entry for quick access."""
        # Cache by various keys for different query patterns
        timestamp_key = f"cost_entry:{entry.timestamp.strftime('%Y%m%d%H')}"
        category_key = f"cost_category:{entry.category.value}:{entry.timestamp.strftime('%Y%m%d')}"
        user_key = f"cost_user:{entry.user_id}:{entry.timestamp.strftime('%Y%m%d')}" if entry.user_id else None
        
        # Get existing entries from cache
        hourly_entries = await cache_manager.async_get(timestamp_key) or []
        hourly_entries.append(entry.to_dict())
        await cache_manager.async_set(timestamp_key, hourly_entries, self.cache_ttl)
        
        category_entries = await cache_manager.async_get(category_key) or []
        category_entries.append(entry.to_dict())
        await cache_manager.async_set(category_key, category_entries, self.cache_ttl)
        
        if user_key:
            user_entries = await cache_manager.async_get(user_key) or []
            user_entries.append(entry.to_dict())
            await cache_manager.async_set(user_key, user_entries, self.cache_ttl)
    
    async def check_budget_limits(
        self,
        category: CostCategory,
        estimated_cost: float,
        user_id: Optional[str] = None
    ) -> List[BudgetStatus]:
        """
        Check if request would exceed budget limits.
        
        Args:
            category: Cost category
            estimated_cost: Estimated cost of the request
            user_id: Optional user ID
            
        Returns:
            List of budget statuses that would be affected
        """
        affected_budgets = []
        
        for budget_limit in self.budget_limits:
            # Check if this budget applies
            if budget_limit.category and budget_limit.category != category:
                continue
            if budget_limit.user_id and budget_limit.user_id != user_id:
                continue
            
            status = await self._get_budget_status(budget_limit)
            
            # Check if adding estimated cost would exceed limit
            projected_spend = status.current_spend + Decimal(str(estimated_cost))
            if projected_spend > budget_limit.limit:
                status.limit_exceeded = True
            
            # Check alert threshold
            projected_percentage = float(projected_spend / budget_limit.limit)
            if projected_percentage >= budget_limit.alert_threshold:
                status.alert_triggered = True
            
            affected_budgets.append(status)
        
        return affected_budgets
    
    async def _get_budget_status(self, budget_limit: BudgetLimit) -> BudgetStatus:
        """Get current status for a budget limit."""
        # Calculate period boundaries
        now = datetime.utcnow()
        period_start, period_end = self._get_period_boundaries(now, budget_limit.period)
        
        # Get current spend for this period
        current_spend = await self._calculate_period_spend(
            budget_limit, period_start, period_end
        )
        
        remaining = budget_limit.limit - current_spend
        percentage_used = float(current_spend / budget_limit.limit) if budget_limit.limit > 0 else 0.0
        
        return BudgetStatus(
            limit=budget_limit,
            current_spend=current_spend,
            remaining=remaining,
            percentage_used=percentage_used,
            period_start=period_start,
            period_end=period_end,
            alert_triggered=percentage_used >= budget_limit.alert_threshold,
            limit_exceeded=current_spend >= budget_limit.limit
        )
    
    def _get_period_boundaries(self, timestamp: datetime, period: BudgetPeriod) -> tuple[datetime, datetime]:
        """Get start and end boundaries for a budget period."""
        if period == BudgetPeriod.HOURLY:
            start = timestamp.replace(minute=0, second=0, microsecond=0)
            end = start + timedelta(hours=1)
        elif period == BudgetPeriod.DAILY:
            start = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif period == BudgetPeriod.WEEKLY:
            days_since_monday = timestamp.weekday()
            start = timestamp.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_since_monday)
            end = start + timedelta(weeks=1)
        elif period == BudgetPeriod.MONTHLY:
            start = timestamp.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1)
            else:
                end = start.replace(month=start.month + 1)
        elif period == BudgetPeriod.YEARLY:
            start = timestamp.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start.replace(year=start.year + 1)
        else:
            raise ValueError(f"Unsupported budget period: {period}")
        
        return start, end
    
    async def _calculate_period_spend(
        self, 
        budget_limit: BudgetLimit, 
        period_start: datetime, 
        period_end: datetime
    ) -> Decimal:
        """Calculate total spend for a budget period."""
        # Try to get from cache first
        cache_key = f"period_spend:{budget_limit.get_cache_key()}:{period_start.isoformat()}"
        cached_spend = await cache_manager.async_get(cache_key)
        if cached_spend is not None:
            return Decimal(str(cached_spend))
        
        total_spend = Decimal('0.00')
        
        # Filter cost entries for this period and budget
        for entry in self.cost_entries:
            if not (period_start <= entry.timestamp < period_end):
                continue
            
            # Check category filter
            if budget_limit.category and entry.category != budget_limit.category:
                continue
            
            # Check user filter
            if budget_limit.user_id and entry.user_id != budget_limit.user_id:
                continue
            
            total_spend += entry.cost
        
        # Cache the result
        await cache_manager.async_set(cache_key, str(total_spend), self.cache_ttl)
        
        return total_spend
    
    async def get_cost_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category: Optional[CostCategory] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get cost summary for specified period and filters.
        
        Args:
            start_date: Start date (default: 24 hours ago)
            end_date: End date (default: now)
            category: Optional category filter
            user_id: Optional user filter
            
        Returns:
            Cost summary dictionary
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=1)
        
        # Filter entries
        filtered_entries = []
        for entry in self.cost_entries:
            if not (start_date <= entry.timestamp <= end_date):
                continue
            if category and entry.category != category:
                continue
            if user_id and entry.user_id != user_id:
                continue
            filtered_entries.append(entry)
        
        # Calculate summary statistics
        total_cost = sum(entry.cost for entry in filtered_entries)
        total_tokens = sum(entry.total_tokens for entry in filtered_entries)
        request_count = len(filtered_entries)
        
        # Group by provider
        by_provider = {}
        for entry in filtered_entries:
            if entry.provider not in by_provider:
                by_provider[entry.provider] = {
                    "cost": Decimal('0.00'),
                    "tokens": 0,
                    "requests": 0
                }
            by_provider[entry.provider]["cost"] += entry.cost
            by_provider[entry.provider]["tokens"] += entry.total_tokens
            by_provider[entry.provider]["requests"] += 1
        
        # Group by category
        by_category = {}
        for entry in filtered_entries:
            cat = entry.category.value
            if cat not in by_category:
                by_category[cat] = {
                    "cost": Decimal('0.00'),
                    "tokens": 0,
                    "requests": 0
                }
            by_category[cat]["cost"] += entry.cost
            by_category[cat]["tokens"] += entry.total_tokens
            by_category[cat]["requests"] += 1
        
        # Convert Decimal to string for JSON serialization
        for provider_data in by_provider.values():
            provider_data["cost"] = str(provider_data["cost"])
        
        for category_data in by_category.values():
            category_data["cost"] = str(category_data["cost"])
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "total_cost": str(total_cost),
                "total_tokens": total_tokens,
                "request_count": request_count,
                "average_cost_per_request": str(total_cost / request_count) if request_count > 0 else "0.00",
                "average_tokens_per_request": total_tokens // request_count if request_count > 0 else 0
            },
            "by_provider": by_provider,
            "by_category": by_category
        }
    
    def add_budget_limit(self, budget_limit: BudgetLimit):
        """Add a new budget limit."""
        self.budget_limits.append(budget_limit)
        logger.info(f"Added budget limit: {budget_limit}")
    
    def remove_budget_limit(self, category: Optional[CostCategory], period: BudgetPeriod, user_id: Optional[str] = None):
        """Remove a budget limit."""
        self.budget_limits = [
            limit for limit in self.budget_limits
            if not (limit.category == category and limit.period == period and limit.user_id == user_id)
        ]
        logger.info(f"Removed budget limit for {category}:{period}:{user_id}")
    
    async def get_all_budget_statuses(self, user_id: Optional[str] = None) -> List[BudgetStatus]:
        """Get status for all applicable budget limits."""
        statuses = []
        for budget_limit in self.budget_limits:
            if budget_limit.user_id and budget_limit.user_id != user_id:
                continue
            status = await self._get_budget_status(budget_limit)
            statuses.append(status)
        return statuses


# Global cost tracker instance
_cost_tracker = None


def get_cost_tracker() -> CostTracker:
    """Get global cost tracker instance."""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker