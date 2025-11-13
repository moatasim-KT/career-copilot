# Code-Level TODOs & Placeholders

This document contains granular implementation items found directly in the codebase, indicating areas for future work or temporary implementations.

## Backend Code TODOs

### Security & Credentials

#### [[security-placeholders.md|Security Placeholders]]
- **Status**: ❌ Not Started
- **Description**: Replace hardcoded placeholder tokens and passwords
- **Specific Issues**:
  - `placeholder_token` in `bandit_report.json`
  - `oauth_` prefixed passwords in security scripts
  - `scripts/security/restore_root_env_from_secrets.py`
- **Priority**: 🔴 Critical
- **Related Files**:
  - `scripts/security/`
  - `bandit_report.json`

### Database & Models

#### [[database-models.md|Database Model Extensions]]
- **Status**: ❌ Not Started
- **Description**: Missing document and goal models
- **Specific Issues**:
  - `# TODO: Create document model` in `profile_service.py`
  - `# TODO: Create goal model` in `backup_service.py`
  - `"""Contract analysis database model (placeholder for compatibility)."""` in `database_models.py`
- **Related Files**:
  - `backend/app/models/database_models.py`
  - `backend/app/services/profile_service.py`
  - `backend/app/services/backup_service.py`

#### [[async-queries.md|Async Query Conversion]]
- **Status**: ❌ Not Started
- **Description**: Convert synchronous database queries to async
- **Specific Issues**:
  - `# TODO: Convert to async queries` in `scripts/database/convert_to_async.py`
- **Related Files**:
  - `scripts/database/convert_to_async.py`

### Service Layer Placeholders

#### [[service-placeholders.md|Service Implementation Placeholders]]
- **Status**: ❌ Not Started
- **Description**: Various service classes with placeholder implementations
- **Specific Services**:
  - `chroma_health_monitor.py`: Slack health alerts
  - `analytics_service.py`: Risk trend analysis, contract comparison
  - `llm_config_manager.py`: Accuracy evaluation checks
  - `slack_service.py`: Message templates
  - `integration_service.py`: Fallback with placeholder doc id
  - `template_service.py`: ATS compatibility and readability scores
  - `job_service.py`: User object placeholder
  - `scheduled_notification_service.py`: Interview tracking placeholders
  - `cloud.py`: Cloud storage implementation
  - `job_source_manager.py`: Summary and trend building
  - `task_queue_manager.py`: Returns placeholder
  - `intelligent_cache_service.py`: Returns placeholder or raises error
  - `analytics_processing_service.py`: Returns placeholder
  - `recommendation_engine.py`: Scoring placeholder
  - `briefing_service.py`: Integration with recommendations
  - `sharding_migration_strategy_service.py`: Returns placeholder structure
  - `task_handlers.py`: Registry placeholder
  - `scraping/themuse_scraper.py`: Placeholder values treatment
  - `job_scraping_service.py`: Rate limiting and quota management
- **Related Files**:
  - `backend/app/services/`

### API Endpoint TODOs

#### [[api-endpoints.md|API Endpoint Implementation]]
- **Status**: ❌ Not Started
- **Description**: API endpoints with placeholder implementations or missing features
- **Specific Issues**:
  - `enhanced_recommendations.py`: `return True` placeholders
  - `skill_gap_analysis.py`: `data_freshness: "placeholder"`
  - `help_articles.py`: Missing relevance scoring
  - `advanced_user_analytics.py`: Returns placeholder structure
  - `database_performance.py`: Returns placeholder data
  - `job_ingestion.py`: Missing admin permission check
  - `feedback.py`: Missing async query conversion
  - `resume.py`: Missing schema definitions
- **Related Files**:
  - `backend/app/api/v1/`

### Core & Utilities

#### [[core-utilities.md|Core Utilities Enhancement]]
- **Status**: ❌ Not Started
- **Description**: Core system utilities requiring implementation
- **Specific Issues**:
  - `docstring_enhancer.py`: Basic placeholder using function name
  - `alerting.py`: Evaluate all alert rules
  - `optimized_database.py`: Parameter placeholder normalization
  - `monitoring.py`: Placeholder metrics values
- **Related Files**:
  - `backend/app/core/`
  - `backend/app/utils/`

## Frontend Code TODOs

### Component Implementation

#### [[component-placeholders.md|Component Placeholders]]
- **Status**: ❌ Not Started
- **Description**: UI components with placeholder functionality
- **Specific Issues**:
  - `LazyRichTextEditor.tsx`: Future rich text editor integration
  - `ApplicationKanban.tsx`: Add application modal implementation
  - `benchmark.ts`: Job benchmarking functionality
- **Related Files**:
  - `frontend/src/components/`

### Testing Infrastructure

#### [[frontend-testing.md|Frontend Testing Setup]]
- **Status**: ❌ Not Started
- **Description**: Testing infrastructure issues and setup
- **Specific Issues**:
  - `Auth.test.tsx`: MSW setup or migration needed
- **Related Files**:
  - `frontend/src/__tests__/`
  - `frontend/tests/`

---

*For broader architectural context, see [[backend-gaps.md]] and [[frontend-gaps.md]]*