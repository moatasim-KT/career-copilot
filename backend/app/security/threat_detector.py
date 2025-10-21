"""
Advanced threat detection system for identifying security risks.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from ..core.logging import get_logger

logger = get_logger(__name__)


class ThreatLevel(Enum):
    """Threat severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """Types of threats that can be detected."""
    MALWARE = "malware"
    PHISHING = "phishing"
    INJECTION = "injection"
    SOCIAL_ENGINEERING = "social_engineering"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DENIAL_OF_SERVICE = "denial_of_service"
    SUSPICIOUS_BEHAVIOR = "suspicious_behavior"


@dataclass
class ThreatDetection:
    """Detected threat information."""
    threat_type: ThreatType
    threat_level: ThreatLevel
    description: str
    evidence: List[str]
    confidence: float  # 0.0 to 1.0
    mitigation_suggestions: List[str]


class ThreatDetector:
    """Advanced threat detection system."""
    
    # Injection attack patterns
    INJECTION_PATTERNS = {
        # SQL Injection
        r"(?i)(union\s+select|drop\s+table|insert\s+into|delete\s+from|update\s+set)": ThreatLevel.HIGH,
        r"(?i)(\'\s*or\s*\'\s*=\s*\'|\'\s*or\s*1\s*=\s*1|admin\'\s*--|\'\s*;\s*drop)": ThreatLevel.CRITICAL,
        
        # XSS patterns
        r"(?i)(<script[^>]*>|javascript:|vbscript:|onload\s*=|onerror\s*=)": ThreatLevel.HIGH,
        r"(?i)(document\.write|eval\s*\(|innerHTML\s*=|outerHTML\s*=)": ThreatLevel.MEDIUM,
        
        # Command injection
        r"(?i)(;\s*rm\s+-rf|;\s*cat\s+/etc/passwd|;\s*nc\s+-l|\|\s*sh|\|\s*bash)": ThreatLevel.CRITICAL,
        r"(?i)(system\s*\(|exec\s*\(|shell_exec\s*\(|passthru\s*\()": ThreatLevel.HIGH,
        
        # LDAP injection
        r"(?i)(\*\)\(|\)\(\*|\*\)\(.*\)\(|\)\(\&)": ThreatLevel.MEDIUM,
    }
    
    # Malware indicators
    MALWARE_INDICATORS = {
        # Suspicious API calls
        r"(?i)(CreateRemoteThread|WriteProcessMemory|VirtualAllocEx|SetWindowsHookEx)": ThreatLevel.HIGH,
        r"(?i)(RegSetValueEx|RegCreateKeyEx|RegOpenKeyEx|CreateService)": ThreatLevel.MEDIUM,
        
        # Network indicators
        r"(?i)(socket\s*\(|connect\s*\(|bind\s*\(|listen\s*\()": ThreatLevel.MEDIUM,
        r"(?i)(HttpSendRequest|InternetOpen|URLDownloadToFile|WinHttpOpen)": ThreatLevel.MEDIUM,
        
        # Crypto indicators
        r"(?i)(CryptAcquireContext|CryptCreateHash|CryptEncrypt|CryptDecrypt)": ThreatLevel.LOW,
        
        # Process manipulation
        r"(?i)(CreateProcess|ShellExecute|WinExec|CreateThread)": ThreatLevel.MEDIUM,
    }
    
    # Phishing indicators
    PHISHING_PATTERNS = {
        # Suspicious URLs
        r"(?i)(bit\.ly|tinyurl|t\.co|goo\.gl|ow\.ly|short\.link)": ThreatLevel.MEDIUM,
        r"(?i)(click\s+here|urgent\s+action|verify\s+account|suspended\s+account)": ThreatLevel.MEDIUM,
        r"(?i)(congratulations.*winner|lottery.*winner|inheritance.*million)": ThreatLevel.HIGH,
        
        # Credential harvesting
        r"(?i)(enter\s+password|login\s+credentials|verify\s+identity|confirm\s+account)": ThreatLevel.MEDIUM,
        r"(?i)(paypal.*verify|amazon.*security|microsoft.*account|google.*security)": ThreatLevel.HIGH,
    }
    
    # Social engineering patterns
    SOCIAL_ENGINEERING_PATTERNS = {
        r"(?i)(urgent.*action\s+required|account.*will\s+be\s+closed|immediate.*attention)": ThreatLevel.MEDIUM,
        r"(?i)(ceo.*request|executive.*order|confidential.*document|sensitive.*information)": ThreatLevel.HIGH,
        r"(?i)(wire\s+transfer|bank\s+details|routing\s+number|account\s+number)": ThreatLevel.HIGH,
        r"(?i)(gift\s+card|bitcoin|cryptocurrency|western\s+union)": ThreatLevel.MEDIUM,
    }
    
    # Data exfiltration patterns
    DATA_EXFILTRATION_PATTERNS = {
        r"(?i)(ftp\s+upload|sftp\s+put|scp\s+-r|rsync\s+-av)": ThreatLevel.MEDIUM,
        r"(?i)(curl.*-T|wget.*--post-file|nc.*-l.*>|base64.*decode)": ThreatLevel.HIGH,
        r"(?i)(email.*attachment|smtp.*send|mail.*-a|sendmail.*<)": ThreatLevel.MEDIUM,
    }
    
    # Privilege escalation patterns
    PRIVILEGE_ESCALATION_PATTERNS = {
        r"(?i)(sudo\s+-s|su\s+-|chmod\s+777|chown\s+root)": ThreatLevel.HIGH,
        r"(?i)(setuid|setgid|sticky\s+bit|suid\s+binary)": ThreatLevel.MEDIUM,
        r"(?i)(runas.*administrator|net\s+user.*admin|net\s+localgroup.*admin)": ThreatLevel.HIGH,
    }
    
    # Suspicious file extensions and names
    SUSPICIOUS_FILES = {
        r"(?i)\.(exe|bat|cmd|com|pif|scr|vbs|js|jar|app|deb|pkg|dmg|msi)$": ThreatLevel.HIGH,
        r"(?i)\.(dll|so|dylib|sys|drv)$": ThreatLevel.MEDIUM,
        r"(?i)(autorun|setup|install|update|patch|crack|keygen|serial)": ThreatLevel.MEDIUM,
    }
    
    def __init__(self):
        """Initialize threat detector."""
        self.compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, List[Tuple[re.Pattern, ThreatLevel, ThreatType]]]:
        """Compile regex patterns for efficient matching."""
        compiled = {
            "injection": [],
            "malware": [],
            "phishing": [],
            "social_engineering": [],
            "data_exfiltration": [],
            "privilege_escalation": [],
            "suspicious_files": [],
        }
        
        # Compile injection patterns
        for pattern, level in self.INJECTION_PATTERNS.items():
            compiled["injection"].append((re.compile(pattern), level, ThreatType.INJECTION))
        
        # Compile malware patterns
        for pattern, level in self.MALWARE_INDICATORS.items():
            compiled["malware"].append((re.compile(pattern), level, ThreatType.MALWARE))
        
        # Compile phishing patterns
        for pattern, level in self.PHISHING_PATTERNS.items():
            compiled["phishing"].append((re.compile(pattern), level, ThreatType.PHISHING))
        
        # Compile social engineering patterns
        for pattern, level in self.SOCIAL_ENGINEERING_PATTERNS.items():
            compiled["social_engineering"].append((re.compile(pattern), level, ThreatType.SOCIAL_ENGINEERING))
        
        # Compile data exfiltration patterns
        for pattern, level in self.DATA_EXFILTRATION_PATTERNS.items():
            compiled["data_exfiltration"].append((re.compile(pattern), level, ThreatType.DATA_EXFILTRATION))
        
        # Compile privilege escalation patterns
        for pattern, level in self.PRIVILEGE_ESCALATION_PATTERNS.items():
            compiled["privilege_escalation"].append((re.compile(pattern), level, ThreatType.PRIVILEGE_ESCALATION))
        
        # Compile suspicious file patterns
        for pattern, level in self.SUSPICIOUS_FILES.items():
            compiled["suspicious_files"].append((re.compile(pattern), level, ThreatType.SUSPICIOUS_BEHAVIOR))
        
        return compiled
    
    def detect_threats(self, content: str, filename: str = "") -> List[ThreatDetection]:
        """
        Detect threats in content and filename.
        
        Args:
            content: Text content to analyze
            filename: Filename to analyze
            
        Returns:
            List of detected threats
        """
        threats = []
        
        # Analyze content
        content_threats = self._analyze_content(content)
        threats.extend(content_threats)
        
        # Analyze filename
        if filename:
            filename_threats = self._analyze_filename(filename)
            threats.extend(filename_threats)
        
        # Perform behavioral analysis
        behavioral_threats = self._behavioral_analysis(content, filename)
        threats.extend(behavioral_threats)
        
        # Remove duplicates and sort by threat level
        unique_threats = self._deduplicate_threats(threats)
        return sorted(unique_threats, key=lambda t: self._threat_level_priority(t.threat_level), reverse=True)
    
    def _analyze_content(self, content: str) -> List[ThreatDetection]:
        """Analyze content for threat patterns."""
        threats = []
        
        for category, patterns in self.compiled_patterns.items():
            if category == "suspicious_files":
                continue  # Handle separately
            
            for pattern, level, threat_type in patterns:
                matches = pattern.findall(content)
                if matches:
                    evidence = [str(match) for match in matches[:5]]  # Limit evidence
                    confidence = min(0.9, 0.3 + (len(matches) * 0.1))  # Scale confidence
                    
                    threat = ThreatDetection(
                        threat_type=threat_type,
                        threat_level=level,
                        description=self._get_threat_description(threat_type, level),
                        evidence=evidence,
                        confidence=confidence,
                        mitigation_suggestions=self._get_mitigation_suggestions(threat_type)
                    )
                    threats.append(threat)
        
        return threats
    
    def _analyze_filename(self, filename: str) -> List[ThreatDetection]:
        """Analyze filename for suspicious patterns."""
        threats = []
        
        for pattern, level, threat_type in self.compiled_patterns["suspicious_files"]:
            if pattern.search(filename):
                threat = ThreatDetection(
                    threat_type=threat_type,
                    threat_level=level,
                    description=f"Suspicious filename pattern detected",
                    evidence=[filename],
                    confidence=0.7,
                    mitigation_suggestions=["Verify file source", "Scan with antivirus", "Consider quarantine"]
                )
                threats.append(threat)
        
        return threats
    
    def _behavioral_analysis(self, content: str, filename: str) -> List[ThreatDetection]:
        """Perform behavioral analysis for advanced threat detection."""
        threats = []
        
        # Check for obfuscation
        if self._is_obfuscated(content):
            threats.append(ThreatDetection(
                threat_type=ThreatType.SUSPICIOUS_BEHAVIOR,
                threat_level=ThreatLevel.MEDIUM,
                description="Content appears to be obfuscated",
                evidence=["High entropy", "Unusual character patterns"],
                confidence=0.6,
                mitigation_suggestions=["Manual review required", "Consider sandboxed execution"]
            ))
        
        # Check for excessive network references
        network_refs = self._count_network_references(content)
        if network_refs > 10:
            threats.append(ThreatDetection(
                threat_type=ThreatType.DATA_EXFILTRATION,
                threat_level=ThreatLevel.MEDIUM,
                description=f"Excessive network references detected ({network_refs})",
                evidence=[f"{network_refs} network references found"],
                confidence=0.5,
                mitigation_suggestions=["Review network destinations", "Monitor network traffic"]
            ))
        
        # Check for credential patterns
        if self._has_credential_patterns(content):
            threats.append(ThreatDetection(
                threat_type=ThreatType.PHISHING,
                threat_level=ThreatLevel.HIGH,
                description="Potential credential harvesting patterns detected",
                evidence=["Password/credential input patterns found"],
                confidence=0.8,
                mitigation_suggestions=["Verify legitimacy", "Check for phishing indicators"]
            ))
        
        return threats
    
    def _is_obfuscated(self, content: str) -> bool:
        """Check if content appears to be obfuscated."""
        if len(content) < 100:
            return False
        
        # Calculate character distribution
        char_counts = {}
        for char in content:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        # Check for unusual character distribution
        total_chars = len(content)
        unusual_chars = sum(1 for char, count in char_counts.items() 
                          if not char.isalnum() and char not in ' \n\t.,;:!?')
        
        unusual_ratio = unusual_chars / total_chars
        return unusual_ratio > 0.3  # 30% unusual characters
    
    def _count_network_references(self, content: str) -> int:
        """Count network-related references in content."""
        network_patterns = [
            r"https?://",
            r"ftp://",
            r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",  # IP addresses
            r"\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",  # Domain names
        ]
        
        count = 0
        for pattern in network_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            count += len(matches)
        
        return count
    
    def _has_credential_patterns(self, content: str) -> bool:
        """Check for credential harvesting patterns."""
        credential_patterns = [
            r"(?i)(password|passwd|pwd)\s*[:=]",
            r"(?i)(username|user|login)\s*[:=]",
            r"(?i)(email|e-mail)\s*[:=]",
            r"(?i)(ssn|social\s+security)\s*[:=]",
            r"(?i)(credit\s+card|card\s+number)\s*[:=]",
        ]
        
        for pattern in credential_patterns:
            if re.search(pattern, content):
                return True
        
        return False
    
    def _deduplicate_threats(self, threats: List[ThreatDetection]) -> List[ThreatDetection]:
        """Remove duplicate threats based on type and description."""
        seen = set()
        unique_threats = []
        
        for threat in threats:
            key = (threat.threat_type, threat.description)
            if key not in seen:
                seen.add(key)
                unique_threats.append(threat)
        
        return unique_threats
    
    def _threat_level_priority(self, level: ThreatLevel) -> int:
        """Get numeric priority for threat level."""
        priorities = {
            ThreatLevel.CRITICAL: 4,
            ThreatLevel.HIGH: 3,
            ThreatLevel.MEDIUM: 2,
            ThreatLevel.LOW: 1,
        }
        return priorities.get(level, 0)
    
    def _get_threat_description(self, threat_type: ThreatType, level: ThreatLevel) -> str:
        """Get description for threat type and level."""
        descriptions = {
            ThreatType.INJECTION: f"{level.value.title()} injection attack pattern detected",
            ThreatType.MALWARE: f"{level.value.title()} malware indicators found",
            ThreatType.PHISHING: f"{level.value.title()} phishing patterns detected",
            ThreatType.SOCIAL_ENGINEERING: f"{level.value.title()} social engineering tactics identified",
            ThreatType.DATA_EXFILTRATION: f"{level.value.title()} data exfiltration patterns found",
            ThreatType.PRIVILEGE_ESCALATION: f"{level.value.title()} privilege escalation attempts detected",
            ThreatType.DENIAL_OF_SERVICE: f"{level.value.title()} DoS attack patterns identified",
            ThreatType.SUSPICIOUS_BEHAVIOR: f"{level.value.title()} suspicious behavior detected",
        }
        return descriptions.get(threat_type, f"{level.value.title()} threat detected")
    
    def _get_mitigation_suggestions(self, threat_type: ThreatType) -> List[str]:
        """Get mitigation suggestions for threat type."""
        suggestions = {
            ThreatType.INJECTION: [
                "Implement input validation and sanitization",
                "Use parameterized queries",
                "Apply principle of least privilege",
                "Regular security testing"
            ],
            ThreatType.MALWARE: [
                "Quarantine the file immediately",
                "Run full system scan",
                "Update antivirus definitions",
                "Monitor system behavior"
            ],
            ThreatType.PHISHING: [
                "Verify sender authenticity",
                "Check URLs before clicking",
                "Report to security team",
                "User awareness training"
            ],
            ThreatType.SOCIAL_ENGINEERING: [
                "Verify requests through alternative channels",
                "Follow established procedures",
                "Report suspicious communications",
                "Security awareness training"
            ],
            ThreatType.DATA_EXFILTRATION: [
                "Monitor network traffic",
                "Implement data loss prevention",
                "Review access controls",
                "Audit data access logs"
            ],
            ThreatType.PRIVILEGE_ESCALATION: [
                "Review user permissions",
                "Implement least privilege principle",
                "Monitor privileged account usage",
                "Regular access reviews"
            ],
            ThreatType.SUSPICIOUS_BEHAVIOR: [
                "Manual security review",
                "Behavioral analysis",
                "Sandboxed execution",
                "Enhanced monitoring"
            ]
        }
        return suggestions.get(threat_type, ["Manual security review required"])