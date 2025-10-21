"""
Enhanced Communication Agent

This module implements the specialized CrewAI agent responsible for
external communication formatting and delivery management with multi-LLM support,
advanced template generation, and multi-language capabilities.
"""

import logging
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
from pathlib import Path

from crewai import Task

from ..core.exceptions import ErrorCategory, ErrorSeverity, ValidationError, WorkflowExecutionError
from ..core.langsmith_integration import trace_ai_operation
from ..services.gmail_service import GmailService, GmailMessage
from ..services.slack_service import EnhancedSlackService, SlackMessage
from ..services.llm_manager import get_enhanced_llm_manager, TaskType
from .base_agent import AgentCommunicationProtocol, BaseContractAgent
from ..core.agent_cache_manager import AgentType

logger = logging.getLogger(__name__)


class CommunicationType(str, Enum):
    """Types of communications."""
    EXECUTIVE_SUMMARY = "executive_summary"
    LEGAL_ANALYSIS = "legal_analysis"
    NEGOTIATION_PROPOSAL = "negotiation_proposal"
    RISK_ALERT = "risk_alert"
    STATUS_UPDATE = "status_update"
    COUNTERPARTY_LETTER = "counterparty_letter"


class TemplateCategory(str, Enum):
    """Template categories for organization."""
    EXECUTIVE = "executive"
    LEGAL = "legal"
    OPERATIONAL = "operational"
    EXTERNAL = "external"
    MULTILINGUAL = "multilingual"


class CommunicationUrgency(str, Enum):
    """Communication urgency levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class CommunicationAgent(BaseContractAgent):
    """
    Enhanced specialized agent for external communication management.
    
    Responsibilities:
    - Format analysis results for external sharing using multiple LLMs
    - Generate and customize communication templates
    - Send emails with contract summaries in multiple languages
    - Post notifications to collaboration platforms
    - Manage advanced communication templates with AI enhancement
    - Support multi-language communications for international contracts
    """
    
    def __init__(
        self,
        communication_protocol: AgentCommunicationProtocol,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the Enhanced Communication Agent.
        
        Args:
            communication_protocol: Shared communication protocol
            config: Optional configuration parameters
        """
        super().__init__(
            agent_name="enhanced_communication",
            role="Senior International Legal Communication Specialist",
            goal="Create professional, clear, and actionable multi-language communication materials for job application tracking results and negotiation processes using advanced AI capabilities",
            backstory="""You are a senior international legal communication specialist with over 20 years of experience in legal 
            writing, client communication, and global stakeholder management. You have worked for top-tier international law firms and 
            multinational corporate legal departments, specializing in translating complex legal analysis into clear, actionable 
            business communications across multiple languages and cultures. Your expertise includes executive briefings, client advisories, 
            international negotiation correspondence, and multi-stakeholder communication coordination across different legal systems. 
            You are fluent in multiple languages and understand cultural nuances in business communication. You are known for your ability to 
            adapt communication style to different audiences and cultures, from C-level executives to operational teams, while 
            maintaining legal precision and professional standards. Your communications consistently drive action, 
            build consensus, and preserve business relationships while protecting legal interests in international contexts.""",
            communication_protocol=communication_protocol,
            config=config
        )
        
        # Initialize enhanced LLM manager for multi-provider support
        self.llm_manager = get_enhanced_llm_manager()
        
        # Initialize external communication services
        self.gmail_service = GmailService()
        self.slack_service = EnhancedSlackService()
        
        # Initialize services
        self._initialize_services()
        
        # Set agent type for caching
        self.agent_type = AgentType.COMMUNICATION
        
        # Enhanced communication templates and styles
        self.communication_styles = {
            "executive": {
                "tone": "concise and strategic",
                "focus": "business impact and decisions",
                "length": "brief with key highlights",
                "formality": "high",
                "technical_level": "low"
            },
            "legal": {
                "tone": "detailed and precise",
                "focus": "legal implications and risks",
                "length": "comprehensive with full analysis",
                "formality": "very high",
                "technical_level": "high"
            },
            "operational": {
                "tone": "practical and actionable",
                "focus": "implementation and next steps",
                "length": "moderate with clear actions",
                "formality": "medium",
                "technical_level": "medium"
            },
            "counterparty": {
                "tone": "professional and collaborative",
                "focus": "mutual benefit and solutions",
                "length": "balanced with rationale",
                "formality": "high",
                "technical_level": "medium"
            },
            "international": {
                "tone": "respectful and culturally aware",
                "focus": "cross-cultural understanding",
                "length": "detailed with context",
                "formality": "very high",
                "technical_level": "medium"
            }
        }
        
        # Enhanced communication channels with AI capabilities
        self.communication_channels = {
            "email": {"format": "professional email", "urgency": "standard", "ai_enhancement": True},
            "slack": {"format": "team notification", "urgency": "immediate", "ai_enhancement": True},
            "report": {"format": "formal document", "urgency": "scheduled", "ai_enhancement": True},
            "presentation": {"format": "executive briefing", "urgency": "meeting", "ai_enhancement": True},
            "letter": {"format": "formal letter", "urgency": "standard", "ai_enhancement": True}
        }
        
        # Template management
        self.template_directory = Path("backend/backend/app/email_templates")
        self.custom_templates = {}
        self.template_usage_stats = {}
        
        # Multi-language support
        self.supported_languages = {
            "en": "English",
            "es": "Spanish", 
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "ru": "Russian",
            "ar": "Arabic"
        }
        
        logger.info("Enhanced Communication Agent initialized with multi-LLM and multi-language support")
    
    def _initialize_services(self):
        """Initialize external communication services"""
        try:
            # Initialize Gmail service
            if hasattr(self.gmail_service, 'authenticate'):
                # Note: Authentication will be handled when actually sending emails
                logger.info("Gmail service initialized")
            
            # Initialize Slack service
            logger.info("Slack service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize communication services: {e}")
    
    async def send_email_communication(
        self,
        recipient_email: str,
        subject: str,
        content: str,
        template_name: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Send email communication using Gmail service.
        
        Args:
            recipient_email: Email address of recipient
            subject: Email subject line
            content: Email content (will be used if no template)
            template_name: Optional template name
            template_data: Optional template data
            priority: Email priority (high, normal, low)
            user_id: User ID for quota tracking
            
        Returns:
            Dict[str, Any]: Send result with success status
        """
        try:
            # Create Gmail message
            message = GmailMessage(
                to=recipient_email,
                subject=subject,
                body=content,
                priority=priority,
                template_name=template_name,
                template_data=template_data
            )
            
            # Send email
            result = await self.gmail_service.send_email(message, user_id)
            
            if result["success"]:
                logger.info(f"Email sent successfully to {recipient_email}")
            else:
                logger.error(f"Failed to send email: {result.get('message', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to send email communication: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": "email_send_failed", "message": error_msg}
    
    async def send_slack_notification(
        self,
        message_text: str,
        channel: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        blocks: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send Slack notification using Slack service.
        
        Args:
            message_text: Main message text
            channel: Slack channel (optional, uses default if not provided)
            attachments: Optional Slack attachments
            blocks: Optional Slack blocks
            
        Returns:
            Dict[str, Any]: Send result with success status
        """
        try:
            # Create Slack message
            message = SlackMessage(
                text=message_text,
                channel=channel,
                attachments=attachments,
                blocks=blocks
            )
            
            # Send message
            success = await self.slack_service.send_message(message)
            
            if success:
                logger.info(f"Slack message sent successfully to {channel or 'default channel'}")
                return {"success": True, "message": "Slack notification sent successfully"}
            else:
                logger.error("Failed to send Slack message")
                return {"success": False, "error": "slack_send_failed", "message": "Failed to send Slack notification"}
            
        except Exception as e:
            error_msg = f"Failed to send Slack notification: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": "slack_send_failed", "message": error_msg}
    
    async def send_contract_analysis_email(
        self,
        recipient_email: str,
        contract_name: str,
        analysis_results: Dict[str, Any],
        risk_results: Dict[str, Any],
        negotiation_results: Dict[str, Any],
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Send job application tracking results via email.
        
        Args:
            recipient_email: Email address of recipient
            contract_name: Name of the analyzed contract
            analysis_results: Contract analysis results
            risk_results: Risk assessment results
            negotiation_results: Negotiation recommendations
            user_id: User ID for quota tracking
            
        Returns:
            Dict[str, Any]: Send result with success status
        """
        try:
            # Extract key data
            risk_score = risk_results.get("overall_risk_score", 0.0)
            risky_clauses = risk_results.get("risky_clauses", [])
            analysis_summary = risk_results.get("risk_summary", "Analysis completed")
            suggested_redlines = negotiation_results.get("suggested_redlines", [])
            
            # Generate recommendations
            recommendations = []
            if suggested_redlines:
                recommendations.append(f"Review {len(suggested_redlines)} suggested contract modifications")
            if risk_score >= 7:
                recommendations.append("Immediate legal review recommended due to high risk score")
            if risky_clauses:
                recommendations.append(f"Address {len(risky_clauses)} identified risk areas")
            
            # Use Gmail service to send analysis email
            result = await self.gmail_service.send_contract_analysis_email(
                recipient_email=recipient_email,
                contract_name=contract_name,
                risk_score=risk_score,
                risky_clauses=risky_clauses,
                analysis_summary=analysis_summary,
                recommendations=recommendations,
                user_id=user_id,
                include_attachments=True
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to send job application tracking email: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": "analysis_email_failed", "message": error_msg}
    
    async def send_contract_analysis_slack_alert(
        self,
        contract_name: str,
        analysis_results: Dict[str, Any],
        risk_results: Dict[str, Any],
        negotiation_results: Dict[str, Any],
        user_id: Optional[str] = None,
        analysis_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send job application tracking alert to Slack.
        
        Args:
            contract_name: Name of the analyzed contract
            analysis_results: Contract analysis results
            risk_results: Risk assessment results
            negotiation_results: Negotiation recommendations
            user_id: Optional user ID for notification preferences
            analysis_url: Optional URL to full analysis
            
        Returns:
            Dict[str, Any]: Send result with success status
        """
        try:
            from uuid import UUID
            
            # Extract key data
            risk_score = risk_results.get("overall_risk_score", 0.0)
            risky_clauses = risk_results.get("risky_clauses", [])
            analysis_summary = risk_results.get("risk_summary", "Analysis completed")
            
            # Convert user_id to UUID if provided
            user_uuid = None
            if user_id:
                try:
                    user_uuid = UUID(user_id)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid user_id format: {user_id}")
            
            # Use Slack service to send analysis alert
            success = await self.slack_service.send_contract_analysis_alert(
                user_id=user_uuid,
                contract_name=contract_name,
                risk_score=risk_score,
                risky_clauses=risky_clauses,
                analysis_summary=analysis_summary,
                analysis_url=analysis_url
            )
            
            if success:
                return {"success": True, "message": "Slack alert sent successfully"}
            else:
                return {"success": False, "error": "slack_alert_failed", "message": "Failed to send Slack alert"}
            
        except Exception as e:
            error_msg = f"Failed to send job application tracking Slack alert: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": "slack_alert_failed", "message": error_msg}
    
    async def send_risk_alert_communications(
        self,
        contract_name: str,
        risk_score: float,
        urgent_clauses: List[Dict[str, Any]],
        recipient_email: Optional[str] = None,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Send high-risk alert communications via both email and Slack.
        
        Args:
            contract_name: Name of the contract
            risk_score: Risk score (should be high)
            urgent_clauses: List of urgent/high-risk clauses
            recipient_email: Optional email recipient
            user_id: User ID for tracking
            
        Returns:
            Dict[str, Any]: Combined results from both channels
        """
        try:
            results = {"email": None, "slack": None}
            
            # Send email alert if recipient provided
            if recipient_email:
                email_result = await self.gmail_service.send_risk_alert_email(
                    recipient_email=recipient_email,
                    contract_name=contract_name,
                    risk_score=risk_score,
                    urgent_clauses=urgent_clauses,
                    user_id=user_id
                )
                results["email"] = email_result
            
            # Send Slack alert
            slack_success = await self.slack_service.send_risk_alert(
                contract_name=contract_name,
                risk_score=risk_score,
                urgent_clauses=urgent_clauses
            )
            results["slack"] = {"success": slack_success}
            
            # Determine overall success
            email_success = results["email"]["success"] if results["email"] else True
            overall_success = email_success and slack_success
            
            return {
                "success": overall_success,
                "results": results,
                "message": "Risk alerts sent" if overall_success else "Some alerts failed"
            }
            
        except Exception as e:
            error_msg = f"Failed to send risk alert communications: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": "risk_alerts_failed", "message": error_msg}
    
    async def send_general_notification(
        self,
        title: str,
        message: str,
        recipient_email: Optional[str] = None,
        slack_channel: Optional[str] = None,
        priority: str = "normal",
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Send general notification via email and/or Slack.
        
        Args:
            title: Notification title
            message: Notification message
            recipient_email: Optional email recipient
            slack_channel: Optional Slack channel
            priority: Priority level (high, normal, low)
            user_id: User ID for tracking
            
        Returns:
            Dict[str, Any]: Combined results from both channels
        """
        try:
            results = {"email": None, "slack": None}
            
            # Send email notification if recipient provided
            if recipient_email:
                email_result = await self.gmail_service.send_notification_email(
                    recipient_email=recipient_email,
                    title=title,
                    message=message,
                    priority=priority,
                    user_id=user_id
                )
                results["email"] = email_result
            
            # Send Slack notification if channel provided or use default
            slack_success = await self.slack_service.send_notification(
                title=title,
                message=message,
                priority=priority,
                channel=slack_channel
            )
            results["slack"] = {"success": slack_success}
            
            # Determine overall success
            email_success = results["email"]["success"] if results["email"] else True
            overall_success = email_success and slack_success
            
            return {
                "success": overall_success,
                "results": results,
                "message": "Notifications sent" if overall_success else "Some notifications failed"
            }
            
        except Exception as e:
            error_msg = f"Failed to send general notification: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": "notification_failed", "message": error_msg}
    
    async def generate_enhanced_communication_template(
        self,
        template_type: CommunicationType,
        template_category: TemplateCategory,
        content_data: Dict[str, Any],
        target_language: str = "en",
        cultural_context: Optional[str] = None,
        customization_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate enhanced communication template using multiple LLM providers.
        
        Args:
            template_type: Type of communication
            template_category: Category for organization
            content_data: Data to include in template
            target_language: Target language code
            cultural_context: Cultural context for adaptation
            customization_params: Additional customization parameters
            
        Returns:
            Dict[str, Any]: Generated template with metadata
        """
        try:
            # Generate templates using different LLM providers for comparison
            templates = {}
            
            # Template 1: OpenAI for comprehensive and polished content
            openai_prompt = self._create_template_prompt(
                template_type, template_category, content_data, "comprehensive", target_language, cultural_context
            )
            openai_template = await self.llm_manager.get_completion(
                prompt=openai_prompt,
                task_type=TaskType.COMMUNICATION,
                preferred_provider="openai"
            )
            templates["comprehensive"] = openai_template.content
            
            # Template 2: GROQ for concise and efficient content
            groq_prompt = self._create_template_prompt(
                template_type, template_category, content_data, "concise", target_language, cultural_context
            )
            groq_template = await self.llm_manager.get_completion(
                prompt=groq_prompt,
                task_type=TaskType.COMMUNICATION,
                preferred_provider="groq"
            )
            templates["concise"] = groq_template.content
            
            # Template 3: Alternative approach (if available)
            try:
                alternative_prompt = self._create_template_prompt(
                    template_type, template_category, content_data, "alternative", target_language, cultural_context
                )
                alternative_template = await self.llm_manager.get_completion(
                    prompt=alternative_prompt,
                    task_type=TaskType.COMMUNICATION,
                    preferred_provider="ollama"
                )
                templates["alternative"] = alternative_template.content
            except Exception as e:
                logger.warning(f"Alternative template generation failed: {e}")
                templates["alternative"] = "Alternative template unavailable"
            
            # Select best template or synthesize
            if customization_params and customization_params.get("synthesis_mode", False):
                final_template = await self._synthesize_templates(templates, template_type, content_data)
            else:
                # Use comprehensive template as default
                final_template = templates["comprehensive"]
            
            # Apply customizations if provided
            if customization_params:
                final_template = await self._apply_template_customizations(
                    final_template, customization_params, target_language
                )
            
            # Store template for reuse
            template_id = f"{template_type.value}_{template_category.value}_{target_language}"
            self.custom_templates[template_id] = {
                "template": final_template,
                "type": template_type.value,
                "category": template_category.value,
                "language": target_language,
                "created_at": datetime.utcnow().isoformat(),
                "usage_count": 0,
                "metadata": {
                    "cultural_context": cultural_context,
                    "customization_params": customization_params,
                    "providers_used": list(templates.keys())
                }
            }
            
            return {
                "success": True,
                "template_id": template_id,
                "template": final_template,
                "individual_templates": templates,
                "metadata": {
                    "type": template_type.value,
                    "category": template_category.value,
                    "language": target_language,
                    "cultural_context": cultural_context,
                    "providers_used": list(templates.keys())
                }
            }
            
        except Exception as e:
            error_msg = f"Enhanced template generation failed: {e}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    async def customize_existing_template(
        self,
        template_id: str,
        customization_params: Dict[str, Any],
        content_updates: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Customize an existing template with new parameters.
        
        Args:
            template_id: ID of existing template
            customization_params: New customization parameters
            content_updates: Optional content updates
            
        Returns:
            Dict[str, Any]: Customized template
        """
        try:
            if template_id not in self.custom_templates:
                return {"success": False, "error": "Template not found"}
            
            original_template = self.custom_templates[template_id]
            base_template = original_template["template"]
            
            # Apply customizations
            customized_template = await self._apply_template_customizations(
                base_template, customization_params, original_template["language"]
            )
            
            # Apply content updates if provided
            if content_updates:
                customized_template = await self._apply_content_updates(
                    customized_template, content_updates, original_template["language"]
                )
            
            # Create new template version
            new_template_id = f"{template_id}_custom_{int(datetime.utcnow().timestamp())}"
            self.custom_templates[new_template_id] = {
                **original_template,
                "template": customized_template,
                "parent_template_id": template_id,
                "created_at": datetime.utcnow().isoformat(),
                "customization_params": customization_params,
                "content_updates": content_updates
            }
            
            return {
                "success": True,
                "template_id": new_template_id,
                "template": customized_template,
                "parent_template_id": template_id,
                "customizations_applied": customization_params
            }
            
        except Exception as e:
            error_msg = f"Template customization failed: {e}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    async def generate_multi_language_communication(
        self,
        base_content: str,
        target_languages: List[str],
        communication_type: CommunicationType,
        cultural_adaptations: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Generate communication in multiple languages with cultural adaptations.
        
        Args:
            base_content: Base content in English
            target_languages: List of target language codes
            communication_type: Type of communication
            cultural_adaptations: Optional cultural adaptation notes per language
            
        Returns:
            Dict[str, Any]: Multi-language communications
        """
        try:
            multi_language_content = {}
            
            for lang_code in target_languages:
                if lang_code not in self.supported_languages:
                    logger.warning(f"Unsupported language: {lang_code}")
                    continue
                
                # Translate content
                translated_content = await self._translate_communication(
                    base_content, lang_code, communication_type
                )
                
                # Apply cultural adaptations if provided
                if cultural_adaptations and lang_code in cultural_adaptations:
                    cultural_context = cultural_adaptations[lang_code]
                    adapted_content = await self._adapt_communication_culturally(
                        translated_content, cultural_context, lang_code, communication_type
                    )
                    multi_language_content[lang_code] = {
                        "content": adapted_content,
                        "language": self.supported_languages[lang_code],
                        "cultural_adaptations": cultural_context,
                        "translation_confidence": 0.9
                    }
                else:
                    multi_language_content[lang_code] = {
                        "content": translated_content,
                        "language": self.supported_languages[lang_code],
                        "cultural_adaptations": None,
                        "translation_confidence": 0.85
                    }
            
            return {
                "success": True,
                "base_language": "en",
                "target_languages": target_languages,
                "communications": multi_language_content,
                "communication_type": communication_type.value
            }
            
        except Exception as e:
            error_msg = f"Multi-language communication generation failed: {e}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    async def analyze_communication_effectiveness(
        self,
        template_id: Optional[str] = None,
        time_period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze communication template effectiveness and usage patterns.
        
        Args:
            template_id: Specific template to analyze (optional)
            time_period_days: Time period for analysis
            
        Returns:
            Dict[str, Any]: Communication effectiveness analysis
        """
        try:
            if template_id and template_id in self.custom_templates:
                # Analyze specific template
                template_data = self.custom_templates[template_id]
                usage_stats = self.template_usage_stats.get(template_id, {})
                
                analysis = {
                    "template_id": template_id,
                    "template_type": template_data["type"],
                    "template_category": template_data["category"],
                    "usage_count": template_data["usage_count"],
                    "creation_date": template_data["created_at"],
                    "effectiveness_score": self._calculate_template_effectiveness(template_id),
                    "usage_trends": usage_stats
                }
            else:
                # Analyze all templates
                total_templates = len(self.custom_templates)
                total_usage = sum(t["usage_count"] for t in self.custom_templates.values())
                
                # Template categories analysis
                category_stats = {}
                for template in self.custom_templates.values():
                    category = template["category"]
                    if category not in category_stats:
                        category_stats[category] = {"count": 0, "usage": 0}
                    category_stats[category]["count"] += 1
                    category_stats[category]["usage"] += template["usage_count"]
                
                analysis = {
                    "total_templates": total_templates,
                    "total_usage": total_usage,
                    "average_usage_per_template": total_usage / total_templates if total_templates > 0 else 0,
                    "category_statistics": category_stats,
                    "most_used_templates": self._get_most_used_templates(5),
                    "language_distribution": self._get_language_distribution()
                }
            
            return {
                "success": True,
                "analysis": analysis,
                "analysis_period_days": time_period_days
            }
            
        except Exception as e:
            error_msg = f"Communication effectiveness analysis failed: {e}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    @trace_ai_operation("enhanced_communication_preparation", "agent")
    async def execute_task(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute communication preparation task.
        
        Args:
            task_input: Input containing analysis_results, risk_results, negotiation_results, and workflow_id
            
        Returns:
            Dict[str, Any]: Communication results including email drafts and templates
        """
        # Validate input
        validation_errors = self.validate_input(
            task_input, 
            ["analysis_results", "risk_results", "negotiation_results"]
        )
        
        if validation_errors:
            raise ValidationError(f"Invalid input for communication preparation: {'; '.join(validation_errors)}")
        
        analysis_results = task_input["analysis_results"]
        risk_results = task_input["risk_results"]
        negotiation_results = task_input["negotiation_results"]
        workflow_id = task_input.get("workflow_id", "unknown")
        
        # Extract relevant data
        risky_clauses = risk_results.get("risky_clauses", [])
        overall_risk_score = risk_results.get("overall_risk_score", 0.0)
        suggested_redlines = negotiation_results.get("suggested_redlines", [])
        negotiation_strategy = negotiation_results.get("negotiation_strategy", "")
        
        logger.info(f"Starting communication preparation for workflow {workflow_id}")
        
        try:
            # Step 1: Generate executive summary email
            executive_email = await self._generate_executive_summary_email(
                analysis_results, risk_results, negotiation_results
            )
            
            # Step 2: Create detailed legal analysis report
            legal_report = await self._create_legal_analysis_report(
                analysis_results, risk_results, negotiation_results
            )
            
            # Step 3: Prepare counterparty communication
            counterparty_communication = await self._prepare_counterparty_communication(
                negotiation_results, risk_results
            )
            
            # Step 4: Generate team notification templates
            team_notifications = await self._generate_team_notifications(
                analysis_results, risk_results, negotiation_results
            )
            
            # Step 5: Create presentation materials
            presentation_materials = await self._create_presentation_materials(
                analysis_results, risk_results, negotiation_results
            )
            
            # Step 6: Generate next steps and action items
            next_steps = self._generate_next_steps(negotiation_results, risk_results)
            
            # Step 7: Send actual communications if requested
            communication_deliveries = {}
            
            # Check if we should send actual communications
            send_communications = task_input.get("send_communications", False)
            recipient_email = task_input.get("recipient_email")
            slack_channel = task_input.get("slack_channel")
            user_id = task_input.get("user_id", "default_user")
            
            if send_communications:
                # Send job application tracking email if recipient provided
                if recipient_email:
                    contract_name = analysis_results.get("original_filename", "Contract")
                    email_result = await self.send_contract_analysis_email(
                        recipient_email=recipient_email,
                        contract_name=contract_name,
                        analysis_results=analysis_results,
                        risk_results=risk_results,
                        negotiation_results=negotiation_results,
                        user_id=user_id
                    )
                    communication_deliveries["email"] = email_result
                
                # Send Slack alert if high risk or if channel specified
                if overall_risk_score >= 7 or slack_channel:
                    contract_name = analysis_results.get("original_filename", "Contract")
                    slack_result = await self.send_contract_analysis_slack_alert(
                        contract_name=contract_name,
                        analysis_results=analysis_results,
                        risk_results=risk_results,
                        negotiation_results=negotiation_results,
                        user_id=user_id
                    )
                    communication_deliveries["slack"] = slack_result
                
                # Send risk alerts if very high risk
                if overall_risk_score >= 8:
                    high_risk_clauses = [c for c in risky_clauses if c.get("risk_level") == "High"]
                    risk_alert_result = await self.send_risk_alert_communications(
                        contract_name=analysis_results.get("original_filename", "Contract"),
                        risk_score=overall_risk_score,
                        urgent_clauses=high_risk_clauses,
                        recipient_email=recipient_email,
                        user_id=user_id
                    )
                    communication_deliveries["risk_alerts"] = risk_alert_result
            
            # Compile results
            results = {
                "success": True,
                "email_draft": executive_email,
                "legal_report": legal_report,
                "counterparty_communication": counterparty_communication,
                "team_notifications": team_notifications,
                "presentation_materials": presentation_materials,
                "next_steps": next_steps,
                "communication_templates": {
                    "executive_summary": executive_email,
                    "legal_analysis": legal_report,
                    "negotiation_letter": counterparty_communication,
                    "team_update": team_notifications.get("general_update", ""),
                    "action_items": next_steps
                },
                "communication_metadata": {
                    "total_communications": 5,
                    "primary_audience": "executive_and_legal",
                    "urgency_level": self._determine_urgency_level(risk_results),
                    "follow_up_required": len(suggested_redlines) > 0,
                    "communications_sent": len(communication_deliveries) > 0
                },
                "communication_deliveries": communication_deliveries,
                "workflow_id": workflow_id
            }
            
            logger.info(f"Communication preparation completed for workflow {workflow_id}")
            
            return results
            
        except Exception as e:
            error_msg = f"Communication preparation failed: {e}"
            logger.error(error_msg, exc_info=True)
            
            return {
                "success": False,
                "error": error_msg,
                "workflow_id": workflow_id
            }
    
    async def _generate_executive_summary_email(
        self,
        analysis_results: Dict[str, Any],
        risk_results: Dict[str, Any],
        negotiation_results: Dict[str, Any]
    ) -> str:
        """
        Generate executive summary email.
        
        Args:
            analysis_results: Contract analysis results
            risk_results: Risk assessment results
            negotiation_results: Negotiation strategy results
            
        Returns:
            str: Executive summary email content
        """
        try:
            # Use CrewAI agent to generate executive email
            email_task = Task(
                description=f"""Generate a professional executive summary email for job application tracking results.
                
                Contract Analysis Summary:
                Contract Type: {analysis_results.get('contract_structure', {}).get('contract_type', 'Unknown')}
                Total Clauses Analyzed: {len(analysis_results.get('identified_clauses', []))}
                
                Risk Assessment Results:
                Overall Risk Score: {risk_results.get('overall_risk_score', 0):.1f}/10
                Risky Clauses Identified: {len(risk_results.get('risky_clauses', []))}
                High-Risk Clauses: {len([c for c in risk_results.get('risky_clauses', []) if c.get('risk_level') == 'High'])}
                
                Risk Summary:
                {risk_results.get('risk_summary', 'No summary available')[:500]}...
                
                Negotiation Recommendations:
                Total Redlines Suggested: {len(negotiation_results.get('suggested_redlines', []))}
                Critical Redlines: {len([r for r in negotiation_results.get('suggested_redlines', []) if r.get('priority') == 'critical'])}
                
                Please create an executive summary email that includes:
                1. Professional subject line
                2. Executive summary of key findings
                3. Risk assessment highlights
                4. Recommended actions and priorities
                5. Next steps and timeline
                6. Request for decision/approval where needed
                
                The email should be:
                - Concise but comprehensive (suitable for C-level executives)
                - Action-oriented with clear recommendations
                - Professional and business-focused
                - Include specific metrics and priorities
                
                Format as a complete email with subject line and body.""",
                agent=self.crew_agent,
                expected_output="Professional executive summary email with subject and body"
            )
            
            # Execute the email generation
            email_result = await email_task.execute_async()
            
            return str(email_result).strip()
            
        except Exception as e:
            logger.warning(f"Failed to generate executive summary email: {e}")
            
            # Fallback email
            return self._generate_fallback_executive_email(analysis_results, risk_results, negotiation_results)
    
    async def _create_legal_analysis_report(
        self,
        analysis_results: Dict[str, Any],
        risk_results: Dict[str, Any],
        negotiation_results: Dict[str, Any]
    ) -> str:
        """
        Create detailed legal analysis report.
        
        Args:
            analysis_results: Contract analysis results
            risk_results: Risk assessment results
            negotiation_results: Negotiation strategy results
            
        Returns:
            str: Detailed legal analysis report
        """
        try:
            # Use CrewAI agent to create legal report
            report_task = Task(
                description=f"""Create a comprehensive legal analysis report for contract review.
                
                Contract Analysis Details:
                {self._format_analysis_for_report(analysis_results)}
                
                Risk Assessment Details:
                {self._format_risk_assessment_for_report(risk_results)}
                
                Negotiation Strategy:
                {self._format_negotiation_for_report(negotiation_results)}
                
                Please create a detailed legal report that includes:
                1. Executive Summary
                2. Contract Structure Analysis
                3. Detailed Risk Assessment
                4. Clause-by-Clause Analysis of High-Risk Items
                5. Negotiation Strategy and Recommendations
                6. Legal Precedent Analysis (if available)
                7. Compliance Considerations
                8. Recommended Actions and Timeline
                9. Appendices with Supporting Documentation
                
                The report should be:
                - Comprehensive and legally precise
                - Well-structured with clear sections
                - Include specific recommendations and rationale
                - Suitable for legal team review and client presentation
                - Professional formatting with proper legal citations where applicable""",
                agent=self.crew_agent,
                expected_output="Comprehensive legal analysis report with detailed sections and recommendations"
            )
            
            # Execute the report creation
            report_result = await report_task.execute_async()
            
            return str(report_result).strip()
            
        except Exception as e:
            logger.warning(f"Failed to create legal analysis report: {e}")
            
            # Fallback report
            return self._generate_fallback_legal_report(analysis_results, risk_results, negotiation_results)
    
    async def _prepare_counterparty_communication(
        self,
        negotiation_results: Dict[str, Any],
        risk_results: Dict[str, Any]
    ) -> str:
        """
        Prepare communication for counterparty.
        
        Args:
            negotiation_results: Negotiation strategy results
            risk_results: Risk assessment results
            
        Returns:
            str: Counterparty communication content
        """
        try:
            # Use CrewAI agent to prepare counterparty communication
            counterparty_task = Task(
                description=f"""Prepare professional communication for contract counterparty regarding proposed changes.
                
                Proposed Redlines:
                {self._format_redlines_for_counterparty(negotiation_results.get('suggested_redlines', []))}
                
                Negotiation Strategy Context:
                {negotiation_results.get('negotiation_strategy', '')[:1000]}...
                
                Risk Context:
                Overall Risk Assessment: {risk_results.get('overall_risk_score', 0):.1f}/10
                Key Risk Areas: {self._format_risk_areas_for_counterparty(risk_results.get('risky_clauses', []))}
                
                Please create a professional communication that includes:
                1. Professional opening and context setting
                2. Business rationale for proposed changes
                3. Specific redline requests with justification
                4. Emphasis on mutual benefit and risk sharing
                5. Reference to industry standards where applicable
                6. Collaborative tone focused on problem-solving
                7. Clear next steps and timeline
                8. Professional closing
                
                The communication should be:
                - Professional and respectful
                - Focused on business rationale rather than legal technicalities
                - Collaborative and solution-oriented
                - Clear about specific requests and expectations
                - Maintain positive business relationship focus""",
                agent=self.crew_agent,
                expected_output="Professional counterparty communication with collaborative tone and clear requests"
            )
            
            # Execute the counterparty communication preparation
            counterparty_result = await counterparty_task.execute_async()
            
            return str(counterparty_result).strip()
            
        except Exception as e:
            logger.warning(f"Failed to prepare counterparty communication: {e}")
            
            # Fallback counterparty communication
            return self._generate_fallback_counterparty_communication(negotiation_results, risk_results)
    
    async def _generate_team_notifications(
        self,
        analysis_results: Dict[str, Any],
        risk_results: Dict[str, Any],
        negotiation_results: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate team notification templates.
        
        Args:
            analysis_results: Contract analysis results
            risk_results: Risk assessment results
            negotiation_results: Negotiation strategy results
            
        Returns:
            Dict[str, str]: Team notification templates
        """
        try:
            # Use CrewAI agent to generate team notifications
            notifications_task = Task(
                description=f"""Generate team notification templates for job application tracking completion.
                
                Analysis Summary:
                Contract: {analysis_results.get('original_filename', 'Unknown')}
                Risk Score: {risk_results.get('overall_risk_score', 0):.1f}/10
                Redlines: {len(negotiation_results.get('suggested_redlines', []))}
                
                Please create notification templates for:
                1. General team update (Slack/Teams format)
                2. Legal team notification (detailed)
                3. Project manager update (action-focused)
                4. Stakeholder alert (high-level summary)
                
                Each notification should be:
                - Appropriate for the target audience
                - Include key metrics and status
                - Highlight urgent items requiring attention
                - Provide clear next steps
                - Be concise but informative
                
                Provide results in JSON format with separate templates.""",
                agent=self.crew_agent,
                expected_output="JSON with team notification templates for different audiences"
            )
            
            # Execute the notifications generation
            notifications_result = await notifications_task.execute_async()
            
            # Parse the notifications
            notifications = self._parse_team_notifications(notifications_result)
            
            return notifications
            
        except Exception as e:
            logger.warning(f"Failed to generate team notifications: {e}")
            
            # Fallback notifications
            return self._generate_fallback_team_notifications(analysis_results, risk_results, negotiation_results)
    
    async def _create_presentation_materials(
        self,
        analysis_results: Dict[str, Any],
        risk_results: Dict[str, Any],
        negotiation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create presentation materials.
        
        Args:
            analysis_results: Contract analysis results
            risk_results: Risk assessment results
            negotiation_results: Negotiation strategy results
            
        Returns:
            Dict[str, Any]: Presentation materials and talking points
        """
        try:
            # Use CrewAI agent to create presentation materials
            presentation_task = Task(
                description=f"""Create presentation materials for job application tracking results.
                
                Key Data Points:
                - Contract Type: {analysis_results.get('contract_structure', {}).get('contract_type', 'Unknown')}
                - Overall Risk Score: {risk_results.get('overall_risk_score', 0):.1f}/10
                - High-Risk Clauses: {len([c for c in risk_results.get('risky_clauses', []) if c.get('risk_level') == 'High'])}
                - Critical Redlines: {len([r for r in negotiation_results.get('suggested_redlines', []) if r.get('priority') == 'critical'])}
                
                Please create presentation materials including:
                1. Executive summary slide content
                2. Risk assessment visualization data
                3. Key findings and recommendations
                4. Action items and timeline
                5. Talking points for presenter
                6. Q&A preparation points
                
                Materials should be suitable for executive presentation and decision-making.
                
                Provide results in JSON format with structured content.""",
                agent=self.crew_agent,
                expected_output="JSON with structured presentation materials and talking points"
            )
            
            # Execute the presentation creation
            presentation_result = await presentation_task.execute_async()
            
            # Parse the presentation materials
            presentation_materials = self._parse_presentation_materials(presentation_result)
            
            return presentation_materials
            
        except Exception as e:
            logger.warning(f"Failed to create presentation materials: {e}")
            
            # Fallback presentation materials
            return self._generate_fallback_presentation_materials(analysis_results, risk_results, negotiation_results)
    
    def _generate_next_steps(
        self,
        negotiation_results: Dict[str, Any],
        risk_results: Dict[str, Any]
    ) -> List[str]:
        """Generate next steps and action items"""
        next_steps = []
        
        # Based on negotiation results
        suggested_redlines = negotiation_results.get("suggested_redlines", [])
        critical_redlines = [r for r in suggested_redlines if r.get("priority") == "critical"]
        
        if critical_redlines:
            next_steps.append(f"URGENT: Review and approve {len(critical_redlines)} critical redline changes")
        
        if suggested_redlines:
            next_steps.append(f"Prepare negotiation materials for {len(suggested_redlines)} proposed changes")
            next_steps.append("Schedule negotiation meeting with counterparty")
        
        # Based on risk assessment
        high_risk_clauses = [c for c in risk_results.get("risky_clauses", []) if c.get("risk_level") == "High"]
        if high_risk_clauses:
            next_steps.append(f"Prioritize resolution of {len(high_risk_clauses)} high-risk clauses")
        
        # General next steps
        next_steps.extend([
            "Distribute analysis results to stakeholders",
            "Obtain internal approvals for negotiation strategy",
            "Set timeline for contract finalization",
            "Prepare fallback positions for negotiation"
        ])
        
        return next_steps[:8]  # Limit to 8 action items
    
    def _determine_urgency_level(self, risk_results: Dict[str, Any]) -> str:
        """Determine urgency level based on risk assessment"""
        overall_risk_score = risk_results.get("overall_risk_score", 0)
        high_risk_count = len([c for c in risk_results.get("risky_clauses", []) if c.get("risk_level") == "High"])
        
        if overall_risk_score >= 8 or high_risk_count >= 5:
            return "high"
        elif overall_risk_score >= 6 or high_risk_count >= 2:
            return "medium"
        else:
            return "low"
    
    def _format_analysis_for_report(self, analysis_results: Dict[str, Any]) -> str:
        """Format analysis results for report generation"""
        contract_structure = analysis_results.get("contract_structure", {})
        identified_clauses = analysis_results.get("identified_clauses", [])
        
        return f"""Contract Structure:
- Type: {contract_structure.get('contract_type', 'Unknown')}
- Total Clauses: {len(identified_clauses)}
- Main Sections: {', '.join(contract_structure.get('main_sections', []))}
- Parties: {', '.join(contract_structure.get('parties', []))}"""
    
    def _format_risk_assessment_for_report(self, risk_results: Dict[str, Any]) -> str:
        """Format risk assessment for report generation"""
        risky_clauses = risk_results.get("risky_clauses", [])
        risk_distribution = {
            "High": len([c for c in risky_clauses if c.get("risk_level") == "High"]),
            "Medium": len([c for c in risky_clauses if c.get("risk_level") == "Medium"]),
            "Low": len([c for c in risky_clauses if c.get("risk_level") == "Low"])
        }
        
        return f"""Risk Assessment Summary:
- Overall Risk Score: {risk_results.get('overall_risk_score', 0):.1f}/10
- Total Risky Clauses: {len(risky_clauses)}
- High Risk: {risk_distribution['High']} clauses
- Medium Risk: {risk_distribution['Medium']} clauses
- Low Risk: {risk_distribution['Low']} clauses

Risk Summary: {risk_results.get('risk_summary', 'No summary available')[:300]}..."""
    
    def _format_negotiation_for_report(self, negotiation_results: Dict[str, Any]) -> str:
        """Format negotiation results for report generation"""
        suggested_redlines = negotiation_results.get("suggested_redlines", [])
        priority_distribution = {
            "critical": len([r for r in suggested_redlines if r.get("priority") == "critical"]),
            "important": len([r for r in suggested_redlines if r.get("priority") == "important"]),
            "preferred": len([r for r in suggested_redlines if r.get("priority") == "preferred"])
        }
        
        return f"""Negotiation Strategy:
- Total Redlines: {len(suggested_redlines)}
- Critical Priority: {priority_distribution['critical']} items
- Important Priority: {priority_distribution['important']} items
- Preferred Priority: {priority_distribution['preferred']} items

Strategy Overview: {negotiation_results.get('negotiation_strategy', 'No strategy available')[:300]}..."""
    
    def _format_redlines_for_counterparty(self, suggested_redlines: List[Dict[str, Any]]) -> str:
        """Format redlines for counterparty communication"""
        formatted_redlines = []
        
        # Focus on critical and important redlines
        priority_redlines = [r for r in suggested_redlines if r.get("priority") in ["critical", "important"]]
        
        for i, redline in enumerate(priority_redlines[:5], 1):  # Limit to top 5
            formatted_redlines.append(
                f"{i}. {redline.get('clause_type', 'Unknown').title()} Clause - "
                f"Priority: {redline.get('priority', 'unknown').title()}\n"
                f"   Rationale: {redline.get('change_rationale', 'No rationale provided')[:150]}..."
            )
        
        return "\n\n".join(formatted_redlines)
    
    def _format_risk_areas_for_counterparty(self, risky_clauses: List[Dict[str, Any]]) -> str:
        """Format risk areas for counterparty communication"""
        risk_areas = {}
        
        for clause in risky_clauses:
            clause_type = clause.get("clause_type", "unknown")
            if clause_type not in risk_areas:
                risk_areas[clause_type] = 0
            risk_areas[clause_type] += 1
        
        return ", ".join([f"{area.title()} ({count})" for area, count in risk_areas.items()])
    
    def _parse_team_notifications(self, notifications_result: str) -> Dict[str, str]:
        """Parse team notifications from agent result"""
        try:
            import json
            
            # Try to extract JSON from the result
            if isinstance(notifications_result, str):
                start_idx = notifications_result.find('{')
                end_idx = notifications_result.rfind('}') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = notifications_result[start_idx:end_idx]
                    return json.loads(json_str)
            
            # If parsing fails, create basic notifications
            return self._generate_fallback_team_notifications({}, {}, {})
            
        except Exception as e:
            logger.warning(f"Failed to parse team notifications: {e}")
            return self._generate_fallback_team_notifications({}, {}, {})
    
    def _parse_presentation_materials(self, presentation_result: str) -> Dict[str, Any]:
        """Parse presentation materials from agent result"""
        try:
            import json
            
            # Try to extract JSON from the result
            if isinstance(presentation_result, str):
                start_idx = presentation_result.find('{')
                end_idx = presentation_result.rfind('}') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = presentation_result[start_idx:end_idx]
                    return json.loads(json_str)
            
            # If parsing fails, create basic materials
            return self._generate_fallback_presentation_materials({}, {}, {})
            
        except Exception as e:
            logger.warning(f"Failed to parse presentation materials: {e}")
            return self._generate_fallback_presentation_materials({}, {}, {})
    
    async def create_communication_template(
        self,
        template_name: str,
        template_type: str,
        subject_template: str,
        body_template: str,
        variables: List[str],
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new communication template.
        
        Args:
            template_name: Name of the template
            template_type: Type of template (email, slack, etc.)
            subject_template: Subject line template
            body_template: Body content template
            variables: List of template variables
            description: Optional description
            
        Returns:
            Dict[str, Any]: Template creation result
        """
        try:
            from pathlib import Path
            
            # Create template file
            template_dir = Path(__file__).parent.parent / "email_templates"
            template_dir.mkdir(exist_ok=True)
            
            template_file = template_dir / f"{template_name}.html"
            
            # Create template content with metadata
            template_content = f"""<!-- Template: {template_name} -->
<!-- Type: {template_type} -->
<!-- Description: {description or 'No description'} -->
<!-- Variables: {', '.join(variables)} -->

<!-- Subject Template -->
{{% set subject = "{subject_template}" %}}

<!-- Body Template -->
{body_template}
"""
            
            # Write template file
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            logger.info(f"Created communication template: {template_name}")
            
            return {
                "success": True,
                "template_name": template_name,
                "template_path": str(template_file),
                "message": f"Template '{template_name}' created successfully"
            }
            
        except Exception as e:
            error_msg = f"Failed to create communication template: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": "template_creation_failed", "message": error_msg}
    
    async def update_communication_template(
        self,
        template_name: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing communication template.
        
        Args:
            template_name: Name of the template to update
            updates: Dictionary of updates to apply
            
        Returns:
            Dict[str, Any]: Template update result
        """
        try:
            from pathlib import Path
            
            template_dir = Path(__file__).parent.parent / "email_templates"
            template_file = template_dir / f"{template_name}.html"
            
            if not template_file.exists():
                return {
                    "success": False,
                    "error": "template_not_found",
                    "message": f"Template '{template_name}' not found"
                }
            
            # Read existing template
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Apply updates (this is a simplified implementation)
            if "body_template" in updates:
                # Update body template (simplified - in production would parse properly)
                content = updates["body_template"]
            
            # Write updated template
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Updated communication template: {template_name}")
            
            return {
                "success": True,
                "template_name": template_name,
                "message": f"Template '{template_name}' updated successfully"
            }
            
        except Exception as e:
            error_msg = f"Failed to update communication template: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": "template_update_failed", "message": error_msg}
    
    async def list_communication_templates(self) -> Dict[str, Any]:
        """
        List all available communication templates.
        
        Returns:
            Dict[str, Any]: List of available templates
        """
        try:
            from pathlib import Path
            
            template_dir = Path(__file__).parent.parent / "email_templates"
            
            if not template_dir.exists():
                return {"success": True, "templates": [], "message": "No templates directory found"}
            
            templates = []
            for template_file in template_dir.glob("*.html"):
                template_info = {
                    "name": template_file.stem,
                    "path": str(template_file),
                    "size": template_file.stat().st_size,
                    "modified": datetime.fromtimestamp(template_file.stat().st_mtime).isoformat()
                }
                
                # Try to extract metadata from template
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Extract metadata from comments (simplified)
                    if "<!-- Type:" in content:
                        type_line = [line for line in content.split('\n') if "<!-- Type:" in line]
                        if type_line:
                            template_info["type"] = type_line[0].split("Type:")[1].split("-->")[0].strip()
                    
                    if "<!-- Description:" in content:
                        desc_line = [line for line in content.split('\n') if "<!-- Description:" in line]
                        if desc_line:
                            template_info["description"] = desc_line[0].split("Description:")[1].split("-->")[0].strip()
                
                except Exception:
                    pass  # Skip metadata extraction if it fails
                
                templates.append(template_info)
            
            return {
                "success": True,
                "templates": templates,
                "count": len(templates),
                "message": f"Found {len(templates)} communication templates"
            }
            
        except Exception as e:
            error_msg = f"Failed to list communication templates: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": "template_list_failed", "message": error_msg}
    
    async def delete_communication_template(self, template_name: str) -> Dict[str, Any]:
        """
        Delete a communication template.
        
        Args:
            template_name: Name of the template to delete
            
        Returns:
            Dict[str, Any]: Template deletion result
        """
        try:
            from pathlib import Path
            
            template_dir = Path(__file__).parent.parent / "email_templates"
            template_file = template_dir / f"{template_name}.html"
            
            if not template_file.exists():
                return {
                    "success": False,
                    "error": "template_not_found",
                    "message": f"Template '{template_name}' not found"
                }
            
            # Delete template file
            template_file.unlink()
            
            logger.info(f"Deleted communication template: {template_name}")
            
            return {
                "success": True,
                "template_name": template_name,
                "message": f"Template '{template_name}' deleted successfully"
            }
            
        except Exception as e:
            error_msg = f"Failed to delete communication template: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": "template_deletion_failed", "message": error_msg}
    
    async def personalize_communication(
        self,
        template_content: str,
        personalization_data: Dict[str, Any]
    ) -> str:
        """
        Personalize communication content with user-specific data.
        
        Args:
            template_content: Template content to personalize
            personalization_data: Data for personalization
            
        Returns:
            str: Personalized content
        """
        try:
            from jinja2 import Template
            
            # Create Jinja2 template
            template = Template(template_content)
            
            # Add default personalization data
            default_data = {
                "current_date": datetime.now().strftime("%B %d, %Y"),
                "current_time": datetime.now().strftime("%I:%M %p"),
                "platform_name": "Career Copilot",
                "support_email": "support@career-copilot.com"
            }
            
            # Merge with provided data
            merged_data = {**default_data, **personalization_data}
            
            # Render template
            personalized_content = template.render(**merged_data)
            
            return personalized_content
            
        except Exception as e:
            logger.error(f"Failed to personalize communication: {e}")
            return template_content  # Return original content if personalization fails
    
    async def test_communication_services(self) -> Dict[str, Any]:
        """
        Test all communication services connectivity.
        
        Returns:
            Dict[str, Any]: Test results for all services
        """
        try:
            results = {}
            
            # Test Gmail service
            try:
                gmail_auth = await self.gmail_service.authenticate()
                results["gmail"] = {
                    "service": "Gmail",
                    "authenticated": gmail_auth,
                    "enabled": self.gmail_service.enabled,
                    "status": "ready" if gmail_auth else "authentication_failed"
                }
            except Exception as e:
                results["gmail"] = {
                    "service": "Gmail",
                    "authenticated": False,
                    "enabled": False,
                    "status": "error",
                    "error": str(e)
                }
            
            # Test Slack service
            try:
                slack_test = await self.slack_service.test_connection()
                results["slack"] = {
                    "service": "Slack",
                    "status": "ready" if slack_test["success"] else "failed",
                    "enabled": self.slack_service.enabled,
                    "details": slack_test
                }
            except Exception as e:
                results["slack"] = {
                    "service": "Slack",
                    "status": "error",
                    "enabled": False,
                    "error": str(e)
                }
            
            # Overall status
            all_services_ready = all(
                result.get("status") == "ready" 
                for result in results.values()
            )
            
            return {
                "success": True,
                "overall_status": "ready" if all_services_ready else "partial",
                "services": results,
                "message": "Communication services tested"
            }
            
        except Exception as e:
            error_msg = f"Failed to test communication services: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": "service_test_failed", "message": error_msg}
    
    def _generate_fallback_executive_email(
        self,
        analysis_results: Dict[str, Any],
        risk_results: Dict[str, Any],
        negotiation_results: Dict[str, Any]
    ) -> str:
        """Generate fallback executive email"""
        risk_score = risk_results.get("overall_risk_score", 0)
        risky_clauses_count = len(risk_results.get("risky_clauses", []))
        redlines_count = len(negotiation_results.get("suggested_redlines", []))
        
        return f"""Subject: Contract Analysis Complete - Risk Score {risk_score:.1f}/10 - Action Required

Dear Team,

We have completed our comprehensive analysis of the contract. Here are the key findings:

EXECUTIVE SUMMARY:
• Overall Risk Score: {risk_score:.1f}/10 ({'High Risk' if risk_score >= 7 else 'Moderate Risk' if risk_score >= 4 else 'Low Risk'})
• Risky Clauses Identified: {risky_clauses_count}
• Redline Recommendations: {redlines_count}

KEY FINDINGS:
• {'Multiple high-risk clauses require immediate attention' if risky_clauses_count >= 3 else 'Contract presents manageable risk profile'}
• {'Significant negotiation effort will be required' if redlines_count >= 5 else 'Limited negotiation points identified'}

RECOMMENDED ACTIONS:
1. Review detailed analysis report
2. Approve negotiation strategy and redlines
3. Schedule counterparty discussion
4. Set timeline for contract finalization

Please review the attached detailed analysis and let me know if you need any clarification.

Best regards,
Legal Team"""
    
    def _generate_fallback_legal_report(
        self,
        analysis_results: Dict[str, Any],
        risk_results: Dict[str, Any],
        negotiation_results: Dict[str, Any]
    ) -> str:
        """Generate fallback legal report"""
        return f"""LEGAL ANALYSIS REPORT

EXECUTIVE SUMMARY
This report presents the results of our comprehensive job application tracking, including risk assessment and negotiation recommendations.

CONTRACT OVERVIEW
• Contract Type: {analysis_results.get('contract_structure', {}).get('contract_type', 'Unknown')}
• Analysis Date: {analysis_results.get('analysis_metadata', {}).get('analysis_timestamp', 'Unknown')}
• Total Clauses Reviewed: {len(analysis_results.get('identified_clauses', []))}

RISK ASSESSMENT
• Overall Risk Score: {risk_results.get('overall_risk_score', 0):.1f}/10
• Risky Clauses Identified: {len(risk_results.get('risky_clauses', []))}
• Risk Summary: {risk_results.get('risk_summary', 'No summary available')}

NEGOTIATION RECOMMENDATIONS
• Total Redlines Suggested: {len(negotiation_results.get('suggested_redlines', []))}
• Critical Priority Items: {len([r for r in negotiation_results.get('suggested_redlines', []) if r.get('priority') == 'critical'])}

RECOMMENDED ACTIONS
1. Address high-priority redlines immediately
2. Develop negotiation timeline
3. Prepare counterparty communications
4. Establish fallback positions

This analysis provides the foundation for informed contract negotiation and risk management decisions."""
    
    def _generate_fallback_counterparty_communication(
        self,
        negotiation_results: Dict[str, Any],
        risk_results: Dict[str, Any]
    ) -> str:
        """Generate fallback counterparty communication"""
        redlines_count = len(negotiation_results.get("suggested_redlines", []))
        
        return f"""Subject: Contract Review - Proposed Revisions for Discussion

Dear [Counterparty Name],

Thank you for providing the contract for our review. We have completed our analysis and would like to discuss some proposed revisions that we believe will benefit both parties.

Our review identified {redlines_count} areas where we believe adjustments would create a more balanced agreement and better align with industry standards. These changes focus on:

• Risk allocation and liability provisions
• Operational clarity and performance standards
• Compliance and regulatory alignment
• Mutual protection of business interests

We believe these revisions will strengthen our partnership while ensuring both parties are appropriately protected. We would welcome the opportunity to discuss these items and work together to finalize terms that work for everyone.

Would you be available for a call next week to review these items? We're committed to moving forward efficiently while ensuring we have a solid foundation for our business relationship.

Thank you for your continued collaboration.

Best regards,
[Your Name]"""
    
    def _generate_fallback_team_notifications(
        self,
        analysis_results: Dict[str, Any],
        risk_results: Dict[str, Any],
        negotiation_results: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate fallback team notifications"""
        return {
            "general_update": f"Contract analysis complete. Risk score: {risk_results.get('overall_risk_score', 0):.1f}/10. {len(negotiation_results.get('suggested_redlines', []))} redlines recommended. Review required.",
            "legal_team": f"Detailed job application tracking available. {len(risk_results.get('risky_clauses', []))} risky clauses identified. Negotiation strategy prepared. Please review and approve.",
            "project_manager": f"Contract review complete. Next steps: approve redlines, schedule counterparty meeting, finalize timeline. {len(negotiation_results.get('suggested_redlines', []))} items to negotiate.",
            "stakeholder_alert": f"Contract analysis shows {risk_results.get('overall_risk_score', 0):.1f}/10 risk score. Management review and approval needed for negotiation strategy."
        }
    
    def _generate_fallback_presentation_materials(
        self,
        analysis_results: Dict[str, Any],
        risk_results: Dict[str, Any],
        negotiation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate fallback presentation materials"""
        return {
            "executive_summary": {
                "title": "Contract Analysis Results",
                "key_points": [
                    f"Overall risk score: {risk_results.get('overall_risk_score', 0):.1f}/10",
                    f"{len(risk_results.get('risky_clauses', []))} risky clauses identified",
                    f"{len(negotiation_results.get('suggested_redlines', []))} redlines recommended"
                ]
            },
            "risk_visualization": {
                "chart_type": "risk_distribution",
                "data": {
                    "high": len([c for c in risk_results.get('risky_clauses', []) if c.get('risk_level') == 'High']),
                    "medium": len([c for c in risk_results.get('risky_clauses', []) if c.get('risk_level') == 'Medium']),
                    "low": len([c for c in risk_results.get('risky_clauses', []) if c.get('risk_level') == 'Low'])
                }
            },
            "talking_points": [
                "Contract presents manageable risk profile",
                "Key areas require negotiation attention",
                "Recommended changes align with industry standards",
                "Timeline for completion is achievable"
            ],
            "qa_preparation": [
                "What are the most critical risks?",
                "How long will negotiations take?",
                "What if counterparty rejects changes?",
                "Are there any deal-breakers?"
            ]
        }
    
    def _create_template_prompt(
        self,
        template_type: CommunicationType,
        template_category: TemplateCategory,
        content_data: Dict[str, Any],
        style: str,
        target_language: str,
        cultural_context: Optional[str]
    ) -> str:
        """Create template generation prompt based on parameters."""
        
        style_guidance = {
            "comprehensive": "detailed, thorough, and professionally comprehensive",
            "concise": "brief, clear, and action-oriented",
            "alternative": "creative, engaging, and relationship-focused"
        }
        
        base_prompt = f"""
        Generate a {style_guidance.get(style, 'professional')} {template_type.value} template 
        for {template_category.value} audience.
        
        Content Data:
        {json.dumps(content_data, indent=2)[:1000]}
        
        Target Language: {self.supported_languages.get(target_language, target_language)}
        Cultural Context: {cultural_context or 'Standard business context'}
        
        Template Requirements:
        - Professional and legally appropriate tone
        - Clear structure with proper formatting
        - Actionable content where applicable
        - Appropriate level of detail for {template_category.value} audience
        - Cultural sensitivity for {target_language} context
        
        Generate a complete template that can be customized with specific data.
        """
        
        return base_prompt
    
    async def _synthesize_templates(
        self,
        templates: Dict[str, str],
        template_type: CommunicationType,
        content_data: Dict[str, Any]
    ) -> str:
        """Synthesize multiple templates into optimal version."""
        
        synthesis_prompt = f"""
        Synthesize the following {template_type.value} templates into an optimal version:
        
        Comprehensive Version:
        {templates.get('comprehensive', 'Not available')[:800]}
        
        Concise Version:
        {templates.get('concise', 'Not available')[:800]}
        
        Alternative Version:
        {templates.get('alternative', 'Not available')[:800]}
        
        Create a synthesized template that:
        1. Combines the best elements of each version
        2. Maintains appropriate length and detail
        3. Ensures clarity and professionalism
        4. Addresses all key points from the content data
        
        Content Context: {json.dumps(content_data, indent=2)[:500]}
        """
        
        try:
            synthesis_response = await self.llm_manager.get_completion(
                prompt=synthesis_prompt,
                task_type=TaskType.COMMUNICATION,
                preferred_provider="openai"
            )
            return synthesis_response.content
        except Exception as e:
            logger.warning(f"Template synthesis failed: {e}")
            return templates.get('comprehensive', templates.get('concise', 'Template synthesis unavailable'))
    
    async def _apply_template_customizations(
        self,
        template: str,
        customization_params: Dict[str, Any],
        target_language: str
    ) -> str:
        """Apply customizations to template."""
        
        customization_prompt = f"""
        Customize the following template based on these parameters:
        
        Original Template:
        {template}
        
        Customization Parameters:
        {json.dumps(customization_params, indent=2)}
        
        Target Language: {self.supported_languages.get(target_language, target_language)}
        
        Apply the customizations while maintaining:
        - Professional tone and structure
        - Legal appropriateness
        - Cultural sensitivity for {target_language}
        - Clear and actionable content
        """
        
        try:
            customization_response = await self.llm_manager.get_completion(
                prompt=customization_prompt,
                task_type=TaskType.COMMUNICATION,
                preferred_provider="openai"
            )
            return customization_response.content
        except Exception as e:
            logger.warning(f"Template customization failed: {e}")
            return template
    
    async def _apply_content_updates(
        self,
        template: str,
        content_updates: Dict[str, Any],
        target_language: str
    ) -> str:
        """Apply content updates to template."""
        
        update_prompt = f"""
        Update the following template with new content:
        
        Current Template:
        {template}
        
        Content Updates:
        {json.dumps(content_updates, indent=2)}
        
        Target Language: {self.supported_languages.get(target_language, target_language)}
        
        Integrate the updates seamlessly while maintaining template structure and tone.
        """
        
        try:
            update_response = await self.llm_manager.get_completion(
                prompt=update_prompt,
                task_type=TaskType.COMMUNICATION,
                preferred_provider="openai"
            )
            return update_response.content
        except Exception as e:
            logger.warning(f"Content update failed: {e}")
            return template
    
    async def _translate_communication(
        self,
        content: str,
        target_language: str,
        communication_type: CommunicationType
    ) -> str:
        """Translate communication content to target language."""
        
        if target_language == "en":
            return content
        
        language_name = self.supported_languages.get(target_language, target_language)
        
        translation_prompt = f"""
        Translate the following {communication_type.value} to {language_name} ({target_language}).
        Maintain professional legal tone and preserve all key information.
        
        Original Content:
        {content}
        
        Ensure the translation is:
        - Legally appropriate for {language_name} context
        - Professionally formatted
        - Culturally sensitive
        - Maintains the original intent and tone
        """
        
        try:
            translation_response = await self.llm_manager.get_completion(
                prompt=translation_prompt,
                task_type=TaskType.COMMUNICATION,
                preferred_provider="openai"
            )
            return translation_response.content
        except Exception as e:
            logger.warning(f"Communication translation failed: {e}")
            return f"[Translation to {language_name} unavailable]\n\n{content}"
    
    async def _adapt_communication_culturally(
        self,
        content: str,
        cultural_context: str,
        target_language: str,
        communication_type: CommunicationType
    ) -> str:
        """Adapt communication for cultural context."""
        
        language_name = self.supported_languages.get(target_language, target_language)
        
        adaptation_prompt = f"""
        Adapt the following {communication_type.value} for cultural context: {cultural_context}
        Target language/culture: {language_name} ({target_language})
        
        Original Content:
        {content}
        
        Apply cultural adaptations considering:
        1. Business communication norms and etiquette
        2. Legal and regulatory context
        3. Relationship management expectations
        4. Decision-making processes
        5. Formality levels and address styles
        
        Maintain professional standards while adapting for cultural appropriateness.
        """
        
        try:
            adaptation_response = await self.llm_manager.get_completion(
                prompt=adaptation_prompt,
                task_type=TaskType.COMMUNICATION,
                preferred_provider="openai"
            )
            return adaptation_response.content
        except Exception as e:
            logger.warning(f"Cultural adaptation failed: {e}")
            return f"[Cultural adaptation for {cultural_context} unavailable]\n\n{content}"
    
    def _calculate_template_effectiveness(self, template_id: str) -> float:
        """Calculate template effectiveness score."""
        if template_id not in self.custom_templates:
            return 0.0
        
        template = self.custom_templates[template_id]
        usage_count = template["usage_count"]
        
        # Simple effectiveness calculation based on usage
        # In a real implementation, this could include feedback scores, success rates, etc.
        if usage_count == 0:
            return 0.5  # Neutral score for unused templates
        elif usage_count < 5:
            return 0.6
        elif usage_count < 20:
            return 0.8
        else:
            return 0.95
    
    def _get_most_used_templates(self, limit: int) -> List[Dict[str, Any]]:
        """Get most used templates."""
        sorted_templates = sorted(
            self.custom_templates.items(),
            key=lambda x: x[1]["usage_count"],
            reverse=True
        )
        
        return [
            {
                "template_id": template_id,
                "type": template_data["type"],
                "category": template_data["category"],
                "usage_count": template_data["usage_count"]
            }
            for template_id, template_data in sorted_templates[:limit]
        ]
    
    def _get_language_distribution(self) -> Dict[str, int]:
        """Get distribution of templates by language."""
        language_counts = {}
        for template in self.custom_templates.values():
            lang = template["language"]
            language_counts[lang] = language_counts.get(lang, 0) + 1
        return language_counts