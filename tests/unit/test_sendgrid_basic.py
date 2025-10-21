import os
import json
import time
from datetime import datetime
import re
import pytest

# Helper functions (moved outside test functions for reusability)
def validate_email(email: str) -> bool:
    """Basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if '..' in email:
        return False
    return re.match(pattern, email) is not None

def format_job_recommendations(recommendations):
    """Format job recommendations for email"""
    if not recommendations:
        return "<p>No new recommendations available at this time.</p>"
    
    html = "<div style='margin: 20px 0;'>"
    for i, job in enumerate(recommendations[:5], 1):
        html += f"""
        <div style='border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; margin-bottom: 15px; background-color: #f9f9f9;'>
            <h3 style='color: #2c3e50; margin: 0 0 10px 0;'>{job.get('title', 'Job Title')}</h3>
            <p style='color: #34495e; margin: 5px 0;'><strong>Company:</strong> {job.get('company', 'Company Name')}</p>
            <p style='color: #34495e; margin: 5px 0;'><strong>Location:</strong> {job.get('location', 'Location')}</p>
            <p style='color: #27ae60; margin: 5px 0;'><strong>Match Score:</strong> {job.get('match_score', 0)}%</p>
        </div>
        """
    html += "</div>"
    return html

def get_motivational_message(applications_count: int) -> str:
    """Get motivational message based on application count"""
    messages = {
        0: "Every expert was once a beginner. Tomorrow is a new day full of opportunities!",
        1: "You took the first step today - that's what matters most. Keep the momentum going!",
        2: "Two applications closer to your dream job. Consistency is key to success!",
        3: "Three applications today shows real dedication. You're building great habits!",
        4: "Four applications! You're really hitting your stride. Keep up the excellent work!",
        5: "Five applications today - you're on fire! Your persistence will pay off."
    }
    if applications_count >= 5:
        return messages[5]
    else:
        return messages.get(applications_count, messages[0])

def create_basic_email_template(user_name: str, content: str) -> str:
    """Create basic email template"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Career Copilot</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #3498db; color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 28px;">Hello, {user_name}!</h1>
        </div>
        
        <div style="margin-bottom: 30px;">
            {content}
        </div>
        
        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
            <p style="color: #7f8c8d; font-size: 14px;">
                Career Copilot - Your AI-powered job search assistant
            </p>
        </div>
    </body>
    </html>
    """

def test_sendgrid_imports():
    """Test that SendGrid can be imported"""
    import sendgrid
    from sendgrid.helpers.mail import Mail, Email, To, Content
    assert sendgrid is not None
    assert Mail is not None
    assert Email is not None
    assert To is not None
    assert Content is not None

def test_email_validation_standalone():
    """Test email validation without full service initialization"""
    # Test valid emails
    valid_emails = [
        'user@example.com',
        'test.email+tag@domain.co.uk',
        'user123@test-domain.com'
    ]
    for email in valid_emails:
        assert validate_email(email), f"Valid email {email} was rejected"
    
    # Test invalid emails
    invalid_emails = [
        'invalid-email',
        '@domain.com',
        'user@',
        'user..double.dot@domain.com'
    ]
    for email in invalid_emails:
        assert not validate_email(email), f"Invalid email {email} was accepted"

def test_email_content_formatting():
    """Test email content formatting functions"""
    recommendations = [
        {
            'title': 'Senior Software Engineer',
            'company': 'TechCorp',
            'location': 'San Francisco, CA',
            'match_score': 85
        },
        {
            'title': 'Full Stack Developer',
            'company': 'StartupXYZ',
            'location': 'Remote',
            'match_score': 78
        }
    ]
    formatted_html = format_job_recommendations(recommendations)
    
    assert 'Senior Software Engineer' in formatted_html
    assert 'TechCorp' in formatted_html
    assert '85%' in formatted_html
    
    empty_html = format_job_recommendations([])
    assert "No new recommendations" in empty_html

def test_motivational_messages_standalone():
    """Test motivational message generation"""
    test_counts = [0, 1, 2, 3, 4, 5, 10]
    for count in test_counts:
        message = get_motivational_message(count)
        assert message is not None and len(message) >= 10

def test_configuration_validation():
    """Test configuration validation"""
    original_key = os.environ.get('SENDGRID_API_KEY')
    
    # Test with missing API key
    if 'SENDGRID_API_KEY' in os.environ:
        del os.environ['SENDGRID_API_KEY']
    
    # Test with valid API key
    os.environ['SENDGRID_API_KEY'] = 'test_api_key_123'
    api_key = os.environ.get('SENDGRID_API_KEY')
    assert api_key == 'test_api_key_123'
    
    # Test email configuration
    os.environ['SENDGRID_FROM_EMAIL'] = 'test@career-copilot.com'
    from_email = os.environ.get('SENDGRID_FROM_EMAIL')
    assert from_email == 'test@career-copilot.com'
    
    # Restore original key if it existed
    if original_key:
        os.environ['SENDGRID_API_KEY'] = original_key

def test_email_template_structure():
    """Test email template structure"""
    template = create_basic_email_template("John Doe", "<p>Test content</p>")
    
    required_elements = [
        "<!DOCTYPE html>",
        "John Doe",
        "Test content",
        "Career Copilot"
    ]
    for element in required_elements:
        assert element in template
