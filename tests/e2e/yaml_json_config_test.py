"""
YAML/JSON Configuration Validation Test for E2E Testing Framework.

This module implements task 2.2: Implement YAML/JSON configuration validator
as part of the E2E testing implementation.
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, List

from tests.e2e.base import ConfigurationTestBase
from tests.e2e.yaml_json_validator import YAMLJSONConfigValidator


class YAMLJSONConfigValidationTest(ConfigurationTestBase):
    """
    E2E test for validating YAML and JSON configuration files.
    
    This test implements the requirements from task 2.2:
    - Create schema validation for all config files in config/ directory
    - Add syntax checking and structure validation
    """
    
    def __init__(self):
        super().__init__()
        self.project_root = Path(__file__).parent.parent.parent
        self.config_dir = self.project_root / "config"
        self.validator = YAMLJSONConfigValidator()
        self.config_schemas = {}
    
    async def setup(self):
        """Set up YAML/JSON configuration validation test."""
        await super().setup()
        
        self.logger.info("Setting up YAML/JSON configuration validation test")
        
        # Load default schemas for common configuration files
        self.config_schemas = self.validator.get_default_config_schemas()
        
        self.logger.info(f"Configuration directory: {self.config_dir}")
        self.logger.info(f"Loaded {len(self.config_schemas)} default schemas")
    
    async def run_test(self) -> Dict[str, Any]:
        """
        Execute YAML/JSON configuration validation test.
        
        Returns:
            Dictionary containing test results and validation details.
        """
        self.logger.info("Running YAML/JSON configuration validation test")
        
        # Validate all configuration files in the config directory
        directory_result = self.validator.validate_config_directory(
            self.config_dir, 
            recursive=True
        )
        
        overall_valid = directory_result["valid"]
        
        # Perform schema validation for files with known schemas
        schema_validation_results = {}
        
        for file_path, file_result in directory_result["file_results"].items():
            if file_result["valid"] and file_result["parsed_data"] is not None:
                # Check if we have a schema for this file
                file_name = Path(file_path).name
                if file_name in self.config_schemas:
                    self.logger.info(f"Validating schema for {file_name}")
                    
                    schema_result = self.validator.validate_config_schema(
                        file_result["parsed_data"],
                        self.config_schemas[file_name]
                    )
                    
                    schema_validation_results[file_path] = schema_result
                    
                    if not schema_result["valid"]:
                        overall_valid = False
                        self.add_validation_error(
                            f"Schema validation failed for {file_name}"
                        )
                        
                        # Log schema validation errors
                        for error in schema_result["errors"]:
                            self.logger.error(f"Schema error in {file_name}: {error}")
                        
                        for missing_field in schema_result["missing_required_fields"]:
                            self.logger.error(f"Missing required field in {file_name}: {missing_field}")
                    else:
                        self.logger.info(f"✅ Schema validation passed for {file_name}")
        
        # Log overall results
        summary = directory_result["summary"]
        self.logger.info(f"Configuration validation summary:")
        self.logger.info(f"  Total files: {summary['total_files']}")
        self.logger.info(f"  Valid files: {summary['valid_files']}")
        self.logger.info(f"  Invalid files: {summary['invalid_files']}")
        self.logger.info(f"  JSON files: {summary['json_files']}")
        self.logger.info(f"  YAML files: {summary['yaml_files']}")
        
        # Report any directory-level errors
        if directory_result["errors"]:
            for error in directory_result["errors"]:
                self.logger.error(f"Directory error: {error}")
                self.add_validation_error(error)
            overall_valid = False
        
        # Report file-level issues
        for file_path, file_result in directory_result["file_results"].items():
            if not file_result["valid"]:
                self.logger.warning(f"❌ {file_path} has validation issues")
                for error in file_result["errors"]:
                    self.logger.error(f"  Error: {error}")
                    self.add_validation_error(f"{file_path}: {error}")
            else:
                self.logger.info(f"✅ {file_path} is valid")
            
            # Report warnings
            for warning in file_result["warnings"]:
                self.logger.warning(f"  Warning in {file_path}: {warning}")
        
        # Generate detailed report
        report = self.validator.generate_config_validation_report(directory_result)
        
        # Calculate additional statistics
        total_schema_validations = len(schema_validation_results)
        valid_schema_validations = len([r for r in schema_validation_results.values() if r["valid"]])
        
        test_result = {
            "test_name": "yaml_json_config_validation",
            "status": "passed" if overall_valid else "failed",
            "message": f"Validated {summary['total_files']} configuration files",
            "summary": {
                **summary,
                "schema_validations": total_schema_validations,
                "valid_schema_validations": valid_schema_validations,
                "invalid_schema_validations": total_schema_validations - valid_schema_validations
            },
            "directory_validation": directory_result,
            "schema_validation_results": schema_validation_results,
            "detailed_report": report,
            "validation_errors": self.validation_errors
        }
        
        self.logger.info(f"YAML/JSON configuration validation completed: {test_result['status']}")
        return test_result
    
    def _validate_specific_config_structures(self, directory_result: Dict[str, Any]) -> List[str]:
        """
        Perform additional validation for specific configuration file structures.
        
        Args:
            directory_result: Result from directory validation
            
        Returns:
            List of additional validation errors
        """
        additional_errors = []
        
        for file_path, file_result in directory_result["file_results"].items():
            if not file_result["valid"] or file_result["parsed_data"] is None:
                continue
            
            file_name = Path(file_path).name
            config_data = file_result["parsed_data"]
            
            # Validate backend.yaml specific requirements
            if file_name == "backend.yaml":
                errors = self._validate_backend_config(config_data)
                additional_errors.extend([f"backend.yaml: {error}" for error in errors])
            
            # Validate frontend.yaml specific requirements
            elif file_name == "frontend.yaml":
                errors = self._validate_frontend_config(config_data)
                additional_errors.extend([f"frontend.yaml: {error}" for error in errors])
            
            # Validate feature_flags.json specific requirements
            elif file_name == "feature_flags.json":
                errors = self._validate_feature_flags_config(config_data)
                additional_errors.extend([f"feature_flags.json: {error}" for error in errors])
            
            # Validate llm_config.json specific requirements
            elif file_name == "llm_config.json":
                errors = self._validate_llm_config(config_data)
                additional_errors.extend([f"llm_config.json: {error}" for error in errors])
        
        return additional_errors
    
    def _validate_backend_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate backend configuration specific requirements."""
        errors = []
        
        # Check API configuration
        if "api" in config:
            api_config = config["api"]
            
            # Validate port range
            if "port" in api_config:
                port = api_config["port"]
                if not isinstance(port, int) or port < 1 or port > 65535:
                    errors.append("API port must be an integer between 1 and 65535")
            
            # Validate workers count
            if "workers" in api_config:
                workers = api_config["workers"]
                if not isinstance(workers, int) or workers < 1:
                    errors.append("API workers must be a positive integer")
        
        # Check database configuration
        if "database" in config:
            db_config = config["database"]
            
            # Validate database URL
            if "url" in db_config:
                url = db_config["url"]
                if not isinstance(url, str) or not url.strip():
                    errors.append("Database URL must be a non-empty string")
        
        return errors
    
    def _validate_frontend_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate frontend configuration specific requirements."""
        errors = []
        
        # Check Streamlit configuration
        if "streamlit" in config:
            streamlit_config = config["streamlit"]
            
            if "server" in streamlit_config:
                server_config = streamlit_config["server"]
                
                # Validate port
                if "port" in server_config:
                    port = server_config["port"]
                    if not isinstance(port, int) or port < 1 or port > 65535:
                        errors.append("Streamlit server port must be an integer between 1 and 65535")
        
        return errors
    
    def _validate_feature_flags_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate feature flags configuration specific requirements."""
        errors = []
        
        if "flags" in config:
            flags = config["flags"]
            
            if not isinstance(flags, dict):
                errors.append("Flags must be an object/dictionary")
                return errors
            
            for flag_name, flag_config in flags.items():
                if not isinstance(flag_config, dict):
                    errors.append(f"Flag '{flag_name}' must be an object")
                    continue
                
                # Validate required fields
                required_fields = ["description", "state", "default_value"]
                for field in required_fields:
                    if field not in flag_config:
                        errors.append(f"Flag '{flag_name}' missing required field: {field}")
                
                # Validate state values
                if "state" in flag_config:
                    valid_states = ["enabled", "disabled", "rollout", "testing"]
                    if flag_config["state"] not in valid_states:
                        errors.append(f"Flag '{flag_name}' has invalid state. Must be one of: {valid_states}")
        
        return errors
    
    def _validate_llm_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate LLM configuration specific requirements."""
        errors = []
        
        if "providers" in config:
            providers = config["providers"]
            
            if not isinstance(providers, dict):
                errors.append("Providers must be an object/dictionary")
                return errors
            
            for provider_name, provider_config in providers.items():
                if not isinstance(provider_config, dict):
                    errors.append(f"Provider '{provider_name}' must be an object")
                    continue
                
                # Validate required fields
                required_fields = ["provider", "model_name", "enabled"]
                for field in required_fields:
                    if field not in provider_config:
                        errors.append(f"Provider '{provider_name}' missing required field: {field}")
                
                # Validate temperature range
                if "temperature" in provider_config:
                    temp = provider_config["temperature"]
                    if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                        errors.append(f"Provider '{provider_name}' temperature must be between 0 and 2")
                
                # Validate max_tokens
                if "max_tokens" in provider_config:
                    max_tokens = provider_config["max_tokens"]
                    if not isinstance(max_tokens, int) or max_tokens < 1:
                        errors.append(f"Provider '{provider_name}' max_tokens must be a positive integer")
        
        return errors


class YAMLJSONConfigValidationSuite(ConfigurationTestBase):
    """
    Complete YAML/JSON configuration validation suite.
    """
    
    def __init__(self):
        super().__init__()
        self.test_components = []
    
    async def setup(self):
        """Set up YAML/JSON configuration validation suite."""
        await super().setup()
        
        self.logger.info("Setting up YAML/JSON configuration validation suite")
        
        # Initialize test components
        self.test_components = [
            YAMLJSONConfigValidationTest()
        ]
        
        # Set up each test component
        for component in self.test_components:
            await component.setup()
    
    async def teardown(self):
        """Clean up YAML/JSON configuration validation suite."""
        # Tear down each test component
        for component in self.test_components:
            await component.teardown()
        
        await super().teardown()
    
    async def run_test(self) -> Dict[str, Any]:
        """
        Execute the complete YAML/JSON configuration validation suite.
        
        Returns:
            Dictionary containing aggregated test results.
        """
        self.logger.info("Running YAML/JSON configuration validation suite")
        
        suite_results = []
        overall_status = "passed"
        
        # Run each test component
        for component in self.test_components:
            try:
                result = await component.run_test()
                suite_results.append(result)
                
                if result["status"] != "passed":
                    overall_status = "failed"
                    
                    # Aggregate validation errors
                    if hasattr(component, 'validation_errors'):
                        self.validation_errors.extend(component.validation_errors)
                
            except Exception as e:
                self.logger.error(f"Error running {component.__class__.__name__}: {e}")
                suite_results.append({
                    "test_name": component.__class__.__name__,
                    "status": "error",
                    "message": f"Exception during test execution: {str(e)}",
                    "error": str(e)
                })
                overall_status = "failed"
                self.add_validation_error(f"Error in {component.__class__.__name__}: {str(e)}")
        
        # Generate suite summary
        total_tests = len(suite_results)
        passed_tests = len([r for r in suite_results if r["status"] == "passed"])
        failed_tests = len([r for r in suite_results if r["status"] == "failed"])
        error_tests = len([r for r in suite_results if r["status"] == "error"])
        
        suite_result = {
            "test_name": "yaml_json_config_validation_suite",
            "status": overall_status,
            "message": f"YAML/JSON configuration validation suite completed with {passed_tests}/{total_tests} tests passed",
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "error_tests": error_tests
            },
            "component_results": suite_results,
            "validation_errors": self.validation_errors
        }
        
        self.logger.info(f"YAML/JSON configuration validation suite completed: {overall_status}")
        return suite_result