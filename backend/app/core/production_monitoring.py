"""
Production monitoring and error tracking system.
"""

import logging
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProductionMonitor:
    """Production monitoring and error tracking."""
    
    def __init__(self):
        self._errors: List[Dict[str, Any]] = []
        self._metrics: Dict[str, Any] = {}
        self._alerts: List[Dict[str, Any]] = []
    
    def log_error(
        self,
        error: Exception,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict] = None
    ):
        """Log an error with context."""
        error_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": type(error).__name__,
            "message": str(error),
            "severity": severity.value,
            "traceback": traceback.format_exc(),
            "context": context or {}
        }
        
        self._errors.append(error_entry)
        logger.error(f"[{severity.value}] {error_entry['error_type']}: {error_entry['message']}")
        
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self._create_alert(error_entry)
    
    def record_metric(self, name: str, value: Any, tags: Optional[Dict] = None):
        """Record a metric."""
        if name not in self._metrics:
            self._metrics[name] = []
        
        self._metrics[name].append({
            "timestamp": datetime.utcnow().isoformat(),
            "value": value,
            "tags": tags or {}
        })
    
    def _create_alert(self, error_entry: Dict):
        """Create an alert for critical errors."""
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "error",
            "severity": error_entry["severity"],
            "message": f"{error_entry['error_type']}: {error_entry['message']}"
        }
        self._alerts.append(alert)
    
    def get_errors(self, limit: int = 100) -> List[Dict]:
        """Get recent errors."""
        return self._errors[-limit:]
    
    def get_metrics(self, name: Optional[str] = None) -> Dict:
        """Get metrics."""
        if name:
            return {name: self._metrics.get(name, [])}
        return self._metrics
    
    def get_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent alerts."""
        return self._alerts[-limit:]
    
    def clear_old_data(self, days: int = 7):
        """Clear old monitoring data."""
        cutoff = datetime.utcnow().timestamp() - (days * 86400)
        
        self._errors = [
            e for e in self._errors
            if datetime.fromisoformat(e["timestamp"]).timestamp() > cutoff
        ]
        
        for name in self._metrics:
            self._metrics[name] = [
                m for m in self._metrics[name]
                if datetime.fromisoformat(m["timestamp"]).timestamp() > cutoff
            ]


_monitor: Optional[ProductionMonitor] = None


def get_production_monitor() -> ProductionMonitor:
    """Get production monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = ProductionMonitor()
    return _monitor
