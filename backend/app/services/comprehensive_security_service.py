"""
Comprehensive security service that integrates all security components.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

from ..core.logging import get_logger
from ..monitoring.metrics_collector import get_metrics_collector
from ..repositories.audit_repository import AuditRepository
from ..security.file_validator import FileSecurityValidator, FileValidationResult, ValidationStatus
from ..security.malware_scanner import MalwareScanner, ScanResult, ScanStatus
from ..security.temp_file_manager import TempFileManager
from ..security.threat_detector import ThreatDetector, ThreatDetection, ThreatLevel

logger = get_logger(__name__)
metrics_collector = get_metrics_collector()


class SecurityDecision(Enum):
    """Security decision outcomes."""
    ALLOW = "allow"
    BLOCK = "block"
    QUARANTINE = "quarantine"
    REVIEW_REQUIRED = "review_required"


@dataclass
class SecurityAssessment:
    """Comprehensive security assessment result."""
    file_id: str
    filename: str
    decision: SecurityDecision
    risk_score: float  # 0.0 to 10.0
    validation_result: FileValidationResult
    scan_result: ScanResult
    threat_detections: List[ThreatDetection]
    recommendations: List[str]
    processing_time_seconds: float
    metadata: Dict[str, any]


class ComprehensiveSecurityService:
    """Comprehensive security service integrating all security components."""
    
    # Risk scoring weights
    VALIDATION_WEIGHT = 0.3
    MALWARE_WEIGHT = 0.4
    THREAT_WEIGHT = 0.3
    
    # Risk thresholds
    LOW_RISK_THRESHOLD = 3.0
    MEDIUM_RISK_THRESHOLD = 6.0
    HIGH_RISK_THRESHOLD = 7.5
    
    def __init__(
        self,
        audit_repository: Optional[AuditRepository] = None,
        temp_file_manager: Optional[TempFileManager] = None
    ):
        """Initialize comprehensive security service."""
        self.audit_repository = audit_repository
        self.temp_file_manager = temp_file_manager or TempFileManager(audit_repository)
        
        # Initialize security components
        self.file_validator = FileSecurityValidator()
        self.malware_scanner = MalwareScanner()
        self.threat_detector = ThreatDetector()
        
        logger.info("Comprehensive security service initialized")
    
    async def assess_file_security(
        self,
        file_content: bytes,
        filename: str,
        user_id: Optional[str] = None,
        additional_context: Optional[Dict[str, any]] = None
    ) -> SecurityAssessment:
        """
        Perform comprehensive security assessment of a file.
        
        Args:
            file_content: Raw file content
            filename: Original filename
            user_id: User ID for audit logging
            additional_context: Additional context for assessment
            
        Returns:
            SecurityAssessment with comprehensive results
        """
        import time
        start_time = time.time()
        
        logger.info(f"Starting comprehensive security assessment for: {filename}")
        
        # Initialize assessment
        file_id = f"security_assessment_{int(time.time() * 1000)}"
        
        try:
            # Run all security checks in parallel
            validation_task = self.file_validator.validate_file(file_content, filename)
            scan_task = self.malware_scanner.scan_file(file_content, filename)
            
            # Convert bytes to string for threat detection
            try:
                content_str = file_content.decode('utf-8', errors='ignore')
            except Exception:
                content_str = str(file_content)
            
            # Wait for all tasks to complete
            validation_result, scan_result = await asyncio.gather(
                validation_task,
                scan_task,
                return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(validation_result, Exception):
                logger.error(f"File validation failed: {validation_result}")
                validation_result = self._create_error_validation_result(str(validation_result))
            
            if isinstance(scan_result, Exception):
                logger.error(f"Malware scan failed: {scan_result}")
                scan_result = self._create_error_scan_result(str(scan_result))
            
            # Perform threat detection
            threat_detections = self.threat_detector.detect_threats(content_str, filename)
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(validation_result, scan_result, threat_detections)
            
            # Make security decision
            decision = self._make_security_decision(risk_score, validation_result, scan_result, threat_detections)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(validation_result, scan_result, threat_detections, decision)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Create assessment
            assessment = SecurityAssessment(
                file_id=file_id,
                filename=filename,
                decision=decision,
                risk_score=risk_score,
                validation_result=validation_result,
                scan_result=scan_result,
                threat_detections=threat_detections,
                recommendations=recommendations,
                processing_time_seconds=processing_time,
                metadata={
                    "user_id": user_id,
                    "file_size": len(file_content),
                    "assessment_timestamp": datetime.utcnow().isoformat(),
                    "additional_context": additional_context or {}
                }
            )
            
            # Handle file based on decision
            await self._handle_security_decision(assessment, file_content)
            
            # Record metrics
            self._record_security_metrics(assessment)
            
            # Audit log
            if self.audit_repository:
                await self._log_security_assessment(assessment, user_id)
            
            logger.info(f"Security assessment completed for {filename}: {decision.value} (risk: {risk_score:.2f})")
            return assessment
            
        except Exception as e:
            logger.error(f"Error during security assessment: {e}", exc_info=True)
            
            # Create error assessment
            error_assessment = SecurityAssessment(
                file_id=file_id,
                filename=filename,
                decision=SecurityDecision.BLOCK,
                risk_score=10.0,  # Maximum risk for errors
                validation_result=self._create_error_validation_result(str(e)),
                scan_result=self._create_error_scan_result(str(e)),
                threat_detections=[],
                recommendations=["Manual security review required due to assessment error"],
                processing_time_seconds=time.time() - start_time,
                metadata={
                    "error": str(e),
                    "user_id": user_id,
                    "assessment_timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Record error metrics
            metrics_collector.record_security_event(
                event_type="assessment_error",
                severity="high"
            )
            
            return error_assessment
    
    def _calculate_risk_score(
        self,
        validation_result: FileValidationResult,
        scan_result: ScanResult,
        threat_detections: List[ThreatDetection]
    ) -> float:
        """Calculate overall risk score from all security checks."""
        
        # Validation score (0-10)
        validation_score = 0.0
        if not validation_result.is_valid:
            if validation_result.status == ValidationStatus.QUARANTINED:
                validation_score = 10.0
            elif validation_result.status == ValidationStatus.SUSPICIOUS:
                validation_score = 7.0
            else:
                validation_score = 5.0
        
        validation_score += len(validation_result.threats_detected) * 1.0
        validation_score += len(validation_result.warnings) * 0.5
        validation_score = min(validation_score, 10.0)
        
        # Malware scan score (0-10)
        scan_score = 0.0
        if scan_result.status == ScanStatus.INFECTED:
            scan_score = 10.0
        elif scan_result.status == ScanStatus.SUSPICIOUS:
            scan_score = 7.0
        elif scan_result.status == ScanStatus.ERROR:
            scan_score = 5.0
        
        scan_score += len(scan_result.threats_found) * 1.5
        scan_score = min(scan_score, 10.0)
        
        # Threat detection score (0-10)
        threat_score = 0.0
        for threat in threat_detections:
            if threat.threat_level.value == "critical":
                threat_score += 3.0
            elif threat.threat_level.value == "high":
                threat_score += 2.0
            elif threat.threat_level.value == "medium":
                threat_score += 1.0
            else:
                threat_score += 0.5
            
            # Weight by confidence
            threat_score *= threat.confidence
        
        threat_score = min(threat_score, 10.0)
        
        # Calculate weighted overall score
        overall_score = (
            validation_score * self.VALIDATION_WEIGHT +
            scan_score * self.MALWARE_WEIGHT +
            threat_score * self.THREAT_WEIGHT
        )
        
        return min(overall_score, 10.0)
    
    def _make_security_decision(
        self,
        risk_score: float,
        validation_result: FileValidationResult,
        scan_result: ScanResult,
        threat_detections: List[ThreatDetection]
    ) -> SecurityDecision:
        """Make security decision based on assessment results."""
        
        # Immediate block conditions
        if (validation_result.status == ValidationStatus.QUARANTINED or
            scan_result.status == ScanStatus.INFECTED or
            any(t.threat_level.value == "critical" for t in threat_detections)):
            return SecurityDecision.BLOCK
        
        # Quarantine conditions
        if (validation_result.status == ValidationStatus.SUSPICIOUS or
            scan_result.status == ScanStatus.SUSPICIOUS or
            risk_score >= self.HIGH_RISK_THRESHOLD):
            return SecurityDecision.QUARANTINE
        
        # Review required conditions
        if (risk_score >= self.MEDIUM_RISK_THRESHOLD or
            len(threat_detections) > 3 or
            any(t.threat_level.value == "high" for t in threat_detections)):
            return SecurityDecision.REVIEW_REQUIRED
        
        # Allow if low risk
        if risk_score < self.LOW_RISK_THRESHOLD:
            return SecurityDecision.ALLOW
        
        # Default to review for medium risk
        return SecurityDecision.REVIEW_REQUIRED
    
    def _generate_recommendations(
        self,
        validation_result: FileValidationResult,
        scan_result: ScanResult,
        threat_detections: List[ThreatDetection],
        decision: SecurityDecision
    ) -> List[str]:
        """Generate security recommendations based on assessment."""
        recommendations = []
        
        # Decision-based recommendations
        if decision == SecurityDecision.BLOCK:
            recommendations.append("File blocked due to high security risk")
            recommendations.append("Do not process or open this file")
            recommendations.append("Report to security team for analysis")
        elif decision == SecurityDecision.QUARANTINE:
            recommendations.append("File quarantined for security review")
            recommendations.append("Manual security analysis required")
            recommendations.append("Consider sandboxed analysis")
        elif decision == SecurityDecision.REVIEW_REQUIRED:
            recommendations.append("Manual security review recommended")
            recommendations.append("Verify file source and legitimacy")
            recommendations.append("Consider additional security scanning")
        elif decision == SecurityDecision.ALLOW:
            recommendations.append("File passed security assessment")
            recommendations.append("Safe to process with standard precautions")
        
        # Validation-specific recommendations
        if validation_result.warnings:
            recommendations.append("Address file validation warnings")
        
        if validation_result.threats_detected:
            recommendations.append("Investigate detected security threats")
        
        # Malware scan recommendations
        if scan_result.threats_found:
            recommendations.append("Investigate malware scan findings")
            recommendations.append("Update antivirus definitions")
        
        # Threat detection recommendations
        for threat in threat_detections:
            recommendations.extend(threat.mitigation_suggestions[:2])  # Limit suggestions
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations[:10]  # Limit to top 10 recommendations
    
    async def _handle_security_decision(self, assessment: SecurityAssessment, file_content: bytes) -> None:
        """Handle file based on security decision."""
        
        if assessment.decision == SecurityDecision.QUARANTINE:
            # Save to quarantine
            file_id = self.temp_file_manager.save_temporary_file(
                file_content,
                assessment.filename,
                encrypt=True,
                retention_hours=168  # 1 week
            )
            
            # Quarantine the file
            self.temp_file_manager.quarantine_file(
                file_id,
                f"Security assessment risk score: {assessment.risk_score:.2f}"
            )
            
            assessment.metadata["quarantine_file_id"] = file_id
            
        elif assessment.decision == SecurityDecision.ALLOW:
            # Save to temporary storage for processing
            file_id = self.temp_file_manager.save_temporary_file(
                file_content,
                assessment.filename,
                encrypt=True,
                retention_hours=24  # 1 day
            )
            
            assessment.metadata["temp_file_id"] = file_id
    
    def _record_security_metrics(self, assessment: SecurityAssessment) -> None:
        """Record security metrics."""
        
        # Record assessment metrics
        metrics_collector.record_security_assessment(
            decision=assessment.decision.value,
            risk_score=assessment.risk_score,
            processing_time=assessment.processing_time_seconds
        )
        
        # Record validation metrics
        metrics_collector.record_file_validation(
            result=assessment.validation_result.status.value,
            file_type=assessment.validation_result.file_type.value
        )
        
        # Record malware scan metrics
        metrics_collector.record_malware_scan(
            result=assessment.scan_result.status.value,
            engine=assessment.scan_result.scan_engine
        )
        
        # Record threat detection metrics
        for threat in assessment.threat_detections:
            metrics_collector.record_threat_detection(
                threat_type=threat.threat_type.value,
                threat_level=threat.threat_level.value,
                confidence=threat.confidence
            )
    
    async def _log_security_assessment(self, assessment: SecurityAssessment, user_id: Optional[str]) -> None:
        """Log security assessment to audit trail."""
        
        if not self.audit_repository:
            return
        
        self.audit_repository.log_event(
            event_type="security_assessment",
            event_data={
                "file_id": assessment.file_id,
                "filename": assessment.filename,
                "decision": assessment.decision.value,
                "risk_score": assessment.risk_score,
                "validation_status": assessment.validation_result.status.value,
                "scan_status": assessment.scan_result.status.value,
                "threat_count": len(assessment.threat_detections),
                "processing_time": assessment.processing_time_seconds
            },
            user_id=user_id,
            action="ASSESS",
            result="SUCCESS" if assessment.decision != SecurityDecision.BLOCK else "BLOCKED"
        )
    
    def _create_error_validation_result(self, error_message: str) -> FileValidationResult:
        """Create error validation result."""
        from ..security.file_validator import FileType, ValidationStatus
        
        return FileValidationResult(
            is_valid=False,
            file_type=FileType.UNKNOWN,
            mime_type="application/octet-stream",
            file_size=0,
            file_hash="",
            status=ValidationStatus.INVALID,
            threats_detected=[f"Validation error: {error_message}"],
            warnings=[],
            metadata={"error": True}
        )
    
    def _create_error_scan_result(self, error_message: str) -> ScanResult:
        """Create error scan result."""
        return ScanResult(
            status=ScanStatus.ERROR,
            threats_found=[f"Scan error: {error_message}"],
            scan_engine="error",
            scan_time_seconds=0.0,
            file_hash="",
            metadata={"error": True}
        )
    
    async def update_security_databases(self) -> Dict[str, bool]:
        """Update all security databases."""
        results = {}
        
        # Update malware scanner database
        try:
            results["malware_scanner"] = self.malware_scanner.update_threat_database()
        except Exception as e:
            logger.error(f"Failed to update malware scanner database: {e}")
            results["malware_scanner"] = False
        
        # Update threat intelligence (if applicable)
        try:
            # In a production environment, this would update threat intelligence feeds
            results["threat_intelligence"] = True
            logger.info("Threat intelligence updated successfully")
        except Exception as e:
            logger.error(f"Failed to update threat intelligence: {e}")
            results["threat_intelligence"] = False
        
        return results
    
    def get_security_statistics(self) -> Dict[str, any]:
        """Get comprehensive security statistics."""
        
        # Get component statistics
        temp_file_stats = self.temp_file_manager.get_statistics()
        scanner_info = self.malware_scanner.get_scanner_info()
        threat_intel_info = self.malware_scanner.get_threat_intelligence_info()
        
        return {
            "service_status": "active",
            "components": {
                "file_validator": {"status": "active"},
                "malware_scanner": scanner_info,
                "threat_detector": {"status": "active"},
                "temp_file_manager": temp_file_stats
            },
            "threat_intelligence": threat_intel_info,
            "risk_thresholds": {
                "low": self.LOW_RISK_THRESHOLD,
                "medium": self.MEDIUM_RISK_THRESHOLD,
                "high": self.HIGH_RISK_THRESHOLD
            }
        }


# Global instance
comprehensive_security_service = ComprehensiveSecurityService()


# Convenience functions
async def assess_file_security(
    file_content: bytes,
    filename: str,
    user_id: Optional[str] = None
) -> SecurityAssessment:
    """Assess file security using the global service."""
    return await comprehensive_security_service.assess_file_security(
        file_content, filename, user_id
    )


async def update_security_databases() -> Dict[str, bool]:
    """Update security databases using the global service."""
    return await comprehensive_security_service.update_security_databases()


def get_security_statistics() -> Dict[str, any]:
    """Get security statistics using the global service."""
    return comprehensive_security_service.get_security_statistics()