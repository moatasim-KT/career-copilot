# Career Copilot Documentation

**Central documentation hub with direct codebase integration.**

## 🚀 Getting Started

New to Career Copilot? Start here:

1. **[[career-copilot/README|Project README]]** - Project overview and features
2. **[[LOCAL_SETUP]]** - Complete local development setup
3. **[[PROJECT_STATUS]]** - Current project status and architecture

## 📖 Core Documentation

### Setup & Development
- **[[LOCAL_SETUP]]** - Docker setup, configuration, common tasks, troubleshooting
- **[[DEVELOPER_GUIDE]]** - Development workflows and best practices
- **[[career-copilot/CONTRIBUTING|Contributing Guidelines]]** - Contribution guidelines and code standards
- **[[FRONTEND_QUICK_START]]** - Frontend-specific setup and patterns

### Project Management
- **[[PROJECT_STATUS]]** - Architecture, services, models, test coverage, known issues
- **[[CHANGELOG]]** - Version history and release notes

### User Guides
- **[[USER_GUIDE]]** - End-user documentation and tutorials
- **[[DEMO_VIDEO_GUIDE]]** - Video walkthroughs and demonstrations

## 🏗️ Architecture

### Backend Architecture
- **FastAPI Application**: `backend/app/main.py`
- **Core Configuration**: Core modules in `backend/app/core/`
  - Database: `backend/app/core/database.py`
  - Config: `backend/app/core/config.py`
  - Security: `backend/app/core/security.py`
  - Celery: `backend/app/core/celery_app.py`
  - WebSocket: `backend/app/core/websocket_manager.py`
  - Logging: `backend/app/core/logging.py`

### Service Layer
All business logic in `backend/app/services/`:

**Core AI & Job Services**:
- **LLM Service**: `backend/app/services/llm_service.py` (Multi-provider AI: GPT-4/Claude/Groq)
- **AI Service Manager**: `backend/app/services/ai_service_manager.py` (Compatibility layer for LLM)
- **Job Service**: `backend/app/services/job_service.py` (Job management & search)
- **Job Deduplication**: `backend/app/services/job_deduplication_service.py` (MinHash + Jaccard)
- **Job Scraping Service**: `backend/app/services/job_scraping_service.py` (Orchestrates 9 job boards)
- **Job Ingestion Service**: `backend/app/services/job_ingestion_service.py` (Background ingestion)
- **Job Recommendation**: `backend/app/services/job_recommendation_service.py` (AI-powered matching)

**Application & User Services**:
- **Application Service**: `backend/app/services/application_service.py` (Application tracking)
- **User Service**: `backend/app/services/user_service.py` (User management)
- **Profile Service**: `backend/app/services/profile_service.py` (User profiles)
- **Goal Service**: `backend/app/services/goal_service.py` (Career goals tracking)

**Communication & Notification**:
- **Notification Service**: `backend/app/services/notification_service.py` (Real-time notifications)
- **Email Service**: `backend/app/services/email_service.py` (Email delivery)
- **Slack Service**: `backend/app/services/slack_service.py` (Slack integration)
- **WebSocket Service**: `backend/app/services/websocket_service.py` (Real-time updates)

**Content Generation & Analysis**:
- **Content Generator**: `backend/app/services/content_generator_service.py` (Resume/cover letter AI)
- **Resume Parser**: `backend/app/services/resume_parser_service.py` (Resume parsing)
- **Skill Analysis**: `backend/app/services/skill_analysis_service.py` (Skill extraction)
- **Skill Gap Analyzer**: `backend/app/services/skill_gap_analyzer.py` (Gap identification)
- **Skill Matching**: `backend/app/services/skill_matching_service.py` (Job-skill matching)
- **Market Analysis**: `backend/app/services/market_analysis_service.py` (Market insights)

**Infrastructure & Management**:
- **Quota Manager**: `backend/app/services/quota_manager.py` (API quota & fallback management)
- **Cache Service**: `backend/app/services/cache_service.py` (Redis caching)
- **Analytics Service**: `backend/app/services/analytics_service.py` (Analytics & metrics)
- **Dashboard Service**: `backend/app/services/dashboard_service.py` (Dashboard data)
- **Monitoring Service**: `backend/app/services/monitoring_service.py` (Service health monitoring)
- **Observability Service**: `backend/app/services/observability_service.py` (Logging & tracing)

**Data Management**:
- **Vector Store**: `backend/app/services/vector_store_service.py` (ChromaDB embeddings)
- **Database Storage**: `backend/app/services/database_storage_service.py` (Storage management)
- **File Storage**: `backend/app/services/file_storage_integration.py` (File handling)
- **Import Service**: `backend/app/services/import_service.py` (Data import)
- **Export Service**: `backend/app/services/export_service.py` (Data export)
- **Backup Service**: `backend/app/services/backup_service.py` (Database backups)

**Security & Compliance**:
- **Encryption Service**: `backend/app/services/encryption_service.py` (Data encryption)
- **RBAC Service**: `backend/app/services/rbac_service.py` (Role-based access control)
- **Security Service**: `backend/app/services/security_service.py` (Security utilities)
- **Compliance Service**: `backend/app/services/compliance_service.py` (Compliance checks)
- **Audit Trail**: `backend/app/services/audit_trail_service.py` (Activity logging)

**External Integrations**:
- **LinkedIn Service**: `backend/app/services/linkedin_service.py` (LinkedIn API)
- **GitHub Service**: `backend/app/services/github_service.py` (GitHub integration)
- **HubSpot Service**: `backend/app/services/hubspot_service.py` (CRM integration)
- **OAuth Service**: `backend/app/services/oauth_service.py` (OAuth flows)
- **External Service Manager**: `backend/app/services/external_service_manager.py` (Manages external APIs)

**Utilities & Support**:
- **Template Service**: `backend/app/services/template_service.py` (Document templates)
- **Feedback Service**: `backend/app/services/feedback_service.py` (User feedback)
- **Briefing Service**: `backend/app/services/briefing_service.py` (Daily briefings)
- **Interview Practice**: `backend/app/services/interview_practice_service.py` (Interview prep)
- **Career Resources**: `backend/app/services/career_resources_service.py` (Career guides)
- **Progress Tracker**: `backend/app/services/progress_tracker.py` (Progress tracking)

### API Routes
All endpoints in `backend/app/api/v1/`:

**Authentication & Users**:
- **Auth**: `backend/app/api/v1/auth.py` (JWT authentication, login, register)
- **Users**: `backend/app/api/v1/users.py` (User management, profiles)
- **OAuth**: `backend/app/api/v1/oauth.py` (OAuth integrations)

**Job Management**:
- **Jobs**: `backend/app/api/v1/jobs.py` (Job search, filtering, recommendations)
- **Job Sources**: `backend/app/api/v1/job_sources.py` (Job source configuration)
- **Job Ingestion**: `backend/app/api/v1/job_ingestion.py` (Manual job ingestion)
- **LinkedIn Jobs**: `backend/app/api/v1/linkedin_jobs.py` (LinkedIn integration)
- **Saved Searches**: `backend/app/api/v1/saved_searches.py` (Save search filters)

**Application Tracking**:
- **Applications**: `backend/app/api/v1/applications.py` (Application CRUD, status tracking)
- **Bulk Operations**: `backend/app/api/v1/bulk_operations.py` (Batch updates)
- **Progress**: `backend/app/api/v1/progress.py` (Application progress tracking)
- **Goals**: `backend/app/api/v1/goals.py` (Career goals)

**Communication**:
- **Notifications**: `backend/app/api/v1/notifications.py` (Notification management)
- **WebSocket**: `backend/app/api/v1/websocket.py` (Real-time updates)
- **WebSocket Notifications**: `backend/app/api/v1/websocket_notifications.py` (WebSocket-based notifications)
- **Email**: `backend/app/api/v1/email.py` (Email operations)
- **Slack**: `backend/app/api/v1/slack.py` (Slack integration)
- **Slack Integration**: `backend/app/api/v1/slack_integration.py` (Extended Slack features)

**Content & Documents**:
- **Content**: `backend/app/api/v1/content.py` (AI content generation)
- **Resume**: `backend/app/api/v1/resume.py` (Resume operations)
- **Upload**: `backend/app/api/v1/upload.py` (File uploads)
- **Cloud Storage**: `backend/app/api/v1/cloud_storage.py` (Cloud file management)

**Analytics & Insights**:
- **Analytics**: `backend/app/api/v1/analytics.py` (Analytics endpoints)
- **Dashboard**: `backend/app/api/v1/dashboard.py` (Dashboard data)
- **Dashboard Layouts**: `backend/app/api/v1/dashboard_layouts.py` (Dashboard customization)
- **Market**: `backend/app/api/v1/market.py` (Market trends)
- **Market Analysis**: `backend/app/api/v1/market_analysis.py` (Detailed market insights)
- **Skill Gap Analysis**: `backend/app/api/v1/skill_gap_analysis.py` (Skill gaps)
- **Skill Matching**: `backend/app/api/v1/skill_matching.py` (Job-skill matching)

**Recommendations & Personalization**:
- **Recommendations**: `backend/app/api/v1/recommendations.py` (Job recommendations)
- **Enhanced Recommendations**: `backend/app/api/v1/enhanced_recommendations.py` (Advanced AI recommendations)
- **Job Recommendation Feedback**: `backend/app/api/v1/job_recommendation_feedback.py` (Feedback loop)
- **Personalization**: `backend/app/api/v1/personalization.py` (User preferences)

**System & Admin**:
- **Health**: `backend/app/api/v1/health.py` (System health checks)
- **Metrics**: `backend/app/api/v1/metrics.py` (System metrics)
- **Cache**: `backend/app/api/v1/cache.py` (Cache management)
- **Cache Admin**: `backend/app/api/v1/cache_admin.py` (Cache administration)
- **Configuration**: `backend/app/api/v1/configuration.py` (System configuration)
- **Database Admin**: `backend/app/api/v1/database_admin.py` (Database management)
- **Database Performance**: `backend/app/api/v1/database_performance.py` (DB optimization)
- **Database Migrations**: `backend/app/api/v1/database_migrations.py` (Migration management)
- **Vector Store Admin**: `backend/app/api/v1/vector_store_admin.py` (ChromaDB admin)

**AI & LLM**:
- **LLM**: `backend/app/api/v1/llm.py` (LLM operations)
- **LLM Admin**: `backend/app/api/v1/llm_admin.py` (LLM configuration)
- **Groq**: `backend/app/api/v1/groq.py` (Groq provider endpoints)

**Import/Export & Data Management**:
- **Import Data**: `backend/app/api/v1/import_data.py` (Data import)
- **Export**: `backend/app/api/v1/export.py` (Data export)
- **Feedback**: `backend/app/api/v1/feedback.py` (User feedback)
- **Feedback Analysis**: `backend/app/api/v1/feedback_analysis.py` (Feedback analytics)

**Extended Features**:
- **Interview**: `backend/app/api/v1/interview.py` (Interview practice)
- **Learning**: `backend/app/api/v1/learning.py` (Learning resources)
- **Resources**: `backend/app/api/v1/resources.py` (Career resources)
- **Help Articles**: `backend/app/api/v1/help_articles.py` (Help documentation)
- **Briefings**: `backend/app/api/v1/briefings.py` (Daily briefings)
- **Scheduled Reports**: `backend/app/api/v1/scheduled_reports.py` (Automated reports)
- **Reporting Insights**: `backend/app/api/v1/reporting_insights.py` (Report generation)

**Integrations & Services**:
- **External Services**: `backend/app/api/v1/external_services.py` (External API management)
- **Services Admin**: `backend/app/api/v1/services_admin.py` (Service administration)
- **Integrations Admin**: `backend/app/api/v1/integrations_admin.py` (Integration management)
- **Social**: `backend/app/api/v1/social.py` (Social features)
- **Workflows**: `backend/app/api/v1/workflows.py` (Workflow automation)

**Background Tasks**:
- **Background Tasks**: `backend/app/api/v1/background_tasks.py` (Task management)
- **Tasks**: `backend/app/api/v1/tasks.py` (Celery task operations)
- **Realtime Status**: `backend/app/api/v1/realtime_status.py` (Task status updates)

**Security & Monitoring**:
- **Data Security**: `backend/app/api/v1/data_security.py` (Security operations)
- **Security Validation**: `backend/app/api/v1/security_validation.py` (Security checks)
- **Email Admin**: `backend/app/api/v1/email_admin.py` (Email configuration)
- **Storage Admin**: `backend/app/api/v1/storage_admin.py` (Storage management)
- **Progress Admin**: `backend/app/api/v1/progress_admin.py` (Progress administration)
- **Status Admin**: `backend/app/api/v1/status_admin.py` (Status management)

**Specialized Services**:
- **Offline**: `backend/app/api/v1/offline.py` (Offline mode support)
- **Migrations**: `backend/app/api/v1/migrations.py` (Data migrations)
- **Migration Strategy**: `backend/app/api/v1/migration_strategy.py` (Migration planning)
- **Load Balancer**: `backend/app/api/v1/load_balancer.py` (Load balancing)
- **Production Optimization**: `backend/app/api/v1/production_optimization.py` (Performance tuning)
- **Production Orchestration**: `backend/app/api/v1/production_orchestration.py` (Deployment orchestration)
- **System Integration**: `backend/app/api/v1/system_integration.py` (System integrations)
- **Service Management**: `backend/app/api/v1/service_management.py` (Service lifecycle)
- **Cost Management**: `backend/app/api/v1/cost_management.py` (Cost tracking)
- **Agent Cache**: `backend/app/api/v1/agent_cache.py` (Agent caching)

**Webhooks**:
- **SendGrid Webhooks**: `backend/app/api/v1/sendgrid_webhooks.py` (Email event webhooks)

### Database Models
All models in `backend/app/models/`:
- **User**: `backend/app/models/user.py`
- **Job**: `backend/app/models/job.py`
- **Application**: `backend/app/models/application.py`
- **Notification**: `backend/app/models/notification.py`
- **Template**: `backend/app/models/template.py`
- **Document**: `backend/app/models/document.py`
- **Goal**: `backend/app/models/goal.py`

### Background Tasks
Celery tasks in `backend/app/tasks/`:
- **Job Ingestion**: `backend/app/tasks/job_ingestion_tasks.py`
- **Notifications**: `backend/app/tasks/notification_tasks.py`

### Frontend Architecture
- **Next.js App Router**: Frontend application in [[frontend/src/app/]]
  - **Dashboard**: `frontend/src/app/dashboard/` (Main dashboard pages)
  - **Jobs**: `frontend/src/app/jobs/` (Job search & browsing)
  - **Applications**: `frontend/src/app/applications/` (Application tracking)
  - **Analytics**: `frontend/src/app/analytics/` (Analytics dashboards)
  - **Notifications**: `frontend/src/app/notifications/` (Notification center)
  - **Settings**: `frontend/src/app/settings/` (User settings)
  - **Resume**: `frontend/src/app/resume/` (Resume management)
  - **Interview Practice**: `frontend/src/app/interview-practice/` (Interview prep)
  - **Recommendations**: `frontend/src/app/recommendations/` (Job recommendations)
  - **Content Generation**: `frontend/src/app/content-generation/` (AI content tools)
  - **Advanced Features**: `frontend/src/app/advanced-features/` (Premium features)
  - **Design System**: `frontend/src/app/design-system/` (Component showcase)
  - **Help**: `frontend/src/app/help/` (Help & support)
  - **Health**: `frontend/src/app/health/` (System health)
  - **Offline**: `frontend/src/app/offline/` (Offline mode)

- **Components**: UI components in [[frontend/src/components/]]
  - **UI Components**: `frontend/src/components/ui/` (shadcn/ui primitives)
  - **Applications**: `frontend/src/components/applications/` (Application management)
  - **Jobs**: `frontend/src/components/jobs/` (Job listings)
  - **Dashboard**: `frontend/src/components/dashboard/` (Dashboard widgets)
  - **Analytics**: `frontend/src/components/analytics/` (Analytics charts)
  - **Notifications**: `frontend/src/components/notifications/` (Notification UI)
  - **Forms**: `frontend/src/components/forms/` (Form components)
  - **Layout**: `frontend/src/components/layout/` (Layout components)
  - **Charts**: `frontend/src/components/charts/` (Chart components)
  - **Features**: `frontend/src/components/features/` (Feature-specific)
  - **Lazy Loading**: `frontend/src/components/lazy/` (Code splitting)
  - **Loading States**: `frontend/src/components/loading/` (Loading UI)
  - **Help**: `frontend/src/components/help/` (Help system)
  - **Onboarding**: `frontend/src/components/onboarding/` (User onboarding)
  - **Settings**: `frontend/src/components/settings/` (Settings UI)
  - **Social**: `frontend/src/components/social/` (Social features)
  - **Kanban**: `frontend/src/components/kanban/` (Kanban board)
  - **Recommendations**: `frontend/src/components/recommendations/` (Recommendation cards)
  - **Filters**: `frontend/src/components/filters/` (Filter components)
  - **Bulk Operations**: `frontend/src/components/bulk/` (Bulk actions)
  - **Monitoring**: `frontend/src/components/monitoring/` (System monitoring)
  - **Providers**: `frontend/src/components/providers/` (Context providers)

- **API Client**: `frontend/src/lib/api/client.ts` (Unified API client with type safety)
- **Utilities**: Utility libraries in `frontend/src/lib/`
  - **Hooks**: `frontend/src/lib/hooks/` (Custom React hooks)
  - **Utils**: `frontend/src/lib/utils/` (Utility functions)

## 🎨 Frontend Features

### Frontend Documentation Hub
- **[[frontend/docs/README|Complete Frontend Features Guide]]** - Comprehensive frontend documentation
  - **Performance**: Lazy loading, code splitting, loading states
  - **UI Components**: DataTable, Card2 enhancements, dark mode
  - **Domain Features**: Jobs module, Applications module
  - **Integration**: Sentry error monitoring, contextual help
  - **Testing**: Dark mode tests, UI component tests, accessibility tests
  - **Frontend-Backend**: API client, endpoint discovery, gap analysis

### Key Frontend Features
- **[[frontend/src/components/lazy/README|Lazy Loading]]** - Code splitting & performance
  - [[frontend/src/components/lazy/USAGE_EXAMPLES|Usage Examples]]
- **[[frontend/src/components/ui/loading/README|Loading States]]** - Skeleton loaders & suspense
- **[[frontend/src/components/ui/DataTable/README|DataTable Component]]** - Advanced data tables
  - [[frontend/src/components/ui/DataTable/INTEGRATION_GUIDE|Integration Guide]]
- **[[frontend/src/lib/SENTRY_INTEGRATION_GUIDE|Sentry Integration]]** - Error monitoring
- **[[frontend/src/components/help/CONTEXTUAL_HELP_INTEGRATION_GUIDE|Contextual Help]]** - User guidance

### Domain Components
- **[[frontend/src/components/jobs/README|Jobs Module]]** - Job search & tracking
  - [[frontend/src/components/jobs/INTEGRATION_GUIDE|Integration Guide]]
- **[[frontend/src/components/applications/README|Applications Module]]** - Application management
  - [[frontend/src/components/applications/QUICK_START|Quick Start]]
  - [[frontend/src/components/applications/INTEGRATION_GUIDE|Integration Guide]]

### Frontend Testing
- **[[frontend/src/components/ui/__tests__/README|UI Component Tests]]**
- **Dark Mode Tests**:
  - [[frontend/src/components/ui/__tests__/DARK_MODE_TEST_REPORT|Test Report]]
  - [[frontend/src/components/ui/__tests__/DARK_MODE_VERIFICATION|Verification]]
  - [[frontend/src/components/ui/__tests__/DARK_MODE_MANUAL_TEST_CHECKLIST|Manual Checklist]]
- **Card2 Enhancement Tests**:
  - [[frontend/src/components/ui/__tests__/Card2.implementation-summary|Implementation]]
  - [[frontend/src/components/ui/__tests__/Card2.verification|Verification]]
  - [[frontend/src/components/ui/__tests__/Card2.before-after|Before/After]]
- **Dashboard Tests**:
  - [[frontend/src/components/pages/__tests__/Dashboard.implementation-summary|Implementation]]
  - [[frontend/src/components/pages/__tests__/Dashboard.contrast-verification|Contrast Verification]]

### Frontend-Backend Integration
- **[[backend/app/testing/README|Endpoint Discovery Framework]]** - Automatic endpoint detection
- **[[backend/app/testing/README_GAP_ANALYSIS|Gap Analysis System]]** - Frontend-backend mismatch detection

## 🔧 Development Utilities

### Utility Scripts
- **[[../scripts/README|Scripts Directory]]** - All development utility scripts organized by category

**Analysis & Code Generation**:
- **[[../scripts/analyze_api_endpoints.py|API Endpoint Analyzer]]** - Generates comprehensive API endpoint documentation
- **[[../scripts/analyze_database_schema.py|Database Schema Analyzer]]** - Analyzes SQLAlchemy models and generates ERD
- **[[../scripts/analyze-components.ts|Component Analyzer]]** - Analyzes React components structure
- **[[../scripts/generate_openapi_docs.py|OpenAPI Generator]]** - Generates OpenAPI documentation from FastAPI
- **[[../scripts/create_missing_routers.py|Router Scaffolder]]** - Creates missing API router files

**Documentation & Validation**:
- **[[../scripts/check_wikilinks.py|WikiLink Validator]]** - Validates documentation wikilinks and network health
- **[[../scripts/monitor_docs_health.py|Documentation Health Monitor]]** - Monitors documentation completeness and quality
- **[[../scripts/update_architecture_diagrams.py|Architecture Diagram Updater]]** - Updates architecture diagrams from code

**Testing & Quality**:
- **[[../scripts/test_all_apis.py|API Test Suite]]** - Comprehensive API endpoint testing
- **[[../scripts/test_all_endpoints.sh|Endpoint Test Runner]]** - Shell script for endpoint testing
- **[[../scripts/runtime-smoke.js|Runtime Smoke Tests]]** - Frontend runtime smoke tests

**Specialized Scripts** (by directory):
- **[[../scripts/setup/|Setup Scripts]]** - Initial setup and installation
- **[[../scripts/database/|Database Scripts]]** - Database operations and migrations
- **[[../scripts/testing/|Testing Scripts]]** - Test runners and validation
- **[[../scripts/security/|Security Scripts]]** - Security audits and key management
- **[[../scripts/performance/|Performance Scripts]]** - Performance testing and optimization
- **[[../scripts/analytics/|Analytics Scripts]]** - Analytics validation
- **[[../scripts/services/|Service Scripts]]** - Service management (Celery, etc.)
- **[[../scripts/reporting/|Reporting Scripts]]** - Report generation
- **[[../scripts/cleanup/|Cleanup Scripts]]** - Maintenance and cleanup tasks

## 🧪 Testing

### Backend Testing
- **Test Documentation**: [[backend/tests/TESTING_NOTES]]
- **Test Configuration**: `backend/pytest.ini`
- **Test Fixtures**: [[backend/tests/conftest.py]]
- **Unit Tests**: Backend unit tests in backend/tests/unit/
- **Integration Tests**: Backend integration tests in backend/tests/integration/

### Frontend Testing
See [[#Frontend Testing]] section above for:
- UI Component Tests
- Dark Mode Tests (verification, reports, checklists)
- Card2 Enhancement Tests
- Dashboard Tests (contrast, implementation)

### Integration Testing
- **[[../backend/app/testing/README.md|Endpoint Discovery]]** - Automatic endpoint testing
- **[[../backend/app/testing/README_GAP_ANALYSIS.md|Gap Analysis]]** - Frontend-backend integration validation

## ⚙️ Configuration

### Environment Configuration
- **Backend Environment**: [[../backend/.env.example]] → Copy to `backend/.env`
- **Frontend Environment**: [[../frontend/.env.example]] → Copy to `frontend/.env`

### Config Files
- **LLM Providers**: [[../config/llm_config.json]] (OpenAI, Groq, Anthropic)
- **Feature Flags**: [[../config/feature_flags.json]]
- **Application Config**: [[../config/application.yaml]]
- **Linting**: [[../config/ruff.toml]]
- **Spell Check**: [[../config/cspell.json]]

### Docker & Deployment
- **Docker Compose**: [[../docker-compose.yml]] (All services)
- **Backend Dockerfile**: [[../deployment/docker/Dockerfile.backend]]
- **Frontend Dockerfile**: [[../deployment/docker/Dockerfile.frontend]]
- **Nginx Config**: [[../deployment/nginx/]]
- **Init SQL**: [[../backend/init.sql]]

### Build & Development
- **Makefile**: `Makefile` at project root (All development commands)
- **Package Config**: [[../backend/pyproject.toml]]
- **TypeScript Config**: [[../frontend/tsconfig.json]]
- **ESLint Config**: [[../frontend/eslint.config.mjs]]

## 📚 Additional Documentation

### Architecture Docs
- **[[architecture/ARCHITECTURE.md]]** - System architecture overview
- **[[architecture/database-schema.md]]** - Database design and relationships
- **[[architecture/job-services-architecture.md]]** - Job services design
- **[[architecture/security-architecture.md]]** - Security design and patterns
- **[[architecture/api-architecture.md]]** - API architecture
- **[[architecture/data-architecture.md]]** - Data layer design
- **[[architecture/performance-architecture.md]]** - Performance optimization
- **[[architecture/ARCHITECTURE]]** - All architecture documents

### API Documentation
- **[[API]]** - Complete API reference
- **OpenAPI**: http://localhost:8000/docs (when running)

### Setup & Configuration
- **[[INSTALLATION]]** - Detailed installation guide
- **[[CONFIGURATION]]** - Configuration reference
- **[[JOB_DATA_SOURCES]]** - Job data sources and web scraping setup

### Deployment
- **[[DEPLOYMENT]]** - Production deployment guide
- **[[deployment/README|Deployment README]]** - Deployment documentation
- **[[deployment/PRODUCTION_CHECKLIST]]** - Pre-deployment checklist

### Development Guides
- **[[DEVELOPMENT]]** - Development workflow
- **[[testing-strategies]]** - Testing best practices
- **[[code-patterns]]** - Code patterns and examples
- **[[workflow-documentation]]** - Git workflow

### Troubleshooting
- **[[COMMON_ISSUES]]** - Common issues and solutions
- **[[RUNBOOK]]** - Operations runbook

### Design Decisions
- **[[adr-index]]** - Architectural decision records (ADRs)

## 🔗 Quick Links

**Development Commands** (see `Makefile` at project root):
```bash
make install          # Install all dependencies
make dev-setup        # Complete dev environment
make test             # Run all tests
make quality-check    # Lint, type-check, security
make format           # Auto-format code
```

**Docker Commands** (see [[LOCAL_SETUP]]):
```bash
docker-compose up -d                        # Start all services
docker-compose exec backend alembic upgrade head  # Run migrations
docker-compose logs -f backend              # View logs
```

**Access Points**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Database: postgresql://postgres:postgres@localhost:5432/career_copilot

## 🆘 Need Help?

1. **Setup Issues**: See [[LOCAL_SETUP]] and [[COMMON_ISSUES]]
2. **Test Issues**: See [[../backend/tests/TESTING_NOTES.md]]
3. **Code Patterns**: See [[../.github/copilot-instructions.md]]
4. **Project Status**: See [[../PROJECT_STATUS.md]]
5. **Development**: See [[development/DEVELOPMENT.md]] and [[DEVELOPER_GUIDE.md]]

---

*Documentation maintained as part of the codebase. All links reference actual files.*