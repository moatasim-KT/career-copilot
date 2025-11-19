# Career Copilot Services Directory

---
## 🧭 Quick Navigation

- [[PLAN]] – Project Plan
- [[TESTING_AND_UI_REFACTORING_OVERVIEW]] – Testing & UI Refactoring Overview
- [[COMPONENT_LIBRARY_INVENTORY.md]] – Component Inventory
- [[DESIGN_SYSTEM.md]] – Design System Guide
- [[ERROR_HANDLING_GUIDE.md]] – Error Handling Guide
- [[E2E_TESTING_MIGRATION.md]] – E2E Testing Migration Guide
- [[docs/DEVELOPER_GUIDE]] – Developer Guide
- [[TODO.md]] – Todo List
- [[FRONTEND_QUICK_START.md]] – Frontend Quick Start
- [[USER_GUIDE.md]] – User Guide
- [[ENVIRONMENT_CONFIGURATION.md]] – Environment Configuration
---

Comprehensive index of all backend services organized by category.

**Quick Links**: [[../../README|Project README]] | [[../../docs/DEVELOPER_GUIDE|Developer Guide]] | [[../../docs/architecture/ARCHITECTURE|Architecture]] | [[../../PROJECT_STATUS|Project Status]]

## 📋 Service Categories

- [Core Business Logic](#core-business-logic) - Job management, applications, recommendations
- [AI & Content Generation](#ai--content-generation) - LLM services, content generation, skill analysis
- [Job Scraping](#job-scraping) - Multi-source job board scrapers
- [Data Processing](#data-processing) - Parsing, deduplication, migration
- [User Management](#user-management) - Authentication, profiles, settings
- [Notifications & Communication](#notifications--communication) - Email, Slack, WebSocket
- [Analytics & Reporting](#analytics--reporting) - Metrics, analytics, reports
- [Storage & Caching](#storage--caching) - Database, file storage, caching
- [Security & Compliance](#security--compliance) - Encryption, RBAC, audit trails
- [Integration & External APIs](#integration--external-apis) - OAuth, GitHub, HubSpot, LinkedIn
- [Monitoring & Health](#monitoring--health) - Health checks, observability, logging
- [Utilities & Infrastructure](#utilities--infrastructure) - Task queues, compression, error handling

---

## Core Business Logic

### Job Management
- **[[job_service.py|JobManagementSystem]]** - Consolidated job CRUD, scraping coordination, recommendations, deduplication
  - *Primary service for all job-related operations*
  - *Integrates 9+ job board scrapers with AI-powered recommendations*
  - *See: [[../../docs/architecture/job-services-architecture|Job Services Architecture]]*

- **[[job_scraping_service.py|JobScrapingService]]** - Legacy job scraping orchestration (use JobManagementSystem instead)

- **[[job_recommendation_service.py|JobRecommendationService]]** - AI-powered job recommendations with skill matching

- **[[job_ingestion_service.py|JobIngestionService]]** - User-specific job ingestion workflows

- **[[job_source_manager.py|JobSourceManager]]** - Manages job source configurations and priorities

### Application Tracking
- **[[application_service.py|ApplicationService]]** - Application lifecycle management (create, update, status tracking)
  - *Status transitions: Applied → Interviewing → Offered → Accepted/Rejected*

- **[[bulk_operations_service.py|BulkOperationsService]]** - Batch operations on applications (status updates, exports, deletions)

### Career Resources
- **[[career_resources_service.py|CareerResourcesService]]** - Career guidance content and resources

- **[[goal_service.py|GoalService]]** - User career goals tracking and progress monitoring

- **[[interview_practice_service.py|InterviewPracticeService]]** - Interview preparation and practice sessions

---

## AI & Content Generation

### LLM Services
- **[[llm_service.py|LLMService]]** - Unified multi-provider LLM service (OpenAI, Anthropic, Groq)
  - *Intelligent model selection based on task complexity*
  - *Automatic fallback and cost optimization*
  - *See: [[../../config/llm_config.json|LLM Configuration]]*

- **[[llm_service_plugin.py|LLMServicePlugin]]** - Plugin architecture for extending LLM capabilities

- **[[llm_config_manager.py|LLMConfigManager]]** - Dynamic LLM configuration management

- **[[ai_service_manager.py|AIServiceManager]]** - Orchestrates multiple AI services

### Content Generation
- **[[content_generator_service.py|ContentGeneratorService]]** - Resume and cover letter AI generation

- **[[content_quality_service.py|ContentQualityService]]** - Content quality assessment and validation

- **[[template_service.py|TemplateService]]** - Document template management (resume, cover letter templates)

### Skill Analysis
- **[[skill_analysis_service.py|SkillAnalysisService]]** - Skill extraction and analysis from job postings

- **[[skill_matching_service.py|SkillMatchingService]]** - Candidate-to-job skill matching algorithms

- **[[skill_gap_analyzer.py|SkillGapAnalyzer]]** - Identifies skill gaps and recommends learning paths

- **[[language_processor.py|LanguageProcessor]]** - Natural language processing for skill normalization

---

## Job Scraping

### Scraper Management
- **[[scraping/scraper_manager.py|ScraperManager]]** - Coordinates all job board scrapers with rate limiting
  - *Manages 15+ scraper implementations*
  - *See: [[scraping/|Scraping Directory]]*

- **[[scraping/base_scraper.py|BaseScraper]]** - Abstract base class for all scrapers

- **[[scraping/harness.py|ScraperHarness]]** - Testing harness for scraper validation

### Job Board Scrapers
- **[[scraping/linkedin_scraper.py|LinkedInScraper]]** - LinkedIn job scraper (Selenium-based, requires auth)
- **[[scraping/indeed_scraper.py|IndeedScraper]]** - Indeed job scraper (BeautifulSoup)
- **[[scraping/adzuna_scraper.py|AdzunaScraper]]** - Adzuna API scraper
- **[[scraping/arbeitnow_scraper.py|ArbeitnowScraper]]** - Arbeitnow EU tech jobs
- **[[scraping/berlinstartupjobs_scraper.py|BerlinStartupJobsScraper]]** - Berlin startup ecosystem
- **[[scraping/relocateme_scraper.py|RelocateMeScraper]]** - Relocation support jobs
- **[[scraping/eures_scraper.py|EURESScraper]]** - European Employment Services
- **[[scraping/landingjobs_scraper.py|LandingJobsScraper]]** - Portuguese tech jobs
- **[[scraping/eutechjobs_scraper.py|EUTechJobsScraper]]** - EU tech job aggregator
- **[[scraping/eurotechjobs_scraper.py|EuroTechJobsScraper]]** - European tech jobs
- **[[scraping/aijobs_scraper.py|AIJobsScraper]]** - AI/ML specialized jobs
- **[[scraping/datacareer_scraper.py|DataCareerScraper]]** - Data science career jobs
- **[[scraping/angellist_scraper.py|AngelListScraper]]** - Startup jobs from AngelList
- **[[scraping/themuse_scraper.py|TheMuseScraper]]** - The Muse job board
- **[[scraping/rapidapi_jsearch_scraper.py|RapidAPIJSearchScraper]]** - RapidAPI JSearch integration
- **[[scraping/firecrawl_scraper.py|FirecrawlScraper]]** - Firecrawl web scraping service
- **[[scraping/eu_company_playwright_scraper.py|EUCompanyPlaywrightScraper]]** - EU company career pages (Playwright)

---

## Data Processing

### Parsing & Extraction
- **[[job_description_parser_service.py|JobDescriptionParserService]]** - Extracts structured data from job descriptions

- **[[resume_parser_service.py|ResumeParserService]]** - Resume parsing and data extraction

- **[[file_processing_service.py|FileProcessingService]]** - Generic file upload and processing

- **[[pdf_processing_service.py|PDFProcessingService]]** - PDF document processing and text extraction

### Deduplication
- **[[job_deduplication_service.py|JobDeduplicationService]]** - Advanced job duplicate detection
  - *MinHash + Jaccard similarity (0.85 threshold)*
  - *Fuzzy matching for titles and companies*
  - *95%+ detection accuracy*

### Data Migration
- **[[data_migration_service.py|DataMigrationService]]** - Database schema migrations and data transformations

- **[[sharding_migration_strategy_service.py|ShardingMigrationStrategyService]]** - Database sharding migration strategies

- **[[database_seeder.py|DatabaseSeeder]]** - Development database seeding with sample data

---

## User Management

### Authentication & Authorization
- **[[user_service.py|UserService]]** - User CRUD operations and account management

- **[[rbac_service.py|RBACService]]** - Role-Based Access Control implementation

- **[[api_key_service.py|APIKeyService]]** - API key generation and validation

### User Data
- **[[profile_service.py|ProfileService]]** - User profile management (skills, preferences, experience)

- **[[user_settings_service.py|UserSettingsService]]** - User preferences and application settings

- **[[progress_tracker.py|ProgressTracker]]** - Tracks user progress and achievements

---

## Notifications & Communication

### Email
- **[[email_service.py|EmailService]]** - Email sending via SMTP/SendGrid

- **[[email_template_manager.py|EmailTemplateManager]]** - Email template rendering and management

### Multi-Channel Notifications
- **[[notification_service.py|NotificationService]]** - Unified notification service (email, WebSocket, push)
  - *Supports email digests (immediate, daily, weekly)*
  - *Real-time WebSocket notifications*

- **[[slack_service.py|SlackService]]** - Slack integration for notifications and bot commands

- **[[slack_bot_commands.py|SlackBotCommands]]** - Slack bot command handlers

- **[[websocket_service.py|WebSocketService]]** - WebSocket connection management for real-time updates

### RSS & External
- **[[rss_feed_service.py|RSSFeedService]]** - RSS feed parsing for job sources

---

## Analytics & Reporting

### Analytics
- **[[analytics_service.py|AnalyticsService]]** - Application analytics and metrics calculation

- **[[analytics_specialized.py|AnalyticsSpecialized]]** - Advanced analytics queries and aggregations

- **[[analytics_cache_service.py|AnalyticsCacheService]]** - Analytics result caching for performance

- **[[scheduled_analytics_reports_service.py|ScheduledAnalyticsReportsService]]** - Automated analytics report generation

### Metrics & Monitoring
- **[[metrics_service.py|MetricsService]]** - System metrics collection and aggregation

- **[[health_analytics_service.py|HealthAnalyticsService]]** - Health metrics and system analytics

### Reports
- **[[report_generation_service.py|ReportGenerationService]]** - PDF/CSV report generation

- **[[test_report_generator.py|TestReportGenerator]]** - Test execution report generation

- **[[export_service.py|ExportService]]** - Data export to various formats (CSV, JSON, Excel)

### Feedback & Prediction
- **[[feedback_service.py|FeedbackService]]** - User feedback collection and management

- **[[feedback_analysis_service.py|FeedbackAnalysisService]]** - Feedback sentiment analysis

- **[[feedback_impact_service.py|FeedbackImpactService]]** - Feedback impact assessment

- **[[predictive_service.py|PredictiveService]]** - Predictive analytics for job success rates

- **[[recommendation_engine.py|RecommendationEngine]]** - General recommendation engine framework

---

## Storage & Caching

### Database
- **[[database_storage_service.py|DatabaseStorageService]]** - Database connection and transaction management

- **[[database_optimization_service.py|DatabaseOptimizationService]]** - Query optimization and indexing

### File Storage
- **[[upload_service.py|UploadService]]** - File upload handling and storage

- **[[file_storage_integration.py|FileStorageIntegration]]** - Cloud storage integration (S3, GCS, Azure)

- **[[backup_service.py|BackupService]]** - Automated database and file backups

### Caching
- **[[cache_service.py|CacheService]]** - Redis-based caching service

### Vector Stores
- **[[vector_store_service.py|VectorStoreService]]** - ChromaDB vector store for job embeddings
  - *Enables semantic job search and similarity matching*

- **[[vector_store.py|VectorStore]]** - Abstract vector store interface

- **[[chroma_client.py|ChromaClient]]** - ChromaDB client wrapper

- **[[vector_backends/|Vector Backends]]** - Alternative vector database implementations

---

## Security & Compliance

### Encryption & Crypto
- **[[encryption_service.py|EncryptionService]]** - Data encryption/decryption (AES-256)

- **[[crypto_service.py|CryptoService]]** - Cryptographic operations and key management

- **[[local_pdf_signing_service.py|LocalPDFSigningService]]** - PDF digital signature generation

### Security & Audit
- **[[security_service.py|SecurityService]]** - Security policy enforcement and validation

- **[[audit_trail_service.py|AuditTrailService]]** - Audit logging for compliance

- **[[compliance_service.py|ComplianceService]]** - Data compliance (GDPR, CCPA) management

---

## Integration & External APIs

### OAuth & Calendar
- **[[oauth_service.py|OAuthService]]** - OAuth 2.0 authentication flow (Google, Microsoft)

- **[[calendar_service.py|CalendarService]]** - Google Calendar and Outlook integration
  - *Two-way sync for interview events*
  - *See: [[../../docs/features/CALENDAR_INTEGRATION_GUIDE|Calendar Integration Guide]]*

### External Services
- **[[github_service.py|GitHubService]]** - GitHub API integration for job postings

- **[[linkedin_service.py|LinkedInService]]** - LinkedIn API integration

- **[[hubspot_service.py|HubSpotService]]** - HubSpot CRM integration

- **[[integration_service.py|IntegrationService]]** - Generic third-party integration framework

### Service Management
- **[[external_service_manager.py|ExternalServiceManager]]** - Manages external API connections

- **[[external_service_validator.py|ExternalServiceValidator]]** - Validates external service responses

---

## Monitoring & Health

### Health Checks
- **[[health_monitoring_service.py|HealthMonitoringService]]** - Service health monitoring and alerting

- **[[health_automation_service.py|HealthAutomationService]]** - Automated health check remediation

- **[[chroma_health_monitor.py|ChromaHealthMonitor]]** - ChromaDB-specific health monitoring

- **[[logging_health_service.py|LoggingHealthService]]** - Logging system health checks

### Observability
- **[[observability_service.py|ObservabilityService]]** - Distributed tracing and monitoring

- **[[monitoring_service.py|MonitoringService]]** - System monitoring and alerting

- **[[logging_service.py|LoggingService]]** - Centralized logging infrastructure

---

## Utilities & Infrastructure

### Task Management
- **[[task_queue_manager.py|TaskQueueManager]]** - Celery task queue management

- **[[task_handlers.py|TaskHandlers]]** - Background task handler implementations

- **[[quota_manager.py|QuotaManager]]** - API quota and rate limiting

- **[[workflow_service.py|WorkflowService]]** - Multi-step workflow orchestration

### Infrastructure
- **[[base_service_plugin.py|BaseServicePlugin]]** - Plugin architecture base class

- **[[feature_flag_service.py|FeatureFlagService]]** - Feature flag management
  - *See: [[../../config/feature_flags.json|Feature Flags]]*

- **[[compression_service.py|CompressionService]]** - Data compression utilities

- **[[error_handling_service.py|ErrorHandlingService]]** - Centralized error handling and reporting

- **[[graceful_degradation_service.py|GracefulDegradationService]]** - Fallback and degradation strategies

- **[[offline_service.py|OfflineService]]** - Offline functionality support

- **[[performance_optimizer.py|PerformanceOptimizer]]** - Performance optimization utilities

### Dashboard & Briefing
- **[[dashboard_service.py|DashboardService]]** - Dashboard data aggregation

- **[[briefing_service.py|BriefingService]]** - Daily briefing generation

- **[[import_service.py|ImportService]]** - Data import from external sources

- **[[market_analysis_service.py|MarketAnalysisService]]** - Job market analysis and trends

---

## 📊 Service Statistics

- **Total Services**: 100+
- **Core Business Logic**: 15 services
- **AI & Content**: 12 services
- **Job Scraping**: 18 scrapers
- **Data Processing**: 8 services
- **User Management**: 6 services
- **Notifications**: 7 services
- **Analytics**: 13 services
- **Storage**: 8 services
- **Security**: 6 services
- **Integrations**: 9 services
- **Monitoring**: 6 services
- **Utilities**: 13 services

## 🔧 Development Guidelines

### Adding a New Service

1. **Create service file** in `backend/app/services/`
2. **Follow naming convention**: `*_service.py` for services
3. **Add comprehensive docstring** with:
   - Purpose and functionality
   - Usage examples
   - Configuration references
   - Related documentation wikilinks
4. **Update this README** with service description
5. **Add tests** in `backend/tests/test_services/`

### Service Patterns

- **Dependency Injection**: Use `__init__(self, db: Session)` pattern
- **Type Hints**: Full type annotations for all methods
- **Error Handling**: Use structured logging and raise appropriate exceptions
- **Documentation**: Include docstrings, examples, and wikilinks
- **Testing**: Minimum 70% code coverage

### Related Documentation

- **[[../../docs/DEVELOPER_GUIDE|Developer Guide]]** - Service Layer patterns
- **[[../../docs/architecture/ARCHITECTURE|Architecture]]** - System architecture overview
- **[[../../backend/README|Backend Guide]]** - Backend development guide
- **[[../../docs/development/testing-strategies|Testing Strategies]]** - Testing guidelines
- **[[../../PROJECT_STATUS|Project Status]]** - Current implementation status

---

**Last Updated**: November 17, 2025
