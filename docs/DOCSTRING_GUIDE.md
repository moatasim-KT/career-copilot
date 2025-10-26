# Docstring Style Guide

This document outlines the mandatory docstring requirements for the Career Copilot codebase, updated to reflect the consolidated architecture with streamlined services and components.

## General Guidelines

1. All modules, classes, methods, and functions MUST have docstrings
2. Use Google-style docstring format
3. Include type hints in function/method signatures
4. Document exceptions that may be raised
5. Provide usage examples for complex functions
6. Document consolidated service interfaces and their responsibilities
7. Include migration notes for deprecated import paths

## Format Requirements

### Module Docstrings

```python
"""
Module description goes here.

This module provides functionality for X, Y, Z.
Handles operations such as A, B, C.

Typical usage example:
    from module import MyClass
    obj = MyClass()
    obj.do_something()
"""
```

### Class Docstrings

```python
class MyClass:
    """
    Class description and purpose.
    
    Provides methods for handling X operations.
    Can be used for Y and Z purposes.
    
    Attributes:
        attr1 (type): Description of attr1
        attr2 (type): Description of attr2
    
    Note:
        Important notes about the class usage
    """
```

### Method/Function Docstrings

```python
def my_function(arg1: str, arg2: int, *args, **kwargs) -> bool:
    """
    Short description of function purpose.
    
    Longer description explaining the function's behavior,
    including any important implementation details.
    
    Args:
        arg1 (str): Description of arg1
        arg2 (int): Description of arg2
        *args: Variable length argument list
        **kwargs: Arbitrary keyword arguments
    
    Returns:
        bool: Description of return value
    
    Raises:
        ValueError: When input validation fails
        TypeError: When incorrect types are provided
    
    Example:
        >>> result = my_function("test", 42)
        >>> print(result)
        True
    """
```

### Property Docstrings

```python
@property
def my_property(self) -> str:
    """
    Short description of the property.
    
    Returns:
        str: Description of return value
    """
```

## Special Documentation Requirements

### Async Functions

```python
async def my_async_function(param: str) -> Dict[str, Any]:
    """
    Short description.
    
    Args:
        param (str): Parameter description
    
    Returns:
        Dict[str, Any]: Description of return value
    
    Raises:
        aiohttp.ClientError: When network request fails
    
    Note:
        Include any asyncio-specific usage notes
    """
```

### Generator Functions

```python
def my_generator(items: List[str]) -> Iterator[str]:
    """
    Short description.
    
    Args:
        items (List[str]): Description of items
    
    Yields:
        str: Description of yielded items
    
    Example:
        >>> for item in my_generator(["a", "b"]):
        ...     print(item)
        a
        b
    """
```

## Best Practices

1. Be concise but descriptive
2. Include usage examples for non-obvious functionality
3. Document default values and their significance
4. Explain any side effects
5. Document thread safety considerations
6. Note any performance implications
7. Include warnings about deprecated features

## Common Mistakes to Avoid

1. Missing parameter descriptions
2. Incomplete return value documentation
3. Undocumented exceptions
4. Outdated examples
5. Inconsistent formatting

## Consolidated Architecture Examples

### Consolidated Service Example

```python
from typing import List, Optional, Dict, Any

class AnalyticsService:
    """
    Consolidated analytics service handling all analytics operations.
    
    This service consolidates functionality from multiple analytics modules:
    - analytics.py (core analytics)
    - analytics_data_collection_service.py (data collection)
    - advanced_user_analytics_service.py (user analytics)
    - application_analytics_service.py (application analytics)
    
    The service provides unified interfaces for analytics data collection,
    processing, and reporting across all application domains.
    
    Attributes:
        collectors (Dict[str, AnalyticsCollector]): Domain-specific collectors
        processors (List[AnalyticsProcessor]): Data processing pipelines
        storage_backend (AnalyticsStorage): Analytics data storage
    
    Note:
        This service replaces multiple individual analytics services.
        Use analytics_specialized.py for domain-specific functionality.
    """
    
    def collect_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> bool:
        """
        Collect analytics event data.
        
        Consolidates event collection from multiple sources into a unified
        interface. Handles validation, enrichment, and routing to appropriate
        storage backends.
        
        Args:
            event_type (str): Type of event (e.g., 'user_action', 'system_event')
            data (Dict[str, Any]): Event data payload
            user_id (str, optional): Associated user identifier
            session_id (str, optional): Session identifier for tracking
        
        Returns:
            bool: True if event was successfully collected
        
        Raises:
            ValueError: If event_type is invalid or data is malformed
            AnalyticsError: If collection pipeline fails
        
        Example:
            >>> analytics = AnalyticsService()
            >>> success = analytics.collect_event(
            ...     "job_application_submitted",
            ...     {"job_id": "123", "application_type": "quick_apply"},
            ...     user_id="user_456"
            ... )
            >>> print(success)
            True
        
        Migration Note:
            Replaces individual collect_* methods from:
            - analytics_data_collection_service.collect_user_event()
            - application_analytics_service.track_application()
        """
```

### Configuration Manager Example

```python
from typing import Dict, Any, Optional

class ConfigurationManager:
    """
    Unified configuration management system.
    
    Consolidates configuration functionality from:
    - config.py, config_loader.py, config_manager.py, config_validator.py
    - config_advanced.py (hot reload, templates, integrations)
    
    Provides centralized configuration loading, validation, and management
    with support for environment-specific overrides and hot reloading.
    
    Attributes:
        config_data (Dict[str, Any]): Loaded configuration data
        validators (List[ConfigValidator]): Configuration validators
        hot_reload_enabled (bool): Whether hot reload is active
    """
    
    def load_config(self, env: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration for specified environment.
        
        Args:
            env (str, optional): Environment name. Defaults to current environment.
        
        Returns:
            Dict[str, Any]: Loaded and validated configuration
        
        Raises:
            ConfigurationError: If configuration loading fails
            ValidationError: If configuration validation fails
        
        Migration Note:
            Replaces config_loader.load_configuration() and config_manager.get_config()
        """

def bad_example():
    """Don't do this - missing consolidation context."""
    # Processes data without explaining consolidated architecture
    pass
```

## Consolidated Architecture Documentation Requirements

### Service Consolidation Documentation

When documenting consolidated services, always include:

1. **Consolidation Context**: List original files that were consolidated
2. **Migration Notes**: Document import path changes and deprecated methods
3. **Interface Changes**: Highlight any API changes from consolidation
4. **Backward Compatibility**: Note any compatibility layers or breaking changes

### Import Path Documentation

```python
"""
Analytics Service Module

This module consolidates analytics functionality from multiple services:

Original modules (now consolidated):
- backend.app.services.analytics
- backend.app.services.analytics_data_collection_service  
- backend.app.services.advanced_user_analytics_service
- backend.app.services.application_analytics_service

New import paths:
- from backend.app.services.analytics_service import AnalyticsService
- from backend.app.services.analytics_specialized import DomainAnalytics

Deprecated imports (use compatibility layer):
- from backend.app.services.analytics import Analytics  # Use AnalyticsService
- from backend.app.services.analytics_data_collection_service import DataCollector  # Use AnalyticsService.collect_event
"""
```