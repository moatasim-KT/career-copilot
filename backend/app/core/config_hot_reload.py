"""
Configuration Hot-Reloading System for Career Copilot.

This module provides hot-reloading capabilities for configuration changes without
requiring application restart. It includes:
- File system monitoring for configuration changes
- Safe configuration reloading with validation
- Rollback capabilities for invalid configurations
- Event-driven configuration updates
- Thread-safe configuration management
"""

import asyncio
import json
import threading
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    # Create dummy classes for when watchdog is not available
    class FileSystemEventHandler:
        def on_modified(self, event):
            pass
    
    class Observer:
        def __init__(self):
            pass
        def schedule(self, *args, **kwargs):
            pass
        def start(self):
            pass
        def stop(self):
            pass
        def join(self, timeout=None):
            pass

from .logging import get_logger
from .config_validation import validate_startup_configuration, ValidationLevel

logger = get_logger(__name__)


class ReloadTrigger(str, Enum):
    """Configuration reload triggers."""
    FILE_CHANGE = "file_change"
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    API_REQUEST = "api_request"


class ReloadStatus(str, Enum):
    """Configuration reload status."""
    SUCCESS = "success"
    FAILED = "failed"
    VALIDATION_ERROR = "validation_error"
    ROLLBACK = "rollback"
    SKIPPED = "skipped"


@dataclass
class ReloadEvent:
    """Configuration reload event."""
    timestamp: datetime
    trigger: ReloadTrigger
    status: ReloadStatus
    changed_files: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    validation_errors: int = 0
    validation_warnings: int = 0
    reload_duration: float = 0.0
    config_hash: Optional[str] = None


@dataclass
class ConfigurationSnapshot:
    """Configuration snapshot for rollback purposes."""
    timestamp: datetime
    config_data: Dict[str, Any]
    config_hash: str
    source_files: Dict[str, float]  # file_path -> modification_time


class ConfigurationWatcher(FileSystemEventHandler):
    """File system watcher for configuration files."""
    
    def __init__(self, hot_reloader: 'ConfigurationHotReloader'):
        self.hot_reloader = hot_reloader
        self.debounce_time = 1.0  # 1 second debounce
        self.pending_changes: Dict[str, float] = {}
        self.lock = threading.Lock()
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Only watch configuration files
        if not self.hot_reloader.is_watched_file(file_path):
            return
        
        current_time = time.time()
        
        with self.lock:
            self.pending_changes[str(file_path)] = current_time
        
        # Schedule debounced reload
        threading.Timer(self.debounce_time, self._process_pending_changes).start()
    
    def _process_pending_changes(self):
        """Process pending file changes after debounce period."""
        current_time = time.time()
        files_to_reload = []
        
        with self.lock:
            for file_path, change_time in list(self.pending_changes.items()):
                if current_time - change_time >= self.debounce_time:
                    files_to_reload.append(file_path)
                    del self.pending_changes[file_path]
        
        if files_to_reload:
            logger.info(f"Configuration files changed: {files_to_reload}")
            asyncio.create_task(self.hot_reloader.reload_configuration(
                trigger=ReloadTrigger.FILE_CHANGE,
                changed_files=files_to_reload
            ))


class ConfigurationHotReloader:
    """Main configuration hot-reloader."""
    
    def __init__(self, config_manager, environment: str = "development"):
        self.config_manager = config_manager
        self.environment = environment
        self.observer: Optional[Observer] = None
        self.reload_callbacks: List[Callable[[Dict[str, Any], Dict[str, Any]], None]] = []
        self.validation_callbacks: List[Callable[[Dict[str, Any]], bool]] = []
        self.snapshots: List[ConfigurationSnapshot] = []
        self.max_snapshots = 10
        self.reload_history: List[ReloadEvent] = []
        self.max_history = 100
        self.lock = threading.RLock()
        self.enabled = True
        self.safe_mode = True  # Enable rollback on validation errors
        
        # Create initial snapshot
        self._create_snapshot()
    
    def start_watching(self):
        """Start watching configuration files for changes."""
        if not WATCHDOG_AVAILABLE:
            logger.warning("Watchdog not available - configuration hot-reloading disabled")
            return
            
        if self.observer is not None:
            logger.warning("Configuration watcher is already running")
            return
        
        if not self.enabled:
            logger.info("Configuration hot-reloading is disabled")
            return
        
        try:
            self.observer = Observer()
            event_handler = ConfigurationWatcher(self)
            
            # Watch all configuration directories
            watched_paths = self._get_watched_paths()
            
            for path in watched_paths:
                if path.exists():
                    self.observer.schedule(event_handler, str(path), recursive=False)
                    logger.info(f"Watching configuration directory: {path}")
            
            self.observer.start()
            logger.info("Configuration hot-reloading started")
        
        except Exception as e:
            logger.error(f"Failed to start configuration watcher: {e}")
            self.observer = None
    
    def stop_watching(self):
        """Stop watching configuration files."""
        if self.observer is not None:
            try:
                self.observer.stop()
                self.observer.join(timeout=5)
                self.observer = None
                logger.info("Configuration hot-reloading stopped")
            except Exception as e:
                logger.error(f"Error stopping configuration watcher: {e}")
    
    def _get_watched_paths(self) -> Set[Path]:
        """Get all paths that should be watched for configuration changes."""
        paths = set()
        
        # Add configuration source paths
        for source in self.config_manager.config_sources:
            if source.watch and source.path.exists():
                paths.add(source.path.parent)
        
        # Add feature flags path
        try:
            from .feature_flags import get_feature_flag_manager
            ff_manager = get_feature_flag_manager()
            if hasattr(ff_manager.provider, 'config_path'):
                paths.add(ff_manager.provider.config_path.parent)
        except Exception:
            pass
        
        return paths
    
    def is_watched_file(self, file_path: Path) -> bool:
        """Check if a file is being watched for configuration changes."""
        # Check configuration sources
        for source in self.config_manager.config_sources:
            if source.watch and source.path == file_path:
                return True
        
        # Check feature flags file
        if file_path.name == "feature_flags.json":
            return True
        
        # Check for configuration file extensions
        if file_path.suffix in ['.yaml', '.yml', '.json', '.env']:
            return True
        
        return False
    
    async def reload_configuration(self, trigger: ReloadTrigger = ReloadTrigger.MANUAL,
                                 changed_files: Optional[List[str]] = None) -> ReloadEvent:
        """Reload configuration from all sources."""
        start_time = time.time()
        event = ReloadEvent(
            timestamp=datetime.utcnow(),
            trigger=trigger,
            status=ReloadStatus.FAILED,
            changed_files=changed_files or []
        )
        
        try:
            with self.lock:
                logger.info(f"Reloading configuration (trigger: {trigger.value})")
                
                # Store current configuration for rollback
                old_config = self.config_manager.config_data.copy()
                
                # Reload configuration
                new_config = self.config_manager.load_configuration()
                
                # Validate new configuration
                validation_report = validate_startup_configuration(new_config, self.environment)
                event.validation_errors = validation_report.errors
                event.validation_warnings = validation_report.warnings
                
                # Check if reload should proceed
                if validation_report.has_errors() and self.safe_mode:
                    logger.error("Configuration validation failed, rolling back changes")
                    self.config_manager.config_data = old_config
                    event.status = ReloadStatus.VALIDATION_ERROR
                    event.error_message = "Configuration validation failed"
                    return event
                
                # Run custom validation callbacks
                for callback in self.validation_callbacks:
                    try:
                        if not callback(new_config):
                            logger.error("Custom validation callback failed, rolling back changes")
                            self.config_manager.config_data = old_config
                            event.status = ReloadStatus.VALIDATION_ERROR
                            event.error_message = "Custom validation failed"
                            return event
                    except Exception as e:
                        logger.error(f"Validation callback error: {e}")
                        if self.safe_mode:
                            self.config_manager.config_data = old_config
                            event.status = ReloadStatus.VALIDATION_ERROR
                            event.error_message = f"Validation callback error: {e}"
                            return event
                
                # Configuration is valid, create snapshot
                self._create_snapshot()
                
                # Notify reload callbacks
                for callback in self.reload_callbacks:
                    try:
                        callback(old_config, new_config)
                    except Exception as e:
                        logger.error(f"Reload callback error: {e}")
                
                # Update feature flags if changed
                await self._reload_feature_flags_if_changed(changed_files)
                
                event.status = ReloadStatus.SUCCESS
                event.config_hash = self._calculate_config_hash(new_config)
                
                logger.info("Configuration reloaded successfully")
        
        except Exception as e:
            logger.error(f"Configuration reload failed: {e}")
            event.status = ReloadStatus.FAILED
            event.error_message = str(e)
        
        finally:
            event.reload_duration = time.time() - start_time
            self._add_reload_event(event)
        
        return event
    
    async def _reload_feature_flags_if_changed(self, changed_files: Optional[List[str]]):
        """Reload feature flags if the feature flags file was changed."""
        if not changed_files:
            return
        
        feature_flags_changed = any(
            "feature_flags.json" in str(file_path) for file_path in changed_files
        )
        
        if feature_flags_changed:
            try:
                from .feature_flags import get_feature_flag_manager
                ff_manager = get_feature_flag_manager()
                ff_manager.clear_cache()
                logger.info("Feature flags cache cleared due to configuration change")
            except Exception as e:
                logger.error(f"Failed to reload feature flags: {e}")
    
    def _create_snapshot(self):
        """Create a configuration snapshot for rollback purposes."""
        try:
            snapshot = ConfigurationSnapshot(
                timestamp=datetime.utcnow(),
                config_data=self.config_manager.config_data.copy(),
                config_hash=self._calculate_config_hash(self.config_manager.config_data),
                source_files={}
            )
            
            # Record source file modification times
            for source in self.config_manager.config_sources:
                if source.path.exists():
                    snapshot.source_files[str(source.path)] = source.path.stat().st_mtime
            
            with self.lock:
                self.snapshots.append(snapshot)
                
                # Keep only the most recent snapshots
                if len(self.snapshots) > self.max_snapshots:
                    self.snapshots = self.snapshots[-self.max_snapshots:]
            
            logger.debug(f"Created configuration snapshot: {snapshot.config_hash}")
        
        except Exception as e:
            logger.error(f"Failed to create configuration snapshot: {e}")
    
    def rollback_to_snapshot(self, snapshot_index: int = -1) -> bool:
        """Rollback configuration to a previous snapshot."""
        try:
            with self.lock:
                if not self.snapshots:
                    logger.error("No configuration snapshots available for rollback")
                    return False
                
                if abs(snapshot_index) > len(self.snapshots):
                    logger.error(f"Invalid snapshot index: {snapshot_index}")
                    return False
                
                snapshot = self.snapshots[snapshot_index]
                old_config = self.config_manager.config_data.copy()
                
                # Restore configuration
                self.config_manager.config_data = snapshot.config_data.copy()
                
                # Notify callbacks
                for callback in self.reload_callbacks:
                    try:
                        callback(old_config, snapshot.config_data)
                    except Exception as e:
                        logger.error(f"Rollback callback error: {e}")
                
                # Record rollback event
                event = ReloadEvent(
                    timestamp=datetime.utcnow(),
                    trigger=ReloadTrigger.MANUAL,
                    status=ReloadStatus.ROLLBACK,
                    config_hash=snapshot.config_hash
                )
                self._add_reload_event(event)
                
                logger.info(f"Configuration rolled back to snapshot from {snapshot.timestamp}")
                return True
        
        except Exception as e:
            logger.error(f"Configuration rollback failed: {e}")
            return False
    
    def add_reload_callback(self, callback: Callable[[Dict[str, Any], Dict[str, Any]], None]):
        """Add a callback to be called when configuration is reloaded."""
        self.reload_callbacks.append(callback)
        logger.debug(f"Added configuration reload callback: {callback.__name__}")
    
    def add_validation_callback(self, callback: Callable[[Dict[str, Any]], bool]):
        """Add a custom validation callback."""
        self.validation_callbacks.append(callback)
        logger.debug(f"Added configuration validation callback: {callback.__name__}")
    
    def get_reload_history(self, limit: int = 20) -> List[ReloadEvent]:
        """Get recent configuration reload history."""
        with self.lock:
            return self.reload_history[-limit:] if limit > 0 else self.reload_history.copy()
    
    def get_snapshots_info(self) -> List[Dict[str, Any]]:
        """Get information about available configuration snapshots."""
        with self.lock:
            return [
                {
                    'timestamp': snapshot.timestamp.isoformat(),
                    'config_hash': snapshot.config_hash,
                    'source_files': len(snapshot.source_files)
                }
                for snapshot in self.snapshots
            ]
    
    def _add_reload_event(self, event: ReloadEvent):
        """Add a reload event to the history."""
        with self.lock:
            self.reload_history.append(event)
            
            # Keep only the most recent events
            if len(self.reload_history) > self.max_history:
                self.reload_history = self.reload_history[-self.max_history:]
    
    def _calculate_config_hash(self, config: Dict[str, Any]) -> str:
        """Calculate a hash of the configuration for change detection."""
        import hashlib
        config_str = json.dumps(config, sort_keys=True, default=str)
        return hashlib.md5(config_str.encode()).hexdigest()
    
    def enable_hot_reload(self):
        """Enable configuration hot-reloading."""
        self.enabled = True
        if self.observer is None:
            self.start_watching()
        logger.info("Configuration hot-reloading enabled")
    
    def disable_hot_reload(self):
        """Disable configuration hot-reloading."""
        self.enabled = False
        self.stop_watching()
        logger.info("Configuration hot-reloading disabled")
    
    def enable_safe_mode(self):
        """Enable safe mode (rollback on validation errors)."""
        self.safe_mode = True
        logger.info("Configuration safe mode enabled")
    
    def disable_safe_mode(self):
        """Disable safe mode (allow invalid configurations)."""
        self.safe_mode = False
        logger.warning("Configuration safe mode disabled - invalid configurations will be applied")


# Global hot-reloader instance
_hot_reloader: Optional[ConfigurationHotReloader] = None
_reloader_lock = threading.Lock()


def get_configuration_hot_reloader(config_manager=None, environment: str = "development") -> ConfigurationHotReloader:
    """Get the global configuration hot-reloader instance."""
    global _hot_reloader
    
    with _reloader_lock:
        if _hot_reloader is None:
            if config_manager is None:
                from .config import get_config_manager
                config_manager = get_config_manager()
            
            _hot_reloader = ConfigurationHotReloader(config_manager, environment)
            logger.info(f"Created configuration hot-reloader for {environment} environment")
        
        return _hot_reloader


def start_configuration_hot_reload(config_manager=None, environment: str = "development"):
    """Start configuration hot-reloading."""
    hot_reloader = get_configuration_hot_reloader(config_manager, environment)
    hot_reloader.start_watching()


def stop_configuration_hot_reload():
    """Stop configuration hot-reloading."""
    global _hot_reloader
    if _hot_reloader is not None:
        _hot_reloader.stop_watching()


async def reload_configuration_now(trigger: ReloadTrigger = ReloadTrigger.MANUAL) -> ReloadEvent:
    """Manually trigger configuration reload."""
    hot_reloader = get_configuration_hot_reloader()
    return await hot_reloader.reload_configuration(trigger)


def add_configuration_reload_callback(callback: Callable[[Dict[str, Any], Dict[str, Any]], None]):
    """Add a callback for configuration reload events."""
    hot_reloader = get_configuration_hot_reloader()
    hot_reloader.add_reload_callback(callback)