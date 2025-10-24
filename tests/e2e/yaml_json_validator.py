"""
YAML/JSON Configuration Validator for E2E Testing Framework.

This module implements task 2.2: Implement YAML/JSON configuration validator
as part of the E2E testing implementation.
"""

import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Union


class YAMLJSONConfigValidator:
    """
    Validator for YAML and JSON configuration files.
    
    This class implements the requirements from task 2.2:
    - Create schema validation for all config files in config/ directory
    - Add syntax checking and structure validation
    """
    
    @staticmethod
    def validate_yaml_file(yaml_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate YAML file syntax and structure.
        
        Args:
            yaml_path: Path to the YAML file to validate.
            
        Returns:
            Dictionary containing validation results.
        """
        yaml_path = Path(yaml_path)
        
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "file_type": "yaml",
            "file_path": str(yaml_path),
            "parsed_data": None
        }
        
        try:
            if not yaml_path.exists():
                result["errors"].append(f"YAML file not found: {yaml_path}")
                result["valid"] = False
                return result
            
            with open(yaml_path, 'r', encoding='utf-8') as f:
                parsed_data = yaml.safe_load(f)
                result["parsed_data"] = parsed_data
                
                # Check for common YAML issues
                if parsed_data is None:
                    result["warnings"].append("YAML file is empty or contains only null values")
                
        except yaml.YAMLError as e:
            result["errors"].append(f"Invalid YAML syntax: {str(e)}")
            result["valid"] = False
        except Exception as e:
            result["errors"].append(f"Error reading YAML file: {str(e)}")
            result["valid"] = False
        
        return result
    
    @staticmethod
    def validate_json_file(json_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate JSON file syntax and structure.
        
        Args:
            json_path: Path to the JSON file to validate.
            
        Returns:
            Dictionary containing validation results.
        """
        json_path = Path(json_path)
        
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "file_type": "json",
            "file_path": str(json_path),
            "parsed_data": None
        }
        
        try:
            if not json_path.exists():
                result["errors"].append(f"JSON file not found: {json_path}")
                result["valid"] = False
                return result
            
            with open(json_path, 'r', encoding='utf-8') as f:
                parsed_data = json.load(f)
                result["parsed_data"] = parsed_data
                
        except json.JSONDecodeError as e:
            result["errors"].append(f"Invalid JSON syntax: {str(e)}")
            result["valid"] = False
        except Exception as e:
            result["errors"].append(f"Error reading JSON file: {str(e)}")
            result["valid"] = False
        
        return result
    
    @staticmethod
    def validate_config_file(config_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate configuration file (JSON or YAML) based on file extension.
        
        Args:
            config_path: Path to the configuration file to validate.
            
        Returns:
            Dictionary containing validation results.
        """
        config_path = Path(config_path)
        
        if config_path.suffix.lower() in ['.json']:
            return YAMLJSONConfigValidator.validate_json_file(config_path)
        elif config_path.suffix.lower() in ['.yaml', '.yml']:
            return YAMLJSONConfigValidator.validate_yaml_file(config_path)
        else:
            return {
                "valid": False,
                "errors": [f"Unsupported file type: {config_path.suffix}"],
                "warnings": [],
                "file_type": "unknown",
                "file_path": str(config_path),
                "parsed_data": None
            }
    
    @staticmethod
    def validate_config_directory(config_dir: Union[str, Path], 
                                 recursive: bool = True) -> Dict[str, Any]:
        """
        Validate all configuration files in a directory.
        
        Args:
            config_dir: Path to the configuration directory.
            recursive: Whether to search subdirectories recursively.
            
        Returns:
            Dictionary containing aggregated validation results.
        """
        config_dir = Path(config_dir)
        
        result = {
            "valid": True,
            "directory": str(config_dir),
            "file_results": {},
            "summary": {
                "total_files": 0,
                "valid_files": 0,
                "invalid_files": 0,
                "json_files": 0,
                "yaml_files": 0,
                "total_errors": 0,
                "total_warnings": 0
            },
            "errors": [],
            "warnings": []
        }
        
        try:
            if not config_dir.exists():
                result["errors"].append(f"Configuration directory not found: {config_dir}")
                result["valid"] = False
                return result
            
            if not config_dir.is_dir():
                result["errors"].append(f"Path is not a directory: {config_dir}")
                result["valid"] = False
                return result
            
            # Find all configuration files
            config_patterns = ['*.json', '*.yaml', '*.yml']
            config_files = []
            
            for pattern in config_patterns:
                if recursive:
                    config_files.extend(config_dir.rglob(pattern))
                else:
                    config_files.extend(config_dir.glob(pattern))
            
            # Remove duplicates and sort
            config_files = sorted(set(config_files))
            
            if not config_files:
                result["warnings"].append(f"No configuration files found in {config_dir}")
            
            # Validate each configuration file
            for config_file in config_files:
                file_result = YAMLJSONConfigValidator.validate_config_file(config_file)
                relative_path = str(config_file.relative_to(config_dir))
                result["file_results"][relative_path] = file_result
                
                # Update summary statistics
                result["summary"]["total_files"] += 1
                
                if file_result["valid"]:
                    result["summary"]["valid_files"] += 1
                else:
                    result["summary"]["invalid_files"] += 1
                    result["valid"] = False
                
                if file_result["file_type"] == "json":
                    result["summary"]["json_files"] += 1
                elif file_result["file_type"] == "yaml":
                    result["summary"]["yaml_files"] += 1
                
                result["summary"]["total_errors"] += len(file_result["errors"])
                result["summary"]["total_warnings"] += len(file_result["warnings"])
                
        except Exception as e:
            result["errors"].append(f"Error scanning configuration directory: {str(e)}")
            result["valid"] = False
        
        return result
    
    @staticmethod
    def validate_config_schema(config_data: Dict[str, Any], 
                              schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate configuration data against a schema.
        
        Args:
            config_data: Configuration data to validate.
            schema: Schema definition for validation.
            
        Returns:
            Dictionary containing schema validation results.
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "missing_required_fields": [],
            "invalid_field_types": [],
            "extra_fields": []
        }
        
        try:
            # Validate required fields
            required_fields = schema.get("required", [])
            for field in required_fields:
                if field not in config_data:
                    result["missing_required_fields"].append(field)
                    result["valid"] = False
            
            # Validate field types and values
            properties = schema.get("properties", {})
            for field_name, field_schema in properties.items():
                if field_name in config_data:
                    field_value = config_data[field_name]
                    field_validation = YAMLJSONConfigValidator._validate_field_against_schema(
                        field_name, field_value, field_schema
                    )
                    
                    if not field_validation["valid"]:
                        result["invalid_field_types"].extend(field_validation["errors"])
                        result["valid"] = False
                    
                    result["warnings"].extend(field_validation["warnings"])
            
            # Check for extra fields (if strict mode)
            if schema.get("additionalProperties", True) is False:
                allowed_fields = set(properties.keys())
                actual_fields = set(config_data.keys())
                extra_fields = actual_fields - allowed_fields
                
                if extra_fields:
                    result["extra_fields"] = list(extra_fields)
                    result["warnings"].extend([
                        f"Extra field not allowed in schema: {field}" 
                        for field in extra_fields
                    ])
                    
        except Exception as e:
            result["errors"].append(f"Error validating schema: {str(e)}")
            result["valid"] = False
        
        return result
    
    @staticmethod
    def _validate_field_against_schema(field_name: str, field_value: Any, 
                                     field_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single field against its schema definition.
        
        Args:
            field_name: Name of the field being validated.
            field_value: Value of the field.
            field_schema: Schema definition for the field.
            
        Returns:
            Dictionary containing field validation results.
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Check type
            expected_type = field_schema.get("type")
            if expected_type:
                if not YAMLJSONConfigValidator._check_field_type(field_value, expected_type):
                    result["errors"].append(
                        f"Field '{field_name}' has invalid type. "
                        f"Expected: {expected_type}, Got: {type(field_value).__name__}"
                    )
                    result["valid"] = False
            
            # Check enum values
            enum_values = field_schema.get("enum")
            if enum_values and field_value not in enum_values:
                result["errors"].append(
                    f"Field '{field_name}' has invalid value. "
                    f"Must be one of: {enum_values}, Got: {field_value}"
                )
                result["valid"] = False
            
            # Check minimum/maximum for numbers
            if isinstance(field_value, (int, float)):
                minimum = field_schema.get("minimum")
                maximum = field_schema.get("maximum")
                
                if minimum is not None and field_value < minimum:
                    result["errors"].append(
                        f"Field '{field_name}' value {field_value} is below minimum {minimum}"
                    )
                    result["valid"] = False
                
                if maximum is not None and field_value > maximum:
                    result["errors"].append(
                        f"Field '{field_name}' value {field_value} is above maximum {maximum}"
                    )
                    result["valid"] = False
            
            # Check string length
            if isinstance(field_value, str):
                min_length = field_schema.get("minLength")
                max_length = field_schema.get("maxLength")
                
                if min_length is not None and len(field_value) < min_length:
                    result["errors"].append(
                        f"Field '{field_name}' length {len(field_value)} is below minimum {min_length}"
                    )
                    result["valid"] = False
                
                if max_length is not None and len(field_value) > max_length:
                    result["errors"].append(
                        f"Field '{field_name}' length {len(field_value)} is above maximum {max_length}"
                    )
                    result["valid"] = False
            
            # Validate nested objects
            if expected_type == "object" and isinstance(field_value, dict):
                properties = field_schema.get("properties", {})
                if properties:
                    nested_result = YAMLJSONConfigValidator.validate_config_schema(field_value, field_schema)
                    if not nested_result["valid"]:
                        result["errors"].extend([
                            f"In field '{field_name}': {error}" 
                            for error in nested_result["errors"]
                        ])
                        result["valid"] = False
                    
                    result["warnings"].extend([
                        f"In field '{field_name}': {warning}" 
                        for warning in nested_result["warnings"]
                    ])
            
            # Validate arrays
            if expected_type == "array" and isinstance(field_value, list):
                items_schema = field_schema.get("items")
                if items_schema:
                    for i, item in enumerate(field_value):
                        item_result = YAMLJSONConfigValidator._validate_field_against_schema(
                            f"{field_name}[{i}]", item, items_schema
                        )
                        if not item_result["valid"]:
                            result["errors"].extend(item_result["errors"])
                            result["valid"] = False
                        result["warnings"].extend(item_result["warnings"])
                
                # Check array length
                min_items = field_schema.get("minItems")
                max_items = field_schema.get("maxItems")
                
                if min_items is not None and len(field_value) < min_items:
                    result["errors"].append(
                        f"Array field '{field_name}' has {len(field_value)} items, minimum is {min_items}"
                    )
                    result["valid"] = False
                
                if max_items is not None and len(field_value) > max_items:
                    result["errors"].append(
                        f"Array field '{field_name}' has {len(field_value)} items, maximum is {max_items}"
                    )
                    result["valid"] = False
                    
        except Exception as e:
            result["errors"].append(f"Error validating field '{field_name}': {str(e)}")
            result["valid"] = False
        
        return result
    
    @staticmethod
    def _check_field_type(value: Any, expected_type: str) -> bool:
        """
        Check if a value matches the expected type.
        
        Args:
            value: Value to check.
            expected_type: Expected type string.
            
        Returns:
            True if type matches, False otherwise.
        """
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None)
        }
        
        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type is None:
            return True  # Unknown type, assume valid
        
        return isinstance(value, expected_python_type)
    
    @staticmethod
    def generate_config_validation_report(validation_result: Dict[str, Any]) -> str:
        """
        Generate a human-readable report from configuration validation results.
        
        Args:
            validation_result: Result from validate_config_directory or validate_config_file
            
        Returns:
            Formatted report string
        """
        if "file_results" in validation_result:
            # Directory validation report
            return YAMLJSONConfigValidator._generate_directory_validation_report(validation_result)
        else:
            # Single file validation report
            return YAMLJSONConfigValidator._generate_file_validation_report(validation_result)
    
    @staticmethod
    def _generate_directory_validation_report(result: Dict[str, Any]) -> str:
        """Generate report for directory validation."""
        lines = []
        lines.append("Configuration Directory Validation Report")
        lines.append("=" * 50)
        lines.append("")
        
        # Summary
        summary = result["summary"]
        status = "✅ VALID" if result["valid"] else "❌ INVALID"
        lines.append(f"Status: {status}")
        lines.append(f"Directory: {result['directory']}")
        lines.append("")
        
        lines.append("Summary:")
        lines.append(f"  Total Files: {summary['total_files']}")
        lines.append(f"  Valid Files: {summary['valid_files']}")
        lines.append(f"  Invalid Files: {summary['invalid_files']}")
        lines.append(f"  JSON Files: {summary['json_files']}")
        lines.append(f"  YAML Files: {summary['yaml_files']}")
        lines.append(f"  Total Errors: {summary['total_errors']}")
        lines.append(f"  Total Warnings: {summary['total_warnings']}")
        lines.append("")
        
        # Directory-level errors and warnings
        if result["errors"]:
            lines.append("Directory Errors:")
            for error in result["errors"]:
                lines.append(f"  • {error}")
            lines.append("")
        
        if result["warnings"]:
            lines.append("Directory Warnings:")
            for warning in result["warnings"]:
                lines.append(f"  • {warning}")
            lines.append("")
        
        # File-specific results
        if result["file_results"]:
            lines.append("File Results:")
            for file_path, file_result in result["file_results"].items():
                status_icon = "✅" if file_result["valid"] else "❌"
                file_type = file_result["file_type"].upper()
                lines.append(f"  {status_icon} {file_path} ({file_type})")
                
                if not file_result["valid"]:
                    for error in file_result["errors"]:
                        lines.append(f"      Error: {error}")
                
                if file_result["warnings"]:
                    for warning in file_result["warnings"]:
                        lines.append(f"      Warning: {warning}")
        
        return "\n".join(lines)
    
    @staticmethod
    def _generate_file_validation_report(result: Dict[str, Any]) -> str:
        """Generate report for single file validation."""
        lines = []
        lines.append("Configuration File Validation Report")
        lines.append("=" * 45)
        lines.append("")
        
        status = "✅ VALID" if result["valid"] else "❌ INVALID"
        file_type = result["file_type"].upper()
        lines.append(f"Status: {status}")
        lines.append(f"File: {result['file_path']}")
        lines.append(f"Type: {file_type}")
        lines.append("")
        
        if result["errors"]:
            lines.append("Errors:")
            for error in result["errors"]:
                lines.append(f"  • {error}")
            lines.append("")
        
        if result["warnings"]:
            lines.append("Warnings:")
            for warning in result["warnings"]:
                lines.append(f"  • {warning}")
            lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def get_default_config_schemas() -> Dict[str, Dict[str, Any]]:
        """
        Get default schemas for common configuration files.
        
        Returns:
            Dictionary mapping file patterns to their schemas.
        """
        return {
            "backend.yaml": {
                "type": "object",
                "required": ["api", "database"],
                "properties": {
                    "api": {
                        "type": "object",
                        "required": ["host", "port"],
                        "properties": {
                            "host": {"type": "string"},
                            "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                            "debug": {"type": "boolean"},
                            "workers": {"type": "integer", "minimum": 1}
                        }
                    },
                    "database": {
                        "type": "object",
                        "required": ["url"],
                        "properties": {
                            "url": {"type": "string", "minLength": 1},
                            "pool_size": {"type": "integer", "minimum": 1},
                            "echo": {"type": "boolean"}
                        }
                    }
                }
            },
            "frontend.yaml": {
                "type": "object",
                "required": ["streamlit"],
                "properties": {
                    "streamlit": {
                        "type": "object",
                        "required": ["server"],
                        "properties": {
                            "server": {
                                "type": "object",
                                "required": ["port"],
                                "properties": {
                                    "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                                    "address": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            },
            "feature_flags.json": {
                "type": "object",
                "required": ["flags"],
                "properties": {
                    "flags": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "object",
                            "required": ["description", "state", "default_value"],
                            "properties": {
                                "description": {"type": "string", "minLength": 1},
                                "state": {"type": "string", "enum": ["enabled", "disabled", "rollout", "testing"]},
                                "default_value": {"type": "boolean"},
                                "tags": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    }
                }
            },
            "llm_config.json": {
                "type": "object",
                "required": ["providers"],
                "properties": {
                    "providers": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "object",
                            "required": ["provider", "model_name", "enabled"],
                            "properties": {
                                "provider": {"type": "string", "minLength": 1},
                                "model_name": {"type": "string", "minLength": 1},
                                "enabled": {"type": "boolean"},
                                "temperature": {"type": "number", "minimum": 0, "maximum": 2},
                                "max_tokens": {"type": "integer", "minimum": 1}
                            }
                        }
                    }
                }
            }
        }