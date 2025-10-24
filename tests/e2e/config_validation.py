"""
Configuration validation tests for E2E testing framework.

This module implements task 2.1: Create environment file validator
as part of the E2E testing implementation.
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, List

from tests.e2e.base import ConfigurationTestBase
from tests.e2e.utils import ConfigValidator
from tests.e2e.yaml_json_config_test import YAMLJSONConfigValidationTest


class EnvironmentFileValidationTest(ConfigurationTestBase):
    """
    E2E test for validating environment files against example templates.
    
    This test implements the requirements from task 2.1:
    - Write validator to compare .env files against .env.example templates
    - Implement missing variable detection and reporting
    """
    
    def __init__(self):
        super().__init__()
        self.project_root = Path(__file__).parent.parent.parent
        self.env_file_configs = []
    
    async def setup(self):
        """Set up environment file validation test."""
        await super().setup()
        
        self.logger.info("Setting up environment file validation test")
        
        # Define environment file configurations to validate
        self.env_file_configs = [
            {
                "name": "root",
                "env_path": self.project_root / ".env",
                "example_path": self.project_root / ".env.example",
                "required": True
            },
            {
                "name": "backend",
                "env_path": self.project_root / "backend" / ".env",
                "example_path": self.project_root / "backend" / ".env.example",
                "required": True
            },
            {
                "name": "frontend",
                "env_path": self.project_root / "frontend" / ".env.local",
                "example_path": self.project_root / "frontend" / ".env.example",
                "required": False  # Frontend env file is optional
            }
        ]
        
        # Filter to only include configs where example files exist
        self.env_file_configs = [
            config for config in self.env_file_configs
            if config["example_path"].exists()
        ]
        
        self.logger.info(f"Found {len(self.env_file_configs)} environment file configurations to validate")
    
    async def run_test(self) -> Dict[str, Any]:
        """
        Execute environment file validation test.
        
        Returns:
            Dictionary containing test results and validation details.
        """
        self.logger.info("Running environment file validation test")
        
        validation_results = []
        overall_valid = True
        
        # Validate each environment file configuration
        for config in self.env_file_configs:
            self.logger.info(f"Validating {config['name']} environment file")
            
            try:
                result = ConfigValidator.validate_env_file(
                    config["env_path"],
                    config["example_path"]
                )
                
                result["config_name"] = config["name"]
                result["required"] = config["required"]
                validation_results.append(result)
                
                # Log validation results
                if result["valid"]:
                    self.logger.info(f"✅ {config['name']} environment file is valid")
                else:
                    self.logger.warning(f"❌ {config['name']} environment file has issues")
                    
                    if result["missing_variables"]:
                        self.logger.warning(f"Missing variables: {', '.join(result['missing_variables'])}")
                    
                    if result["empty_required_variables"]:
                        self.logger.warning(f"Empty required variables: {', '.join(result['empty_required_variables'])}")
                    
                    if result["errors"]:
                        for error in result["errors"]:
                            self.logger.error(f"Error: {error}")
                    
                    # Only mark overall as invalid if this is a required config
                    if config["required"]:
                        overall_valid = False
                        self.add_validation_error(
                            f"{config['name']} environment file validation failed"
                        )
                
            except Exception as e:
                self.logger.error(f"Exception validating {config['name']}: {e}")
                validation_results.append({
                    "config_name": config["name"],
                    "valid": False,
                    "errors": [f"Exception during validation: {str(e)}"],
                    "missing_variables": [],
                    "extra_variables": [],
                    "empty_required_variables": [],
                    "warnings": [],
                    "required": config["required"]
                })
                
                if config["required"]:
                    overall_valid = False
                    self.add_validation_error(
                        f"Exception validating {config['name']}: {str(e)}"
                    )
        
        # Generate summary statistics
        total_configs = len(validation_results)
        valid_configs = len([r for r in validation_results if r["valid"]])
        invalid_configs = total_configs - valid_configs
        total_missing_vars = sum(len(r["missing_variables"]) for r in validation_results)
        total_errors = sum(len(r["errors"]) for r in validation_results)
        
        # Generate detailed report
        report = self._generate_validation_report(validation_results)
        
        test_result = {
            "test_name": "environment_file_validation",
            "status": "passed" if overall_valid else "failed",
            "message": f"Validated {total_configs} environment configurations",
            "summary": {
                "total_configurations": total_configs,
                "valid_configurations": valid_configs,
                "invalid_configurations": invalid_configs,
                "total_missing_variables": total_missing_vars,
                "total_errors": total_errors
            },
            "validation_results": validation_results,
            "detailed_report": report,
            "validation_errors": self.validation_errors
        }
        
        self.logger.info(f"Environment file validation completed: {test_result['status']}")
        return test_result
    
    def _generate_validation_report(self, validation_results: List[Dict[str, Any]]) -> str:
        """
        Generate a detailed validation report.
        
        Args:
            validation_results: List of validation results for each configuration
            
        Returns:
            Formatted report string
        """
        lines = []
        lines.append("Environment File Validation Report")
        lines.append("=" * 45)
        lines.append("")
        
        # Summary section
        total_configs = len(validation_results)
        valid_configs = len([r for r in validation_results if r["valid"]])
        invalid_configs = total_configs - valid_configs
        
        lines.append("Summary:")
        lines.append(f"  Total Configurations: {total_configs}")
        lines.append(f"  Valid Configurations: {valid_configs}")
        lines.append(f"  Invalid Configurations: {invalid_configs}")
        lines.append("")
        
        # Detailed results for each configuration
        for result in validation_results:
            config_name = result["config_name"]
            status_icon = "✅" if result["valid"] else "❌"
            required_text = " (Required)" if result["required"] else " (Optional)"
            
            lines.append(f"{status_icon} {config_name.upper()}{required_text}")
            
            if not result["valid"]:
                if result["missing_variables"]:
                    lines.append(f"    Missing Required Variables:")
                    for var in result["missing_variables"]:
                        lines.append(f"      • {var}")
                
                if result["empty_required_variables"]:
                    lines.append(f"    Empty Required Variables:")
                    for var in result["empty_required_variables"]:
                        lines.append(f"      • {var}")
                
                if result["errors"]:
                    lines.append(f"    Errors:")
                    for error in result["errors"]:
                        lines.append(f"      • {error}")
            
            if result["extra_variables"]:
                lines.append(f"    Extra Variables (not in example):")
                for var in result["extra_variables"]:
                    lines.append(f"      • {var}")
            
            if result["warnings"]:
                lines.append(f"    Warnings:")
                for warning in result["warnings"]:
                    lines.append(f"      • {warning}")
            
            lines.append("")
        
        return "\n".join(lines)


class ConfigurationValidationSuite(ConfigurationTestBase):
    """
    Complete configuration validation suite that includes environment file validation
    and can be extended with additional configuration tests.
    """
    
    def __init__(self):
        super().__init__()
        self.test_components = []
    
    async def setup(self):
        """Set up configuration validation suite."""
        await super().setup()
        
        self.logger.info("Setting up configuration validation suite")
        
        # Initialize test components
        self.test_components = [
            EnvironmentFileValidationTest(),
            YAMLJSONConfigValidationTest()
        ]
        
        # Set up each test component
        for component in self.test_components:
            await component.setup()
    
    async def teardown(self):
        """Clean up configuration validation suite."""
        # Tear down each test component
        for component in self.test_components:
            await component.teardown()
        
        await super().teardown()
    
    async def run_test(self) -> Dict[str, Any]:
        """
        Execute the complete configuration validation suite.
        
        Returns:
            Dictionary containing aggregated test results.
        """
        self.logger.info("Running configuration validation suite")
        
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
            "test_name": "configuration_validation_suite",
            "status": overall_status,
            "message": f"Configuration validation suite completed with {passed_tests}/{total_tests} tests passed",
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "error_tests": error_tests
            },
            "component_results": suite_results,
            "validation_errors": self.validation_errors
        }
        
        self.logger.info(f"Configuration validation suite completed: {overall_status}")
        return suite_result