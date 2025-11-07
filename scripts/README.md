# Scripts Directory

Organized collection of utility scripts for Career Copilot development, testing, deployment, and maintenance.

## 📁 Directory Structure

```
scripts/
├── setup/              # Initial setup and installation scripts
├── user-management/    # User creation and management
├── database/           # Database operations and migrations
├── testing/            # Test runners and validation
├── security/           # Security audits and key management
├── performance/        # Performance testing and optimization
├── analytics/          # Analytics validation
├── initialization/     # Service initialization
├── migrations/         # Data migration scripts
├── services/           # Service management (Celery, etc.)
├── verify/             # Deployment verification
├── reporting/          # Report generation
├── maintenance/        # Maintenance tasks
├── backup/             # Backup scripts
├── cleanup/            # Temporary cleanup scripts
└── deprecated/         # Old scripts kept for reference
```

## 🚀 Setup Scripts

**Location**: `setup/`

| Script | Purpose | Usage |
|--------|---------|-------|
| `setup.sh` | Complete environment setup | `./setup.sh` |
| `initialize_demo_data.py` | Load demo/test data | `python initialize_demo_data.py` |
| `upload_resume.sh` | Upload test resume | `./upload_resume.sh` |

**Quick Start**:
```bash
cd scripts/setup
./setup.sh
python initialize_demo_data.py
```

## 👤 User Management

**Location**: `user-management/`

| Script | Purpose | Usage |
|--------|---------|-------|
| `create_test_user.py` | Create test user account | `python create_test_user.py` |

**Example**:
```bash
cd scripts/user-management
python create_test_user.py
```

## 🗄️ Database Scripts

**Location**: `database/`

| Script | Purpose | Usage |
|--------|---------|-------|
| `initialize_database.py` | Initialize database schema | `python initialize_database.py` |
| `reset_database.py` | Reset database (CAUTION) | `python reset_database.py` |
| `seed.py` | Seed database with data | `python seed.py` |
| `database_optimization.py` | Optimize database performance | `python database_optimization.py` |
| `database_health_monitor.py` | Monitor database health | `python database_health_monitor.py` |

**Seeders** (`database/seeders/`):
- `user_seeder.py` - Seed users
- `job_seeder.py` - Seed jobs
- `application_seeder.py` - Seed applications
- `precedent_seeder.py` - Seed precedents

**Example**:
```bash
cd scripts/database
python initialize_database.py
python seed.py
```

## 🧪 Testing Scripts

**Location**: `testing/`

| Script | Purpose | Usage |
|--------|---------|-------|
| `test_runner.py` | Run all tests | `python test_runner.py` |
| `test_orchestrator.py` | Orchestrate test suites | `python test_orchestrator.py` |
| `test_all_endpoints.sh` | Test all API endpoints | `./test_all_endpoints.sh` |
| `test-authentication.sh` | Test authentication flow | `./test-authentication.sh` |
| `ci_test_runner.sh` | CI/CD test runner | `./ci_test_runner.sh` |

**Example**:
```bash
cd scripts/testing
python test_runner.py
./test_all_endpoints.sh
```

## 🔐 Security Scripts

**Location**: `security/`

| Script | Purpose | Usage |
|--------|---------|-------|
| `security_audit.py` | Run security audit | `python security_audit.py` |
| `check_secrets.py` | Check for exposed secrets | `python check_secrets.py` |
| `rotate_api_keys.sh` | Rotate API keys | `./rotate_api_keys.sh` |
| `lock_env.sh` | Lock environment files | `./lock_env.sh` |

**Example**:
```bash
cd scripts/security
python security_audit.py
python check_secrets.py
```

## ⚡ Performance Scripts

**Location**: `performance/`

| Script | Purpose | Usage |
|--------|---------|-------|
| `performance_optimization_suite.py` | Full optimization suite | `python performance_optimization_suite.py` |
| `stress_test.py` | Load/stress testing | `python stress_test.py` |
| `database_test.py` | Database performance test | `python database_test.py` |
| `memory_test.py` | Memory usage testing | `python memory_test.py` |
| `test_load_performance.py` | Load performance test | `python test_load_performance.py` |
| `cost_efficiency_validator.py` | Validate cost efficiency | `python cost_efficiency_validator.py` |

**Example**:
```bash
cd scripts/performance
python stress_test.py
python database_test.py
```

## ✅ Verification Scripts

**Location**: `verify/`

| Script | Purpose | Usage |
|--------|---------|-------|
| `verify_deployment.py` | Verify deployment | `python verify_deployment.py` |
| `validate_pyproject.py` | Validate Python project | `python validate_pyproject.py` |
| `frontend.sh` | Verify frontend setup | `./frontend.sh` |

**Example**:
```bash
cd scripts/verify
python verify_deployment.py
```

## 🔧 Service Management

**Location**: `services/`

| Script | Purpose | Usage |
|--------|---------|-------|
| `celery_worker.sh` | Start Celery worker | `./celery_worker.sh` |
| `celery_beat.sh` | Start Celery beat scheduler | `./celery_beat.sh` |

**Example**:
```bash
cd scripts/services
./celery_worker.sh &
./celery_beat.sh &
```

## 📊 Analytics Scripts

**Location**: `analytics/`

| Script | Purpose | Usage |
|--------|---------|-------|
| `check_analytics_files.py` | Validate analytics files | `python check_analytics_files.py` |

## 🔄 Migration Scripts

**Location**: `migrations/`

| Script | Purpose | Usage |
|--------|---------|-------|
| `migrate_config.py` | Migrate configuration | `python migrate_config.py` |
| `migrate_blueprint.py` | Migrate blueprint files | `python migrate_blueprint.py` |

## 🏗️ Initialization Scripts

**Location**: `initialization/`

| Script | Purpose | Usage |
|--------|---------|-------|
| `initialize_services.py` | Initialize all services | `python initialize_services.py` |
| `initialize_vector_database.py` | Initialize ChromaDB | `python initialize_vector_database.py` |
| `setup_authentication.py` | Set up authentication | `python setup_authentication.py` |

## 📝 Reporting Scripts

**Location**: `reporting/`

| Script | Purpose | Usage |
|--------|---------|-------|
| `consolidation_final_report.py` | Generate consolidation report | `python consolidation_final_report.py` |

## 🧹 Cleanup Scripts (Temporary)

**Location**: `cleanup/`

⚠️ **These are temporary scripts used for one-time fixes. Archive after use.**

| Script | Purpose | Status |
|--------|---------|--------|
| `fix_console_logs.py` | Fix console.log statements | Completed |
| `fix_datetime_utcnow.py` | Fix datetime.utcnow usage | Completed |
| `validate_phase2.py` | Validate Phase 2 completion | Completed |
| `verify-all-fixes.sh` | Verify all fixes | Completed |
| `verify-fixes.sh` | Verify specific fixes | Completed |

## 📦 Deprecated Scripts

**Location**: `deprecated/`

⚠️ **Old scripts kept for reference. Do not use in production.**

| Script | Reason | Replacement |
|--------|--------|-------------|
| `create_moatasim_user.py` | User-specific | `user-management/create_test_user.py` |
| `setup_moatasim_user.py` | User-specific | `user-management/create_test_user.py` |
| `update_moatasim_skills.py` | User-specific | Database seeders |
| `update_skills_direct.py` | Old approach | Database seeders |
| `update_skills_simple.py` | Old approach | Database seeders |
| `update_user_to_moatasim.py` | User-specific | Database seeders |

## 🔨 Common Workflows

### Initial Setup

```bash
# 1. Set up environment
cd scripts/setup
./setup.sh

# 2. Initialize database
cd ../database
python initialize_database.py

# 3. Create test user
cd ../user-management
python create_test_user.py

# 4. Load demo data
cd ../setup
python initialize_demo_data.py
```

### Testing Workflow

```bash
# 1. Run unit tests
cd scripts/testing
python test_runner.py

# 2. Test API endpoints
./test_all_endpoints.sh

# 3. Test authentication
./test-authentication.sh
```

### Performance Testing

```bash
# 1. Run stress test
cd scripts/performance
python stress_test.py

# 2. Test database performance
python database_test.py

# 3. Run full optimization suite
python performance_optimization_suite.py
```

### Security Audit

```bash
# 1. Run security audit
cd scripts/security
python security_audit.py

# 2. Check for secrets
python check_secrets.py
```

### Deployment Verification

```bash
# 1. Verify deployment
cd scripts/verify
python verify_deployment.py

# 2. Verify frontend
./frontend.sh
```

## 🛠️ Development Guidelines

### Creating New Scripts

1. **Choose appropriate directory** based on script purpose
2. **Add shebang line**: `#!/usr/bin/env python3` or `#!/bin/bash`
3. **Make executable**: `chmod +x script_name.sh`
4. **Add docstring** explaining purpose and usage
5. **Update this README** with script information

### Script Template (Python)

```python
#!/usr/bin/env python3
"""
Script Name: example_script.py
Purpose: Brief description of what this script does
Usage: python example_script.py [arguments]
Author: Career Copilot Team
Date: YYYY-MM-DD
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main function."""
    logger.info("Script starting...")
    # Your code here
    logger.info("Script completed successfully")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
```

### Script Template (Bash)

```bash
#!/bin/bash
# Script Name: example_script.sh
# Purpose: Brief description
# Usage: ./example_script.sh
# Author: Career Copilot Team
# Date: YYYY-MM-DD

set -e  # Exit on error
set -u  # Exit on undefined variable

echo "Script starting..."

# Your code here

echo "Script completed successfully"
```

## 📚 Additional Resources

- [Installation Guide](../docs/setup/INSTALLATION.md)
- [Development Guide](../docs/development/DEVELOPMENT.md)
- [Deployment Guide](../docs/deployment/DEPLOYMENT.md)
- [Troubleshooting](../docs/troubleshooting/COMMON_ISSUES.md)

## 🤝 Contributing

When adding new scripts:

1. Place in appropriate directory
2. Follow naming conventions (lowercase with underscores)
3. Add comprehensive docstrings
4. Update this README
5. Test thoroughly before committing

## 📝 Notes

- **Backup scripts** before running destructive operations
- **Test in development** before running in production
- **Check logs** after running scripts
- **Archive completed** one-time scripts to `cleanup/`
- **Document** custom scripts with clear usage instructions

## 🆘 Support

For issues with scripts:
- Check script documentation (docstrings)
- Review [Troubleshooting Guide](../docs/troubleshooting/COMMON_ISSUES.md)
- Open an issue on [GitHub](https://github.com/moatasim-KT/career-copilot/issues)
- Contact: <moatasimfarooque@gmail.com>

---

**Last Updated**: November 7, 2025  
**Status**: Active Development
