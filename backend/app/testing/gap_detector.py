"""
Gap Detection System

Compares frontend API calls with backend endpoints to identify integration gaps.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from .endpoint_discovery import EndpointInfo
from .frontend_scanner import ApiCall, FeatureRequirement


class GapType(str, Enum):
    """Type of integration gap"""

    MISSING_ENDPOINT = "missing_endpoint"
    INCOMPLETE_IMPLEMENTATION = "incomplete_implementation"
    PARAMETER_MISMATCH = "parameter_mismatch"
    RESPONSE_FORMAT_ISSUE = "response_format_issue"
    METHOD_MISMATCH = "method_mismatch"


class GapSeverity(str, Enum):
    """Severity level of a gap"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Gap:
    """Represents an integration gap between frontend and backend"""

    gap_type: GapType
    severity: GapSeverity
    frontend_component: str
    expected_endpoint: str
    expected_method: str
    expected_parameters: Dict[str, Any] = field(default_factory=dict)
    backend_status: str = "not_found"  # not_found, partial, mismatch
    backend_endpoint: Optional[str] = None
    backend_method: Optional[str] = None
    description: str = ""
    recommendation: str = ""
    affected_features: List[str] = field(default_factory=list)
    line_number: Optional[int] = None
    file_path: Optional[str] = None

    def __repr__(self) -> str:
        return f"<Gap {self.gap_type.value} [{self.severity.value}] {self.expected_method} {self.expected_endpoint}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "gap_type": self.gap_type.value,
            "severity": self.severity.value,
            "frontend_component": self.frontend_component,
            "expected_endpoint": self.expected_endpoint,
            "expected_method": self.expected_method,
            "expected_parameters": self.expected_parameters,
            "backend_status": self.backend_status,
            "backend_endpoint": self.backend_endpoint,
            "backend_method": self.backend_method,
            "description": self.description,
            "recommendation": self.recommendation,
            "affected_features": self.affected_features,
            "line_number": self.line_number,
            "file_path": self.file_path,
        }


class GapDetector:
    """
    Detects integration gaps between frontend and backend.

    Compares frontend API calls with backend endpoints to identify:
    - Missing endpoints
    - Parameter mismatches
    - Method mismatches
    - Incomplete implementations
    """

    def __init__(self):
        """Initialize the gap detector"""
        self.gaps: List[Gap] = []
        self.frontend_calls: List[ApiCall] = []
        self.backend_endpoints: List[EndpointInfo] = []
        self.feature_requirements: List[FeatureRequirement] = []

    def compare_frontend_backend(
        self,
        frontend_calls: List[ApiCall],
        backend_endpoints: List[EndpointInfo],
        feature_requirements: Optional[List[FeatureRequirement]] = None,
    ) -> List[Gap]:
        """
        Compare frontend API calls with backend endpoints.

        Args:
            frontend_calls: List of API calls from frontend
            backend_endpoints: List of backend endpoints
            feature_requirements: Optional list of feature requirements

        Returns:
            List of Gap objects
        """
        self.frontend_calls = frontend_calls
        self.backend_endpoints = backend_endpoints
        self.feature_requirements = feature_requirements or []
        self.gaps = []

        # Create a map of backend endpoints for quick lookup
        backend_map = self._create_backend_map(backend_endpoints)

        # Check each frontend call
        for call in frontend_calls:
            self._check_api_call(call, backend_map)

        return self.gaps

    def _create_backend_map(self, endpoints: List[EndpointInfo]) -> Dict[str, EndpointInfo]:
        """
        Create a map of backend endpoints for quick lookup.

        Args:
            endpoints: List of backend endpoints

        Returns:
            Dictionary mapping "METHOD /path" to EndpointInfo
        """
        backend_map = {}
        for endpoint in endpoints:
            key = f"{endpoint.method} {endpoint.path}"
            backend_map[key] = endpoint

            # Also add normalized version (without path parameters)
            normalized_path = self._normalize_path(endpoint.path)
            normalized_key = f"{endpoint.method} {normalized_path}"
            if normalized_key != key:
                backend_map[normalized_key] = endpoint

        return backend_map

    def _normalize_path(self, path: str) -> str:
        """
        Normalize a path by replacing path parameters with {id}.

        Args:
            path: Original path

        Returns:
            Normalized path
        """
        # Replace {param_name} with {id}
        normalized = re.sub(r"\{[^}]+\}", "{id}", path)
        return normalized

    def _check_api_call(self, call: ApiCall, backend_map: Dict[str, EndpointInfo]) -> None:
        """
        Check a single API call against backend endpoints.

        Args:
            call: Frontend API call
            backend_map: Map of backend endpoints
        """
        # Normalize the endpoint
        normalized_endpoint = self._normalize_path(call.endpoint)
        key = f"{call.method} {normalized_endpoint}"

        # Check if endpoint exists
        if key in backend_map:
            backend_endpoint = backend_map[key]
            # Endpoint exists, check for parameter mismatches
            self._check_parameter_match(call, backend_endpoint)
        else:
            # Try to find similar endpoints
            similar = self._find_similar_endpoint(call, backend_map)

            if similar:
                # Found similar endpoint with different method
                self._create_method_mismatch_gap(call, similar)
            else:
                # Endpoint is completely missing
                self._create_missing_endpoint_gap(call)

    def _check_parameter_match(self, call: ApiCall, backend_endpoint: EndpointInfo) -> None:
        """
        Check if parameters match between frontend call and backend endpoint.

        Args:
            call: Frontend API call
            backend_endpoint: Backend endpoint info
        """
        # For now, we'll skip detailed parameter checking
        # This would require more sophisticated analysis of the frontend code
        # to extract actual parameters being passed

        # Check if endpoint has required parameters that might not be provided
        required_params = backend_endpoint.get_required_parameters()

        if len(required_params) > 0:
            # Create a warning gap for potential parameter issues
            gap = Gap(
                gap_type=GapType.PARAMETER_MISMATCH,
                severity=GapSeverity.LOW,
                frontend_component=call.component,
                expected_endpoint=call.endpoint,
                expected_method=call.method,
                backend_status="partial",
                backend_endpoint=backend_endpoint.path,
                backend_method=backend_endpoint.method,
                description=f"Endpoint exists but requires {len(required_params)} parameters. Verify frontend provides all required parameters.",
                recommendation=f"Review the API call in {call.component} to ensure all required parameters are provided: {', '.join(p.name for p in required_params)}",
                affected_features=self._get_affected_features(call),
                line_number=call.line_number,
                file_path=call.file_path,
            )
            # Only add if it's a significant concern
            # self.gaps.append(gap)

    def _find_similar_endpoint(self, call: ApiCall, backend_map: Dict[str, EndpointInfo]) -> Optional[EndpointInfo]:
        """
        Find similar endpoints with different methods.

        Args:
            call: Frontend API call
            backend_map: Map of backend endpoints

        Returns:
            Similar endpoint or None
        """
        normalized_endpoint = self._normalize_path(call.endpoint)

        # Check all HTTP methods for the same path
        for method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
            if method != call.method:
                key = f"{method} {normalized_endpoint}"
                if key in backend_map:
                    return backend_map[key]

        return None

    def _create_missing_endpoint_gap(self, call: ApiCall) -> None:
        """
        Create a gap for a missing endpoint.

        Args:
            call: Frontend API call
        """
        severity = self._determine_severity(call)

        gap = Gap(
            gap_type=GapType.MISSING_ENDPOINT,
            severity=severity,
            frontend_component=call.component,
            expected_endpoint=call.endpoint,
            expected_method=call.method,
            backend_status="not_found",
            description=f"Frontend expects {call.method} {call.endpoint} but endpoint does not exist in backend",
            recommendation=self._generate_recommendation(call),
            affected_features=self._get_affected_features(call),
            line_number=call.line_number,
            file_path=call.file_path,
        )
        self.gaps.append(gap)

    def _create_method_mismatch_gap(self, call: ApiCall, backend_endpoint: EndpointInfo) -> None:
        """
        Create a gap for a method mismatch.

        Args:
            call: Frontend API call
            backend_endpoint: Backend endpoint with different method
        """
        gap = Gap(
            gap_type=GapType.METHOD_MISMATCH,
            severity=GapSeverity.HIGH,
            frontend_component=call.component,
            expected_endpoint=call.endpoint,
            expected_method=call.method,
            backend_status="mismatch",
            backend_endpoint=backend_endpoint.path,
            backend_method=backend_endpoint.method,
            description=f"Frontend expects {call.method} but backend provides {backend_endpoint.method}",
            recommendation=f"Either update frontend to use {backend_endpoint.method} or add {call.method} support to backend",
            affected_features=self._get_affected_features(call),
            line_number=call.line_number,
            file_path=call.file_path,
        )
        self.gaps.append(gap)

    def _determine_severity(self, call: ApiCall) -> GapSeverity:
        """
        Determine the severity of a missing endpoint.

        Args:
            call: Frontend API call

        Returns:
            Severity level
        """
        # Check if it's part of a critical feature
        affected_features = self._get_affected_features(call)

        for feature in self.feature_requirements:
            if feature.feature_name in affected_features:
                if feature.priority == "critical":
                    return GapSeverity.CRITICAL
                elif feature.priority == "high":
                    return GapSeverity.HIGH
                elif feature.priority == "medium":
                    return GapSeverity.MEDIUM

        # Determine by endpoint type
        if any(keyword in call.endpoint.lower() for keyword in ["auth", "login", "register"]):
            return GapSeverity.CRITICAL

        if any(keyword in call.endpoint.lower() for keyword in ["job", "application", "dashboard"]):
            return GapSeverity.HIGH

        if any(keyword in call.endpoint.lower() for keyword in ["notification", "profile", "analytics"]):
            return GapSeverity.MEDIUM

        return GapSeverity.LOW

    def _get_affected_features(self, call: ApiCall) -> List[str]:
        """
        Get list of features affected by this API call.

        Args:
            call: Frontend API call

        Returns:
            List of feature names
        """
        affected = []

        for feature in self.feature_requirements:
            endpoint_key = f"{call.method} {call.endpoint}"
            if endpoint_key in feature.required_endpoints:
                affected.append(feature.feature_name)

        return affected

    def _generate_recommendation(self, call: ApiCall) -> str:
        """
        Generate a recommendation for implementing a missing endpoint.

        Args:
            call: Frontend API call

        Returns:
            Recommendation string
        """
        method = call.method
        endpoint = call.endpoint

        # Extract resource from endpoint
        parts = endpoint.split("/")
        resource = parts[-1] if parts else "resource"

        if "{id}" in resource or "{" in resource:
            resource = parts[-2] if len(parts) > 1 else "resource"

        recommendations = {
            "GET": f"Implement GET endpoint to retrieve {resource} data. Add route handler in appropriate router file.",
            "POST": f"Implement POST endpoint to create new {resource}. Include request validation and database insertion.",
            "PUT": f"Implement PUT endpoint to update existing {resource}. Include ID validation and update logic.",
            "DELETE": f"Implement DELETE endpoint to remove {resource}. Include ID validation and deletion logic.",
            "PATCH": f"Implement PATCH endpoint to partially update {resource}. Include field validation.",
        }

        base_recommendation = recommendations.get(method, f"Implement {method} endpoint for {endpoint}")

        # Add specific details based on endpoint
        if "search" in endpoint.lower():
            base_recommendation += " Include query parameters for filtering and pagination."
        elif "bulk" in endpoint.lower():
            base_recommendation += " Support batch operations with transaction handling."
        elif "export" in endpoint.lower():
            base_recommendation += " Support multiple export formats (JSON, CSV, PDF)."
        elif "import" in endpoint.lower():
            base_recommendation += " Include file upload handling and data validation."

        return base_recommendation

    def categorize_gaps(self) -> Dict[str, List[Gap]]:
        """
        Categorize gaps by type.

        Returns:
            Dictionary mapping gap types to lists of gaps
        """
        categorized: Dict[str, List[Gap]] = {}

        for gap in self.gaps:
            gap_type = gap.gap_type.value
            if gap_type not in categorized:
                categorized[gap_type] = []
            categorized[gap_type].append(gap)

        return categorized

    def prioritize_gaps(self) -> List[Gap]:
        """
        Sort gaps by priority (severity).

        Returns:
            List of gaps sorted by severity
        """
        severity_order = {
            GapSeverity.CRITICAL: 0,
            GapSeverity.HIGH: 1,
            GapSeverity.MEDIUM: 2,
            GapSeverity.LOW: 3,
        }

        return sorted(self.gaps, key=lambda g: severity_order[g.severity])

    def get_gaps_by_severity(self, severity: GapSeverity) -> List[Gap]:
        """
        Get all gaps of a specific severity.

        Args:
            severity: Severity level to filter by

        Returns:
            List of gaps with the specified severity
        """
        return [gap for gap in self.gaps if gap.severity == severity]

    def get_gaps_by_feature(self, feature_name: str) -> List[Gap]:
        """
        Get all gaps affecting a specific feature.

        Args:
            feature_name: Name of the feature

        Returns:
            List of gaps affecting the feature
        """
        return [gap for gap in self.gaps if feature_name in gap.affected_features]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about detected gaps.

        Returns:
            Dictionary with statistics
        """
        categorized = self.categorize_gaps()

        severity_counts = {
            "critical": len(self.get_gaps_by_severity(GapSeverity.CRITICAL)),
            "high": len(self.get_gaps_by_severity(GapSeverity.HIGH)),
            "medium": len(self.get_gaps_by_severity(GapSeverity.MEDIUM)),
            "low": len(self.get_gaps_by_severity(GapSeverity.LOW)),
        }

        return {
            "total_gaps": len(self.gaps),
            "gaps_by_type": {gap_type: len(gaps) for gap_type, gaps in categorized.items()},
            "gaps_by_severity": severity_counts,
            "unique_endpoints_missing": len(set(gap.expected_endpoint for gap in self.gaps if gap.gap_type == GapType.MISSING_ENDPOINT)),
            "unique_components_affected": len(set(gap.frontend_component for gap in self.gaps)),
        }

    def export_to_dict(self) -> Dict[str, Any]:
        """
        Export all gap information to a dictionary.

        Returns:
            Dictionary with all gap data
        """
        return {
            "gaps": [gap.to_dict() for gap in self.gaps],
            "statistics": self.get_statistics(),
            "categorized": {gap_type: [gap.to_dict() for gap in gaps] for gap_type, gaps in self.categorize_gaps().items()},
            "prioritized": [gap.to_dict() for gap in self.prioritize_gaps()],
        }
