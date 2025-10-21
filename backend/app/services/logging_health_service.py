"""
Logging health monitoring service.
"""

import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..core.logging import get_logger, get_audit_logger

logger = get_logger(__name__)

class LoggingHealthService:
    """Service for monitoring logging system health."""
    
    def __init__(self):
        self.log_paths = {
            "main_log_dir": Path("logs"),
            "backend_log_dir": Path("backend/logs"),
            "audit_log": Path("logs/audit.log"),
            "backend_audit_log": Path("backend/logs/audit.log"),
            "audit_dir": Path("logs/audit"),
            "backend_audit_dir": Path("backend/logs/audit")
        }
        self.last_health_check = None
        self.health_history = []
        self.max_history = 100
    
    def check_log_directories(self) -> Dict[str, Any]:
        """Check log directory health."""
        directory_status = {}
        
        for name, path in self.log_paths.items():
            if "dir" in name:
                status = {
                    "exists": path.exists(),
                    "is_directory": path.is_dir() if path.exists() else False,
                    "writable": False,
                    "readable": False
                }
                
                if path.exists() and path.is_dir():
                    try:
                        status["writable"] = os.access(path, os.W_OK)
                        status["readable"] = os.access(path, os.R_OK)
                    except Exception as e:
                        status["error"] = str(e)
                
                directory_status[name] = status
        
        return directory_status
    
    def check_log_files(self) -> Dict[str, Any]:
        """Check log file health."""
        file_status = {}
        
        for name, path in self.log_paths.items():
            if "log" in name and "dir" not in name:
                status = {
                    "exists": path.exists(),
                    "is_file": path.is_file() if path.exists() else False,
                    "writable": False,
                    "readable": False,
                    "size_bytes": 0,
                    "modified_time": None
                }
                
                if path.exists():
                    try:
                        stat_info = path.stat()
                        status["size_bytes"] = stat_info.st_size
                        status["modified_time"] = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                        status["writable"] = os.access(path, os.W_OK)
                        status["readable"] = os.access(path, os.R_OK)
                    except Exception as e:
                        status["error"] = str(e)
                
                file_status[name] = status
        
        return file_status
    
    def test_logging_functionality(self) -> Dict[str, Any]:
        """Test actual logging functionality."""
        test_results = {}
        
        # Test standard logging
        try:
            test_message = f"Logging test at {datetime.utcnow().isoformat()}"
            logger.info(test_message)
            test_results["standard_logging"] = {
                "success": True,
                "test_message": test_message
            }
        except Exception as e:
            test_results["standard_logging"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test audit logging
        try:
            audit_logger = get_audit_logger()
            audit_logger.log_system_event(
                event_type="logging_health_test",
                component="logging_health_service",
                details={"test": True, "timestamp": datetime.utcnow().isoformat()}
            )
            test_results["audit_logging"] = {
                "success": True,
                "message": "Audit logging test completed"
            }
        except Exception as e:
            test_results["audit_logging"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test structured logging
        try:
            import structlog
            struct_logger = structlog.get_logger(__name__)
            struct_logger.info(
                "Structured logging test",
                test=True,
                timestamp=datetime.utcnow().isoformat(),
                component="logging_health_service"
            )
            test_results["structured_logging"] = {
                "success": True,
                "message": "Structured logging test completed"
            }
        except Exception as e:
            test_results["structured_logging"] = {
                "success": False,
                "error": str(e)
            }
        
        return test_results
    
    def check_log_rotation(self) -> Dict[str, Any]:
        """Check log rotation status."""
        rotation_status = {}
        
        for name, path in self.log_paths.items():
            if "log" in name and "dir" not in name and path.exists():
                try:
                    stat_info = path.stat()
                    size_mb = stat_info.st_size / (1024 * 1024)
                    
                    # Check if log file is getting too large (>100MB)
                    rotation_status[name] = {
                        "size_mb": round(size_mb, 2),
                        "needs_rotation": size_mb > 100,
                        "last_modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                    }
                except Exception as e:
                    rotation_status[name] = {
                        "error": str(e)
                    }
        
        return rotation_status
    
    def get_recent_log_activity(self) -> Dict[str, Any]:
        """Get recent log activity information."""
        activity = {}
        
        for name, path in self.log_paths.items():
            if "log" in name and "dir" not in name and path.exists():
                try:
                    stat_info = path.stat()
                    modified_time = datetime.fromtimestamp(stat_info.st_mtime)
                    time_since_modified = datetime.now() - modified_time
                    
                    activity[name] = {
                        "last_modified": modified_time.isoformat(),
                        "minutes_since_modified": int(time_since_modified.total_seconds() / 60),
                        "recently_active": time_since_modified < timedelta(minutes=5)
                    }
                except Exception as e:
                    activity[name] = {
                        "error": str(e)
                    }
        
        return activity
    
    def perform_comprehensive_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive logging health check."""
        start_time = time.time()
        
        # Run all health checks
        directory_status = self.check_log_directories()
        file_status = self.check_log_files()
        functionality_test = self.test_logging_functionality()
        rotation_status = self.check_log_rotation()
        activity_status = self.get_recent_log_activity()
        
        # Determine overall health
        critical_issues = []
        warnings = []
        
        # Check for critical directory issues
        for name, status in directory_status.items():
            if not status["exists"]:
                critical_issues.append(f"Log directory {name} does not exist")
            elif not status["writable"]:
                critical_issues.append(f"Log directory {name} is not writable")
        
        # Check for functionality issues
        for test_name, result in functionality_test.items():
            if not result["success"]:
                critical_issues.append(f"{test_name} failed: {result.get('error', 'Unknown error')}")
        
        # Check for rotation warnings
        for name, status in rotation_status.items():
            if status.get("needs_rotation", False):
                warnings.append(f"Log file {name} is large ({status['size_mb']}MB) and may need rotation")
        
        # Overall status
        if critical_issues:
            overall_status = "critical"
        elif warnings:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        health_result = {
            "overall_status": overall_status,
            "critical_issues": critical_issues,
            "warnings": warnings,
            "checks": {
                "directories": directory_status,
                "files": file_status,
                "functionality": functionality_test,
                "rotation": rotation_status,
                "activity": activity_status
            },
            "check_duration_ms": round((time.time() - start_time) * 1000, 2),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store in history
        self.health_history.append(health_result)
        if len(self.health_history) > self.max_history:
            self.health_history = self.health_history[-self.max_history:]
        
        self.last_health_check = datetime.utcnow()
        
        return health_result
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get logging health summary."""
        if not self.health_history:
            return {
                "status": "unknown",
                "message": "No health checks performed yet"
            }
        
        latest = self.health_history[-1]
        
        # Calculate health trends
        recent_checks = self.health_history[-10:]  # Last 10 checks
        healthy_count = len([c for c in recent_checks if c["overall_status"] == "healthy"])
        
        return {
            "current_status": latest["overall_status"],
            "last_check": latest["timestamp"],
            "critical_issues_count": len(latest["critical_issues"]),
            "warnings_count": len(latest["warnings"]),
            "health_trend": {
                "recent_checks": len(recent_checks),
                "healthy_checks": healthy_count,
                "health_percentage": round((healthy_count / len(recent_checks)) * 100, 1)
            },
            "check_history_count": len(self.health_history)
        }
    
    def create_missing_directories(self) -> Dict[str, Any]:
        """Create missing log directories."""
        creation_results = {}
        
        for name, path in self.log_paths.items():
            if "dir" in name and not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    creation_results[name] = {
                        "success": True,
                        "message": f"Created directory {path}"
                    }
                    logger.info(f"Created missing log directory: {path}")
                except Exception as e:
                    creation_results[name] = {
                        "success": False,
                        "error": str(e)
                    }
                    logger.error(f"Failed to create log directory {path}: {e}")
        
        return creation_results

# Global logging health service instance
_logging_health_service = None

def get_logging_health_service() -> LoggingHealthService:
    """Get global logging health service instance."""
    global _logging_health_service
    if _logging_health_service is None:
        _logging_health_service = LoggingHealthService()
    return _logging_health_service