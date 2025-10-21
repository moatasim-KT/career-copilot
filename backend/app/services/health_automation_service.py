"""
Health automation service for automatic issue resolution.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from ..core.logging import get_logger
from .logging_health_service import get_logging_health_service
from .monitoring_service import get_monitoring_service

logger = get_logger(__name__)

class HealthAutomationService:
    """Service for automated health monitoring and issue resolution."""
    
    def __init__(self):
        self.running = False
        self.check_interval = 60  # Check every minute
        self.automation_enabled = True
        self.last_automation_run = None
        self.automation_history = []
        self.max_history = 100
    
    async def start(self):
        """Start the health automation service."""
        if self.running:
            return
        
        self.running = True
        logger.info("Starting health automation service")
        
        # Start background task
        asyncio.create_task(self._automation_loop())
    
    async def stop(self):
        """Stop the health automation service."""
        self.running = False
        logger.info("Stopping health automation service")
    
    async def _automation_loop(self):
        """Main automation loop."""
        while self.running:
            try:
                if self.automation_enabled:
                    await self._run_automation_checks()
                
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Health automation error: {e}")
                await asyncio.sleep(10)  # Short delay on error
    
    async def _run_automation_checks(self):
        """Run automated health checks and fixes."""
        automation_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "actions_taken": [],
            "issues_detected": [],
            "fixes_applied": []
        }
        
        try:
            # Check and fix logging issues
            logging_fixes = await self._check_and_fix_logging()
            if logging_fixes:
                automation_results["actions_taken"].extend(logging_fixes)
            
            # Check service monitoring
            monitoring_issues = await self._check_service_monitoring()
            if monitoring_issues:
                automation_results["issues_detected"].extend(monitoring_issues)
            
            # Log automation results if any actions were taken
            if automation_results["actions_taken"] or automation_results["issues_detected"]:
                logger.info(
                    "Health automation completed",
                    actions_taken=len(automation_results["actions_taken"]),
                    issues_detected=len(automation_results["issues_detected"])
                )
                
                # Store in history
                self.automation_history.append(automation_results)
                if len(self.automation_history) > self.max_history:
                    self.automation_history = self.automation_history[-self.max_history:]
            
            self.last_automation_run = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Automation check failed: {e}")
            automation_results["error"] = str(e)
    
    async def _check_and_fix_logging(self) -> List[str]:
        """Check and automatically fix logging issues."""
        actions_taken = []
        
        try:
            logging_health = get_logging_health_service()
            health_result = logging_health.perform_comprehensive_health_check()
            
            # Fix missing directories
            if any("does not exist" in issue for issue in health_result.get("critical_issues", [])):
                logger.info("Attempting to create missing log directories")
                creation_results = logging_health.create_missing_directories()
                
                for name, result in creation_results.items():
                    if result["success"]:
                        actions_taken.append(f"Created missing log directory: {name}")
                        logger.info(f"Auto-created log directory: {name}")
            
            # Check for log rotation needs
            rotation_status = health_result.get("checks", {}).get("rotation", {})
            for log_name, status in rotation_status.items():
                if status.get("needs_rotation", False):
                    actions_taken.append(f"Log rotation needed for {log_name} ({status['size_mb']}MB)")
                    # Note: Actual log rotation would be implemented here
                    # For now, just log the need for rotation
                    logger.warning(f"Log file {log_name} needs rotation: {status['size_mb']}MB")
            
        except Exception as e:
            logger.error(f"Logging automation check failed: {e}")
        
        return actions_taken
    
    async def _check_service_monitoring(self) -> List[str]:
        """Check service monitoring for issues."""
        issues_detected = []
        
        try:
            monitoring_service = get_monitoring_service()
            
            # Get current alerts
            alerts = monitoring_service.get_alerts()
            
            for alert in alerts:
                if alert["severity"] == "critical":
                    issues_detected.append(f"Critical alert: {alert['message']}")
                    logger.warning(f"Critical service alert detected: {alert['message']}")
            
            # Check if monitoring is active
            if not monitoring_service.monitoring_active:
                issues_detected.append("Service monitoring is not active")
                logger.warning("Service monitoring is not active")
        
        except Exception as e:
            logger.error(f"Service monitoring check failed: {e}")
            issues_detected.append(f"Service monitoring check failed: {str(e)}")
        
        return issues_detected
    
    def get_automation_status(self) -> Dict[str, Any]:
        """Get current automation status."""
        return {
            "running": self.running,
            "automation_enabled": self.automation_enabled,
            "check_interval_seconds": self.check_interval,
            "last_run": self.last_automation_run.isoformat() if self.last_automation_run else None,
            "history_count": len(self.automation_history),
            "recent_actions": len([
                h for h in self.automation_history[-10:] 
                if h.get("actions_taken")
            ]) if self.automation_history else 0
        }
    
    def get_automation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent automation history."""
        return self.automation_history[-limit:] if self.automation_history else []
    
    def enable_automation(self):
        """Enable automated fixes."""
        self.automation_enabled = True
        logger.info("Health automation enabled")
    
    def disable_automation(self):
        """Disable automated fixes."""
        self.automation_enabled = False
        logger.info("Health automation disabled")
    
    async def run_manual_check(self) -> Dict[str, Any]:
        """Run manual health check and automation."""
        logger.info("Running manual health automation check")
        
        automation_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "manual_run": True,
            "actions_taken": [],
            "issues_detected": [],
            "fixes_applied": []
        }
        
        # Run all checks
        logging_fixes = await self._check_and_fix_logging()
        monitoring_issues = await self._check_service_monitoring()
        
        automation_results["actions_taken"].extend(logging_fixes)
        automation_results["issues_detected"].extend(monitoring_issues)
        
        # Store in history
        self.automation_history.append(automation_results)
        if len(self.automation_history) > self.max_history:
            self.automation_history = self.automation_history[-self.max_history:]
        
        logger.info(
            "Manual health automation completed",
            actions_taken=len(automation_results["actions_taken"]),
            issues_detected=len(automation_results["issues_detected"])
        )
        
        return automation_results

# Global health automation service instance
_health_automation_service = None

def get_health_automation_service() -> HealthAutomationService:
    """Get global health automation service instance."""
    global _health_automation_service
    if _health_automation_service is None:
        _health_automation_service = HealthAutomationService()
    return _health_automation_service