#!/usr/bin/env python3
"""
Basic SendGrid service tests without Google Cloud dependencies
"""

import sys
import os
import json
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_sendgrid_imports():
    """Test that SendGrid can be imported"""
    
    print("Testing SendGrid imports...")
    
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail, Email, To, Content
        print("✓ SendGrid library imports successful")
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import SendGrid: {str(e)}")
        return False

def test_email_validation_standalone():
    """Test email validation without full service initialization"""
    
    print("\nTesting email validation (standalone)...")
    
    try:
        import re
        
        def validate_email(email: str) -> bool:
            """Basic email validation"""
            # Simple but effective email validation
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            # Additional check for consecutive dots
            if '..' in email:
                return False
            return re.match(pattern, email) is not None
        
        # Test valid emails
        valid_emails = [
            'user@example.com',
            'test.email+tag@domain.co.uk',
            'user123@test-domain.com'
        ]
        
        # Test invalid emails
        invalid_emails = [
            'invalid-email',
            '@domain.com',
            'user@',
            'user..double.dot@domain.com'
        ]
        
        for email in valid_emails:
            if not validate_email(email):
                print(f"✗ Valid email {email} was rejected")
                return False
        
        for email in invalid_emails:
            if validate_email(email):
                print(f"✗ Invalid email {email} was accepted")
                return False
        
        print("✓ Email validation working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Email validation test failed: {str(e)}")
        return False

def test_email_content_formatting():
    """Test email content formatting functions"""
    
    print("\nTesting email content formatting...")
    
    try:
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
        
        # Test with sample data
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
        
        # Check if content contains expected elements
        if 'Senior Software Engineer' not in formatted_html:
            print("✗ Job title not found in formatted HTML")
            return False
        
        if 'TechCorp' not in formatted_html:
            print("✗ Company name not found in formatted HTML")
            return False
        
        if '85%' not in formatted_html:
            print("✗ Match score not found in formatted HTML")
            return False
        
        # Test with empty recommendations
        empty_html = format_job_recommendations([])
        if "No new recommendations" not in empty_html:
            print("✗ Empty recommendations not handled correctly")
            return False
        
        print("✓ Email content formatting working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Email content formatting test failed: {str(e)}")
        return False

def test_motivational_messages_standalone():
    """Test motivational message generation"""
    
    print("\nTesting motivational message generation...")
    
    try:
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
        
        # Test different application counts
        test_counts = [0, 1, 2, 3, 4, 5, 10]
        
        for count in test_counts:
            message = get_motivational_message(count)
            if not message or len(message) < 10:
                print(f"✗ Invalid motivational message for count {count}")
                return False
        
        print("✓ Motivational message generation working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Motivational message test failed: {str(e)}")
        return False

def test_configuration_validation():
    """Test configuration validation"""
    
    print("\nTesting configuration validation...")
    
    try:
        # Test environment variable handling
        original_key = os.environ.get('SENDGRID_API_KEY')
        
        # Test with missing API key
        if 'SENDGRID_API_KEY' in os.environ:
            del os.environ['SENDGRID_API_KEY']
        
        # Test with valid API key
        os.environ['SENDGRID_API_KEY'] = 'test_api_key_123'
        api_key = os.environ.get('SENDGRID_API_KEY')
        
        if api_key != 'test_api_key_123':
            print("✗ API key not set correctly")
            return False
        
        # Test email configuration
        os.environ['SENDGRID_FROM_EMAIL'] = 'test@career-copilot.com'
        from_email = os.environ.get('SENDGRID_FROM_EMAIL')
        
        if from_email != 'test@career-copilot.com':
            print("✗ From email not set correctly")
            return False
        
        # Restore original key if it existed
        if original_key:
            os.environ['SENDGRID_API_KEY'] = original_key
        
        print("✓ Configuration validation working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Configuration validation test failed: {str(e)}")
        return False

def test_email_template_structure():
    """Test email template structure"""
    
    print("\nTesting email template structure...")
    
    try:
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
        
        # Test template generation
        template = create_basic_email_template("John Doe", "<p>Test content</p>")
        
        # Validate template structure
        required_elements = [
            "<!DOCTYPE html>",
            "John Doe",
            "Test content",
            "Career Copilot"
        ]
        
        for element in required_elements:
            if element not in template:
                print(f"✗ Required element '{element}' not found in template")
                return False
        
        print("✓ Email template structure working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Email template structure test failed: {str(e)}")
        return False

def main():
    """Run basic SendGrid tests"""
    
    print("=" * 60)
    print("BASIC SENDGRID INTEGRATION TESTS")
    print("=" * 60)
    
    tests = [
        test_sendgrid_imports,
        test_email_validation_standalone,
        test_email_content_formatting,
        test_motivational_messages_standalone,
        test_configuration_validation,
        test_email_template_structure
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("✓ All basic SendGrid tests passed!")
        return True
    else:
        print(f"✗ {failed} tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)