"""
Enhanced component for managing user settings and preferences.
"""

import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime
import pytz

from ..utils.api_client import APIClient
from ..utils.validators import validate_email, validate_password_strength


class SettingsManager:
    """Enhanced settings manager for user preferences and configuration."""
    
    def __init__(self):
        """Initialize settings manager."""
        self.api_client = APIClient()
        self.available_models = [
            "gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o",
            "claude-3-haiku", "claude-3-sonnet", "claude-3-opus",
            "claude-3-5-sonnet", "ollama-llama2", "ollama-mistral"
        ]
        self.available_timezones = [
            "UTC", "US/Eastern", "US/Central", "US/Mountain", "US/Pacific",
            "Europe/London", "Europe/Paris", "Europe/Berlin", "Asia/Tokyo",
            "Asia/Shanghai", "Australia/Sydney"
        ]
    
    def render(self):
        """Render the complete settings interface."""
        st.header("⚙️ User Settings & Preferences")
        
        # Load current settings
        settings = self._load_settings()
        profile = self._load_profile()
        
        if not settings or not profile:
            st.error("Failed to load user settings. Please try again.")
            return
        
        # Create tabs for different setting categories
        tabs = st.tabs([
            "🤖 AI Preferences", 
            "🔔 Notifications", 
            "⚠️ Risk Thresholds",
            "🎨 Interface", 
            "👤 Profile", 
            "🔐 Security",
            "🔗 Integrations"
        ])
        
        with tabs[0]:
            self._render_ai_preferences(settings)
        
        with tabs[1]:
            self._render_notification_preferences(settings)
        
        with tabs[2]:
            self._render_risk_thresholds(settings)
        
        with tabs[3]:
            self._render_interface_preferences(settings)
        
        with tabs[4]:
            self._render_profile_management(profile)
        
        with tabs[5]:
            self._render_security_settings()
        
        with tabs[6]:
            self._render_integration_settings(settings)
        
        # Global actions
        st.divider()
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("💾 Save All Settings", type="primary", use_container_width=True):
                self._save_all_settings()
        
        with col2:
            if st.button("🔄 Reset to Defaults", use_container_width=True):
                self._reset_to_defaults()
        
        with col3:
            if st.button("📥 Export Settings", use_container_width=True):
                self._export_settings(settings)
    
    def _render_ai_preferences(self, settings: Dict[str, Any]):
        """Render AI model and analysis preferences."""
        st.subheader("🤖 AI Model Preferences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            ai_model = st.selectbox(
                "Preferred AI Model",
                options=self.available_models,
                index=self.available_models.index(settings.get("ai_model_preference", "gpt-3.5-turbo")),
                help="Select your preferred AI model for job application tracking"
            )
            
            analysis_depth = st.select_slider(
                "Analysis Depth",
                options=["shallow", "normal", "deep"],
                value=settings.get("analysis_depth", "normal"),
                help="Choose the depth of analysis: shallow (faster), normal (balanced), deep (thorough)"
            )
        
        with col2:
            auto_redlines = st.checkbox(
                "Auto-generate Redlines",
                value=settings.get("auto_generate_redlines", True),
                help="Automatically generate redline suggestions during analysis"
            )
            
            auto_emails = st.checkbox(
                "Auto-generate Email Drafts",
                value=settings.get("auto_generate_email_drafts", True),
                help="Automatically generate email drafts for contract negotiations"
            )
        
        # Store in session state for saving
        st.session_state.ai_preferences = {
            "ai_model_preference": ai_model,
            "analysis_depth": analysis_depth,
            "auto_generate_redlines": auto_redlines,
            "auto_generate_email_drafts": auto_emails
        }
        
        # Model information
        with st.expander("ℹ️ Model Information"):
            model_info = self._get_model_info(ai_model)
            st.info(model_info)
    
    def _render_notification_preferences(self, settings: Dict[str, Any]):
        """Render notification preferences."""
        st.subheader("🔔 Notification Preferences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            email_notifications = st.checkbox(
                "📧 Email Notifications",
                value=settings.get("email_notifications_enabled", True),
                help="Receive email notifications for analysis results and alerts"
            )
            
            slack_notifications = st.checkbox(
                "💬 Slack Notifications",
                value=settings.get("slack_notifications_enabled", True),
                help="Receive Slack notifications for team collaboration"
            )
        
        with col2:
            docusign_notifications = st.checkbox(
                "📝 DocuSign Notifications",
                value=settings.get("docusign_notifications_enabled", True),
                help="Receive notifications for document signing workflows"
            )
        
        st.session_state.notification_preferences = {
            "email_notifications_enabled": email_notifications,
            "slack_notifications_enabled": slack_notifications,
            "docusign_notifications_enabled": docusign_notifications
        }
        
        # Notification test
        if st.button("🧪 Test Notifications"):
            self._test_notifications()
    
    def _render_risk_thresholds(self, settings: Dict[str, Any]):
        """Render risk threshold configuration."""
        st.subheader("⚠️ Risk Assessment Thresholds")
        
        st.info("Configure the risk score thresholds for job application tracking. Values should be between 0.0 and 1.0.")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            low_threshold = st.slider(
                "🟢 Low Risk Threshold",
                min_value=0.0,
                max_value=1.0,
                value=float(settings.get("risk_threshold_low", 0.30)),
                step=0.05,
                help="Contracts below this score are considered low risk"
            )
        
        with col2:
            medium_threshold = st.slider(
                "🟡 Medium Risk Threshold",
                min_value=low_threshold + 0.05,
                max_value=1.0,
                value=max(float(settings.get("risk_threshold_medium", 0.60)), low_threshold + 0.05),
                step=0.05,
                help="Contracts between low and medium thresholds are medium risk"
            )
        
        with col3:
            high_threshold = st.slider(
                "🔴 High Risk Threshold",
                min_value=medium_threshold + 0.05,
                max_value=1.0,
                value=max(float(settings.get("risk_threshold_high", 0.80)), medium_threshold + 0.05),
                step=0.05,
                help="Contracts above this score are considered high risk"
            )
        
        st.session_state.risk_thresholds = {
            "risk_threshold_low": low_threshold,
            "risk_threshold_medium": medium_threshold,
            "risk_threshold_high": high_threshold
        }
        
        # Visual representation
        self._render_risk_threshold_visualization(low_threshold, medium_threshold, high_threshold)
    
    def _render_interface_preferences(self, settings: Dict[str, Any]):
        """Render UI/UX preferences."""
        st.subheader("🎨 Interface Preferences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            theme = st.selectbox(
                "Theme",
                options=["light", "dark", "auto"],
                index=["light", "dark", "auto"].index(settings.get("theme_preference", "light")),
                help="Choose your preferred interface theme"
            )
            
            language = st.selectbox(
                "Language",
                options=["en", "es", "fr", "de", "ja", "zh"],
                index=["en", "es", "fr", "de", "ja", "zh"].index(settings.get("preferred_language", "en")),
                help="Select your preferred language"
            )
        
        with col2:
            timezone = st.selectbox(
                "Timezone",
                options=self.available_timezones,
                index=self.available_timezones.index(settings.get("timezone", "UTC")),
                help="Select your timezone for date/time displays"
            )
        
        st.session_state.interface_preferences = {
            "theme_preference": theme,
            "preferred_language": language,
            "timezone": timezone
        }
        
        # Dashboard layout customization
        with st.expander("📊 Dashboard Layout"):
            self._render_dashboard_layout_options(settings)
    
    def _render_profile_management(self, profile: Dict[str, Any]):
        """Render user profile management."""
        st.subheader("👤 Profile Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input(
                "Username",
                value=profile.get("username", ""),
                help="Your unique username"
            )
            
            email = st.text_input(
                "Email Address",
                value=profile.get("email", ""),
                help="Your email address for notifications and login"
            )
        
        with col2:
            st.write("**Account Information**")
            st.write(f"**Account ID:** {profile.get('id', 'N/A')}")
            st.write(f"**Account Status:** {'Active' if profile.get('is_active') else 'Inactive'}")
            st.write(f"**Account Type:** {'Administrator' if profile.get('is_superuser') else 'User'}")
            
            if profile.get("created_at"):
                created_date = datetime.fromisoformat(profile["created_at"].replace("Z", "+00:00"))
                st.write(f"**Member Since:** {created_date.strftime('%B %d, %Y')}")
        
        st.session_state.profile_updates = {
            "username": username if username != profile.get("username") else None,
            "email": email if email != profile.get("email") else None
        }
        
        # Profile update button
        if st.button("💾 Update Profile"):
            self._update_profile()
    
    def _render_security_settings(self):
        """Render security and password settings."""
        st.subheader("🔐 Security Settings")
        
        # Password change section
        with st.expander("🔑 Change Password"):
            current_password = st.text_input(
                "Current Password",
                type="password",
                help="Enter your current password"
            )
            
            new_password = st.text_input(
                "New Password",
                type="password",
                help="Enter your new password"
            )
            
            confirm_password = st.text_input(
                "Confirm New Password",
                type="password",
                help="Confirm your new password"
            )
            
            # Password strength indicator
            if new_password:
                strength = validate_password_strength(new_password)
                self._render_password_strength(strength)
            
            if st.button("🔄 Change Password"):
                self._change_password(current_password, new_password, confirm_password)
        
        # Security information
        st.info("🛡️ **Security Tips:**\n"
                "- Use a strong, unique password\n"
                "- Enable two-factor authentication when available\n"
                "- Regularly review your account activity\n"
                "- Log out from shared devices")
    
    def _render_integration_settings(self, settings: Dict[str, Any]):
        """Render integration settings."""
        st.subheader("🔗 Integration Settings")
        
        integration_settings = settings.get("integration_settings", {})
        
        # Slack integration
        with st.expander("💬 Slack Integration"):
            slack_settings = integration_settings.get("slack", {})
            
            slack_webhook = st.text_input(
                "Slack Webhook URL",
                value=slack_settings.get("webhook_url", ""),
                type="password",
                help="Your Slack webhook URL for notifications"
            )
            
            slack_channel = st.text_input(
                "Default Channel",
                value=slack_settings.get("default_channel", "#contracts"),
                help="Default Slack channel for notifications"
            )
        
        # DocuSign integration
        with st.expander("📝 DocuSign Integration"):
            docusign_settings = integration_settings.get("docusign", {})
            
            docusign_env = st.selectbox(
                "Environment",
                options=["sandbox", "production"],
                index=0 if docusign_settings.get("environment", "sandbox") == "sandbox" else 1,
                help="DocuSign environment to use"
            )
        
        # Email integration
        with st.expander("📧 Email Integration"):
            email_settings = integration_settings.get("email", {})
            
            email_signature = st.text_area(
                "Email Signature",
                value=email_settings.get("signature", ""),
                help="Your default email signature for contract communications"
            )
        
        st.session_state.integration_settings = {
            "slack": {
                "webhook_url": slack_webhook,
                "default_channel": slack_channel
            },
            "docusign": {
                "environment": docusign_env
            },
            "email": {
                "signature": email_signature
            }
        }
    
    def _load_settings(self) -> Optional[Dict[str, Any]]:
        """Load user settings from API."""
        try:
            response = self.api_client.get("/api/v1/users/me/settings")
            return response.json() if response and response.status_code == 200 else None
        except Exception as e:
            st.error(f"Failed to load settings: {e}")
            return None
    
    def _load_profile(self) -> Optional[Dict[str, Any]]:
        """Load user profile from API."""
        try:
            response = self.api_client.get("/api/v1/users/me/profile")
            return response.json() if response and response.status_code == 200 else None
        except Exception as e:
            st.error(f"Failed to load profile: {e}")
            return None
    
    def _save_all_settings(self):
        """Save all settings to the backend."""
        try:
            # Combine all settings
            all_settings = {}
            
            if hasattr(st.session_state, 'ai_preferences'):
                all_settings.update(st.session_state.ai_preferences)
            
            if hasattr(st.session_state, 'notification_preferences'):
                all_settings.update(st.session_state.notification_preferences)
            
            if hasattr(st.session_state, 'risk_thresholds'):
                all_settings.update(st.session_state.risk_thresholds)
            
            if hasattr(st.session_state, 'interface_preferences'):
                all_settings.update(st.session_state.interface_preferences)
            
            if hasattr(st.session_state, 'integration_settings'):
                all_settings["integration_settings"] = st.session_state.integration_settings
            
            # Save to backend
            response = self.api_client.put("/api/v1/users/me/settings", json=all_settings)
            
            if response and response.status_code == 200:
                st.success("✅ Settings saved successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to save settings. Please try again.")
                
        except Exception as e:
            st.error(f"❌ Error saving settings: {e}")
    
    def _reset_to_defaults(self):
        """Reset settings to default values."""
        try:
            response = self.api_client.post("/api/v1/users/me/settings/reset")
            
            if response and response.status_code == 200:
                st.success("✅ Settings reset to defaults!")
                st.rerun()
            else:
                st.error("❌ Failed to reset settings. Please try again.")
                
        except Exception as e:
            st.error(f"❌ Error resetting settings: {e}")
    
    def _update_profile(self):
        """Update user profile."""
        try:
            profile_updates = st.session_state.get('profile_updates', {})
            
            # Filter out None values
            updates = {k: v for k, v in profile_updates.items() if v is not None}
            
            if not updates:
                st.info("No profile changes to save.")
                return
            
            response = self.api_client.put("/api/v1/users/me/profile", json=updates)
            
            if response and response.status_code == 200:
                st.success("✅ Profile updated successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to update profile. Please try again.")
                
        except Exception as e:
            st.error(f"❌ Error updating profile: {e}")
    
    def _change_password(self, current_password: str, new_password: str, confirm_password: str):
        """Change user password."""
        try:
            # Validation
            if not current_password:
                st.error("Current password is required.")
                return
            
            if not new_password:
                st.error("New password is required.")
                return
            
            if new_password != confirm_password:
                st.error("New passwords do not match.")
                return
            
            strength = validate_password_strength(new_password)
            if strength["score"] < 3:
                st.error("Password is too weak. Please choose a stronger password.")
                return
            
            # Change password
            response = self.api_client.post("/api/v1/users/me/change-password", json={
                "current_password": current_password,
                "new_password": new_password
            })
            
            if response and response.status_code == 200:
                st.success("✅ Password changed successfully!")
            else:
                st.error("❌ Failed to change password. Please check your current password.")
                
        except Exception as e:
            st.error(f"❌ Error changing password: {e}")
    
    def _get_model_info(self, model: str) -> str:
        """Get information about the selected AI model."""
        model_info = {
            "gpt-3.5-turbo": "Fast and cost-effective model, good for most job application tracking tasks.",
            "gpt-4": "More capable model with better reasoning, ideal for complex contracts.",
            "gpt-4-turbo": "Enhanced GPT-4 with improved performance and larger context window.",
            "gpt-4o": "Latest GPT-4 variant optimized for speed and accuracy.",
            "claude-3-haiku": "Fast and efficient model from Anthropic, good for quick analysis.",
            "claude-3-sonnet": "Balanced model with good performance for most use cases.",
            "claude-3-opus": "Most capable Claude model, excellent for complex legal analysis.",
            "claude-3-5-sonnet": "Enhanced Sonnet with improved capabilities.",
            "ollama-llama2": "Open-source model running locally, good for privacy-sensitive contracts.",
            "ollama-mistral": "Open-source model with strong performance for legal text analysis."
        }
        return model_info.get(model, "No information available for this model.")
    
    def _render_password_strength(self, strength: Dict[str, Any]):
        """Render password strength indicator."""
        score = strength["score"]
        
        if score < 2:
            st.error(f"🔴 Weak password: {strength['feedback']}")
        elif score < 3:
            st.warning(f"🟡 Fair password: {strength['feedback']}")
        elif score < 4:
            st.info(f"🟢 Good password: {strength['feedback']}")
        else:
            st.success(f"🟢 Strong password: {strength['feedback']}")
    
    def _render_risk_threshold_visualization(self, low: float, medium: float, high: float):
        """Render visual representation of risk thresholds."""
        st.write("**Risk Threshold Visualization:**")
        
        # Create a simple visual representation
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Low Risk", f"0.0 - {low:.2f}", delta="Safe")
        
        with col2:
            st.metric("Medium Risk", f"{low:.2f} - {medium:.2f}", delta="Caution")
        
        with col3:
            st.metric("High Risk", f"{medium:.2f} - {high:.2f}", delta="Review")
        
        with col4:
            st.metric("Critical Risk", f"{high:.2f} - 1.0", delta="Alert")
    
    def _render_dashboard_layout_options(self, settings: Dict[str, Any]):
        """Render dashboard layout customization options."""
        layout = settings.get("dashboard_layout", {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            show_recent_analyses = st.checkbox(
                "Show Recent Analyses",
                value=layout.get("show_recent_analyses", True)
            )
            
            show_risk_summary = st.checkbox(
                "Show Risk Summary",
                value=layout.get("show_risk_summary", True)
            )
        
        with col2:
            show_performance_metrics = st.checkbox(
                "Show Performance Metrics",
                value=layout.get("show_performance_metrics", True)
            )
            
            show_integration_status = st.checkbox(
                "Show Integration Status",
                value=layout.get("show_integration_status", True)
            )
        
        # Update session state
        if not hasattr(st.session_state, 'interface_preferences'):
            st.session_state.interface_preferences = {}
        
        st.session_state.interface_preferences["dashboard_layout"] = {
            "show_recent_analyses": show_recent_analyses,
            "show_risk_summary": show_risk_summary,
            "show_performance_metrics": show_performance_metrics,
            "show_integration_status": show_integration_status
        }
    
    def _test_notifications(self):
        """Test notification settings."""
        st.info("🧪 Testing notifications... (This would send test notifications to configured channels)")
        # In a real implementation, this would trigger test notifications
    
    def _export_settings(self, settings: Dict[str, Any]):
        """Export settings as JSON."""
        import json
        
        settings_json = json.dumps(settings, indent=2)
        st.download_button(
            label="📥 Download Settings JSON",
            data=settings_json,
            file_name=f"user_settings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )


def SettingsManager():
    """Render the settings manager component."""
    manager = SettingsManager()
    manager.render()
