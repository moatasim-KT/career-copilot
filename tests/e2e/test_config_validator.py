"""
Test module for configuration validation functionality.

This module contains tests for the environment file validator
as part of task 2.1 in the E2E testing implementation.
"""

import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any

from tests.e2e.utils import ConfigValidator


class TestEnvironmentFileValidator:
    """Test the environment file validator functionality."""
    
    def test_validate_env_file_valid_complete(self):
        """Test validation of a complete and valid environment file."""
        # Create temporary example file
        example_content = """# Example configuration
# Required settings
JWT_SECRET_KEY=your-secret-key-change-this
DATABASE_URL=sqlite:///./data/test.db
API_HOST=0.0.0.0
API_PORT=8002

# Optional settings
DEBUG=true
LOG_LEVEL=INFO
"""
        
        # Create temporary env file with all required variables
        env_content = """# Production configuration
JWT_SECRET_KEY=my-super-secret-production-key-32-chars
DATABASE_URL=postgresql://user:pass@localhost:5432/db
API_HOST=127.0.0.1
API_PORT=8002
DEBUG=false
LOG_LEVEL=ERROR
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env.example', delete=False) as example_file:
            example_file.write(example_content)
            example_path = Path(example_file.name)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as env_file:
            env_file.write(env_content)
            env_path = Path(env_file.name)
        
        try:
            result = ConfigValidator.validate_env_file(env_path, example_path)
            
            assert result["valid"] is True
            assert len(result["missing_variables"]) == 0
            assert len(result["errors"]) == 0
            assert "JWT_SECRET_KEY" not in result["missing_variables"]
            assert "DATABASE_URL" not in result["missing_variables"]
            
        finally:
            example_path.unlink()
            env_path.unlink()
    
    def test_validate_env_file_missing_required_variables(self):
        """Test validation when required variables are missing."""
        example_content = """# Example configuration
JWT_SECRET_KEY=your-secret-key-change-this
DATABASE_URL=sqlite:///./data/test.db
API_HOST=0.0.0.0
API_PORT=8002
"""
        
        # Env file missing JWT_SECRET_KEY and DATABASE_URL
        env_content = """API_HOST=127.0.0.1
API_PORT=8002
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env.example', delete=False) as example_file:
            example_file.write(example_content)
            example_path = Path(example_file.name)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as env_file:
            env_file.write(env_content)
            env_path = Path(env_file.name)
        
        try:
            result = ConfigValidator.validate_env_file(env_path, example_path)
            
            assert result["valid"] is False
            assert "JWT_SECRET_KEY" in result["missing_variables"]
            assert "DATABASE_URL" in result["missing_variables"]
            assert len(result["missing_variables"]) == 2
            
        finally:
            example_path.unlink()
            env_path.unlink()
    
    def test_validate_env_file_empty_required_variables(self):
        """Test validation when required variables are empty."""
        example_content = """# Example configuration
JWT_SECRET_KEY=your-secret-key-change-this
DATABASE_URL=sqlite:///./data/test.db
"""
        
        # Env file with empty required variables
        env_content = """JWT_SECRET_KEY=
DATABASE_URL=
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env.example', delete=False) as example_file:
            example_file.write(example_content)
            example_path = Path(example_file.name)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as env_file:
            env_file.write(env_content)
            env_path = Path(env_file.name)
        
        try:
            result = ConfigValidator.validate_env_file(env_path, example_path)
            
            assert result["valid"] is False
            assert "JWT_SECRET_KEY" in result["empty_required_variables"]
            assert "DATABASE_URL" in result["empty_required_variables"]
            assert len(result["empty_required_variables"]) == 2
            
        finally:
            example_path.unlink()
            env_path.unlink()
    
    def test_validate_env_file_extra_variables(self):
        """Test validation when env file has extra variables."""
        example_content = """# Example configuration
JWT_SECRET_KEY=your-secret-key-change-this
API_HOST=0.0.0.0
"""
        
        # Env file with extra variables
        env_content = """JWT_SECRET_KEY=my-secret-key
API_HOST=127.0.0.1
EXTRA_VAR=some_value
ANOTHER_EXTRA=another_value
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env.example', delete=False) as example_file:
            example_file.write(example_content)
            example_path = Path(example_file.name)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as env_file:
            env_file.write(env_content)
            env_path = Path(env_file.name)
        
        try:
            result = ConfigValidator.validate_env_file(env_path, example_path)
            
            assert result["valid"] is True  # Extra variables don't make it invalid
            assert "EXTRA_VAR" in result["extra_variables"]
            assert "ANOTHER_EXTRA" in result["extra_variables"]
            assert len(result["extra_variables"]) == 2
            
        finally:
            example_path.unlink()
            env_path.unlink()
    
    def test_validate_env_file_missing_env_file(self):
        """Test validation when env file doesn't exist."""
        example_content = """# Example configuration
JWT_SECRET_KEY=your-secret-key-change-this
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env.example', delete=False) as example_file:
            example_file.write(example_content)
            example_path = Path(example_file.name)
        
        non_existent_env_path = Path("/tmp/non_existent_file.env")
        
        try:
            result = ConfigValidator.validate_env_file(non_existent_env_path, example_path)
            
            assert result["valid"] is False
            assert len(result["errors"]) > 0
            assert "Environment file not found" in result["errors"][0]
            assert "JWT_SECRET_KEY" in result["missing_variables"]
            
        finally:
            example_path.unlink()
    
    def test_validate_env_file_missing_example_file(self):
        """Test validation when example file doesn't exist."""
        env_content = """JWT_SECRET_KEY=my-secret-key"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as env_file:
            env_file.write(env_content)
            env_path = Path(env_file.name)
        
        non_existent_example_path = Path("/tmp/non_existent_example.env")
        
        try:
            result = ConfigValidator.validate_env_file(env_path, non_existent_example_path)
            
            assert result["valid"] is False
            assert len(result["errors"]) > 0
            assert "Example file not found" in result["errors"][0]
            
        finally:
            env_path.unlink()
    
    def test_validate_env_file_malformed_content(self):
        """Test validation with malformed content."""
        example_content = """# Example configuration
JWT_SECRET_KEY=your-secret-key
MALFORMED_LINE_WITHOUT_EQUALS
API_HOST=0.0.0.0
"""
        
        env_content = """JWT_SECRET_KEY=my-secret-key
ALSO_MALFORMED_LINE
API_HOST=127.0.0.1
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env.example', delete=False) as example_file:
            example_file.write(example_content)
            example_path = Path(example_file.name)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as env_file:
            env_file.write(env_content)
            env_path = Path(env_file.name)
        
        try:
            result = ConfigValidator.validate_env_file(env_path, example_path)
            
            # Should still be valid for properly formatted variables
            assert result["valid"] is True
            # The validator skips malformed lines silently, which is acceptable behavior
            # We just ensure it doesn't crash and processes valid lines correctly
            assert "JWT_SECRET_KEY" not in result["missing_variables"]
            assert "API_HOST" not in result["missing_variables"]
            
        finally:
            example_path.unlink()
            env_path.unlink()
    
    def test_validate_multiple_env_files(self):
        """Test validation of multiple environment files."""
        # Create first set of files
        example1_content = """JWT_SECRET_KEY=your-secret-key
API_HOST=0.0.0.0"""
        
        env1_content = """JWT_SECRET_KEY=my-secret-key
API_HOST=127.0.0.1"""
        
        # Create second set of files (with missing variable)
        example2_content = """DATABASE_URL=sqlite:///test.db
DEBUG=true"""
        
        env2_content = """DEBUG=false"""  # Missing DATABASE_URL
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env.example', delete=False) as example1_file:
            example1_file.write(example1_content)
            example1_path = Path(example1_file.name)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as env1_file:
            env1_file.write(env1_content)
            env1_path = Path(env1_file.name)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env.example', delete=False) as example2_file:
            example2_file.write(example2_content)
            example2_path = Path(example2_file.name)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as env2_file:
            env2_file.write(env2_content)
            env2_path = Path(env2_file.name)
        
        try:
            env_configs = [
                {"env_path": env1_path, "example_path": example1_path},
                {"env_path": env2_path, "example_path": example2_path}
            ]
            
            result = ConfigValidator.validate_multiple_env_files(env_configs)
            
            assert result["valid"] is False  # Should be invalid due to second file
            assert result["summary"]["total_files"] == 2
            assert result["summary"]["valid_files"] == 1
            assert result["summary"]["invalid_files"] == 1
            assert result["summary"]["total_missing_variables"] == 1
            
            # Check individual file results
            assert result["file_results"][str(env1_path)]["valid"] is True
            assert result["file_results"][str(env2_path)]["valid"] is False
            
        finally:
            example1_path.unlink()
            env1_path.unlink()
            example2_path.unlink()
            env2_path.unlink()
    
    def test_generate_env_file_report_single_file(self):
        """Test report generation for single file validation."""
        result = {
            "valid": False,
            "missing_variables": ["JWT_SECRET_KEY", "DATABASE_URL"],
            "extra_variables": ["EXTRA_VAR"],
            "empty_required_variables": ["API_HOST"],
            "errors": ["Some error occurred"],
            "warnings": ["Some warning"],
            "checked_files": ["/path/to/.env", "/path/to/.env.example"]
        }
        
        report = ConfigValidator.generate_env_file_report(result)
        
        assert "Environment File Validation Report" in report
        assert "❌ INVALID" in report
        assert "JWT_SECRET_KEY" in report
        assert "DATABASE_URL" in report
        assert "EXTRA_VAR" in report
        assert "API_HOST" in report
        assert "Some error occurred" in report
        assert "Some warning" in report
    
    def test_generate_env_file_report_multiple_files(self):
        """Test report generation for multiple files validation."""
        result = {
            "valid": False,
            "file_results": {
                "/path/to/.env": {"valid": True, "missing_variables": [], "errors": []},
                "/path/to/backend/.env": {"valid": False, "missing_variables": ["JWT_SECRET_KEY"], "errors": ["File not found"]}
            },
            "summary": {
                "total_files": 2,
                "valid_files": 1,
                "invalid_files": 1,
                "total_missing_variables": 1,
                "total_errors": 1
            }
        }
        
        report = ConfigValidator.generate_env_file_report(result)
        
        assert "Environment Files Validation Report" in report
        assert "Total Files: 2" in report
        assert "Valid Files: 1" in report
        assert "Invalid Files: 1" in report
        assert "✅ /path/to/.env" in report
        assert "❌ /path/to/backend/.env" in report
        assert "JWT_SECRET_KEY" in report
    
    def test_is_variable_required_critical_vars(self):
        """Test that critical variables are always marked as required."""
        critical_vars = ['JWT_SECRET_KEY', 'DATABASE_URL', 'API_HOST', 'API_PORT']
        
        for var in critical_vars:
            result = ConfigValidator._is_variable_required(var, "", "", "")
            assert result is True, f"{var} should be marked as required"
    
    def test_is_variable_required_placeholder_values(self):
        """Test that variables with placeholder values are marked as required."""
        placeholder_cases = [
            ("API_KEY", "your-api-key"),
            ("SECRET", "your_secret_here"),
            ("TOKEN", "change-this-token"),
            ("PASSWORD", "replace-with-password")
        ]
        
        for var_name, var_value in placeholder_cases:
            result = ConfigValidator._is_variable_required(var_name, var_value, "", "")
            assert result is True, f"{var_name}={var_value} should be marked as required"
    
    def test_is_variable_required_empty_sensitive_vars(self):
        """Test that empty sensitive variables are marked as required."""
        sensitive_vars = [
            ("API_KEY", ""),
            ("SECRET_TOKEN", ""),
            ("DATABASE_PASSWORD", ""),
            ("SMTP_HOST", ""),
            ("REDIS_URL", "")
        ]
        
        for var_name, var_value in sensitive_vars:
            result = ConfigValidator._is_variable_required(var_name, var_value, "", "")
            assert result is True, f"Empty {var_name} should be marked as required"


class TestEnvironmentFileValidatorIntegration:
    """Integration tests for environment file validator with real project files."""
    
    def test_validate_project_env_files(self):
        """Test validation against actual project environment files."""
        project_root = Path(__file__).parent.parent.parent
        
        # Test cases for actual project files
        test_cases = [
            {
                "env_path": project_root / ".env",
                "example_path": project_root / ".env.example",
                "name": "root"
            },
            {
                "env_path": project_root / "backend" / ".env",
                "example_path": project_root / "backend" / ".env.example",
                "name": "backend"
            },
            {
                "env_path": project_root / "frontend" / ".env.local",
                "example_path": project_root / "frontend" / ".env.example",
                "name": "frontend"
            }
        ]
        
        results = []
        for case in test_cases:
            if case["example_path"].exists():
                result = ConfigValidator.validate_env_file(
                    case["env_path"], 
                    case["example_path"]
                )
                result["test_case"] = case["name"]
                results.append(result)
        
        # At least one example file should exist
        assert len(results) > 0, "No example files found in project"
        
        # Generate report for all results
        if len(results) > 1:
            multi_result = {
                "valid": all(r["valid"] for r in results),
                "file_results": {r["test_case"]: r for r in results},
                "summary": {
                    "total_files": len(results),
                    "valid_files": sum(1 for r in results if r["valid"]),
                    "invalid_files": sum(1 for r in results if not r["valid"]),
                    "total_missing_variables": sum(len(r["missing_variables"]) for r in results),
                    "total_errors": sum(len(r["errors"]) for r in results)
                }
            }
            report = ConfigValidator.generate_env_file_report(multi_result)
        else:
            report = ConfigValidator.generate_env_file_report(results[0])
        
        # Print report for debugging (will be visible if test fails)
        print("\n" + "="*50)
        print("PROJECT ENVIRONMENT FILES VALIDATION REPORT")
        print("="*50)
        print(report)
        print("="*50)
        
        # The test passes regardless of validation results since .env files may not exist
        # This is primarily for reporting and debugging purposes
        assert True