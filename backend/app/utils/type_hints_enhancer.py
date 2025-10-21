"""
Type Hints Enhancement Module.

This module provides utilities for adding comprehensive type hints throughout
the codebase to improve code clarity, IDE support, and static analysis.
"""

import ast
import inspect
from typing import (
    Any, Callable, Dict, List, Optional, Tuple, Union, Type, 
    TypeVar, Generic, Protocol, runtime_checkable, get_type_hints,
    Awaitable, AsyncGenerator, Generator, Iterator, AsyncIterator
)
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import json


# Type aliases for common patterns
JSONDict = Dict[str, Any]
JSONList = List[Dict[str, Any]]
PathLike = Union[str, Path]
OptionalStr = Optional[str]
OptionalInt = Optional[int]
OptionalFloat = Optional[float]
OptionalBool = Optional[bool]
OptionalDict = Optional[Dict[str, Any]]
OptionalList = Optional[List[Any]]

# Generic type variables
T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

# Response type aliases
APIResponse = Dict[str, Any]
ErrorResponse = Dict[str, Union[str, int, List[str]]]
SuccessResponse = Dict[str, Union[str, bool, Any]]

# File processing type aliases
FileContent = Union[str, bytes]
FileMetadata = Dict[str, Union[str, int, float, bool]]
ProcessingResult = Tuple[bool, Optional[str], Optional[Dict[str, Any]]]

# Analysis type aliases
RiskScore = float
ConfidenceScore = float
AnalysisMetadata = Dict[str, Union[str, int, float, List[str]]]
ClauseData = Dict[str, Union[str, float, List[str]]]

# Database type aliases
DatabaseRow = Dict[str, Any]
QueryResult = List[DatabaseRow]
TransactionResult = Tuple[bool, Optional[str]]

# Agent type aliases
AgentResult = Dict[str, Any]
AgentConfig = Dict[str, Union[str, int, float, bool]]
AgentMetrics = Dict[str, Union[int, float]]

# WebSocket type aliases
WebSocketMessage = Dict[str, Any]
WebSocketResponse = Dict[str, Union[str, Any]]

# Upload type aliases
ChunkData = bytes
UploadSession = Dict[str, Union[str, int, float, bool]]
UploadProgress = Dict[str, Union[str, int, float]]


@dataclass
class TypeHintConfig:
    """Configuration for type hint enhancement."""
    
    strict_mode: bool = True
    include_return_types: bool = True
    include_parameter_types: bool = True
    use_generic_types: bool = True
    add_optional_for_defaults: bool = True
    preserve_existing_hints: bool = True


class TypeInferenceEngine:
    """Engine for inferring types from code patterns and usage."""
    
    def __init__(self, config: Optional[TypeHintConfig] = None):
        """
        Initialize the type inference engine.
        
        Args:
            config: Configuration for type inference behavior
        """
        self.config = config or TypeHintConfig()
        self._common_patterns = self._build_common_patterns()
    
    def _build_common_patterns(self) -> Dict[str, str]:
        """
        Build dictionary of common variable name patterns and their inferred types.
        
        Returns:
            Dict[str, str]: Mapping of patterns to type hints
        """
        return {
            # ID patterns
            r'.*_id$': 'str',
            r'^id$': 'str',
            r'.*_uuid$': 'str',
            
            # Count/size patterns
            r'.*_count$': 'int',
            r'.*_size$': 'int',
            r'.*_length$': 'int',
            r'^count$': 'int',
            r'^size$': 'int',
            r'^length$': 'int',
            
            # Score/rate patterns
            r'.*_score$': 'float',
            r'.*_rate$': 'float',
            r'.*_ratio$': 'float',
            r'.*_percentage$': 'float',
            
            # Boolean patterns
            r'^is_.*': 'bool',
            r'^has_.*': 'bool',
            r'^can_.*': 'bool',
            r'^should_.*': 'bool',
            r'.*_enabled$': 'bool',
            r'.*_active$': 'bool',
            
            # Time patterns
            r'.*_time$': 'datetime',
            r'.*_date$': 'datetime',
            r'.*_timestamp$': 'datetime',
            r'^created_at$': 'datetime',
            r'^updated_at$': 'datetime',
            
            # File patterns
            r'.*_path$': 'PathLike',
            r'.*_file$': 'PathLike',
            r'.*_filename$': 'str',
            r'.*_content$': 'FileContent',
            
            # Collection patterns
            r'.*_list$': 'List[Any]',
            r'.*_dict$': 'Dict[str, Any]',
            r'.*_data$': 'Dict[str, Any]',
            r'.*_config$': 'Dict[str, Any]',
            r'.*_metadata$': 'Dict[str, Any]',
            r'.*_params$': 'Dict[str, Any]',
            r'.*_options$': 'Dict[str, Any]',
            
            # Response patterns
            r'.*_response$': 'APIResponse',
            r'.*_result$': 'Dict[str, Any]',
            r'.*_output$': 'Dict[str, Any]',
            
            # Error patterns
            r'.*_error$': 'Optional[str]',
            r'.*_exception$': 'Optional[Exception]',
        }
    
    def infer_parameter_type(self, param_name: str, default_value: Any = None) -> str:
        """
        Infer type hint for a parameter based on name and default value.
        
        Args:
            param_name: Name of the parameter
            default_value: Default value of the parameter (if any)
            
        Returns:
            str: Inferred type hint string
        """
        # Check default value first
        if default_value is not None:
            base_type = type(default_value).__name__
            if self.config.add_optional_for_defaults:
                return f"Optional[{base_type}]"
            return base_type
        
        # Check common patterns
        import re
        for pattern, type_hint in self._common_patterns.items():
            if re.match(pattern, param_name):
                return type_hint
        
        # Special cases for common parameter names
        special_cases = {
            'request': 'Request',
            'response': 'Response',
            'session': 'Session',
            'user': 'User',
            'file': 'UploadFile',
            'background_tasks': 'BackgroundTasks',
            'db': 'Session',
            'redis': 'Redis',
            'cache': 'Cache',
            'logger': 'Logger',
            'settings': 'Settings',
        }
        
        if param_name in special_cases:
            return special_cases[param_name]
        
        # Default to Any
        return 'Any'
    
    def infer_return_type(self, func_name: str, func_body: Optional[str] = None) -> str:
        """
        Infer return type for a function based on name and body analysis.
        
        Args:
            func_name: Name of the function
            func_body: Function body source code (optional)
            
        Returns:
            str: Inferred return type hint string
        """
        # Async function patterns
        if func_name.startswith('async_') or (func_body and 'async def' in func_body):
            base_type = self._infer_sync_return_type(func_name, func_body)
            if base_type == 'None':
                return 'Awaitable[None]'
            return f"Awaitable[{base_type}]"
        
        return self._infer_sync_return_type(func_name, func_body)
    
    def _infer_sync_return_type(self, func_name: str, func_body: Optional[str] = None) -> str:
        """
        Infer return type for synchronous functions.
        
        Args:
            func_name: Name of the function
            func_body: Function body source code (optional)
            
        Returns:
            str: Inferred return type hint string
        """
        # Check function name patterns
        if func_name.startswith('get_'):
            if func_name.endswith('_list'):
                return 'List[Dict[str, Any]]'
            elif func_name.endswith('_dict'):
                return 'Dict[str, Any]'
            elif func_name.endswith('_count'):
                return 'int'
            elif func_name.endswith('_status'):
                return 'bool'
            else:
                return 'Optional[Dict[str, Any]]'
        
        elif func_name.startswith('create_'):
            return 'Dict[str, Any]'
        
        elif func_name.startswith('update_'):
            return 'bool'
        
        elif func_name.startswith('delete_'):
            return 'bool'
        
        elif func_name.startswith('validate_'):
            return 'bool'
        
        elif func_name.startswith('process_'):
            return 'Dict[str, Any]'
        
        elif func_name.startswith('analyze_'):
            return 'Dict[str, Any]'
        
        elif func_name.startswith('is_') or func_name.startswith('has_') or func_name.startswith('can_'):
            return 'bool'
        
        elif func_name.startswith('calculate_') or func_name.startswith('compute_'):
            return 'float'
        
        # Check body patterns if available
        if func_body:
            if 'return True' in func_body or 'return False' in func_body:
                return 'bool'
            elif 'return []' in func_body or 'return list(' in func_body:
                return 'List[Any]'
            elif 'return {}' in func_body or 'return dict(' in func_body:
                return 'Dict[str, Any]'
            elif 'return None' in func_body:
                return 'Optional[Any]'
        
        # Default return type
        return 'Any'


class TypeHintApplier:
    """Applies type hints to function and class definitions."""
    
    def __init__(self, inference_engine: Optional[TypeInferenceEngine] = None):
        """
        Initialize the type hint applier.
        
        Args:
            inference_engine: Engine for type inference
        """
        self.inference_engine = inference_engine or TypeInferenceEngine()
    
    def apply_to_function(
        self,
        func: Callable,
        custom_hints: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Generate type hints for a function.
        
        Args:
            func: Function to analyze
            custom_hints: Custom type hints to override inference
            
        Returns:
            Dict[str, str]: Dictionary of parameter names to type hints
        """
        try:
            sig = inspect.signature(func)
            hints = {}
            
            # Get existing type hints
            existing_hints = get_type_hints(func) if hasattr(func, '__annotations__') else {}
            
            # Process parameters
            for param_name, param in sig.parameters.items():
                if param_name in ('self', 'cls'):
                    continue
                
                # Use custom hint if provided
                if custom_hints and param_name in custom_hints:
                    hints[param_name] = custom_hints[param_name]
                # Use existing hint if available and preserve_existing_hints is True
                elif (self.inference_engine.config.preserve_existing_hints and 
                      param_name in existing_hints):
                    hints[param_name] = str(existing_hints[param_name])
                # Infer type hint
                else:
                    default_val = param.default if param.default != param.empty else None
                    hints[param_name] = self.inference_engine.infer_parameter_type(
                        param_name, default_val
                    )
            
            # Process return type
            if self.inference_engine.config.include_return_types:
                if custom_hints and 'return' in custom_hints:
                    hints['return'] = custom_hints['return']
                elif (self.inference_engine.config.preserve_existing_hints and 
                      'return' in existing_hints):
                    hints['return'] = str(existing_hints['return'])
                else:
                    func_source = None
                    try:
                        func_source = inspect.getsource(func)
                    except (OSError, TypeError):
                        pass
                    
                    hints['return'] = self.inference_engine.infer_return_type(
                        func.__name__, func_source
                    )
            
            return hints
            
        except Exception as e:
            return {'error': f"Failed to generate type hints: {e}"}
    
    def generate_typed_signature(
        self,
        func: Callable,
        custom_hints: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Generate a typed function signature string.
        
        Args:
            func: Function to generate signature for
            custom_hints: Custom type hints to override inference
            
        Returns:
            str: Typed function signature
        """
        hints = self.apply_to_function(func, custom_hints)
        
        if 'error' in hints:
            return f"# Error generating signature: {hints['error']}"
        
        try:
            sig = inspect.signature(func)
            params = []
            
            for param_name, param in sig.parameters.items():
                param_str = param_name
                
                # Add type hint
                if param_name in hints:
                    param_str += f": {hints[param_name]}"
                
                # Add default value
                if param.default != param.empty:
                    if isinstance(param.default, str):
                        param_str += f' = "{param.default}"'
                    else:
                        param_str += f" = {param.default}"
                
                params.append(param_str)
            
            # Build signature
            is_async = inspect.iscoroutinefunction(func)
            func_def = "async def" if is_async else "def"
            params_str = ", ".join(params)
            
            signature = f"{func_def} {func.__name__}({params_str})"
            
            # Add return type
            if 'return' in hints:
                signature += f" -> {hints['return']}"
            
            signature += ":"
            
            return signature
            
        except Exception as e:
            return f"# Error generating signature: {e}"


@runtime_checkable
class TypedAPIEndpoint(Protocol):
    """Protocol for typed API endpoint functions."""
    
    def __call__(self, *args: Any, **kwargs: Any) -> Awaitable[APIResponse]:
        """Call the API endpoint function."""
        ...


@runtime_checkable
class TypedServiceMethod(Protocol):
    """Protocol for typed service method functions."""
    
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Call the service method."""
        ...


class CommonTypeHints:
    """Collection of common type hints for the job application tracking system."""
    
    # FastAPI specific types
    FASTAPI_REQUEST = "Request"
    FASTAPI_RESPONSE = "Response"
    FASTAPI_UPLOAD_FILE = "UploadFile"
    FASTAPI_BACKGROUND_TASKS = "BackgroundTasks"
    FASTAPI_WEBSOCKET = "WebSocket"
    FASTAPI_DEPENDS = "Depends"
    
    # Database types
    DATABASE_SESSION = "Session"
    DATABASE_ENGINE = "Engine"
    DATABASE_CONNECTION = "Connection"
    DATABASE_TRANSACTION = "Transaction"
    
    # Redis/Cache types
    REDIS_CLIENT = "Redis"
    CACHE_CLIENT = "Cache"
    
    # File processing types
    FILE_PATH = "PathLike"
    FILE_CONTENT = "FileContent"
    FILE_METADATA = "FileMetadata"
    PROCESSING_RESULT = "ProcessingResult"
    
    # Analysis types
    ANALYSIS_RESULT = "Dict[str, Any]"
    RISK_ASSESSMENT = "Dict[str, Union[str, float, List[str]]]"
    CLAUSE_DATA = "ClauseData"
    AGENT_RESULT = "AgentResult"
    
    # API response types
    API_RESPONSE = "APIResponse"
    SUCCESS_RESPONSE = "SuccessResponse"
    ERROR_RESPONSE = "ErrorResponse"
    
    # Configuration types
    SETTINGS = "Settings"
    CONFIG_DICT = "Dict[str, Any]"
    FEATURE_FLAGS = "Dict[str, bool]"
    
    # Monitoring types
    METRICS = "Dict[str, Union[int, float]]"
    HEALTH_STATUS = "Dict[str, Any]"
    LOG_ENTRY = "Dict[str, Any]"
    
    @classmethod
    def get_all_hints(cls) -> Dict[str, str]:
        """
        Get all common type hints as a dictionary.
        
        Returns:
            Dict[str, str]: All type hints
        """
        return {
            name: getattr(cls, name)
            for name in dir(cls)
            if not name.startswith('_') and isinstance(getattr(cls, name), str)
        }


def enhance_function_with_types(
    func: Callable,
    custom_hints: Optional[Dict[str, str]] = None,
    pattern: Optional[str] = None
) -> str:
    """
    Generate enhanced function definition with type hints and docstring.
    
    Args:
        func: Function to enhance
        custom_hints: Custom type hints to apply
        pattern: Pattern name for predefined type hint sets
        
    Returns:
        str: Enhanced function definition with types and docstring
    """
    applier = TypeHintApplier()
    
    # Apply pattern-specific hints if specified
    if pattern:
        pattern_hints = get_pattern_type_hints(pattern)
        if custom_hints:
            pattern_hints.update(custom_hints)
        custom_hints = pattern_hints
    
    # Generate typed signature
    signature = applier.generate_typed_signature(func, custom_hints)
    
    # Generate docstring if function doesn't have one
    docstring = ""
    if not func.__doc__:
        from .docstring_enhancer import DocstringGenerator
        generator = DocstringGenerator()
        docstring = generator.generate_function_docstring(func)
        # Indent docstring
        docstring_lines = docstring.split('\n')
        indented_docstring = '\n'.join(f"    {line}" for line in docstring_lines)
        docstring = f"\n{indented_docstring}\n"
    
    # Combine signature and docstring
    if docstring:
        return f"{signature}{docstring}    pass  # Implementation here"
    else:
        return f"{signature}\n    pass  # Implementation here"


def get_pattern_type_hints(pattern: str) -> Dict[str, str]:
    """
    Get predefined type hints for common patterns.
    
    Args:
        pattern: Pattern name (api_endpoint, service_method, etc.)
        
    Returns:
        Dict[str, str]: Type hints for the pattern
    """
    patterns = {
        'api_endpoint': {
            'request': CommonTypeHints.FASTAPI_REQUEST,
            'background_tasks': CommonTypeHints.FASTAPI_BACKGROUND_TASKS,
            'file': CommonTypeHints.FASTAPI_UPLOAD_FILE,
            'return': CommonTypeHints.API_RESPONSE
        },
        'service_method': {
            'db': CommonTypeHints.DATABASE_SESSION,
            'cache': CommonTypeHints.CACHE_CLIENT,
            'return': 'Dict[str, Any]'
        },
        'repository_method': {
            'db': CommonTypeHints.DATABASE_SESSION,
            'return': 'Optional[Dict[str, Any]]'
        },
        'agent_method': {
            'return': CommonTypeHints.AGENT_RESULT
        },
        'file_processor': {
            'file_path': CommonTypeHints.FILE_PATH,
            'file_content': CommonTypeHints.FILE_CONTENT,
            'return': CommonTypeHints.PROCESSING_RESULT
        },
        'websocket_handler': {
            'websocket': CommonTypeHints.FASTAPI_WEBSOCKET,
            'return': 'Awaitable[None]'
        }
    }
    
    return patterns.get(pattern, {})


# Export commonly used type aliases for easy importing
__all__ = [
    'JSONDict', 'JSONList', 'PathLike', 'OptionalStr', 'OptionalInt', 'OptionalFloat',
    'OptionalBool', 'OptionalDict', 'OptionalList', 'APIResponse', 'ErrorResponse',
    'SuccessResponse', 'FileContent', 'FileMetadata', 'ProcessingResult', 'RiskScore',
    'ConfidenceScore', 'AnalysisMetadata', 'ClauseData', 'DatabaseRow', 'QueryResult',
    'TransactionResult', 'AgentResult', 'AgentConfig', 'AgentMetrics', 'WebSocketMessage',
    'WebSocketResponse', 'ChunkData', 'UploadSession', 'UploadProgress',
    'TypeHintConfig', 'TypeInferenceEngine', 'TypeHintApplier', 'TypedAPIEndpoint',
    'TypedServiceMethod', 'CommonTypeHints', 'enhance_function_with_types',
    'get_pattern_type_hints'
]