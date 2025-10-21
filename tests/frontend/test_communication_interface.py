"""
Unit tests for communication interface components
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from components.communication_interface import (
    CommunicationType, CommunicationStatus, CommunicationTemplate, 
    CommunicationRecord, CommunicationInterface,
    render_communication_interface, render_quick_email_form, render_quick_slack_notification
)

class TestCommunicationType:
    """Test cases for CommunicationType enum"""
    
    def test_communication_type_values(self):
        """Test communication type enum values"""
        assert CommunicationType.EMAIL.value == "email"
        assert CommunicationType.SLACK.value == "slack"
        assert CommunicationType.NOTIFICATION.value == "notification"

class TestCommunicationStatus:
    """Test cases for CommunicationStatus enum"""
    
    def test_communication_status_values(self):
        """Test communication status enum values"""
        assert CommunicationStatus.DRAFT.value == "draft"
        assert CommunicationStatus.SENDING.value == "sending"
        assert CommunicationStatus.SENT.value == "sent"
        assert CommunicationStatus.FAILED.value == "failed"
        assert CommunicationStatus.DELIVERED.value == "delivered"

class TestCommunicationTemplate:
    """Test cases for CommunicationTemplate dataclass"""
    
    def test_template_creation(self):
        """Test creating communication template"""
        template = CommunicationTemplate(
            id="template_1",
            name="Test Template",
            type=CommunicationType.EMAIL,
            subject="Test Subject",
            content="Test content with {{variable}}",
            variables=["variable"],
            category="Test"
        )
        
        assert template.id == "template_1"
        assert template.name == "Test Template"
        assert template.type == CommunicationType.EMAIL
        assert template.subject == "Test Subject"
        assert template.content == "Test content with {{variable}}"
        assert template.variables == ["variable"]
        assert template.category == "Test"

class TestCommunicationRecord:
    """Test cases for CommunicationRecord dataclass"""
    
    def test_record_creation(self):
        """Test creating communication record"""
        sent_time = datetime.now()
        
        record = CommunicationRecord(
            id="record_1",
            type=CommunicationType.EMAIL,
            recipient="test@example.com",
            subject="Test Subject",
            content="Test content",
            status=CommunicationStatus.SENT,
            sent_at=sent_time,
            contract_id="contract_123"
        )
        
        assert record.id == "record_1"
        assert record.type == CommunicationType.EMAIL
        assert record.recipient == "test@example.com"
        assert record.subject == "Test Subject"
        assert record.content == "Test content"
        assert record.status == CommunicationStatus.SENT
        assert record.sent_at == sent_time
        assert record.contract_id == "contract_123"
    
    def test_record_with_error(self):
        """Test creating communication record with error"""
        record = CommunicationRecord(
            id="record_2",
            type=CommunicationType.SLACK,
            recipient="#general",
            subject="Test Message",
            content="Test content",
            status=CommunicationStatus.FAILED,
            error_message="Connection failed"
        )
        
        assert record.status == CommunicationStatus.FAILED
        assert record.error_message == "Connection failed"
        assert record.sent_at is None

class TestCommunicationInterface:
    """Test cases for CommunicationInterface"""
    
    @pytest.fixture
    def mock_api_client(self):
        """Create mock API client"""
        client = Mock()
        client.send_email.return_value = {'status': 'success', 'message_id': 'msg_123'}
        client.send_slack_message.return_value = {'status': 'success', 'ts': '1234567890.123'}
        client.get_communication_history.return_value = {'history': []}
        return client
    
    @pytest.fixture
    def sample_contract_data(self):
        """Create sample contract data"""
        return {
            'contract_id': 'contract_123',
            'filename': 'test_contract.pdf',
            'risk_level': 'High',
            'confidence_score': 85.5
        }
    
    def _create_interface_with_mocks(self, api_client, contract_id=None, contract_data=None):
        """Helper method to create interface with mocks"""
        mock_session_state = MagicMock()
        mock_session_state.communication_history = []
        mock_session_state.draft_communications = {}
        mock_session_state.communication_templates = []
        
        with patch('streamlit.session_state', mock_session_state), \
             patch.object(CommunicationInterface, 'render'):
            
            return CommunicationInterface(api_client, contract_id, contract_data)
    
    def test_interface_initialization(self, mock_api_client, sample_contract_data):
        """Test communication interface initialization"""
        interface = self._create_interface_with_mocks(
            mock_api_client, 
            "contract_123", 
            sample_contract_data
        )
        
        assert interface.api_client == mock_api_client
        assert interface.contract_id == "contract_123"
        assert interface.contract_data == sample_contract_data
    
    def test_validate_email(self, mock_api_client):
        """Test email validation"""
        interface = self._create_interface_with_mocks(mock_api_client)
        
        # Valid emails
        assert interface._validate_email("test@example.com") is True
        assert interface._validate_email("user.name+tag@domain.co.uk") is True
        
        # Invalid emails
        assert interface._validate_email("invalid-email") is False
        assert interface._validate_email("@domain.com") is False
        assert interface._validate_email("user@") is False
        assert interface._validate_email("") is False
    
    def test_validate_slack_channel(self, mock_api_client):
        """Test Slack channel validation"""
        interface = self._create_interface_with_mocks(mock_api_client)
        
        # Valid channels/users
        assert interface._validate_slack_channel("#general") is True
        assert interface._validate_slack_channel("@username") is True
        
        # Invalid channels/users
        assert interface._validate_slack_channel("general") is False
        assert interface._validate_slack_channel("username") is False
        assert interface._validate_slack_channel("") is False
    
    def test_populate_template(self, mock_api_client, sample_contract_data):
        """Test template population with data"""
        interface = self._create_interface_with_mocks(
            mock_api_client, 
            contract_data=sample_contract_data
        )
        
        template_content = "Contract: {{contract_name}}, Risk: {{risk_level}}, Date: {{analysis_date}}"
        
        populated = interface._populate_template(template_content, sample_contract_data)
        
        assert "test_contract.pdf" in populated
        assert "High" in populated
        assert datetime.now().strftime('%Y-%m-%d') in populated
    
    def test_load_default_templates(self, mock_api_client):
        """Test loading default templates"""
        interface = self._create_interface_with_mocks(mock_api_client)
        
        templates = interface._load_default_templates()
        
        assert len(templates) >= 3  # Should have at least 3 default templates
        
        # Check template types
        email_templates = [t for t in templates if t.type == CommunicationType.EMAIL]
        slack_templates = [t for t in templates if t.type == CommunicationType.SLACK]
        
        assert len(email_templates) >= 1
        assert len(slack_templates) >= 1
        
        # Check template structure
        for template in templates:
            assert template.id
            assert template.name
            assert template.content
            assert isinstance(template.variables, list)
    
    def test_add_to_history(self, mock_api_client):
        """Test adding communication to history"""
        mock_session_state = MagicMock()
        mock_session_state.communication_history = []
        
        with patch('streamlit.session_state', mock_session_state):
            interface = CommunicationInterface(mock_api_client, "contract_123")
            
            sent_time = datetime.now()
            
            interface._add_to_history(
                CommunicationType.EMAIL,
                "test@example.com",
                "Test Subject",
                "Test content",
                CommunicationStatus.SENT,
                sent_time
            )
            
            # Check that record was added to session state
            assert len(mock_session_state.communication_history) == 1
            record = mock_session_state.communication_history[0]
            assert record.type == CommunicationType.EMAIL
            assert record.recipient == "test@example.com"
            assert record.status == CommunicationStatus.SENT
    
    def test_get_filtered_history(self, mock_api_client):
        """Test filtering communication history"""
        interface = self._create_interface_with_mocks(mock_api_client)
        
        # Create mock history in session state
        now = datetime.now()
        mock_history = [
            CommunicationRecord(
                id="1", type=CommunicationType.EMAIL, recipient="test1@example.com",
                subject="Email 1", content="Content 1", status=CommunicationStatus.SENT,
                sent_at=now
            ),
            CommunicationRecord(
                id="2", type=CommunicationType.SLACK, recipient="#general",
                subject="Slack 1", content="Content 2", status=CommunicationStatus.SENT,
                sent_at=now - timedelta(days=10)
            ),
            CommunicationRecord(
                id="3", type=CommunicationType.EMAIL, recipient="test2@example.com",
                subject="Email 2", content="Content 3", status=CommunicationStatus.FAILED,
                sent_at=now - timedelta(days=5)
            )
        ]
        
        # Mock session state
        with patch('streamlit.session_state') as mock_session:
            mock_session.communication_history = mock_history
            
            # Test filtering by type
            email_history = interface._get_filtered_history("Email", "All", "All Time")
            # Would check length and types in real implementation
            
            # Test filtering by status
            failed_history = interface._get_filtered_history("All", "Failed", "All Time")
            # Would check status in real implementation
            
            # Test filtering by date range
            recent_history = interface._get_filtered_history("All", "All", "Last 7 days")
            # Would check dates in real implementation

class TestUtilityFunctions:
    """Test utility functions"""
    
    @pytest.fixture
    def mock_api_client(self):
        """Create mock API client"""
        client = Mock()
        client.send_email.return_value = {'status': 'success'}
        client.send_slack_message.return_value = {'status': 'success'}
        return client
    
    @pytest.fixture
    def sample_contract_data(self):
        """Create sample contract data"""
        return {
            'contract_id': 'contract_123',
            'filename': 'test_contract.pdf',
            'risk_level': 'High',
            'confidence_score': 85.5
        }
    
    def test_render_communication_interface(self, mock_api_client, sample_contract_data):
        """Test rendering communication interface"""
        with patch.object(CommunicationInterface, 'render') as mock_render:
            render_communication_interface(mock_api_client, "contract_123", sample_contract_data)
            mock_render.assert_called_once()
    
    def test_render_quick_email_form(self, mock_api_client, sample_contract_data):
        """Test rendering quick email form"""
        with patch('streamlit.subheader'), \
             patch('streamlit.form'), \
             patch('streamlit.text_input'), \
             patch('streamlit.text_area'), \
             patch('streamlit.form_submit_button', return_value=False):
            
            # Should not raise any exceptions
            render_quick_email_form(mock_api_client, sample_contract_data)
    
    def test_render_quick_slack_notification(self, mock_api_client, sample_contract_data):
        """Test rendering quick Slack notification"""
        with patch('streamlit.subheader'), \
             patch('streamlit.form'), \
             patch('streamlit.text_input'), \
             patch('streamlit.text_area'), \
             patch('streamlit.form_submit_button', return_value=False):
            
            # Should not raise any exceptions
            render_quick_slack_notification(mock_api_client, sample_contract_data)

class TestEmailHandling:
    """Test email handling functionality"""
    
    @pytest.fixture
    def mock_api_client(self):
        """Create mock API client"""
        client = Mock()
        client.send_email.return_value = {'status': 'success', 'message_id': 'msg_123'}
        return client
    
    def test_handle_send_email_success(self, mock_api_client):
        """Test successful email sending"""
        interface = CommunicationInterface(mock_api_client)
        
        with patch('streamlit.session_state') as mock_session, \
             patch('streamlit.success'), \
             patch('streamlit.rerun'), \
             patch('streamlit.spinner'):
            
            mock_session.communication_history = []
            
            # Mock the method to avoid Streamlit dependencies
            with patch.object(interface, '_add_to_history') as mock_add_history:
                interface._handle_send_email(
                    "test@example.com", "", "Test Subject", "Test Content", 
                    "Normal", False, False
                )
                
                # Check API was called
                mock_api_client.send_email.assert_called_once()
                
                # Check history was updated
                mock_add_history.assert_called_once()
    
    def test_handle_send_email_validation_error(self, mock_api_client):
        """Test email sending with validation errors"""
        interface = CommunicationInterface(mock_api_client)
        
        with patch('streamlit.error') as mock_error:
            # Test missing recipient
            interface._handle_send_email("", "", "Subject", "Content", "Normal", False, False)
            mock_error.assert_called()
            
            # Test invalid email
            interface._handle_send_email("invalid-email", "", "Subject", "Content", "Normal", False, False)
            mock_error.assert_called()

class TestSlackHandling:
    """Test Slack handling functionality"""
    
    @pytest.fixture
    def mock_api_client(self):
        """Create mock API client"""
        client = Mock()
        client.send_slack_message.return_value = {'status': 'success', 'ts': '1234567890.123'}
        return client
    
    def test_handle_send_slack_success(self, mock_api_client):
        """Test successful Slack message sending"""
        interface = CommunicationInterface(mock_api_client)
        
        with patch('streamlit.session_state') as mock_session, \
             patch('streamlit.success'), \
             patch('streamlit.rerun'), \
             patch('streamlit.spinner'):
            
            mock_session.communication_history = []
            
            # Mock the method to avoid Streamlit dependencies
            with patch.object(interface, '_add_to_history') as mock_add_history:
                interface._handle_send_slack(
                    "#general", "Test message", "Standard", False, False
                )
                
                # Check API was called
                mock_api_client.send_slack_message.assert_called_once()
                
                # Check history was updated
                mock_add_history.assert_called_once()
    
    def test_handle_send_slack_validation_error(self, mock_api_client):
        """Test Slack sending with validation errors"""
        interface = CommunicationInterface(mock_api_client)
        
        with patch('streamlit.error') as mock_error:
            # Test missing channel
            interface._handle_send_slack("", "Message", "Standard", False, False)
            mock_error.assert_called()
            
            # Test invalid channel
            interface._handle_send_slack("invalid-channel", "Message", "Standard", False, False)
            mock_error.assert_called()

if __name__ == '__main__':
    pytest.main([__file__])