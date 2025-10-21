"""
Enhanced email template management system with customization, versioning, and analytics.
Provides comprehensive template management for all email communications.
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

from pydantic import BaseModel, Field, validator
from jinja2 import Environment, FileSystemLoader, Template, TemplateError

from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class TemplateStatus(str, Enum):
    """Template status types"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class TemplateCategory(str, Enum):
    """Template categories"""
    TRANSACTIONAL = "transactional"
    MARKETING = "marketing"
    NOTIFICATION = "notification"
    SYSTEM = "system"
    LEGAL = "legal"


class TemplateType(str, Enum):
    """Email template types"""
    CONTRACT_ANALYSIS = "contract_analysis"
    RISK_ALERT = "risk_alert"
    NOTIFICATION = "notification"
    WELCOME = "welcome"
    REMINDER = "reminder"
    REPORT = "report"
    MARKETING = "marketing"
    SYSTEM = "system"


class TemplateFormat(str, Enum):
    """Template format types"""
    HTML = "html"
    TEXT = "text"
    MIXED = "mixed"


@dataclass
class TemplateVariable:
    """Template variable definition"""
    name: str
    type: str  # string, number, boolean, array, object
    required: bool = True
    default_value: Optional[Any] = None
    description: Optional[str] = None
    validation_rules: Optional[Dict[str, Any]] = None


@dataclass
class TemplateVersion:
    """Template version information"""
    version: str
    created_at: datetime
    created_by: str
    changelog: str
    is_active: bool = False


@dataclass
class TemplateMetrics:
    """Template usage metrics"""
    sent_count: int = 0
    open_rate: float = 0.0
    click_rate: float = 0.0
    bounce_rate: float = 0.0
    unsubscribe_rate: float = 0.0
    last_used: Optional[datetime] = None


class EmailTemplate(BaseModel):
    """Enhanced email template model"""
    id: str = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    type: TemplateType = Field(..., description="Template type")
    category: TemplateCategory = Field(..., description="Template category")
    status: TemplateStatus = Field(TemplateStatus.DRAFT, description="Template status")
    
    # Content
    subject_template: str = Field(..., description="Subject template")
    html_template: Optional[str] = Field(None, description="HTML template")
    text_template: Optional[str] = Field(None, description="Text template")
    
    # Metadata
    variables: List[TemplateVariable] = Field(default_factory=list, description="Template variables")
    tags: List[str] = Field(default_factory=list, description="Template tags")
    language: str = Field("en", description="Template language")
    
    # Versioning
    version: str = Field("1.0.0", description="Template version")
    versions: List[TemplateVersion] = Field(default_factory=list, description="Version history")
    
    # Settings
    tracking_enabled: bool = Field(True, description="Enable tracking")
    unsubscribe_enabled: bool = Field(True, description="Enable unsubscribe")
    
    # Metrics
    metrics: TemplateMetrics = Field(default_factory=TemplateMetrics, description="Usage metrics")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: str = Field("system", description="Creator")
    updated_by: str = Field("system", description="Last updater")

    @validator('subject_template', 'html_template', 'text_template')
    def validate_templates(cls, v):
        if v and len(v) > 100000:  # 100KB limit
            raise ValueError('Template too large (max 100KB)')
        return v


class EnhancedEmailTemplateManager:
    """Enhanced email template manager with versioning, analytics, and customization"""
    
    def __init__(self):
        self.templates: Dict[str, EmailTemplate] = {}
        self.jinja_env = Environment(
            loader=FileSystemLoader('templates/email'),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        self.template_cache = {}
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize the template manager"""
        logger.info("Initializing Enhanced Email Template Manager...")
        
        # Load built-in templates
        await self._load_builtin_templates()
        
        # Setup Jinja2 filters and functions
        self._setup_jinja_filters()
        
        self.is_initialized = True
        logger.info("Enhanced Email Template Manager initialized successfully")
    
    async def create_template(
        self,
        template_data: Dict[str, Any],
        created_by: str = "system"
    ) -> EmailTemplate:
        """Create a new email template"""
        # Validate template data
        await self._validate_template_data(template_data)
        
        # Create template
        template = EmailTemplate(
            **template_data,
            created_by=created_by,
            updated_by=created_by
        )
        
        # Add initial version
        template.versions.append(TemplateVersion(
            version=template.version,
            created_at=datetime.now(),
            created_by=created_by,
            changelog="Initial version",
            is_active=True
        ))
        
        # Store template
        self.templates[template.id] = template
        
        logger.info(f"Created email template: {template.id}")
        return template
    
    async def get_template(self, template_id: str) -> Optional[EmailTemplate]:
        """Get template by ID"""
        return self.templates.get(template_id)
    
    async def list_templates(
        self,
        type_filter: Optional[TemplateType] = None,
        category_filter: Optional[TemplateCategory] = None,
        status_filter: Optional[TemplateStatus] = None,
        tags_filter: Optional[List[str]] = None
    ) -> List[EmailTemplate]:
        """List templates with optional filters"""
        templates = list(self.templates.values())
        
        if type_filter:
            templates = [t for t in templates if t.type == type_filter]
        
        if category_filter:
            templates = [t for t in templates if t.category == category_filter]
        
        if status_filter:
            templates = [t for t in templates if t.status == status_filter]
        
        if tags_filter:
            templates = [
                t for t in templates
                if any(tag in t.tags for tag in tags_filter)
            ]
        
        return sorted(templates, key=lambda t: t.updated_at, reverse=True)
    
    async def render_template(
        self,
        template_id: str,
        variables: Dict[str, Any],
        format_type: TemplateFormat = TemplateFormat.HTML
    ) -> str:
        """Render template with variables"""
        template = await self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        # Validate variables
        await self._validate_template_variables(template, variables)
        
        # Get template content
        if format_type == TemplateFormat.HTML and template.html_template:
            template_content = template.html_template
        elif format_type == TemplateFormat.TEXT and template.text_template:
            template_content = template.text_template
        else:
            raise ValueError(f"Template format not available: {format_type}")
        
        # Check cache
        cache_key = f"{template_id}_{format_type}_{hash(str(variables))}"
        if cache_key in self.template_cache:
            return self.template_cache[cache_key]
        
        try:
            # Render template
            jinja_template = self.jinja_env.from_string(template_content)
            rendered = jinja_template.render(**variables)
            
            # Cache result
            self.template_cache[cache_key] = rendered
            
            # Update metrics
            await self._update_template_metrics(template_id, 'render')
            
            return rendered
            
        except TemplateError as e:
            logger.error(f"Template rendering error for {template_id}: {e}")
            raise ValueError(f"Template rendering failed: {e}")
    
    async def render_subject(
        self,
        template_id: str,
        variables: Dict[str, Any]
    ) -> str:
        """Render template subject"""
        template = await self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        try:
            jinja_template = self.jinja_env.from_string(template.subject_template)
            return jinja_template.render(**variables)
        except TemplateError as e:
            logger.error(f"Subject rendering error for {template_id}: {e}")
            raise ValueError(f"Subject rendering failed: {e}")
    
    async def get_template_analytics(self, template_id: str) -> Dict[str, Any]:
        """Get template analytics and metrics"""
        template = await self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        return {
            "template_id": template_id,
            "name": template.name,
            "type": template.type,
            "category": template.category,
            "status": template.status,
            "metrics": {
                "sent_count": template.metrics.sent_count,
                "open_rate": template.metrics.open_rate,
                "click_rate": template.metrics.click_rate,
                "bounce_rate": template.metrics.bounce_rate,
                "unsubscribe_rate": template.metrics.unsubscribe_rate,
                "last_used": template.metrics.last_used.isoformat() if template.metrics.last_used else None
            },
            "versions": [
                {
                    "version": v.version,
                    "created_at": v.created_at.isoformat(),
                    "created_by": v.created_by,
                    "is_active": v.is_active
                }
                for v in template.versions
            ],
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat()
        }
    
    async def _validate_template_data(self, template_data: Dict[str, Any]):
        """Validate template data"""
        required_fields = ['id', 'name', 'type', 'subject_template']
        for field in required_fields:
            if field not in template_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Check for duplicate ID
        if template_data['id'] in self.templates:
            raise ValueError(f"Template ID already exists: {template_data['id']}")
        
        # Validate template syntax
        if 'subject_template' in template_data:
            try:
                self.jinja_env.from_string(template_data['subject_template'])
            except TemplateError as e:
                raise ValueError(f"Invalid subject template syntax: {e}")
        
        if 'html_template' in template_data and template_data['html_template']:
            try:
                self.jinja_env.from_string(template_data['html_template'])
            except TemplateError as e:
                raise ValueError(f"Invalid HTML template syntax: {e}")
        
        if 'text_template' in template_data and template_data['text_template']:
            try:
                self.jinja_env.from_string(template_data['text_template'])
            except TemplateError as e:
                raise ValueError(f"Invalid text template syntax: {e}")
    
    async def _validate_template_variables(
        self,
        template: EmailTemplate,
        variables: Dict[str, Any]
    ):
        """Validate template variables"""
        errors = []
        
        for var in template.variables:
            if var.required and var.name not in variables:
                errors.append(f"Missing required variable: {var.name}")
                continue
            
            if var.name in variables:
                value = variables[var.name]
                
                # Type validation
                if var.type == "string" and not isinstance(value, str):
                    errors.append(f"Variable '{var.name}' must be a string")
                elif var.type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"Variable '{var.name}' must be a number")
                elif var.type == "boolean" and not isinstance(value, bool):
                    errors.append(f"Variable '{var.name}' must be a boolean")
                elif var.type == "array" and not isinstance(value, list):
                    errors.append(f"Variable '{var.name}' must be an array")
                elif var.type == "object" and not isinstance(value, dict):
                    errors.append(f"Variable '{var.name}' must be an object")
        
        if errors:
            raise ValueError(f"Template variable validation failed: {'; '.join(errors)}")
    
    async def _load_builtin_templates(self):
        """Load built-in email templates"""
        builtin_templates = [
            {
                "id": "contract_analysis_complete",
                "name": "Contract Analysis Complete",
                "description": "Notification when job application tracking is completed",
                "type": TemplateType.CONTRACT_ANALYSIS,
                "category": TemplateCategory.TRANSACTIONAL,
                "status": TemplateStatus.ACTIVE,
                "subject_template": "Contract Analysis Complete - {{ contract_name }}",
                "html_template": """
                <h2>Contract Analysis Complete</h2>
                <p>Hello {{ recipient_name }},</p>
                <p>The analysis for contract "{{ contract_name }}" has been completed.</p>
                
                <h3>Analysis Summary</h3>
                <ul>
                    <li><strong>Risk Score:</strong> {{ risk_score }}/10</li>
                    <li><strong>Risk Level:</strong> {{ risk_level }}</li>
                    <li><strong>Clauses Analyzed:</strong> {{ clauses_count }}</li>
                </ul>
                
                {% if risky_clauses %}
                <h3>Risky Clauses Identified</h3>
                <ul>
                {% for clause in risky_clauses %}
                    <li>{{ clause }}</li>
                {% endfor %}
                </ul>
                {% endif %}
                
                {% if recommendations %}
                <h3>Recommendations</h3>
                <ul>
                {% for recommendation in recommendations %}
                    <li>{{ recommendation }}</li>
                {% endfor %}
                </ul>
                {% endif %}
                
                <p>{{ analysis_summary }}</p>
                
                <p>Best regards,<br>Career Copilot Team</p>
                """,
                "text_template": """
                Contract Analysis Complete
                
                Hello {{ recipient_name }},
                
                The analysis for contract "{{ contract_name }}" has been completed.
                
                Analysis Summary:
                - Risk Score: {{ risk_score }}/10
                - Risk Level: {{ risk_level }}
                - Clauses Analyzed: {{ clauses_count }}
                
                {% if risky_clauses %}
                Risky Clauses Identified:
                {% for clause in risky_clauses %}
                - {{ clause }}
                {% endfor %}
                {% endif %}
                
                {% if recommendations %}
                Recommendations:
                {% for recommendation in recommendations %}
                - {{ recommendation }}
                {% endfor %}
                {% endif %}
                
                {{ analysis_summary }}
                
                Best regards,
                Career Copilot Team
                """,
                "variables": [
                    TemplateVariable("recipient_name", "string", False, description="Recipient name"),
                    TemplateVariable("contract_name", "string", True, description="Name of the contract"),
                    TemplateVariable("risk_score", "number", True, description="Overall risk score (0-10)"),
                    TemplateVariable("risk_level", "string", True, description="Risk level text"),
                    TemplateVariable("clauses_count", "number", True, description="Number of clauses analyzed"),
                    TemplateVariable("risky_clauses", "array", True, description="List of risky clauses"),
                    TemplateVariable("recommendations", "array", True, description="List of recommendations"),
                    TemplateVariable("analysis_summary", "string", True, description="Analysis summary text")
                ]
            }
        ]
        
        for template_data in builtin_templates:
            try:
                template = EmailTemplate(**template_data)
                template.versions.append(TemplateVersion(
                    version=template.version,
                    created_at=datetime.now(),
                    created_by="system",
                    changelog="Built-in template",
                    is_active=True
                ))
                self.templates[template.id] = template
                logger.info(f"Loaded built-in template: {template.id}")
            except Exception as e:
                logger.error(f"Failed to load built-in template {template_data.get('id')}: {e}")
    
    def _setup_jinja_filters(self):
        """Setup custom Jinja2 filters and functions"""
        def format_currency(value, currency='USD'):
            """Format currency values"""
            return f"${value:,.2f} {currency}"
        
        def format_date(value, format='%Y-%m-%d'):
            """Format date values"""
            if isinstance(value, str):
                value = datetime.fromisoformat(value)
            return value.strftime(format)
        
        def truncate_text(value, length=100, suffix='...'):
            """Truncate text to specified length"""
            if len(value) <= length:
                return value
            return value[:length] + suffix
        
        # Add filters
        self.jinja_env.filters['currency'] = format_currency
        self.jinja_env.filters['date'] = format_date
        self.jinja_env.filters['truncate'] = truncate_text
    
    async def _update_template_metrics(self, template_id: str, event_type: str):
        """Update template usage metrics"""
        template = self.templates.get(template_id)
        if not template:
            return
        
        if event_type == 'render':
            template.metrics.sent_count += 1
            template.metrics.last_used = datetime.now()
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get service health status"""
        return {
            "healthy": True,
            "service": "enhanced_email_template_manager",
            "templates_loaded": len(self.templates),
            "cache_size": len(self.template_cache),
            "jinja_env_ready": self.jinja_env is not None,
            "timestamp": datetime.now().isoformat()
        }
    
    async def shutdown(self):
        """Shutdown template manager"""
        logger.info("Shutting down Enhanced Email Template Manager...")
        
        # Clear caches
        self.template_cache.clear()
        self.templates.clear()
        
        logger.info("Enhanced Email Template Manager shutdown completed")