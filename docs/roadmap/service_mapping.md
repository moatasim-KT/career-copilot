# Service Mapping Document for Career Copilot Consolidation

This document outlines the current state of backend services, their responsibilities, and recommendations for consolidation as part of the "Phase 0: Critical Consolidation" effort. The goal is to reduce duplication, improve maintainability, and establish single sources of truth for core functionalities.

## Current Service Landscape Overview

The Career Copilot backend currently features over 150 service files, many with overlapping functionalities. Key areas of duplication include:

*   **Analytics Services:** 8+ implementations
*   **Job Management Services:** 12+ implementations
*   **LLM Services:** 8+ implementations
*   **Notification Services:** 7+ implementations
*   **Storage Implementations:** Multiple, redundant approaches

## Consolidation Strategy

The consolidation strategy aims for a 65% reduction in service files (from 150+ to ~50) by:
1.  Identifying core responsibilities for each logical domain.
2.  Centralizing logic into single, unified service classes or well-defined patterns (e.g., facade, plugin architecture).
3.  Removing redundant or deprecated implementations.
4.  Updating all consumers (API endpoints, other services) to use the consolidated services.

## Detailed Service Mapping and Consolidation Plan

### 1. Analytics Services

*   **Current Files Identified:**
    *   `analytics_service.py` (identified as primary/consolidated)
    *   `analytics_service_facade.py` (facade pattern)
    *   `analytics_collection_service.py`
    *   `analytics_processing_service.py`
    *   `analytics_query_service.py`
    *   `analytics_reporting_service.py`
    *   `comprehensive_analytics_service.py`
    *   `analytics_specialized.py`
*   **Issue:** Multiple services handling similar analytics operations with different interfaces.
*   **Recommendation:**
    *   **Keep:** `analytics_service.py` (as the main entry point for analytics logic) and `analytics_service_facade.py` (if a facade pattern is desired for external interaction).
    *   **Consolidate/Remove:** Merge functionality from `analytics_collection_service.py`, `analytics_processing_service.py`, `analytics_query_service.py`, `analytics_reporting_service.py`, `comprehensive_analytics_service.py`, `analytics_specialized.py` into `analytics_service.py` or its facade.
    *   **Action:** Refactor `analytics_service.py` to encompass all core analytics logic. Update all API endpoints and other services that consume these analytics functionalities to use the consolidated `analytics_service.py`.

### 2. Job Management Services

*   **Current Files Identified:**
    *   `job_service.py` (identified as primary/consolidated)
    *   `job_scraping_service.py`
    *   `job_ingestion_service.py`
    *   `job_scraper.py`
    *   `job_recommendation_service.py`
*   **Issue:** Scattered job processing logic across multiple services (CRUD, scraping, ingestion, recommendations).
*   **Recommendation:**
    *   **Create Unified Class:** Implement a `JobManagementSystem` class (or similar) that centralizes all job-related operations.
    *   **Consolidate/Remove:** Merge functionality from `job_scraping_service.py`, `job_ingestion_service.py`, `job_scraper.py`, `job_recommendation_service.py` into the new `JobManagementSystem` or integrate them as modules/components within `job_service.py`.
    *   **Action:** Design and implement the `JobManagementSystem` to manage the lifecycle of jobs, from scraping and ingestion to recommendations and user interaction. Update all consumers.

### 3. LLM Services

*   **Current Files Identified:**
    *   `llm_service.py` (identified as primary/consolidated)
    *   `groq_service.py`
    *   `openai_service.py`
    *   `ollama_service.py`
    *   `llm_config_manager.py`
    *   `llm_service_plugin.py`
*   **Issue:** Provider-specific services instead of a unified interface for LLM interactions.
*   **Recommendation:**
    *   **Single Provider-Agnostic Service:** Consolidate into a single `llm_service.py` that acts as a provider-agnostic interface.
    *   **Plugin Architecture:** Implement a plugin architecture (potentially using `llm_service_plugin.py` as a base) to dynamically load and manage different LLM providers (Groq, OpenAI, Ollama) without exposing provider-specific logic to consumers.
    *   **Action:** Refactor `llm_service.py` to manage LLM provider selection and interaction. Integrate `llm_config_manager.py` for dynamic configuration.

### 4. Notification Services

*   **Current Files Identified:**
    *   `notification_service.py`
    *   `email_service.py`
    *   `email_notification_optimizer.py`
    *   `websocket_notification_service.py`
    *   `scheduled_notification_service.py`
*   **Issue:** Different notification channels (email, WebSocket, scheduled) handled separately, leading to fragmentation.
*   **Recommendation:**
    *   **Unified Notification Service:** Consolidate into a single `notification_service.py` that provides a unified interface for sending notifications across various channels.
    *   **Channel Abstraction:** Implement an abstraction layer within `notification_service.py` to handle different notification channels (email, WebSocket, scheduled) internally.
    *   **Action:** Refactor `notification_service.py` to manage all notification types and delivery mechanisms.

### 5. Storage Implementations

*   **Current Files Identified:** Multiple, redundant approaches (e.g., `backend/app/services/storage/cloud.py` is a placeholder).
*   **Issue:** Lack of a standardized approach for file storage and management.
*   **Recommendation:**
    *   **Standardize:** Implement a single, unified storage service (e.g., `storage_service.py`) that abstracts away the underlying storage mechanism (local, cloud, etc.).
    *   **Remove Duplicates:** Eliminate any other redundant storage implementations.
    *   **Action:** Develop `storage_service.py` to provide a consistent interface for file operations.

## Next Steps

1.  **Implement Consolidation:** Proceed with the actual code changes to consolidate services as per the recommendations above.
2.  **Update Consumers:** Ensure all API endpoints and other services are updated to use the new, consolidated service interfaces.
3.  **Verify Functionality:** Thoroughly test all consolidated functionalities to ensure no regressions.
4.  **Remove Old Files:** Once consolidation is complete and verified, safely remove the deprecated service files.
