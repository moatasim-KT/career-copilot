# Docstring Style Guide

This document outlines the mandatory docstring requirements for the Career Copilot codebase.

## General Guidelines

1. All modules, classes, methods, and functions MUST have docstrings
2. Use Google-style docstring format
3. Include type hints in function/method signatures
4. Document exceptions that may be raised
5. Provide usage examples for complex functions

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

## Example Usage

### Good Example

```python
from typing import List, Optional

class DataProcessor:
    """
    Processes and validates input data.
    
    This class provides methods for data validation,
    transformation, and error handling.
    
    Attributes:
        schema (Dict[str, type]): Data validation schema
        strict_mode (bool): Enable/disable strict validation
    """
    
    def process_items(
        self,
        items: List[dict],
        validate: bool = True,
        transform: Optional[callable] = None
    ) -> List[dict]:
        """
        Process a list of items according to schema.
        
        Args:
            items (List[dict]): Items to process
            validate (bool, optional): Perform validation.
                Defaults to True.
            transform (callable, optional): Transform function.
                Defaults to None.
        
        Returns:
            List[dict]: Processed items
        
        Raises:
            ValueError: If validation fails
            TypeError: If items are not dictionaries
        
        Example:
            >>> processor = DataProcessor()
            >>> items = [{"name": "test"}]
            >>> result = processor.process_items(items)
        """
```

### Bad Example (Don't Do This)

```python
class DataProcessor:
    # Processes data
    
    def process_items(self, items, validate=True, transform=None):
        # Process items
        pass
```