"""
AI security module for preventing prompt injection, validating outputs, and monitoring AI behavior.
"""

import re
import json
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..core.logging import get_logger
from ..core.config import get_settings
from ..monitoring.metrics_collector import get_metrics_collector
from ..core.caching import get_cache_manager

logger = get_logger(__name__)
settings = get_settings()
metrics_collector = get_metrics_collector()
cache_manager = get_cache_manager()

@dataclass
class SecurityValidationResult:
    """Result of security validation checks."""
    is_safe: bool
    risk_level: str  # low, medium, high, critical
    detected_threats: List[str]
    sanitized_content: str
    validation_time: float
    metadata: Dict[str, Any]

class AISecurityManager:
    """
    Comprehensive AI security management system.
    
    Features:
    - Prompt injection prevention
    - Output validation and sanitization
    - Model behavior monitoring
    - Data anonymization
    - Security logging
    """
    
    # Common prompt injection patterns
    INJECTION_PATTERNS = [
        r"ignore previous instructions",
        r"disregard (all|previous|above).*instructions",
        r"forget (all|previous|above).*instructions",
        r"do not follow.*instructions",
        r"override.*instructions",
        r"new instruction set",
        r"system:\s*override",
        r"<\/?system>",
        r"{{.*}}",  # Template injection
        r"\[\[.*\]\]",  # Template injection
        r"<script.*>",  # XSS prevention
        r"function\s*\(",  # Code injection
        r"eval\s*\(",
        r"exec\s*\("
    ]
    
    # Patterns for sensitive data
    SENSITIVE_DATA_PATTERNS = [
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
        r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",  # Phone numbers
        r"\b\d{3}[-]?\d{2}[-]?\d{4}\b",  # SSN
        r"password[s]?\s*[=:]\s*\S+",  # Passwords
        r"api[_-]?key[s]?\s*[=:]\s*\S+",  # API keys
        r"token[s]?\s*[=:]\s*\S+",  # Tokens
        r"secret[s]?\s*[=:]\s*\S+",  # Secrets
        r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})\b"  # Credit card numbers
    ]
    
    def __init__(self):
        """Initialize AI security manager."""
        self.anomaly_thresholds = self._load_anomaly_thresholds()
        self.allowed_tokens = self._load_allowed_tokens()
        self.blocked_patterns = set()
        self.suspicious_patterns = set()
        self.last_update = datetime.min
        self.update_interval = timedelta(hours=1)
    
    async def validate_prompt(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> SecurityValidationResult:
        """
        Validate and sanitize input prompts.
        
        Args:
            prompt: The input prompt to validate
            context: Optional context about the request
            
        Returns:
            SecurityValidationResult with validation details
        """
        start_time = datetime.now()
        threats = []
        sanitized = prompt
        
        # Check for prompt injection attempts
        for pattern in self.INJECTION_PATTERNS:
            matches = re.finditer(pattern, prompt, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                threat = f"Potential prompt injection detected: {match.group()}"
                threats.append(threat)
                sanitized = sanitized.replace(match.group(), "[FILTERED]")
        
        # Check for sensitive data
        for pattern in self.SENSITIVE_DATA_PATTERNS:
            matches = re.finditer(pattern, prompt, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                threat = f"Sensitive data detected: {pattern}"
                threats.append(threat)
                sanitized = sanitized.replace(match.group(), "[REDACTED]")
        
        # Determine risk level
        risk_level = self._calculate_risk_level(threats)
        
        # Record metrics
        self._record_security_metrics("prompt_validation", risk_level, len(threats))
        
        validation_time = (datetime.now() - start_time).total_seconds()
        
        return SecurityValidationResult(
            is_safe=risk_level in ["low", "medium"],
            risk_level=risk_level,
            detected_threats=threats,
            sanitized_content=sanitized,
            validation_time=validation_time,
            metadata={
                "context": context,
                "original_length": len(prompt),
                "sanitized_length": len(sanitized)
            }
        )
    
    async def validate_output(self, output: str, model_info: Optional[Dict[str, Any]] = None) -> SecurityValidationResult:
        """
        Validate AI model outputs for security concerns.
        
        Args:
            output: The model output to validate
            model_info: Optional information about the model used
            
        Returns:
            SecurityValidationResult with validation details
        """
        start_time = datetime.now()
        threats = []
        sanitized = output
        
        # Check for sensitive data leakage
        for pattern in self.SENSITIVE_DATA_PATTERNS:
            matches = re.finditer(pattern, output, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                threat = f"Sensitive data in output: {pattern}"
                threats.append(threat)
                sanitized = sanitized.replace(match.group(), "[REDACTED]")
        
        # Check for malicious code patterns
        code_patterns = [
            r"<script.*?>",
            r"javascript:",
            r"eval\(",
            r"document\.",
            r"window\.",
            r"process\.",
            r"require\(",
            r"import\s+['\"]os['\"]",
            r"subprocess\."
        ]
        
        for pattern in code_patterns:
            matches = re.finditer(pattern, output, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                threat = f"Potential malicious code in output: {match.group()}"
                threats.append(threat)
                sanitized = sanitized.replace(match.group(), "[FILTERED]")
        
        risk_level = self._calculate_risk_level(threats)
        
        # Record metrics
        self._record_security_metrics("output_validation", risk_level, len(threats))
        
        validation_time = (datetime.now() - start_time).total_seconds()
        
        return SecurityValidationResult(
            is_safe=risk_level in ["low", "medium"],
            risk_level=risk_level,
            detected_threats=threats,
            sanitized_content=sanitized,
            validation_time=validation_time,
            metadata={
                "model_info": model_info,
                "original_length": len(output),
                "sanitized_length": len(sanitized)
            }
        )
    
    def monitor_model_behavior(self, 
                             model_id: str,
                             request_data: Dict[str, Any],
                             response_data: Dict[str, Any]
                             ) -> Dict[str, Any]:
        """
        Monitor AI model behavior for anomalies and potential misuse.
        
        Args:
            model_id: Identifier for the model
            request_data: Information about the request
            response_data: Information about the response
            
        Returns:
            Dict with monitoring results and any detected anomalies
        """
        anomalies = []
        metrics = {
            "request_tokens": len(str(request_data.get("prompt", ""))),
            "response_tokens": len(str(response_data.get("content", ""))),
            "processing_time": response_data.get("processing_time", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Check for anomalous token usage
        if metrics["request_tokens"] > self.anomaly_thresholds["max_input_tokens"]:
            anomalies.append({
                "type": "excessive_input_tokens",
                "value": metrics["request_tokens"],
                "threshold": self.anomaly_thresholds["max_input_tokens"]
            })
        
        if metrics["response_tokens"] > self.anomaly_thresholds["max_output_tokens"]:
            anomalies.append({
                "type": "excessive_output_tokens",
                "value": metrics["response_tokens"],
                "threshold": self.anomaly_thresholds["max_output_tokens"]
            })
        
        # Check for processing time anomalies
        if metrics["processing_time"] > self.anomaly_thresholds["max_processing_time"]:
            anomalies.append({
                "type": "slow_processing",
                "value": metrics["processing_time"],
                "threshold": self.anomaly_thresholds["max_processing_time"]
            })
        
        # Record monitoring metrics
        self._record_security_metrics(
            "model_monitoring",
            "high" if anomalies else "low",
            len(anomalies)
        )
        
        return {
            "model_id": model_id,
            "anomalies": anomalies,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def anonymize_data(self, data: str) -> str:
        """
        Anonymize sensitive data before AI processing.
        
        Args:
            data: The data to anonymize
            
        Returns:
            Anonymized version of the data
        """
        anonymized = data
        
        # Replace sensitive patterns with anonymized versions
        for pattern in self.SENSITIVE_DATA_PATTERNS:
            anonymized = re.sub(
                pattern,
                "[ANONYMIZED]",
                anonymized,
                flags=re.IGNORECASE | re.MULTILINE
            )
        
        return anonymized
    
    def _calculate_risk_level(self, threats: List[str]) -> str:
        """Calculate risk level based on threats."""
        if not threats:
            return "low"
        
        num_threats = len(threats)
        has_injection = any("injection" in t.lower() for t in threats)
        has_sensitive = any("sensitive" in t.lower() for t in threats)
        
        if has_injection or num_threats >= 3:
            return "critical"
        elif has_sensitive or num_threats == 2:
            return "high"
        else:
            return "medium"
    
    def _record_security_metrics(self, category: str, risk_level: str, num_threats: int):
        """Record security-related metrics."""
        metrics_collector.increment_counter(
            f"ai_security_{category}_total",
            tags={"risk_level": risk_level}
        )
        
        if num_threats > 0:
            metrics_collector.increment_counter(
                f"ai_security_{category}_threats",
                value=num_threats
            )
    
    def _load_anomaly_thresholds(self) -> Dict[str, float]:
        """Load anomaly detection thresholds."""
        return {
            "max_input_tokens": settings.security.max_input_tokens,
            "max_output_tokens": settings.security.max_output_tokens,
            "max_processing_time": settings.security.max_processing_time,
            "request_frequency_limit": settings.security.request_frequency_limit
        }
    
    def _load_allowed_tokens(self) -> Set[str]:
        """Load allowed tokens and patterns."""
        return set(settings.security.allowed_tokens)