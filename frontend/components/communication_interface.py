"""
Communication Interface Components for Contract Analysis
Handles email composition, Slack notifications, and communication history
"""

import streamlit as st
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re

class CommunicationType(Enum):
    """Communication type enumeration"""
    EMAIL = "email"
    SLACK = "slack"
    NOTIFICATION = "notification"

class CommunicationStatus(Enum):
    """Communication status enumeration"""
    DRAFT = "draft"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"

@dataclass
class CommunicationTemplate:
    """Communication template data structure"""
    id: str
    name: str
    type: CommunicationType
    subject: str
    content: str
    variables: List[str]
    category: str

@dataclass
class CommunicationRecord:
    """Communication record data structure"""
    id: str
    type: CommunicationType
    recipient: str
    subject: str
    content: str
    status: CommunicationStatus
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    contract_id: Optional[str] = None
    template_id: Optional[str] = None

class CommunicationInterface:
    """Main communication interface component"""
    
    def __init__(self, api_client, contract_id: Optional[str] = None, contract_data: Optional[Dict] = None):
        self.api_client = api_client
        self.contract_id = contract_id
        self.contract_data = contract_data or {}
        
        # Initialize session state
        if 'communication_history' not in st.session_state:
            st.session_state.communication_history = []
        if 'draft_communications' not in st.session_state:
            st.session_state.draft_communications = {}
        if 'communication_templates' not in st.session_state:
            st.session_state.communication_templates = self._load_default_templates()
    
    def render(self):
        """Render the communication interface"""
        st.header("💬 Communication Center")
        
        # Create tabs for different communication types
        tab1, tab2, tab3, tab4 = st.tabs([
            "📧 Email", 
            "💬 Slack", 
            "📋 Templates", 
            "📊 History"
        ])
        
        with tab1:
            self._render_email_interface()
        
        with tab2:
            self._render_slack_interface()
        
        with tab3:
            self._render_templates_interface()
        
        with tab4:
            self._render_history_interface()
    
    def _render_email_interface(self):
        """Render email composition interface"""
        st.subheader("📧 Email Composition")
        
        # Email composition form
        with st.form("email_composition"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                recipient = st.text_input(
                    "To *",
                    placeholder="recipient@example.com",
                    help="Enter recipient email address"
                )
                
                cc_recipients = st.text_input(
                    "CC",
                    placeholder="cc1@example.com, cc2@example.com",
                    help="Enter CC recipients (comma-separated)"
                )
                
                subject = st.text_input(
                    "Subject *",
                    placeholder="Contract Analysis Results",
                    help="Enter email subject"
                )
            
            with col2:
                # Template selection
                template_names = ["Custom"] + [t.name for t in st.session_state.communication_templates if t.type == CommunicationType.EMAIL]
                selected_template = st.selectbox(
                    "Use Template",
                    template_names,
                    help="Select a pre-defined template"
                )
                
                # Priority selection
                priority = st.selectbox(
                    "Priority",
                    ["Normal", "High", "Low"],
                    help="Email priority level"
                )
                
                # Include attachments
                include_analysis = st.checkbox(
                    "Include Analysis Report",
                    value=True,
                    help="Attach job application tracking report"
                )
                
                include_contract = st.checkbox(
                    "Include Original Contract",
                    value=False,
                    help="Attach original contract file"
                )
            
            # Email content
            if selected_template != "Custom":
                template = next((t for t in st.session_state.communication_templates if t.name == selected_template), None)
                if template:
                    content = self._populate_template(template.content, self.contract_data)
                else:
                    content = ""
            else:
                content = ""
            
            email_content = st.text_area(
                "Message *",
                value=content,
                height=200,
                placeholder="Enter your email message here...",
                help="Email content (supports basic HTML)"
            )
            
            # Action buttons
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                send_button = st.form_submit_button("📤 Send Email", type="primary")
            
            with col2:
                save_draft_button = st.form_submit_button("💾 Save Draft")
            
            with col3:
                preview_button = st.form_submit_button("👁️ Preview")
            
            with col4:
                clear_button = st.form_submit_button("🗑️ Clear")
            
            # Handle form submissions
            if send_button:
                self._handle_send_email(recipient, cc_recipients, subject, email_content, priority, include_analysis, include_contract)
            
            elif save_draft_button:
                self._handle_save_draft("email", recipient, subject, email_content)
            
            elif preview_button:
                self._handle_preview_email(recipient, subject, email_content)
            
            elif clear_button:
                st.rerun()
        
        # Show drafts
        self._render_drafts_section("email")
    
    def _render_slack_interface(self):
        """Render Slack notification interface"""
        st.subheader("💬 Slack Notifications")
        
        # Slack composition form
        with st.form("slack_composition"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                channel = st.text_input(
                    "Channel/User *",
                    placeholder="#general or @username",
                    help="Enter Slack channel or username"
                )
                
                message_type = st.selectbox(
                    "Message Type",
                    ["Standard", "Alert", "Update", "Summary"],
                    help="Type of Slack message"
                )
            
            with col2:
                # Template selection
                template_names = ["Custom"] + [t.name for t in st.session_state.communication_templates if t.type == CommunicationType.SLACK]
                selected_template = st.selectbox(
                    "Use Template",
                    template_names,
                    help="Select a pre-defined template"
                )
                
                # Notification options
                mention_channel = st.checkbox(
                    "Mention @channel",
                    help="Notify all channel members"
                )
                
                include_thread = st.checkbox(
                    "Send as thread",
                    help="Send as threaded message"
                )
            
            # Message content
            if selected_template != "Custom":
                template = next((t for t in st.session_state.communication_templates if t.name == selected_template), None)
                if template:
                    content = self._populate_template(template.content, self.contract_data)
                else:
                    content = ""
            else:
                content = ""
            
            slack_content = st.text_area(
                "Message *",
                value=content,
                height=150,
                placeholder="Enter your Slack message here...",
                help="Slack message content (supports Slack markdown)"
            )
            
            # Action buttons
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                send_button = st.form_submit_button("📤 Send Message", type="primary")
            
            with col2:
                save_draft_button = st.form_submit_button("💾 Save Draft")
            
            with col3:
                preview_button = st.form_submit_button("👁️ Preview")
            
            with col4:
                clear_button = st.form_submit_button("🗑️ Clear")
            
            # Handle form submissions
            if send_button:
                self._handle_send_slack(channel, slack_content, message_type, mention_channel, include_thread)
            
            elif save_draft_button:
                self._handle_save_draft("slack", channel, f"Slack to {channel}", slack_content)
            
            elif preview_button:
                self._handle_preview_slack(channel, slack_content)
            
            elif clear_button:
                st.rerun()
        
        # Show drafts
        self._render_drafts_section("slack")    

    def _render_templates_interface(self):
        """Render templates management interface"""
        st.subheader("📋 Communication Templates")
        
        # Template management tabs
        template_tab1, template_tab2 = st.tabs(["📝 Manage Templates", "➕ Create Template"])
        
        with template_tab1:
            # Display existing templates
            if st.session_state.communication_templates:
                for template in st.session_state.communication_templates:
                    with st.expander(f"{template.type.value.title()}: {template.name}"):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**Category:** {template.category}")
                            st.write(f"**Subject:** {template.subject}")
                            st.write("**Content Preview:**")
                            st.text_area(
                                "Content",
                                value=template.content[:200] + "..." if len(template.content) > 200 else template.content,
                                height=100,
                                disabled=True,
                                key=f"template_preview_{template.id}"
                            )
                            
                            if template.variables:
                                st.write(f"**Variables:** {', '.join(template.variables)}")
                        
                        with col2:
                            if st.button("✏️ Edit", key=f"edit_{template.id}"):
                                self._handle_edit_template(template.id)
                            
                            if st.button("🗑️ Delete", key=f"delete_{template.id}"):
                                self._handle_delete_template(template.id)
                            
                            if st.button("📋 Use", key=f"use_{template.id}"):
                                self._handle_use_template(template.id)
            else:
                st.info("No templates available. Create your first template!")
        
        with template_tab2:
            # Create new template form
            with st.form("create_template"):
                template_name = st.text_input("Template Name *", placeholder="e.g., Contract Analysis Summary")
                
                col1, col2 = st.columns(2)
                with col1:
                    template_type = st.selectbox("Type *", ["email", "slack"])
                    template_category = st.selectbox("Category", ["Analysis", "Notification", "Follow-up", "Alert"])
                
                with col2:
                    template_subject = st.text_input("Subject/Title", placeholder="Subject line or message title")
                
                template_content = st.text_area(
                    "Content *",
                    height=200,
                    placeholder="Enter template content. Use {{variable_name}} for dynamic content.",
                    help="Use {{contract_name}}, {{risk_level}}, {{analysis_date}} etc. for dynamic content"
                )
                
                template_variables = st.text_input(
                    "Variables",
                    placeholder="contract_name, risk_level, analysis_date",
                    help="Comma-separated list of variables used in the template"
                )
                
                if st.form_submit_button("💾 Create Template"):
                    self._handle_create_template(
                        template_name, template_type, template_category, 
                        template_subject, template_content, template_variables
                    )
    
    def _render_history_interface(self):
        """Render communication history interface"""
        st.subheader("📊 Communication History")
        
        # Filters
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            type_filter = st.selectbox("Type", ["All", "Email", "Slack"], key="history_type_filter")
        
        with col2:
            status_filter = st.selectbox("Status", ["All", "Sent", "Failed", "Draft"], key="history_status_filter")
        
        with col3:
            date_range = st.selectbox("Date Range", ["All Time", "Last 7 days", "Last 30 days", "Last 90 days"])
        
        with col4:
            if st.button("🔄 Refresh History"):
                self._refresh_communication_history()
        
        # Load and display history
        history = self._get_filtered_history(type_filter, status_filter, date_range)
        
        if history:
            for record in history:
                status_color = {
                    CommunicationStatus.SENT: "🟢",
                    CommunicationStatus.FAILED: "🔴",
                    CommunicationStatus.DRAFT: "🟡",
                    CommunicationStatus.SENDING: "🔵"
                }.get(record.status, "⚪")
                
                type_icon = {
                    CommunicationType.EMAIL: "📧",
                    CommunicationType.SLACK: "💬"
                }.get(record.type, "📝")
                
                with st.expander(f"{status_color} {type_icon} {record.subject} - {record.recipient}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Recipient:** {record.recipient}")
                        st.write(f"**Subject:** {record.subject}")
                        st.write("**Content:**")
                        st.text_area(
                            "Message Content",
                            value=record.content,
                            height=100,
                            disabled=True,
                            key=f"history_content_{record.id}"
                        )
                    
                    with col2:
                        st.write(f"**Status:** {record.status.value.title()}")
                        st.write(f"**Type:** {record.type.value.title()}")
                        
                        if record.sent_at:
                            st.write(f"**Sent:** {record.sent_at.strftime('%Y-%m-%d %H:%M')}")
                        
                        if record.delivered_at:
                            st.write(f"**Delivered:** {record.delivered_at.strftime('%Y-%m-%d %H:%M')}")
                        
                        if record.error_message:
                            st.error(f"**Error:** {record.error_message}")
                        
                        # Action buttons
                        if record.status == CommunicationStatus.FAILED:
                            if st.button("🔄 Retry", key=f"retry_{record.id}"):
                                self._handle_retry_communication(record.id)
                        
                        if record.status == CommunicationStatus.DRAFT:
                            if st.button("✏️ Edit", key=f"edit_draft_{record.id}"):
                                self._handle_edit_draft(record.id)
        else:
            st.info("No communication history found.")
    
    def _render_drafts_section(self, comm_type: str):
        """Render drafts section for a communication type"""
        drafts = [d for d in st.session_state.draft_communications.values() if d.get('type') == comm_type]
        
        if drafts:
            st.subheader("💾 Saved Drafts")
            
            for draft in drafts:
                with st.expander(f"Draft: {draft.get('subject', 'Untitled')}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**To:** {draft.get('recipient', 'N/A')}")
                        st.write(f"**Subject:** {draft.get('subject', 'N/A')}")
                        st.write(f"**Saved:** {draft.get('saved_at', 'Unknown')}")
                    
                    with col2:
                        if st.button("✏️ Edit", key=f"edit_draft_{draft['id']}"):
                            self._handle_load_draft(draft['id'])
                        
                        if st.button("🗑️ Delete", key=f"delete_draft_{draft['id']}"):
                            self._handle_delete_draft(draft['id'])
    
    def _handle_send_email(self, recipient: str, cc_recipients: str, subject: str, content: str, 
                          priority: str, include_analysis: bool, include_contract: bool):
        """Handle email sending"""
        if not recipient or not subject or not content:
            st.error("Please fill in all required fields (To, Subject, Message)")
            return
        
        if not self._validate_email(recipient):
            st.error("Please enter a valid email address")
            return
        
        # Prepare email data
        email_data = {
            'to': recipient,
            'cc': [email.strip() for email in cc_recipients.split(',') if email.strip()] if cc_recipients else [],
            'subject': subject,
            'content': content,
            'priority': priority.lower(),
            'attachments': []
        }
        
        # Add attachments
        if include_analysis and self.contract_id:
            email_data['attachments'].append({
                'type': 'analysis_report',
                'contract_id': self.contract_id
            })
        
        if include_contract and self.contract_id:
            email_data['attachments'].append({
                'type': 'original_contract',
                'contract_id': self.contract_id
            })
        
        # Send email
        with st.spinner("Sending email..."):
            try:
                response = self.api_client.send_email(email_data)
                
                if 'error' not in response:
                    st.success("✅ Email sent successfully!")
                    
                    # Record in history
                    self._add_to_history(
                        CommunicationType.EMAIL, recipient, subject, content, 
                        CommunicationStatus.SENT, datetime.now()
                    )
                    
                    # Clear form
                    st.rerun()
                else:
                    st.error(f"❌ Failed to send email: {response['error']}")
                    
                    # Record failure in history
                    self._add_to_history(
                        CommunicationType.EMAIL, recipient, subject, content, 
                        CommunicationStatus.FAILED, error_message=response['error']
                    )
                    
            except Exception as e:
                st.error(f"❌ Error sending email: {str(e)}")
                self._add_to_history(
                    CommunicationType.EMAIL, recipient, subject, content, 
                    CommunicationStatus.FAILED, error_message=str(e)
                )
    
    def _handle_send_slack(self, channel: str, content: str, message_type: str, 
                          mention_channel: bool, include_thread: bool):
        """Handle Slack message sending"""
        if not channel or not content:
            st.error("Please fill in all required fields (Channel/User, Message)")
            return
        
        if not self._validate_slack_channel(channel):
            st.error("Please enter a valid Slack channel (#channel) or username (@username)")
            return
        
        # Prepare Slack data
        slack_data = {
            'channel': channel,
            'text': content,
            'message_type': message_type.lower(),
            'mention_channel': mention_channel,
            'thread_ts': None if not include_thread else 'auto'
        }
        
        # Send Slack message
        with st.spinner("Sending Slack message..."):
            try:
                response = self.api_client.send_slack_message(slack_data)
                
                if 'error' not in response:
                    st.success("✅ Slack message sent successfully!")
                    
                    # Record in history
                    self._add_to_history(
                        CommunicationType.SLACK, channel, f"Slack message to {channel}", content, 
                        CommunicationStatus.SENT, datetime.now()
                    )
                    
                    # Clear form
                    st.rerun()
                else:
                    st.error(f"❌ Failed to send Slack message: {response['error']}")
                    
                    # Record failure in history
                    self._add_to_history(
                        CommunicationType.SLACK, channel, f"Slack message to {channel}", content, 
                        CommunicationStatus.FAILED, error_message=response['error']
                    )
                    
            except Exception as e:
                st.error(f"❌ Error sending Slack message: {str(e)}")
                self._add_to_history(
                    CommunicationType.SLACK, channel, f"Slack message to {channel}", content, 
                    CommunicationStatus.FAILED, error_message=str(e)
                )
    
    def _handle_save_draft(self, comm_type: str, recipient: str, subject: str, content: str):
        """Handle saving draft"""
        if not content:
            st.warning("Cannot save empty draft")
            return
        
        draft_id = f"draft_{datetime.now().timestamp()}"
        draft = {
            'id': draft_id,
            'type': comm_type,
            'recipient': recipient,
            'subject': subject,
            'content': content,
            'saved_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        st.session_state.draft_communications[draft_id] = draft
        st.success("💾 Draft saved successfully!")
    
    def _handle_preview_email(self, recipient: str, subject: str, content: str):
        """Handle email preview"""
        st.subheader("👁️ Email Preview")
        
        with st.container():
            st.write("**From:** your-email@company.com")
            st.write(f"**To:** {recipient}")
            st.write(f"**Subject:** {subject}")
            st.write("**Message:**")
            st.markdown(content)
    
    def _handle_preview_slack(self, channel: str, content: str):
        """Handle Slack preview"""
        st.subheader("👁️ Slack Preview")
        
        with st.container():
            st.write(f"**Channel:** {channel}")
            st.write("**Message:**")
            st.code(content, language="markdown")
    
    def _validate_email(self, email: str) -> bool:
        """Validate email address"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_slack_channel(self, channel: str) -> bool:
        """Validate Slack channel or username"""
        return channel.startswith('#') or channel.startswith('@')
    
    def _populate_template(self, template_content: str, data: Dict[str, Any]) -> str:
        """Populate template with data"""
        content = template_content
        
        # Default variables
        default_vars = {
            'contract_name': data.get('filename', 'Contract'),
            'risk_level': data.get('risk_level', 'Unknown'),
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'confidence_score': data.get('confidence_score', 'N/A'),
            'company_name': 'Your Company'
        }
        
        # Replace variables
        for var, value in default_vars.items():
            content = content.replace(f'{{{{{var}}}}}', str(value))
        
        return content
    
    def _load_default_templates(self) -> List[CommunicationTemplate]:
        """Load default communication templates"""
        return [
            CommunicationTemplate(
                id="email_analysis_summary",
                name="Analysis Summary",
                type=CommunicationType.EMAIL,
                subject="Contract Analysis Results - {{contract_name}}",
                content="""Dear Recipient,

I hope this email finds you well. I'm writing to share the results of our job application tracking for {{contract_name}}.

**Analysis Summary:**
- Risk Level: {{risk_level}}
- Confidence Score: {{confidence_score}}%
- Analysis Date: {{analysis_date}}

Please find the detailed analysis report attached. I'd be happy to discuss the findings and any recommended actions.

Best regards,
{{company_name}} Team""",
                variables=["contract_name", "risk_level", "confidence_score", "analysis_date", "company_name"],
                category="Analysis"
            ),
            CommunicationTemplate(
                id="slack_risk_alert",
                name="Risk Alert",
                type=CommunicationType.SLACK,
                subject="High Risk Contract Alert",
                content="""🚨 **High Risk Contract Alert** 🚨

Contract: *{{contract_name}}*
Risk Level: *{{risk_level}}*
Analysis Date: {{analysis_date}}

Please review the analysis results and take appropriate action.

cc: @legal-team""",
                variables=["contract_name", "risk_level", "analysis_date"],
                category="Alert"
            ),
            CommunicationTemplate(
                id="email_follow_up",
                name="Follow-up Request",
                type=CommunicationType.EMAIL,
                subject="Follow-up: Contract Analysis - {{contract_name}}",
                content="""Hello,

I wanted to follow up on the job application tracking results I shared for {{contract_name}}.

Have you had a chance to review the findings? I'm available to discuss any questions or concerns you might have.

Please let me know if you need any additional information or clarification.

Best regards,
{{company_name}} Team""",
                variables=["contract_name", "company_name"],
                category="Follow-up"
            )
        ]
    
    def _add_to_history(self, comm_type: CommunicationType, recipient: str, subject: str, 
                       content: str, status: CommunicationStatus, sent_at: Optional[datetime] = None,
                       error_message: Optional[str] = None):
        """Add communication to history"""
        record = CommunicationRecord(
            id=f"comm_{datetime.now().timestamp()}",
            type=comm_type,
            recipient=recipient,
            subject=subject,
            content=content,
            status=status,
            sent_at=sent_at,
            error_message=error_message,
            contract_id=self.contract_id
        )
        
        st.session_state.communication_history.append(record)
        
        # Keep only last 100 records
        if len(st.session_state.communication_history) > 100:
            st.session_state.communication_history = st.session_state.communication_history[-100:]
    
    def _get_filtered_history(self, type_filter: str, status_filter: str, date_range: str) -> List[CommunicationRecord]:
        """Get filtered communication history"""
        history = st.session_state.communication_history.copy()
        
        # Filter by type
        if type_filter != "All":
            comm_type = CommunicationType.EMAIL if type_filter == "Email" else CommunicationType.SLACK
            history = [h for h in history if h.type == comm_type]
        
        # Filter by status
        if status_filter != "All":
            status = CommunicationStatus(status_filter.lower())
            history = [h for h in history if h.status == status]
        
        # Filter by date range
        if date_range != "All Time":
            days_map = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90}
            days = days_map.get(date_range, 0)
            
            if days > 0:
                cutoff_date = datetime.now() - timedelta(days=days)
                history = [h for h in history if h.sent_at and h.sent_at >= cutoff_date]
        
        # Sort by sent_at descending
        history.sort(key=lambda x: x.sent_at or datetime.min, reverse=True)
        
        return history
    
    def _refresh_communication_history(self):
        """Refresh communication history from API"""
        if self.api_client:
            try:
                response = self.api_client.get_communication_history(self.contract_id)
                if 'error' not in response and 'history' in response:
                    # Convert API response to CommunicationRecord objects
                    history = []
                    for item in response['history']:
                        record = CommunicationRecord(
                            id=item.get('id', ''),
                            type=CommunicationType(item.get('type', 'email')),
                            recipient=item.get('recipient', ''),
                            subject=item.get('subject', ''),
                            content=item.get('content', ''),
                            status=CommunicationStatus(item.get('status', 'sent')),
                            sent_at=datetime.fromisoformat(item['sent_at']) if item.get('sent_at') else None,
                            delivered_at=datetime.fromisoformat(item['delivered_at']) if item.get('delivered_at') else None,
                            error_message=item.get('error_message'),
                            contract_id=item.get('contract_id')
                        )
                        history.append(record)
                    
                    st.session_state.communication_history = history
                    st.success("✅ Communication history refreshed")
                else:
                    st.warning("Could not refresh communication history")
            except Exception as e:
                st.error(f"Error refreshing history: {str(e)}")
    
    def _handle_create_template(self, name: str, template_type: str, category: str, 
                               subject: str, content: str, variables: str):
        """Handle template creation"""
        if not name or not content:
            st.error("Please fill in template name and content")
            return
        
        # Parse variables
        var_list = [v.strip() for v in variables.split(',') if v.strip()] if variables else []
        
        # Create template
        template = CommunicationTemplate(
            id=f"template_{datetime.now().timestamp()}",
            name=name,
            type=CommunicationType(template_type),
            subject=subject,
            content=content,
            variables=var_list,
            category=category
        )
        
        st.session_state.communication_templates.append(template)
        st.success(f"✅ Template '{name}' created successfully!")
        st.rerun()
    
    def _handle_edit_template(self, template_id: str):
        """Handle template editing"""
        st.info(f"Edit functionality for template {template_id} - Implementation pending")
    
    def _handle_delete_template(self, template_id: str):
        """Handle template deletion"""
        st.session_state.communication_templates = [
            t for t in st.session_state.communication_templates if t.id != template_id
        ]
        st.success("Template deleted successfully!")
        st.rerun()
    
    def _handle_use_template(self, template_id: str):
        """Handle using a template"""
        st.info(f"Use template functionality for {template_id} - Implementation pending")
    
    def _handle_load_draft(self, draft_id: str):
        """Handle loading a draft"""
        st.info(f"Load draft functionality for {draft_id} - Implementation pending")
    
    def _handle_delete_draft(self, draft_id: str):
        """Handle deleting a draft"""
        if draft_id in st.session_state.draft_communications:
            del st.session_state.draft_communications[draft_id]
            st.success("Draft deleted successfully!")
            st.rerun()
    
    def _handle_retry_communication(self, record_id: str):
        """Handle retrying failed communication"""
        st.info(f"Retry functionality for {record_id} - Implementation pending")
    
    def _handle_edit_draft(self, record_id: str):
        """Handle editing a draft from history"""
        st.info(f"Edit draft functionality for {record_id} - Implementation pending")


# Utility functions for easy integration
def render_communication_interface(api_client, contract_id: Optional[str] = None, contract_data: Optional[Dict] = None):
    """Render the communication interface"""
    interface = CommunicationInterface(api_client, contract_id, contract_data)
    interface.render()

def render_quick_email_form(api_client, contract_data: Dict[str, Any]):
    """Render a quick email form for immediate use"""
    st.subheader("📧 Quick Email")
    
    with st.form("quick_email"):
        recipient = st.text_input("To", placeholder="recipient@example.com")
        subject = st.text_input("Subject", value=f"Contract Analysis - {contract_data.get('filename', 'Contract')}")
        
        # Quick message with contract summary
        default_message = f"""Hello,

Please find attached the analysis results for {contract_data.get('filename', 'the contract')}.

Key findings:
- Risk Level: {contract_data.get('risk_level', 'Unknown')}
- Confidence: {contract_data.get('confidence_score', 'N/A')}%

Please review and let me know if you have any questions.

Best regards"""
        
        message = st.text_area("Message", value=default_message, height=150)
        
        if st.form_submit_button("📤 Send Quick Email"):
            if recipient and subject and message:
                email_data = {
                    'to': recipient,
                    'subject': subject,
                    'content': message,
                    'attachments': [{'type': 'analysis_report', 'contract_id': contract_data.get('contract_id')}]
                }
                
                try:
                    response = api_client.send_email(email_data)
                    if 'error' not in response:
                        st.success("✅ Email sent successfully!")
                    else:
                        st.error(f"❌ Failed to send email: {response['error']}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            else:
                st.error("Please fill in all fields")

def render_quick_slack_notification(api_client, contract_data: Dict[str, Any]):
    """Render a quick Slack notification form"""
    st.subheader("💬 Quick Slack Notification")
    
    with st.form("quick_slack"):
        channel = st.text_input("Channel", placeholder="#general")
        
        # Quick message template
        risk_level = contract_data.get('risk_level', 'Unknown')
        risk_emoji = {'Low': '🟢', 'Medium': '🟡', 'High': '🔴', 'Critical': '🚨'}.get(risk_level, '⚪')
        
        default_message = f"""{risk_emoji} Contract Analysis Complete

**Contract:** {contract_data.get('filename', 'Unknown')}
**Risk Level:** {risk_level}
**Confidence:** {contract_data.get('confidence_score', 'N/A')}%

Analysis results are ready for review."""
        
        message = st.text_area("Message", value=default_message, height=120)
        
        if st.form_submit_button("📤 Send Notification"):
            if channel and message:
                slack_data = {
                    'channel': channel,
                    'text': message,
                    'message_type': 'notification'
                }
                
                try:
                    response = api_client.send_slack_message(slack_data)
                    if 'error' not in response:
                        st.success("✅ Slack message sent successfully!")
                    else:
                        st.error(f"❌ Failed to send message: {response['error']}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            else:
                st.error("Please fill in all fields")