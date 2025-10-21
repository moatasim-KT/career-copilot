"""
Docstring Enhancement Utility Module.

This module provides utilities for adding and enhancing Google-style docstrings
throughout the codebase, ensuring consistent documentation standards.
"""

import ast
import inspect
import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union


class DocstringTemplate:
    """Template generator for Google-style docstrings."""
    
    @staticmethod
    def function_docstring(
        description: str,
        args: Optional[List[Tuple[str, str, str]]] = None,
        returns: Optional[Tuple[str, str]] = None,
        raises: Optional[List[Tuple[str, str]]] = None,
        examples: Optional[List[str]] = None,
        note: Optional[str] = None,
        warning: Optional[str] = None
    ) -> str:
        """
        Generate a Google-style function docstring.
        
        Args:
            description: Brief description of the function
            args: List of (name, type, description) tuples for arguments
            returns: Tuple of (type, description) for return value
            raises: List of (exception, description) tuples for exceptions
            examples: List of example usage strings
            note: Optional note to include
            warning: Optional warning to include
            
        Returns:
            str: Formatted Google-style docstring
            
        Examples:
            >>> template = DocstringTemplate()
            >>> docstring = template.function_docstring(
            ...     "Calculate the sum of two numbers",
            ...     args=[("a", "int", "First number"), ("b", "int", "Second number")],
            ...     returns=("int", "Sum of a and b")
            ... )
            >>> print(docstring)
        """
        lines = [f'"""', description, '']
        
        if args:
            lines.append('Args:')
            for name, arg_type, desc in args:
                lines.append(f'    {name} ({arg_type}): {desc}')
            lines.append('')
        
        if returns:
            ret_type, ret_desc = returns
            lines.append('Returns:')
            lines.append(f'    {ret_type}: {ret_desc}')
            lines.append('')
        
        if raises:
            lines.append('Raises:')
            for exc_type, exc_desc in raises:
                lines.append(f'    {exc_type}: {exc_desc}')
            lines.append('')
        
        if examples:
            lines.append('Examples:')
            for example in examples:
                for line in example.split('\n'):
                    lines.append(f'    {line}')
            lines.append('')
        
        if note:
            lines.append('Note:')
            lines.append(f'    {note}')
            lines.append('')
        
        if warning:
            lines.append('Warning:')
            lines.append(f'    {warning}')
            lines.append('')
        
        # Remove trailing empty line and close docstring
        if lines[-1] == '':
            lines.pop()
        lines.append('"""')
        
        return '\n'.join(lines)
    
    @staticmethod
    def class_docstring(
        description: str,
        attributes: Optional[List[Tuple[str, str, str]]] = None,
        examples: Optional[List[str]] = None,
        note: Optional[str] = None
    ) -> str:
        """
        Generate a Google-style class docstring.
        
        Args:
            description: Brief description of the class
            attributes: List of (name, type, description) tuples for class attributes
            examples: List of example usage strings
            note: Optional note to include
            
        Returns:
            str: Formatted Google-style class docstring
        """
        lines = [f'"""', description, '']
        
        if attributes:
            lines.append('Attributes:')
            for name, attr_type, desc in attributes:
                lines.append(f'    {name} ({attr_type}): {desc}')
            lines.append('')
        
        if examples:
            lines.append('Examples:')
            for example in examples:
                for line in example.split('\n'):
                    lines.append(f'    {line}')
            lines.append('')
        
        if note:
            lines.append('Note:')
            lines.append(f'    {note}')
            lines.append('')
        
        # Remove trailing empty line and close docstring
        if lines[-1] == '':
            lines.pop()
        lines.append('"""')
        
        return '\n'.join(lines)


class TypeHintAnalyzer:
    """Analyzer for extracting type hints from function signatures."""
    
    @staticmethod
    def extract_function_signature(func: Callable) -> Dict[str, Any]:
        """
        Extract function signature information including type hints.
        
        Args:
            func: Function to analyze
            
        Returns:
            Dict[str, Any]: Dictionary containing signature information
        """
        try:
            sig = inspect.signature(func)
            
            result = {
                'name': func.__name__,
                'parameters': [],
                'return_type': None,
                'is_async': inspect.iscoroutinefunction(func)
            }
            
            for param_name, param in sig.parameters.items():
                param_info = {
                    'name': param_name,
                    'type': None,
                    'default': param.default if param.default != param.empty else None,
                    'kind': param.kind.name
                }
                
                if param.annotation != param.empty:
                    param_info['type'] = TypeHintAnalyzer._format_type_annotation(param.annotation)
                
                result['parameters'].append(param_info)
            
            if sig.return_annotation != sig.empty:
                result['return_type'] = TypeHintAnalyzer._format_type_annotation(sig.return_annotation)
            
            return result
            
        except Exception as e:
            return {'error': str(e), 'name': getattr(func, '__name__', 'unknown')}
    
    @staticmethod
    def _format_type_annotation(annotation: Any) -> str:
        """
        Format type annotation for documentation.
        
        Args:
            annotation: Type annotation object
            
        Returns:
            str: Formatted type string
        """
        if hasattr(annotation, '__name__'):
            return annotation.__name__
        elif hasattr(annotation, '__origin__'):
            # Handle generic types like List[str], Dict[str, int], etc.
            origin = annotation.__origin__
            args = getattr(annotation, '__args__', ())
            
            if origin is Union:
                # Handle Optional and Union types
                if len(args) == 2 and type(None) in args:
                    # Optional type
                    non_none_type = args[0] if args[1] is type(None) else args[1]
                    return f"Optional[{TypeHintAnalyzer._format_type_annotation(non_none_type)}]"
                else:
                    # Union type
                    formatted_args = [TypeHintAnalyzer._format_type_annotation(arg) for arg in args]
                    return f"Union[{', '.join(formatted_args)}]"
            elif args:
                # Generic type with arguments
                formatted_args = [TypeHintAnalyzer._format_type_annotation(arg) for arg in args]
                return f"{origin.__name__}[{', '.join(formatted_args)}]"
            else:
                return origin.__name__
        else:
            return str(annotation)


class DocstringGenerator:
    """Generator for creating comprehensive docstrings based on code analysis."""
    
    def __init__(self):
        """Initialize the docstring generator."""
        self.template = DocstringTemplate()
        self.analyzer = TypeHintAnalyzer()
    
    def generate_function_docstring(
        self,
        func: Callable,
        description: Optional[str] = None,
        custom_args: Optional[Dict[str, str]] = None,
        custom_returns: Optional[str] = None,
        custom_raises: Optional[List[Tuple[str, str]]] = None
    ) -> str:
        """
        Generate a comprehensive docstring for a function.
        
        Args:
            func: Function to generate docstring for
            description: Custom description (if None, generates generic one)
            custom_args: Custom argument descriptions {param_name: description}
            custom_returns: Custom return description
            custom_raises: Custom exception descriptions
            
        Returns:
            str: Generated Google-style docstring
        """
        sig_info = self.analyzer.extract_function_signature(func)
        
        if 'error' in sig_info:
            return f'"""Function docstring generation failed: {sig_info["error"]}"""'
        
        # Generate description if not provided
        if not description:
            description = f"{func.__name__.replace('_', ' ').title()} function."
            if sig_info['is_async']:
                description = f"Asynchronous {description.lower()}"
        
        # Generate args documentation
        args = []
        for param in sig_info['parameters']:
            if param['name'] in ('self', 'cls'):
                continue
            
            param_type = param['type'] or 'Any'
            param_desc = (custom_args or {}).get(param['name'], f"{param['name']} parameter")
            
            if param['default'] is not None:
                param_desc += f" (default: {param['default']})"
            
            args.append((param['name'], param_type, param_desc))
        
        # Generate returns documentation
        returns = None
        if sig_info['return_type']:
            return_desc = custom_returns or "Function return value"
            returns = (sig_info['return_type'], return_desc)
        
        # Generate raises documentation
        raises = custom_raises or []
        
        return self.template.function_docstring(
            description=description,
            args=args if args else None,
            returns=returns,
            raises=raises if raises else None
        )
    
    def generate_class_docstring(
        self,
        cls: Type,
        description: Optional[str] = None,
        custom_attributes: Optional[Dict[str, Tuple[str, str]]] = None
    ) -> str:
        """
        Generate a comprehensive docstring for a class.
        
        Args:
            cls: Class to generate docstring for
            description: Custom description (if None, generates generic one)
            custom_attributes: Custom attribute descriptions {attr_name: (type, description)}
            
        Returns:
            str: Generated Google-style class docstring
        """
        # Generate description if not provided
        if not description:
            description = f"{cls.__name__} class for handling {cls.__name__.lower()} operations."
        
        # Analyze class attributes
        attributes = []
        if custom_attributes:
            for attr_name, (attr_type, attr_desc) in custom_attributes.items():
                attributes.append((attr_name, attr_type, attr_desc))
        
        # Try to extract attributes from __init__ method
        if hasattr(cls, '__init__'):
            init_sig = self.analyzer.extract_function_signature(cls.__init__)
            for param in init_sig.get('parameters', []):
                if param['name'] not in ('self', 'cls') and param['name'] not in [attr[0] for attr in attributes]:
                    param_type = param['type'] or 'Any'
                    param_desc = f"Instance attribute initialized from {param['name']} parameter"
                    attributes.append((param['name'], param_type, param_desc))
        
        return self.template.class_docstring(
            description=description,
            attributes=attributes if attributes else None
        )


def enhance_api_endpoint_docstring(
    endpoint_func: Callable,
    summary: str,
    description: str,
    tags: Optional[List[str]] = None,
    responses: Optional[Dict[int, Dict[str, str]]] = None
) -> str:
    """
    Generate enhanced docstring for FastAPI endpoint functions.
    
    Args:
        endpoint_func: FastAPI endpoint function
        summary: Brief summary of the endpoint
        description: Detailed description of the endpoint functionality
        tags: List of OpenAPI tags for the endpoint
        responses: Dictionary of status codes and their descriptions
        
    Returns:
        str: Enhanced docstring with OpenAPI metadata
    """
    generator = DocstringGenerator()
    
    # Get basic function signature
    sig_info = generator.analyzer.extract_function_signature(endpoint_func)
    
    # Build comprehensive description
    full_description = f"{summary}\n\n{description}"
    
    if tags:
        full_description += f"\n\nTags: {', '.join(tags)}"
    
    # Generate args from function signature
    args = []
    for param in sig_info.get('parameters', []):
        if param['name'] in ('request', 'background_tasks'):
            continue
        
        param_type = param['type'] or 'Any'
        param_desc = f"{param['name']} parameter"
        
        # Add more specific descriptions based on common parameter names
        if 'file' in param['name'].lower():
            param_desc = "File to be uploaded or processed"
        elif 'id' in param['name'].lower():
            param_desc = f"Unique identifier for {param['name'].replace('_id', '').replace('id', 'resource')}"
        elif param['name'] in ('limit', 'page_size'):
            param_desc = "Maximum number of items to return"
        elif param['name'] in ('offset', 'page'):
            param_desc = "Number of items to skip for pagination"
        
        if param['default'] is not None:
            param_desc += f" (default: {param['default']})"
        
        args.append((param['name'], param_type, param_desc))
    
    # Generate returns documentation
    returns = None
    if sig_info.get('return_type'):
        returns = (sig_info['return_type'], "API response with operation results")
    
    # Generate raises documentation for common HTTP exceptions
    raises = [
        ("HTTPException", "For various HTTP error conditions (400, 401, 403, 404, 422, 500)"),
        ("ValidationError", "When request validation fails"),
        ("SecurityError", "When security validation fails")
    ]
    
    # Add response documentation
    response_info = []
    if responses:
        response_info.append("HTTP Status Codes:")
        for status_code, response_data in responses.items():
            description = response_data.get('description', f'HTTP {status_code} response')
            response_info.append(f"    {status_code}: {description}")
    
    examples = []
    if response_info:
        examples.append('\n'.join(response_info))
    
    return generator.template.function_docstring(
        description=full_description,
        args=args if args else None,
        returns=returns,
        raises=raises,
        examples=examples if examples else None
    )


def add_type_hints_to_function(func_source: str, type_hints: Dict[str, str]) -> str:
    """
    Add type hints to a function source code string.
    
    Args:
        func_source: Source code of the function
        type_hints: Dictionary mapping parameter names to type hint strings
        
    Returns:
        str: Function source code with added type hints
    """
    try:
        # Parse the function source
        tree = ast.parse(func_source)
        
        # Find the function definition
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Add type hints to parameters
                for arg in node.args.args:
                    if arg.arg in type_hints:
                        # This is a simplified approach - in practice, you'd need
                        # more sophisticated AST manipulation
                        pass
        
        # For now, return the original source with a comment
        # Full implementation would require more complex AST manipulation
        return func_source + "\n# TODO: Add type hints programmatically"
        
    except Exception as e:
        return func_source + f"\n# Error adding type hints: {e}"


# Predefined docstring templates for common patterns
COMMON_DOCSTRING_PATTERNS = {
    'api_endpoint': {
        'template': enhance_api_endpoint_docstring,
        'description': 'Template for FastAPI endpoint functions'
    },
    'service_method': {
        'description': 'Business logic method in a service class',
        'raises': [
            ('ValidationError', 'When input validation fails'),
            ('ServiceError', 'When service operation fails')
        ]
    },
    'repository_method': {
        'description': 'Data access method in a repository class',
        'raises': [
            ('DatabaseError', 'When database operation fails'),
            ('NotFoundError', 'When requested resource is not found')
        ]
    },
    'utility_function': {
        'description': 'Utility function for common operations',
        'note': 'This is a utility function that can be used across the application'
    }
}


def get_docstring_pattern(pattern_name: str) -> Dict[str, Any]:
    """
    Get predefined docstring pattern configuration.
    
    Args:
        pattern_name: Name of the docstring pattern
        
    Returns:
        Dict[str, Any]: Pattern configuration
        
    Raises:
        KeyError: When pattern name is not found
    """
    if pattern_name not in COMMON_DOCSTRING_PATTERNS:
        raise KeyError(f"Unknown docstring pattern: {pattern_name}")
    
    return COMMON_DOCSTRING_PATTERNS[pattern_name]