"""
CrewAI Integration Service

This module provides integration between the existing workflow system
and the new CrewAI agent framework.
"""

import logging
from typing import Any, Dict, Optional

from ..agents.orchestration_service import get_orchestration_service, WorkflowConfig
from ..core.exceptions import ErrorCategory, ErrorSeverity, WorkflowExecutionError
from ..core.langsmith_integration import trace_ai_operation

logger = logging.getLogger(__name__)


class CrewAIIntegrationService:
    """
    Service for integrating CrewAI agents with the existing workflow system.
    
    This service provides a bridge between the LangGraph-based workflow
    and the new CrewAI agent framework, allowing for gradual migration
    and compatibility.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the CrewAI integration service.
        
        Args:
            config: Optional configuration parameters
        """
        self.config = config or {}
        
        # Initialize workflow configuration
        workflow_config = WorkflowConfig(
            max_execution_time=self.config.get("max_execution_time", 300),
            enable_parallel_execution=self.config.get("enable_parallel_execution", True),
            retry_failed_tasks=self.config.get("retry_failed_tasks", True),
            max_retries=self.config.get("max_retries", 3),
            verbose_logging=self.config.get("verbose_logging", True),
            save_intermediate_results=self.config.get("save_intermediate_results", True)
        )
        
        # Get orchestration service
        self.orchestration_service = get_orchestration_service(workflow_config)
        
        logger.info("CrewAI Integration Service initialized")
    
    @trace_ai_operation("crewai_workflow_execution", "integration")
    async def execute_contract_analysis(
        self,
        contract_text: str,
        contract_filename: str,
        workflow_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute job application tracking using CrewAI agents.
        
        Args:
            contract_text: The contract text to analyze
            contract_filename: Name of the contract file
            workflow_config: Optional workflow-specific configuration
            
        Returns:
            Dict[str, Any]: Complete workflow results
        """
        try:
            logger.info(f"Starting CrewAI job application tracking for {contract_filename}")
            
            # Execute the workflow using CrewAI agents
            results = await self.orchestration_service.execute_contract_analysis_workflow(
                contract_text=contract_text,
                contract_filename=contract_filename,
                workflow_config=workflow_config
            )
            
            # Transform results to match existing workflow format
            transformed_results = self._transform_results_to_workflow_format(results)
            
            logger.info(f"CrewAI job application tracking completed for {contract_filename}")
            
            return transformed_results
            
        except Exception as e:
            error_msg = f"CrewAI job application tracking failed for {contract_filename}: {e}"
            logger.error(error_msg, exc_info=True)
            
            raise WorkflowExecutionError(
                error_msg,
                category=ErrorCategory.WORKFLOW,
                severity=ErrorSeverity.HIGH
            )
    
    def _transform_results_to_workflow_format(self, crewai_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform CrewAI results to match the existing workflow format.
        
        Args:
            crewai_results: Results from CrewAI workflow
            
        Returns:
            Dict[str, Any]: Transformed results in workflow format
        """
        try:
            # Extract data from CrewAI results
            risky_clauses = crewai_results.get("risky_clauses", [])
            suggested_redlines = crewai_results.get("suggested_redlines", [])
            overall_risk_score = crewai_results.get("overall_risk_score", 0.0)
            email_draft = crewai_results.get("email_draft", "")
            precedent_context = crewai_results.get("precedent_context", [])
            
            # Transform risky clauses to workflow format
            transformed_risky_clauses = []
            for clause in risky_clauses:
                transformed_clause = {
                    "clause_text": clause.get("clause_text", ""),
                    "risk_explanation": clause.get("risk_explanation", ""),
                    "risk_level": clause.get("risk_level", "Medium"),
                    "precedent_reference": clause.get("precedent_reference"),
                    "clause_index": clause.get("clause_index", 0)
                }
                transformed_risky_clauses.append(transformed_clause)
            
            # Transform redline suggestions to workflow format
            transformed_redlines = []
            for redline in suggested_redlines:
                transformed_redline = {
                    "original_clause": redline.get("original_clause", ""),
                    "suggested_redline": redline.get("suggested_redline", ""),
                    "risk_explanation": redline.get("change_rationale", ""),
                    "clause_index": redline.get("clause_index", 0),
                    "change_rationale": redline.get("change_rationale", ""),
                    "risk_mitigated": redline.get("risk_mitigated", True)
                }
                transformed_redlines.append(transformed_redline)
            
            # Create workflow-compatible result structure
            workflow_results = {
                "success": crewai_results.get("success", True),
                "workflow_id": crewai_results.get("workflow_id", "unknown"),
                "execution_time": crewai_results.get("execution_time", 0),
                
                # Core analysis results
                "risky_clauses": transformed_risky_clauses,
                "overall_risk_score": overall_risk_score,
                "suggested_redlines": transformed_redlines,
                "email_draft": email_draft,
                "precedent_context": precedent_context,
                
                # Additional CrewAI-specific results
                "contract_structure": crewai_results.get("contract_structure", {}),
                "identified_clauses": crewai_results.get("identified_clauses", []),
                "precedent_matches": crewai_results.get("precedent_matches", []),
                "negotiation_strategy": crewai_results.get("negotiation_strategy", ""),
                "alternative_clauses": crewai_results.get("alternative_clauses", []),
                "communication_templates": crewai_results.get("communication_templates", {}),
                "next_steps": crewai_results.get("next_steps", []),
                
                # Metadata
                "processing_metadata": {
                    "agent_framework": "CrewAI",
                    "completed_agents": crewai_results.get("completed_agents", []),
                    "workflow_metadata": crewai_results.get("workflow_metadata", {}),
                    "warnings": [f"Analysis completed using CrewAI agents: {', '.join(crewai_results.get('completed_agents', []))}"]
                }
            }
            
            return workflow_results
            
        except Exception as e:
            logger.error(f"Failed to transform CrewAI results: {e}")
            
            # Return basic error result in workflow format
            return {
                "success": False,
                "error": f"Failed to transform CrewAI results: {e}",
                "risky_clauses": [],
                "overall_risk_score": 0.0,
                "suggested_redlines": [],
                "email_draft": "",
                "precedent_context": [],
                "processing_metadata": {
                    "agent_framework": "CrewAI",
                    "error": str(e),
                    "warnings": ["Result transformation failed"]
                }
            }
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a CrewAI workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Optional[Dict[str, Any]]: Workflow status information
        """
        try:
            status = self.orchestration_service.get_workflow_status(workflow_id)
            
            if status:
                # Transform to workflow-compatible format
                return {
                    "status": status.status,
                    "current_node": status.current_stage,
                    "execution_id": status.workflow_id,
                    "error_count": len(status.failed_agents),
                    "warnings": [],
                    "last_error": status.error_message,
                    "start_time": status.start_time,
                    "end_time": status.end_time,
                    "processing_duration": status.total_execution_time,
                    "completed_agents": status.completed_agents,
                    "failed_agents": status.failed_agents
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get workflow status for {workflow_id}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_agent_states(self) -> Dict[str, Dict[str, Any]]:
        """Get the current state of all CrewAI agents"""
        try:
            return self.orchestration_service.get_agent_states()
        except Exception as e:
            logger.error(f"Failed to get agent states: {e}")
            return {}
    
    async def create_crew_for_workflow(self, workflow_type: str = "contract_analysis"):
        """Create a CrewAI crew for a specific workflow type"""
        try:
            return await self.orchestration_service.create_crew_for_workflow(workflow_type)
        except Exception as e:
            logger.error(f"Failed to create crew for workflow {workflow_type}: {e}")
            raise WorkflowExecutionError(
                f"Failed to create crew for workflow {workflow_type}: {e}",
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.HIGH
            )


# Global service instance
_crewai_integration_service: Optional[CrewAIIntegrationService] = None


def get_crewai_integration_service(config: Optional[Dict[str, Any]] = None) -> CrewAIIntegrationService:
    """Get or create the global CrewAI integration service instance"""
    global _crewai_integration_service
    
    if _crewai_integration_service is None:
        _crewai_integration_service = CrewAIIntegrationService(config)
    
    return _crewai_integration_service