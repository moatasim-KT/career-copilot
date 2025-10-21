"""
Validation utilities for user input.
"""

import re
from typing import Dict, Any


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate password strength and provide feedback.
    
    Args:
        password: Password to validate
        
    Returns:
        Dictionary with score (0-4) and feedback
    """
    if not password:
        return {"score": 0, "feedback": "Password is required"}
    
    score = 0
    feedback = []
    
    # Length check
    if len(password) >= 8:
        score += 1
    else:
        feedback.append("Use at least 8 characters")
    
    # Uppercase check
    if re.search(r'[A-Z]', password):
        score += 1
    else:
        feedback.append("Include uppercase letters")
    
    # Lowercase check
    if re.search(r'[a-z]', password):
        score += 1
    else:
        feedback.append("Include lowercase letters")
    
    # Number check
    if re.search(r'\d', password):
        score += 1
    else:
        feedback.append("Include numbers")
    
    # Special character check
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1
    else:
        feedback.append("Include special characters")
    
    # Length bonus
    if len(password) >= 12:
        score += 1
    
    # Cap at 4
    score = min(score, 4)
    
    # Generate feedback message
    if score == 0:
        message = "Very weak password"
    elif score == 1:
        message = "Weak password"
    elif score == 2:
        message = "Fair password"
    elif score == 3:
        message = "Good password"
    else:
        message = "Strong password"
    
    if feedback:
        message += f": {', '.join(feedback)}"
    
    return {"score": score, "feedback": message}


def validate_username(username: str) -> Dict[str, Any]:
    """
    Validate username format.
    
    Args:
        username: Username to validate
        
    Returns:
        Dictionary with is_valid and message
    """
    if not username:
        return {"is_valid": False, "message": "Username is required"}
    
    if len(username) < 3:
        return {"is_valid": False, "message": "Username must be at least 3 characters"}
    
    if len(username) > 50:
        return {"is_valid": False, "message": "Username must be less than 50 characters"}
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return {"is_valid": False, "message": "Username can only contain letters, numbers, underscores, and hyphens"}
    
    return {"is_valid": True, "message": "Valid username"}


def validate_risk_thresholds(low: float, medium: float, high: float) -> Dict[str, Any]:
    """
    Validate risk threshold configuration.
    
    Args:
        low: Low risk threshold
        medium: Medium risk threshold
        high: High risk threshold
        
    Returns:
        Dictionary with is_valid and message
    """
    # Check range
    if not (0.0 <= low <= 1.0 and 0.0 <= medium <= 1.0 and 0.0 <= high <= 1.0):
        return {"is_valid": False, "message": "All thresholds must be between 0.0 and 1.0"}
    
    # Check order
    if not (low < medium < high):
        return {"is_valid": False, "message": "Thresholds must be in ascending order: low < medium < high"}
    
    # Check minimum gaps
    if medium - low < 0.05:
        return {"is_valid": False, "message": "Medium threshold must be at least 0.05 higher than low threshold"}
    
    if high - medium < 0.05:
        return {"is_valid": False, "message": "High threshold must be at least 0.05 higher than medium threshold"}
    
    return {"is_valid": True, "message": "Valid risk thresholds"}


def validate_timezone(timezone: str) -> bool:
    """
    Validate timezone string.
    
    Args:
        timezone: Timezone string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        import pytz
        return timezone in pytz.all_timezones
    except ImportError:
        # Basic validation if pytz is not available
        common_timezones = [
            "UTC", "US/Eastern", "US/Central", "US/Mountain", "US/Pacific",
            "Europe/London", "Europe/Paris", "Europe/Berlin", "Asia/Tokyo",
            "Asia/Shanghai", "Australia/Sydney"
        ]
        return timezone in common_timezones


def validate_language_code(language: str) -> bool:
    """
    Validate language code format.
    
    Args:
        language: Language code to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not language:
        return False
    
    # Basic validation for common language codes
    common_languages = ["en", "es", "fr", "de", "it", "pt", "ja", "zh", "ko", "ru"]
    return language.lower() in common_languages


def validate_ai_model(model: str) -> bool:
    """
    Validate AI model selection.
    
    Args:
        model: AI model name to validate
        
    Returns:
        True if valid, False otherwise
    """
    valid_models = [
        "gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o",
        "claude-3-haiku", "claude-3-sonnet", "claude-3-opus",
        "claude-3-5-sonnet", "ollama-llama2", "ollama-mistral"
    ]
    return model in valid_models


def validate_analysis_depth(depth: str) -> bool:
    """
    Validate analysis depth setting.
    
    Args:
        depth: Analysis depth to validate
        
    Returns:
        True if valid, False otherwise
    """
    return depth in ["shallow", "normal", "deep"]


def validate_theme(theme: str) -> bool:
    """
    Validate theme preference.
    
    Args:
        theme: Theme to validate
        
    Returns:
        True if valid, False otherwise
    """
    return theme in ["light", "dark", "auto"]


def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not url:
        return False
    
    pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?$'
    return bool(re.match(pattern, url))


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input by removing potentially harmful content.
    
    Args:
        text: Text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove script tags and content
    text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove potentially harmful characters
    text = re.sub(r'[<>"\']', '', text)
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()