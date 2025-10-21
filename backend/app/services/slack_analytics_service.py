"""
Slack Analytics and Monitoring Service.
Provides comprehensive analytics, monitoring, and insights for Slack integration.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque

from pydantic import BaseModel, Field

from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class SlackEventType(str, Enum):
    """Slack event types for analytics"""
    MESSAGE_SENT = "message_sent"
    MESSAGE_FAILED = "message_failed"
    INTERACTION = "interaction"
    COMMAND_USED = "command_used"
    USER_JOINED = "user_joined"
    CHANNEL_CREATED = "channel_created"


class AnalyticsMetric(str, Enum):
    """Analytics metric types"""
    COUNT = "count"
    RATE = "rate"
    AVERAGE = "average"
    PERCENTAGE = "percentage"


@dataclass
class SlackEvent:
    """Slack event for analytics tracking"""
    id: str
    event_type: SlackEventType
    timestamp: datetime
    user_id: Optional[str] = None
    channel_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalyticsTimeWindow:
    """Time window for analytics aggregation"""
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    
    def __post_init__(self):
        if not self.end_time:
            self.end_time = self.start_time + timedelta(minutes=self.duration_minutes)


class SlackAnalyticsService:
    """Comprehensive Slack analytics and monitoring service"""
    
    def __init__(self):
        self.events: deque = deque(maxlen=10000)  # Keep last 10k events
        self.metrics_cache = {}
        self.real_time_stats = {
            "messages_sent_today": 0,
            "active_users_today": set(),
            "active_channels_today": set(),
            "commands_used_today": 0,
            "interactions_today": 0,
            "errors_today": 0
        }
        
        # Performance tracking
        self.performance_metrics = {
            "response_times": deque(maxlen=1000),
            "api_calls": deque(maxlen=1000),
            "rate_limit_hits": 0,
            "uptime_start": datetime.now()
        }
        
        # User engagement tracking
        self.user_engagement = defaultdict(lambda: {
            "messages_received": 0,
            "interactions": 0,
            "commands_used": 0,
            "last_active": None,
            "channels": set(),
            "response_rate": 0.0
        })
        
        # Channel analytics
        self.channel_analytics = defaultdict(lambda: {
            "messages_sent": 0,
            "unique_users": set(),
            "interactions": 0,
            "peak_activity_hour": None,
            "activity_by_hour": defaultdict(int)
        })
        
        # Command analytics
        self.command_analytics = defaultdict(lambda: {
            "usage_count": 0,
            "success_rate": 0.0,
            "avg_response_time": 0.0,
            "users": set(),
            "errors": 0
        })
        
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize the analytics service"""
        logger.info("Initializing Slack Analytics Service...")
        
        # Start background tasks
        asyncio.create_task(self._update_real_time_stats())
        asyncio.create_task(self._cleanup_old_data())
        asyncio.create_task(self._generate_periodic_reports())
        
        self.is_initialized = True
        logger.info("Slack Analytics Service initialized successfully")
    
    async def track_event(self, event: SlackEvent):
        """Track a Slack event for analytics"""
        try:
            # Add to events queue
            self.events.append(event)
            
            # Update real-time stats
            await self._update_real_time_metrics(event)
            
            # Update specific analytics
            if event.event_type == SlackEventType.MESSAGE_SENT:
                await self._track_message_event(event)
            elif event.event_type == SlackEventType.INTERACTION:
                await self._track_interaction_event(event)
            elif event.event_type == SlackEventType.COMMAND_USED:
                await self._track_command_event(event)
            
            logger.debug(f"Tracked Slack event: {event.event_type} for user {event.user_id}")
            
        except Exception as e:
            logger.error(f"Error tracking Slack event: {e}")
    
    async def _update_real_time_metrics(self, event: SlackEvent):
        """Update real-time metrics"""
        today = datetime.now().date()
        event_date = event.timestamp.date()
        
        if event_date == today:
            if event.event_type == SlackEventType.MESSAGE_SENT:
                self.real_time_stats["messages_sent_today"] += 1
            elif event.event_type == SlackEventType.COMMAND_USED:
                self.real_time_stats["commands_used_today"] += 1
            elif event.event_type == SlackEventType.INTERACTION:
                self.real_time_stats["interactions_today"] += 1
            elif event.event_type == SlackEventType.MESSAGE_FAILED:
                self.real_time_stats["errors_today"] += 1
            
            if event.user_id:
                self.real_time_stats["active_users_today"].add(event.user_id)
            
            if event.channel_id:
                self.real_time_stats["active_channels_today"].add(event.channel_id)
    
    async def _track_message_event(self, event: SlackEvent):
        """Track message-specific analytics"""
        if event.user_id:
            user_stats = self.user_engagement[event.user_id]
            user_stats["messages_received"] += 1
            user_stats["last_active"] = event.timestamp
            
            if event.channel_id:
                user_stats["channels"].add(event.channel_id)
        
        if event.channel_id:
            channel_stats = self.channel_analytics[event.channel_id]
            channel_stats["messages_sent"] += 1
            
            if event.user_id:
                channel_stats["unique_users"].add(event.user_id)
            
            # Track hourly activity
            hour = event.timestamp.hour
            channel_stats["activity_by_hour"][hour] += 1
            
            # Update peak activity hour
            peak_hour = max(channel_stats["activity_by_hour"].items(), key=lambda x: x[1])[0]
            channel_stats["peak_activity_hour"] = peak_hour
    
    async def _track_interaction_event(self, event: SlackEvent):
        """Track interaction-specific analytics"""
        if event.user_id:
            self.user_engagement[event.user_id]["interactions"] += 1
        
        if event.channel_id:
            self.channel_analytics[event.channel_id]["interactions"] += 1
    
    async def _track_command_event(self, event: SlackEvent):
        """Track command-specific analytics"""
        command = event.metadata.get("command")
        if not command:
            return
        
        cmd_stats = self.command_analytics[command]
        cmd_stats["usage_count"] += 1
        
        if event.user_id:
            cmd_stats["users"].add(event.user_id)
            self.user_engagement[event.user_id]["commands_used"] += 1
        
        # Track response time if available
        response_time = event.metadata.get("response_time")
        if response_time:
            current_avg = cmd_stats["avg_response_time"]
            count = cmd_stats["usage_count"]
            cmd_stats["avg_response_time"] = (current_avg * (count - 1) + response_time) / count
        
        # Track success/failure
        if event.metadata.get("success", True):
            # Update success rate
            total_attempts = cmd_stats["usage_count"] + cmd_stats["errors"]
            cmd_stats["success_rate"] = (cmd_stats["usage_count"] / total_attempts) * 100
        else:
            cmd_stats["errors"] += 1
    
    async def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get real-time dashboard metrics"""
        uptime = datetime.now() - self.performance_metrics["uptime_start"]
        
        return {
            "overview": {
                "messages_sent_today": self.real_time_stats["messages_sent_today"],
                "active_users_today": len(self.real_time_stats["active_users_today"]),
                "active_channels_today": len(self.real_time_stats["active_channels_today"]),
                "commands_used_today": self.real_time_stats["commands_used_today"],
                "interactions_today": self.real_time_stats["interactions_today"],
                "errors_today": self.real_time_stats["errors_today"],
                "uptime_hours": round(uptime.total_seconds() / 3600, 2)
            },
            "performance": {
                "avg_response_time": self._calculate_avg_response_time(),
                "api_calls_per_minute": self._calculate_api_rate(),
                "rate_limit_hits": self.performance_metrics["rate_limit_hits"],
                "success_rate": self._calculate_success_rate()
            },
            "top_channels": await self._get_top_channels(5),
            "top_users": await self._get_top_users(5),
            "top_commands": await self._get_top_commands(5),
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get analytics for a specific user"""
        user_stats = self.user_engagement.get(user_id, {})
        
        if not user_stats:
            return {
                "user_id": user_id,
                "message": "No analytics data available for this user"
            }
        
        # Calculate engagement score
        engagement_score = self._calculate_user_engagement_score(user_stats)
        
        return {
            "user_id": user_id,
            "engagement": {
                "messages_received": user_stats.get("messages_received", 0),
                "interactions": user_stats.get("interactions", 0),
                "commands_used": user_stats.get("commands_used", 0),
                "channels_active": len(user_stats.get("channels", set())),
                "last_active": user_stats.get("last_active").isoformat() if user_stats.get("last_active") else None,
                "engagement_score": engagement_score
            },
            "activity_pattern": await self._get_user_activity_pattern(user_id),
            "preferences": await self._analyze_user_preferences(user_id)
        }
    
    async def get_channel_analytics(self, channel_id: str) -> Dict[str, Any]:
        """Get analytics for a specific channel"""
        channel_stats = self.channel_analytics.get(channel_id, {})
        
        if not channel_stats:
            return {
                "channel_id": channel_id,
                "message": "No analytics data available for this channel"
            }
        
        return {
            "channel_id": channel_id,
            "activity": {
                "messages_sent": channel_stats.get("messages_sent", 0),
                "unique_users": len(channel_stats.get("unique_users", set())),
                "interactions": channel_stats.get("interactions", 0),
                "peak_activity_hour": channel_stats.get("peak_activity_hour"),
                "activity_distribution": dict(channel_stats.get("activity_by_hour", {}))
            },
            "engagement_metrics": await self._calculate_channel_engagement(channel_id),
            "trends": await self._analyze_channel_trends(channel_id)
        }
    
    async def get_command_analytics(self) -> Dict[str, Any]:
        """Get analytics for all commands"""
        command_data = {}
        
        for command, stats in self.command_analytics.items():
            command_data[command] = {
                "usage_count": stats["usage_count"],
                "unique_users": len(stats["users"]),
                "success_rate": round(stats["success_rate"], 2),
                "avg_response_time": round(stats["avg_response_time"], 3),
                "error_count": stats["errors"]
            }
        
        # Sort by usage count
        sorted_commands = sorted(command_data.items(), key=lambda x: x[1]["usage_count"], reverse=True)
        
        return {
            "total_commands": len(command_data),
            "total_usage": sum(stats["usage_count"] for stats in self.command_analytics.values()),
            "commands": dict(sorted_commands),
            "insights": await self._generate_command_insights()
        }
    
    async def generate_analytics_report(
        self,
        start_date: datetime,
        end_date: datetime,
        include_details: bool = False
    ) -> Dict[str, Any]:
        """Generate comprehensive analytics report"""
        # Filter events by date range
        filtered_events = [
            event for event in self.events
            if start_date <= event.timestamp <= end_date
        ]
        
        # Calculate metrics
        total_events = len(filtered_events)
        event_types = defaultdict(int)
        hourly_distribution = defaultdict(int)
        daily_distribution = defaultdict(int)
        
        for event in filtered_events:
            event_types[event.event_type.value] += 1
            hourly_distribution[event.timestamp.hour] += 1
            daily_distribution[event.timestamp.date().isoformat()] += 1
        
        report = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "duration_days": (end_date - start_date).days + 1
            },
            "summary": {
                "total_events": total_events,
                "events_per_day": round(total_events / max(1, (end_date - start_date).days + 1), 2),
                "event_types": dict(event_types),
                "peak_hour": max(hourly_distribution.items(), key=lambda x: x[1])[0] if hourly_distribution else None
            },
            "distributions": {
                "hourly": dict(hourly_distribution),
                "daily": dict(daily_distribution)
            },
            "performance": await self._calculate_period_performance(filtered_events),
            "insights": await self._generate_period_insights(filtered_events),
            "generated_at": datetime.now().isoformat()
        }
        
        if include_details:
            report["detailed_events"] = [
                {
                    "id": event.id,
                    "type": event.event_type.value,
                    "timestamp": event.timestamp.isoformat(),
                    "user_id": event.user_id,
                    "channel_id": event.channel_id,
                    "metadata": event.metadata
                }
                for event in filtered_events[-100:]  # Last 100 events
            ]
        
        return report
    
    async def _get_top_channels(self, limit: int) -> List[Dict[str, Any]]:
        """Get top channels by activity"""
        channels = []
        for channel_id, stats in self.channel_analytics.items():
            channels.append({
                "channel_id": channel_id,
                "messages_sent": stats["messages_sent"],
                "unique_users": len(stats["unique_users"]),
                "interactions": stats["interactions"]
            })
        
        return sorted(channels, key=lambda x: x["messages_sent"], reverse=True)[:limit]
    
    async def _get_top_users(self, limit: int) -> List[Dict[str, Any]]:
        """Get top users by engagement"""
        users = []
        for user_id, stats in self.user_engagement.items():
            engagement_score = self._calculate_user_engagement_score(stats)
            users.append({
                "user_id": user_id,
                "messages_received": stats["messages_received"],
                "interactions": stats["interactions"],
                "commands_used": stats["commands_used"],
                "engagement_score": engagement_score
            })
        
        return sorted(users, key=lambda x: x["engagement_score"], reverse=True)[:limit]
    
    async def _get_top_commands(self, limit: int) -> List[Dict[str, Any]]:
        """Get top commands by usage"""
        commands = []
        for command, stats in self.command_analytics.items():
            commands.append({
                "command": command,
                "usage_count": stats["usage_count"],
                "unique_users": len(stats["users"]),
                "success_rate": round(stats["success_rate"], 2)
            })
        
        return sorted(commands, key=lambda x: x["usage_count"], reverse=True)[:limit]
    
    def _calculate_avg_response_time(self) -> float:
        """Calculate average response time"""
        if not self.performance_metrics["response_times"]:
            return 0.0
        return sum(self.performance_metrics["response_times"]) / len(self.performance_metrics["response_times"])
    
    def _calculate_api_rate(self) -> float:
        """Calculate API calls per minute"""
        if not self.performance_metrics["api_calls"]:
            return 0.0
        
        # Count API calls in the last minute
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        recent_calls = [
            call for call in self.performance_metrics["api_calls"]
            if call > one_minute_ago
        ]
        return len(recent_calls)
    
    def _calculate_success_rate(self) -> float:
        """Calculate overall success rate"""
        total_messages = self.real_time_stats["messages_sent_today"]
        errors = self.real_time_stats["errors_today"]
        
        if total_messages == 0:
            return 100.0
        
        return ((total_messages - errors) / total_messages) * 100
    
    def _calculate_user_engagement_score(self, user_stats: Dict[str, Any]) -> float:
        """Calculate user engagement score"""
        messages = user_stats.get("messages_received", 0)
        interactions = user_stats.get("interactions", 0)
        commands = user_stats.get("commands_used", 0)
        channels = len(user_stats.get("channels", set()))
        
        # Weighted engagement score
        score = (messages * 1) + (interactions * 3) + (commands * 2) + (channels * 0.5)
        return round(score, 2)
    
    async def _get_user_activity_pattern(self, user_id: str) -> Dict[str, Any]:
        """Analyze user activity patterns"""
        user_events = [event for event in self.events if event.user_id == user_id]
        
        if not user_events:
            return {"pattern": "no_data"}
        
        # Analyze activity by hour
        hourly_activity = defaultdict(int)
        for event in user_events:
            hourly_activity[event.timestamp.hour] += 1
        
        # Find peak activity hours
        if hourly_activity:
            peak_hour = max(hourly_activity.items(), key=lambda x: x[1])[0]
            
            # Determine activity pattern
            morning_activity = sum(hourly_activity[h] for h in range(6, 12))
            afternoon_activity = sum(hourly_activity[h] for h in range(12, 18))
            evening_activity = sum(hourly_activity[h] for h in range(18, 24))
            
            if morning_activity > afternoon_activity and morning_activity > evening_activity:
                pattern = "morning_person"
            elif evening_activity > morning_activity and evening_activity > afternoon_activity:
                pattern = "evening_person"
            else:
                pattern = "regular_hours"
        else:
            peak_hour = None
            pattern = "irregular"
        
        return {
            "pattern": pattern,
            "peak_hour": peak_hour,
            "hourly_distribution": dict(hourly_activity),
            "total_events": len(user_events)
        }
    
    async def _analyze_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Analyze user preferences based on behavior"""
        user_events = [event for event in self.events if event.user_id == user_id]
        
        # Analyze command preferences
        command_usage = defaultdict(int)
        interaction_types = defaultdict(int)
        
        for event in user_events:
            if event.event_type == SlackEventType.COMMAND_USED:
                command = event.metadata.get("command")
                if command:
                    command_usage[command] += 1
            elif event.event_type == SlackEventType.INTERACTION:
                interaction_type = event.metadata.get("action_id", "unknown")
                interaction_types[interaction_type] += 1
        
        return {
            "preferred_commands": dict(sorted(command_usage.items(), key=lambda x: x[1], reverse=True)[:3]),
            "interaction_preferences": dict(sorted(interaction_types.items(), key=lambda x: x[1], reverse=True)[:3]),
            "response_style": "interactive" if sum(interaction_types.values()) > sum(command_usage.values()) else "command_based"
        }
    
    async def _calculate_channel_engagement(self, channel_id: str) -> Dict[str, Any]:
        """Calculate channel engagement metrics"""
        channel_stats = self.channel_analytics.get(channel_id, {})
        
        messages = channel_stats.get("messages_sent", 0)
        users = len(channel_stats.get("unique_users", set()))
        interactions = channel_stats.get("interactions", 0)
        
        # Calculate engagement rate
        engagement_rate = (interactions / messages * 100) if messages > 0 else 0
        
        # Calculate messages per user
        messages_per_user = messages / users if users > 0 else 0
        
        return {
            "engagement_rate": round(engagement_rate, 2),
            "messages_per_user": round(messages_per_user, 2),
            "interaction_ratio": round(interactions / messages, 3) if messages > 0 else 0,
            "activity_level": "high" if messages > 50 else "medium" if messages > 10 else "low"
        }
    
    async def _analyze_channel_trends(self, channel_id: str) -> Dict[str, Any]:
        """Analyze channel activity trends"""
        channel_events = [event for event in self.events if event.channel_id == channel_id]
        
        if len(channel_events) < 2:
            return {"trend": "insufficient_data"}
        
        # Analyze trend over time
        daily_counts = defaultdict(int)
        for event in channel_events:
            daily_counts[event.timestamp.date()] += 1
        
        if len(daily_counts) >= 2:
            dates = sorted(daily_counts.keys())
            recent_avg = sum(daily_counts[date] for date in dates[-3:]) / min(3, len(dates))
            older_avg = sum(daily_counts[date] for date in dates[:-3]) / max(1, len(dates) - 3)
            
            if recent_avg > older_avg * 1.2:
                trend = "increasing"
            elif recent_avg < older_avg * 0.8:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "daily_activity": {date.isoformat(): count for date, count in daily_counts.items()},
            "peak_day": max(daily_counts.items(), key=lambda x: x[1])[0].isoformat() if daily_counts else None
        }
    
    async def _generate_command_insights(self) -> List[str]:
        """Generate insights about command usage"""
        insights = []
        
        if not self.command_analytics:
            return ["No command usage data available"]
        
        # Most popular command
        most_used = max(self.command_analytics.items(), key=lambda x: x[1]["usage_count"])
        insights.append(f"Most popular command: /{most_used[0]} ({most_used[1]['usage_count']} uses)")
        
        # Command with highest success rate
        successful_commands = [(cmd, stats) for cmd, stats in self.command_analytics.items() if stats["usage_count"] > 0]
        if successful_commands:
            most_reliable = max(successful_commands, key=lambda x: x[1]["success_rate"])
            insights.append(f"Most reliable command: /{most_reliable[0]} ({most_reliable[1]['success_rate']:.1f}% success rate)")
        
        # Command with most unique users
        if successful_commands:
            most_popular = max(successful_commands, key=lambda x: len(x[1]["users"]))
            insights.append(f"Command with most users: /{most_popular[0]} ({len(most_popular[1]['users'])} unique users)")
        
        return insights
    
    async def _calculate_period_performance(self, events: List[SlackEvent]) -> Dict[str, Any]:
        """Calculate performance metrics for a period"""
        if not events:
            return {"message": "No events in period"}
        
        # Count event types
        event_counts = defaultdict(int)
        for event in events:
            event_counts[event.event_type.value] += 1
        
        # Calculate success rate
        successful_events = event_counts.get("message_sent", 0) + event_counts.get("interaction", 0) + event_counts.get("command_used", 0)
        failed_events = event_counts.get("message_failed", 0)
        total_events = successful_events + failed_events
        
        success_rate = (successful_events / total_events * 100) if total_events > 0 else 0
        
        return {
            "total_events": len(events),
            "success_rate": round(success_rate, 2),
            "events_per_hour": round(len(events) / max(1, (events[-1].timestamp - events[0].timestamp).total_seconds() / 3600), 2),
            "event_distribution": dict(event_counts)
        }
    
    async def _generate_period_insights(self, events: List[SlackEvent]) -> List[str]:
        """Generate insights for a time period"""
        insights = []
        
        if not events:
            return ["No activity in this period"]
        
        # Activity level
        events_per_day = len(events) / max(1, (events[-1].timestamp - events[0].timestamp).days + 1)
        if events_per_day > 100:
            insights.append("High activity period with excellent user engagement")
        elif events_per_day > 50:
            insights.append("Moderate activity period with good user engagement")
        else:
            insights.append("Low activity period - consider engagement strategies")
        
        # Peak activity analysis
        hourly_counts = defaultdict(int)
        for event in events:
            hourly_counts[event.timestamp.hour] += 1
        
        if hourly_counts:
            peak_hour = max(hourly_counts.items(), key=lambda x: x[1])[0]
            insights.append(f"Peak activity hour: {peak_hour}:00")
        
        return insights
    
    async def _update_real_time_stats(self):
        """Background task to update real-time statistics"""
        while True:
            try:
                # Reset daily stats at midnight
                now = datetime.now()
                if now.hour == 0 and now.minute == 0:
                    self.real_time_stats["messages_sent_today"] = 0
                    self.real_time_stats["active_users_today"] = set()
                    self.real_time_stats["active_channels_today"] = set()
                    self.real_time_stats["commands_used_today"] = 0
                    self.real_time_stats["interactions_today"] = 0
                    self.real_time_stats["errors_today"] = 0
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in real-time stats update: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_old_data(self):
        """Background task to cleanup old analytics data"""
        while True:
            try:
                # Clean up old events (keep last 7 days)
                cutoff_time = datetime.now() - timedelta(days=7)
                
                # Clean events deque is automatically limited by maxlen
                
                # Clean up old user engagement data
                for user_id in list(self.user_engagement.keys()):
                    user_stats = self.user_engagement[user_id]
                    if user_stats.get("last_active") and user_stats["last_active"] < cutoff_time:
                        # Archive or remove inactive users
                        if user_stats["messages_received"] == 0:
                            del self.user_engagement[user_id]
                
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(3600)
    
    async def _generate_periodic_reports(self):
        """Background task to generate periodic reports"""
        while True:
            try:
                # Generate daily report at 23:00
                now = datetime.now()
                if now.hour == 23 and now.minute == 0:
                    start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_date = now
                    
                    daily_report = await self.generate_analytics_report(start_date, end_date)
                    logger.info(f"Daily analytics report generated: {daily_report['summary']}")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error generating periodic reports: {e}")
                await asyncio.sleep(3600)
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get analytics service health status"""
        return {
            "healthy": True,
            "service": "slack_analytics",
            "events_tracked": len(self.events),
            "users_tracked": len(self.user_engagement),
            "channels_tracked": len(self.channel_analytics),
            "commands_tracked": len(self.command_analytics),
            "uptime": (datetime.now() - self.performance_metrics["uptime_start"]).total_seconds(),
            "timestamp": datetime.now().isoformat()
        }
    
    async def shutdown(self):
        """Shutdown analytics service"""
        logger.info("Shutting down Slack Analytics Service...")
        
        # Generate final report
        try:
            final_report = await self.generate_analytics_report(
                self.performance_metrics["uptime_start"],
                datetime.now()
            )
            logger.info(f"Final analytics report: {final_report['summary']}")
        except Exception as e:
            logger.error(f"Error generating final report: {e}")
        
        # Clear data
        self.events.clear()
        self.user_engagement.clear()
        self.channel_analytics.clear()
        self.command_analytics.clear()
        
        logger.info("Slack Analytics Service shutdown completed")