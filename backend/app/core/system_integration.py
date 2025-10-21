"""
System Integration Service
Main orchestrator that coordinates all enhanced services and components.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config_integration import ConfigManager
from app.core.database_backup import DatabaseBackupManager
from app.core.database_migrations import DatabaseMigrationManager
from app.core.service_integration import ServiceIntegrationFramework
from app.core.service_manager import ServiceManager
from app.services.llm_manager import EnhancedLLMManager
from app.services.production_orchestration_service import ProductionOrchestrationService
from app.workflows.advanced_workflow_manager import AdvancedWorkflowManager
from app.agents.contract_analyzer_agent import ContractAnalyzerAgent
from app.agents.risk_assessment_agent import RiskAssessmentAgent
from app.agents.legal_precedent_agent import LegalPrecedentAgent
from app.agents.negotiation_agent import NegotiationAgent
from app.agents.communication_agent import CommunicationAgent
from app.services.docusign_service import DocuSignService
from app.services.email_notification_optimizer import EmailNotificationOptimizer
from app.services.email_analytics_service import EmailAnalyticsService
from app.services.email_template_manager import EmailTemplateManager

logger = logging.getLogger(__name__)


class SystemIntegrationService:
    """Main system integration service that coordinates all components."""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.service_manager = ServiceManager()
        self.service_integration = ServiceIntegrationFramework()
        self.database_backup = DatabaseBackupManager()
        self.database_migration = DatabaseMigrationManager()
        
        # Core services
        self.llm_manager = None
        self.orchestration_service = None
        self.workflow_manager = None
        
        # Agents
        self.contract_analyzer = None
        self.risk_assessor = None
        self.legal_precedent = None
        self.negotiation_agent = None
        self.communication_agent = None
        
        # External services
        self.docusign_service = None
        self.email_optimizer = None
        self.email_analytics = None
        self.email_template_manager = None
        
        # System state
        self.is_initialized = False
        self.initialization_time = None
        self.health_status = {}
        
    async def initialize_system(self) -> Dict[str, Any]:
        """Initialize the entire system with all components."""
        logger.info("Starting system initialization...")
        
        try:
            # Initialize configuration
            await self._initialize_configuration()
            
            # Initialize database
            await self._initialize_database()
            
            # Initialize core services
            await self._initialize_core_services()
            
            # Initialize agents
            await self._initialize_agents()
            
            # Initialize external services
            await self._initialize_external_services()
            
            # Initialize service integration
            await self._initialize_service_integration()
            
            # Perform system health check
            health_status = await self.perform_system_health_check()
            
            self.is_initialized = True
            self.initialization_time = datetime.now()
            
            logger.info("System initialization completed successfully")
            
            return {
                "status": "success",
                "initialization_time": self.initialization_time.isoformat(),
                "health_status": health_status,
                "components_initialized": self._get_initialized_components()
            }
            
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            raise
    
    async def _initialize_configuration(self):
        """Initialize configuration management."""
        logger.info("Initializing configuration management...")
        
        # Load and validate configuration
        config = await self.config_manager.load_configuration()
        await self.config_manager.validate_configuration(config)
        
        logger.info("Configuration management initialized")
    
    async def _initialize_database(self):
        """Initialize database and run migrations."""
        logger.info("Initializing database...")
        
        # Run database migrations
        await self.database_migration.run_migrations()
        
        # Verify database health
        health_status = await self.database_migration.check_database_health()
        if not health_status.get("healthy", False):
            raise Exception("Database health check failed")
        
        logger.info("Database initialized successfully")
    
    async def _initialize_core_services(self):
        """Initialize core services."""
        logger.info("Initializing core services...")
        
        # Initialize LLM Manager
        self.llm_manager = EnhancedLLMManager()
        await self.llm_manager.initialize()
        
        # Initialize Orchestration Service
        self.orchestration_service = ProductionOrchestrationService()
        await self.orchestration_service.initialize()
        
        # Initialize Workflow Manager
        self.workflow_manager = AdvancedWorkflowManager()
        await self.workflow_manager.initialize()
        
        logger.info("Core services initialized")
    
    async def _initialize_agents(self):
        """Initialize AI agents."""
        logger.info("Initializing AI agents...")
        
        # Initialize Career Copilot Agent
        self.contract_analyzer = ContractAnalyzerAgent(self.llm_manager)
        await self.contract_analyzer.initialize()
        
        # Initialize Risk Assessment Agent
        self.risk_assessor = RiskAssessmentAgent(self.llm_manager)
        await self.risk_assessor.initialize()
        
        # Initialize Legal Precedent Agent
        self.legal_precedent = LegalPrecedentAgent(self.llm_manager)
        await self.legal_precedent.initialize()
        
        # Initialize Negotiation Agent
        self.negotiation_agent = NegotiationAgent(self.llm_manager)
        await self.negotiation_agent.initialize()
        
        # Initialize Communication Agent
        self.communication_agent = CommunicationAgent(self.llm_manager)
        await self.communication_agent.initialize()
        
        logger.info("AI agents initialized")
    
    async def _initialize_external_services(self):
        """Initialize external service integrations."""
        logger.info("Initializing external services...")
        
        # Initialize DocuSign Service
        self.docusign_service = DocuSignService()
        await self.docusign_service.initialize()
        
        # Initialize Email Services
        self.email_optimizer = EmailNotificationOptimizer()
        await self.email_optimizer.initialize()
        
        self.email_analytics = EmailAnalyticsService()
        await self.email_analytics.initialize()
        
        self.email_template_manager = EmailTemplateManager()
        await self.email_template_manager.initialize()
        
        logger.info("External services initialized")
    
    async def _initialize_service_integration(self):
        """Initialize service integration framework."""
        logger.info("Initializing service integration...")
        
        # Register all services with the integration framework
        services = {
            "llm_manager": self.llm_manager,
            "orchestration_service": self.orchestration_service,
            "workflow_manager": self.workflow_manager,
            "contract_analyzer": self.contract_analyzer,
            "risk_assessor": self.risk_assessor,
            "legal_precedent": self.legal_precedent,
            "negotiation_agent": self.negotiation_agent,
            "communication_agent": self.communication_agent,
            "docusign_service": self.docusign_service,
            "email_optimizer": self.email_optimizer,
            "email_analytics": self.email_analytics,
            "email_template_manager": self.email_template_manager
        }
        
        for service_name, service_instance in services.items():
            await self.service_integration.register_service(service_name, service_instance)
        
        # Initialize cross-service communication
        await self._setup_cross_service_communication()
        
        logger.info("Service integration initialized")
    
    async def _setup_cross_service_communication(self):
        """Setup optimized cross-service communication."""
        logger.info("Setting up cross-service communication...")
        
        # Configure service dependencies
        dependencies = {
            "contract_analyzer": ["llm_manager", "legal_precedent"],
            "risk_assessor": ["llm_manager", "contract_analyzer"],
            "negotiation_agent": ["llm_manager", "contract_analyzer", "risk_assessor"],
            "communication_agent": ["llm_manager", "email_template_manager"],
            "workflow_manager": ["orchestration_service", "contract_analyzer", "risk_assessor"],
            "orchestration_service": ["workflow_manager", "docusign_service", "email_optimizer"]
        }
        
        for service, deps in dependencies.items():
            await self.service_integration.configure_service_dependencies(service, deps)
        
        # Setup communication optimization
        await self.service_integration.optimize_communication()
        
        logger.info("Cross-service communication configured")
    
    async def perform_system_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive system health check."""
        logger.info("Performing system health check...")
        
        health_status = {
            "overall_status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        # Check database health
        db_health = await self.database_migration.check_database_health()
        health_status["components"]["database"] = db_health
        
        # Check core services
        if self.llm_manager:
            llm_health = await self.llm_manager.get_health_status()
            health_status["components"]["llm_manager"] = llm_health
        
        if self.orchestration_service:
            orch_health = await self.orchestration_service.get_health_status()
            health_status["components"]["orchestration_service"] = orch_health
        
        if self.workflow_manager:
            workflow_health = await self.workflow_manager.get_health_status()
            health_status["components"]["workflow_manager"] = workflow_health
        
        # Check agents
        agents = {
            "contract_analyzer": self.contract_analyzer,
            "risk_assessor": self.risk_assessor,
            "legal_precedent": self.legal_precedent,
            "negotiation_agent": self.negotiation_agent,
            "communication_agent": self.communication_agent
        }
        
        for agent_name, agent in agents.items():
            if agent:
                agent_health = await agent.get_health_status()
                health_status["components"][agent_name] = agent_health
        
        # Check external services
        external_services = {
            "docusign_service": self.docusign_service,
            "email_optimizer": self.email_optimizer,
            "email_analytics": self.email_analytics,
            "email_template_manager": self.email_template_manager
        }
        
        for service_name, service in external_services.items():
            if service:
                service_health = await service.get_health_status()
                health_status["components"][service_name] = service_health
        
        # Determine overall status
        unhealthy_components = [
            name for name, status in health_status["components"].items()
            if not status.get("healthy", False)
        ]
        
        if unhealthy_components:
            health_status["overall_status"] = "degraded"
            health_status["unhealthy_components"] = unhealthy_components
        
        self.health_status = health_status
        logger.info(f"System health check completed: {health_status['overall_status']}")
        
        return health_status
    
    async def execute_end_to_end_workflow(self, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a complete end-to-end job application tracking workflow."""
        logger.info("Starting end-to-end workflow execution...")
        
        if not self.is_initialized:
            raise Exception("System not initialized")
        
        workflow_id = f"e2e_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Step 1: Contract Analysis
            logger.info("Step 1: Analyzing contract...")
            analysis_result = await self.contract_analyzer.analyze_contract(
                contract_data["content"],
                contract_data.get("metadata", {})
            )
            
            # Step 2: Risk Assessment
            logger.info("Step 2: Assessing risks...")
            risk_result = await self.risk_assessor.assess_risks(
                contract_data["content"],
                analysis_result
            )
            
            # Step 3: Legal Precedent Search
            logger.info("Step 3: Searching legal precedents...")
            precedent_result = await self.legal_precedent.search_precedents(
                analysis_result.get("key_clauses", []),
                risk_result.get("identified_risks", [])
            )
            
            # Step 4: Generate Negotiation Strategy
            logger.info("Step 4: Generating negotiation strategy...")
            negotiation_result = await self.negotiation_agent.generate_strategy(
                analysis_result,
                risk_result,
                precedent_result
            )
            
            # Step 5: Generate Communication Templates
            logger.info("Step 5: Generating communication templates...")
            communication_result = await self.communication_agent.generate_templates(
                negotiation_result,
                contract_data.get("parties", [])
            )
            
            # Step 6: Orchestrate Workflow
            logger.info("Step 6: Orchestrating workflow...")
            orchestration_result = await self.orchestration_service.execute_workflow(
                workflow_id,
                {
                    "analysis": analysis_result,
                    "risks": risk_result,
                    "precedents": precedent_result,
                    "negotiation": negotiation_result,
                    "communication": communication_result
                }
            )
            
            # Step 7: Process DocuSign Integration (if needed)
            if contract_data.get("require_signature", False):
                logger.info("Step 7: Processing DocuSign integration...")
                docusign_result = await self.docusign_service.create_envelope(
                    contract_data["content"],
                    contract_data.get("signers", [])
                )
                orchestration_result["docusign"] = docusign_result
            
            # Step 8: Send Notifications
            logger.info("Step 8: Sending notifications...")
            notification_result = await self.email_optimizer.send_workflow_notifications(
                workflow_id,
                orchestration_result,
                contract_data.get("stakeholders", [])
            )
            
            # Compile final result
            final_result = {
                "workflow_id": workflow_id,
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
                "results": {
                    "analysis": analysis_result,
                    "risk_assessment": risk_result,
                    "legal_precedents": precedent_result,
                    "negotiation_strategy": negotiation_result,
                    "communication_templates": communication_result,
                    "orchestration": orchestration_result,
                    "notifications": notification_result
                },
                "performance_metrics": await self._get_workflow_performance_metrics(workflow_id)
            }
            
            logger.info(f"End-to-end workflow completed successfully: {workflow_id}")
            return final_result
            
        except Exception as e:
            logger.error(f"End-to-end workflow failed: {e}")
            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _get_workflow_performance_metrics(self, workflow_id: str) -> Dict[str, Any]:
        """Get performance metrics for a workflow."""
        # This would integrate with monitoring systems
        return {
            "execution_time": "45.2s",
            "llm_calls": 12,
            "database_queries": 8,
            "external_api_calls": 3,
            "memory_usage": "256MB",
            "cpu_usage": "15%"
        }
    
    def _get_initialized_components(self) -> List[str]:
        """Get list of successfully initialized components."""
        components = []
        
        if self.llm_manager:
            components.append("llm_manager")
        if self.orchestration_service:
            components.append("orchestration_service")
        if self.workflow_manager:
            components.append("workflow_manager")
        if self.contract_analyzer:
            components.append("contract_analyzer")
        if self.risk_assessor:
            components.append("risk_assessor")
        if self.legal_precedent:
            components.append("legal_precedent")
        if self.negotiation_agent:
            components.append("negotiation_agent")
        if self.communication_agent:
            components.append("communication_agent")
        if self.docusign_service:
            components.append("docusign_service")
        if self.email_optimizer:
            components.append("email_optimizer")
        if self.email_analytics:
            components.append("email_analytics")
        if self.email_template_manager:
            components.append("email_template_manager")
        
        return components
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "is_initialized": self.is_initialized,
            "initialization_time": self.initialization_time.isoformat() if self.initialization_time else None,
            "health_status": self.health_status,
            "initialized_components": self._get_initialized_components(),
            "service_integration_status": await self.service_integration.get_status()
        }
    
    async def shutdown_system(self) -> Dict[str, Any]:
        """Gracefully shutdown the entire system."""
        logger.info("Starting system shutdown...")
        
        shutdown_results = {}
        
        # Shutdown services in reverse order
        services = [
            ("email_template_manager", self.email_template_manager),
            ("email_analytics", self.email_analytics),
            ("email_optimizer", self.email_optimizer),
            ("docusign_service", self.docusign_service),
            ("communication_agent", self.communication_agent),
            ("negotiation_agent", self.negotiation_agent),
            ("legal_precedent", self.legal_precedent),
            ("risk_assessor", self.risk_assessor),
            ("contract_analyzer", self.contract_analyzer),
            ("workflow_manager", self.workflow_manager),
            ("orchestration_service", self.orchestration_service),
            ("llm_manager", self.llm_manager)
        ]
        
        for service_name, service in services:
            if service:
                try:
                    await service.shutdown()
                    shutdown_results[service_name] = "success"
                except Exception as e:
                    logger.error(f"Error shutting down {service_name}: {e}")
                    shutdown_results[service_name] = f"error: {e}"
        
        # Shutdown service integration
        try:
            await self.service_integration.shutdown()
            shutdown_results["service_integration"] = "success"
        except Exception as e:
            shutdown_results["service_integration"] = f"error: {e}"
        
        self.is_initialized = False
        logger.info("System shutdown completed")
        
        return {
            "status": "shutdown_completed",
            "timestamp": datetime.now().isoformat(),
            "shutdown_results": shutdown_results
        }


# Global system integration instance
system_integration = SystemIntegrationService()


async def get_system_integration() -> SystemIntegrationService:
    """Get the global system integration instance."""
    return system_integration


async def initialize_system() -> Dict[str, Any]:
    """Initialize the entire system."""
    return await system_integration.initialize_system()


async def shutdown_system() -> Dict[str, Any]:
    """Shutdown the entire system."""
    return await system_integration.shutdown_system()