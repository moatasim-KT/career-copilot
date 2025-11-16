"""Frontend code scanner for enumerating API usage patterns."""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Set, Tuple

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ApiCall:
	"""Information about an API call found in frontend code"""

	component: str
	file_path: str
	line_number: int
	endpoint: str
	method: str
	parameters: Dict[str, Any] = field(default_factory=dict)
	context: Optional[str] = None
	call_type: str = "direct"  # direct, hook, service

	def __repr__(self) -> str:
		return f"<ApiCall {self.method} {self.endpoint} in {self.component}:{self.line_number}>"

	def to_dict(self) -> Dict[str, Any]:
		"""Convert to dictionary for JSON serialization"""
		return {
			"component": self.component,
			"file_path": self.file_path,
			"line_number": self.line_number,
			"endpoint": self.endpoint,
			"method": self.method,
			"parameters": self.parameters,
			"context": self.context,
			"call_type": self.call_type,
		}


@dataclass
class FeatureRequirement:
	"""A feature requirement identified from frontend code"""

	feature_name: str
	required_endpoints: List[str] = field(default_factory=list)
	priority: str = "medium"  # critical, high, medium, low
	components: List[str] = field(default_factory=list)
	description: Optional[str] = None

	def to_dict(self) -> Dict[str, Any]:
		"""Convert to dictionary for JSON serialization"""
		return {
			"feature_name": self.feature_name,
			"required_endpoints": self.required_endpoints,
			"priority": self.priority,
			"components": self.components,
			"description": self.description,
		}


class FrontendScanner:
	"""
	Scans frontend source code to identify API calls and required endpoints.

	This scanner analyzes TypeScript/JavaScript files to find:
	- Direct API client calls
	- Hook usage (useQuery, useMutation, etc.)
	- Service/API client method calls
	- WebSocket connections
	- Fetch/axios calls
	"""

	def __init__(self, frontend_directory: str):
		"""
		Initialize the frontend scanner.

		Args:
		    frontend_directory: Path to the frontend source directory
		"""
		self.frontend_directory = Path(frontend_directory)
		self.api_calls: List[ApiCall] = []
		self.feature_requirements: List[FeatureRequirement] = []

		# Patterns for identifying API calls
		self.api_patterns: Dict[str, Pattern[str]] = {
			# apiClient.method() calls
			"api_client": re.compile(r"apiClient\.(\w+)\((.*?)\)", re.DOTALL),
			# fetch() calls
			"fetch": re.compile(r"fetch\(['\"]([^'\"]+)['\"](?:,\s*\{([^}]+)\})?", re.DOTALL),
			# axios calls
			"axios": re.compile(r"axios\.(\w+)\(['\"]([^'\"]+)['\"]", re.DOTALL),
			# API endpoint strings
			"endpoint_string": re.compile(r"['\"]/(api/v\d+/[^'\"]+)['\"]"),
			# useQuery/useMutation hooks
			"use_query": re.compile(r"use(?:Query|Mutation)\(\{[^}]*queryFn[^}]*\}", re.DOTALL),
		}

	def scan_directory(self, directory: Optional[Path] = None) -> List[ApiCall]:
		"""Recursively scan the provided directory for API usage.

		Args:
		    directory: Optional override for the directory to scan. Defaults to
		        the configured frontend sources.

		Returns:
		    Ordered list of discovered API calls.
		"""
		if directory is None:
			directory = self.frontend_directory

		self.api_calls = []

		# Scan TypeScript and JavaScript files
		for ext in ["*.ts", "*.tsx", "*.js", "*.jsx"]:
			for file_path in directory.rglob(ext):
				# Skip node_modules, build directories, and test files
				if any(part in file_path.parts for part in ["node_modules", ".next", "dist", "build", "__tests__", "test", "tests"]):
					continue

				self._scan_file(file_path)

		return self.api_calls

	def _scan_file(self, file_path: Path) -> None:
		"""Scan a single source file for API calls.

		Args:
		    file_path: Fully-qualified path to the file under inspection.
		"""
		try:
			with open(file_path, "r", encoding="utf-8") as f:
				content = f.read()

			# Extract component name from file path
			component = self._extract_component_name(file_path)

			# Scan for different types of API calls
			self._scan_api_client_calls(content, file_path, component)
			self._scan_fetch_calls(content, file_path, component)
			self._scan_axios_calls(content, file_path, component)
			self._scan_endpoint_strings(content, file_path, component)
			self._scan_hooks(content, file_path, component)

		except Exception as exc:  # pragma: no cover - defensive logging
			logger.exception("Error scanning %s: %s", file_path, exc)

	def _extract_component_name(self, file_path: Path) -> str:
		"""
		Extract a readable component name from file path.

		Args:
		    file_path: Path to the file

		Returns:
		    Component name
		"""
		# Get relative path from frontend directory
		try:
			rel_path = file_path.relative_to(self.frontend_directory)
			# Remove extension and convert to readable name
			name = str(rel_path).replace("/", ".").replace("\\", ".")
			name = name.rsplit(".", 1)[0]  # Remove extension
			return name
		except ValueError:
			return file_path.stem

	def _scan_api_client_calls(self, content: str, file_path: Path, component: str) -> None:
		"""
		Scan for apiClient method calls.

		Args:
		    content: File content
		    file_path: Path to the file
		    component: Component name
		"""
		lines = content.split("\n")

		for line_num, line in enumerate(lines, 1):
			# Look for apiClient.method() patterns
			matches = self.api_patterns["api_client"].finditer(line)

			for match in matches:
				method_name = match.group(1)
				args = match.group(2)

				# Try to determine HTTP method and endpoint
				endpoint, http_method = self._infer_endpoint_from_method(method_name, args)

				if endpoint:
					api_call = ApiCall(
						component=component,
						file_path=str(file_path.relative_to(self.frontend_directory)),
						line_number=line_num,
						endpoint=endpoint,
						method=http_method,
						context=line.strip(),
						call_type="direct",
					)
					self.api_calls.append(api_call)

	def _scan_fetch_calls(self, content: str, file_path: Path, component: str) -> None:
		"""
		Scan for fetch() calls.

		Args:
		    content: File content
		    file_path: Path to the file
		    component: Component name
		"""
		lines = content.split("\n")

		for line_num, line in enumerate(lines, 1):
			matches = self.api_patterns["fetch"].finditer(line)

			for match in matches:
				url = match.group(1)
				options = match.group(2) if match.lastindex >= 2 else ""

				# Extract HTTP method from options
				method = "GET"
				if options:
					method_match = re.search(r"method:\s*['\"](\w+)['\"]", options)
					if method_match:
						method = method_match.group(1).upper()

				# Clean up URL
				endpoint = self._clean_endpoint(url)

				if endpoint:
					api_call = ApiCall(
						component=component,
						file_path=str(file_path.relative_to(self.frontend_directory)),
						line_number=line_num,
						endpoint=endpoint,
						method=method,
						context=line.strip(),
						call_type="direct",
					)
					self.api_calls.append(api_call)

	def _scan_axios_calls(self, content: str, file_path: Path, component: str) -> None:
		"""
		Scan for axios calls.

		Args:
		    content: File content
		    file_path: Path to the file
		    component: Component name
		"""
		lines = content.split("\n")

		for line_num, line in enumerate(lines, 1):
			matches = self.api_patterns["axios"].finditer(line)

			for match in matches:
				method = match.group(1).upper()
				url = match.group(2)

				endpoint = self._clean_endpoint(url)

				if endpoint:
					api_call = ApiCall(
						component=component,
						file_path=str(file_path.relative_to(self.frontend_directory)),
						line_number=line_num,
						endpoint=endpoint,
						method=method,
						context=line.strip(),
						call_type="direct",
					)
					self.api_calls.append(api_call)

	def _scan_endpoint_strings(self, content: str, file_path: Path, component: str) -> None:
		"""
		Scan for endpoint strings in the code.

		Args:
		    content: File content
		    file_path: Path to the file
		    component: Component name
		"""
		lines = content.split("\n")

		for line_num, line in enumerate(lines, 1):
			matches = self.api_patterns["endpoint_string"].finditer(line)

			for match in matches:
				endpoint = "/" + match.group(1)

				# Try to infer HTTP method from context
				method = self._infer_method_from_context(line)

				api_call = ApiCall(
					component=component,
					file_path=str(file_path.relative_to(self.frontend_directory)),
					line_number=line_num,
					endpoint=endpoint,
					method=method,
					context=line.strip(),
					call_type="direct",
				)
				self.api_calls.append(api_call)

	def _scan_hooks(self, content: str, file_path: Path, component: str) -> None:
		"""
		Scan for React Query hooks (useQuery, useMutation).

		Args:
		    content: File content
		    file_path: Path to the file
		    component: Component name
		"""
		lines = content.split("\n")

		for line_num, line in enumerate(lines, 1):
			# Look for useQuery or useMutation
			if "useQuery" in line or "useMutation" in line:
				# Try to find the endpoint in nearby lines
				context_start = max(0, line_num - 5)
				context_end = min(len(lines), line_num + 10)
				context = "\n".join(lines[context_start:context_end])

				# Look for API calls in the context
				endpoint_matches = self.api_patterns["endpoint_string"].finditer(context)
				for match in endpoint_matches:
					endpoint = "/" + match.group(1)
					method = self._infer_method_from_context(context)

					api_call = ApiCall(
						component=component,
						file_path=str(file_path.relative_to(self.frontend_directory)),
						line_number=line_num,
						endpoint=endpoint,
						method=method,
						context=line.strip(),
						call_type="hook",
					)
					self.api_calls.append(api_call)

	def _infer_endpoint_from_method(self, method_name: str, args: str) -> Tuple[Optional[str], str]:
		"""
		Infer endpoint and HTTP method from API client method name.

		Args:
		    method_name: Name of the API client method
		    args: Arguments passed to the method

		Returns:
		    Tuple of (endpoint, http_method)
		"""
		# Common patterns
		method_map = {
			"getJobs": ("/api/v1/jobs", "GET"),
			"searchJobs": ("/api/v1/jobs/search", "GET"),
			"createJob": ("/api/v1/jobs", "POST"),
			"updateJob": ("/api/v1/jobs/{id}", "PUT"),
			"deleteJob": ("/api/v1/jobs/{id}", "DELETE"),
			"getApplications": ("/api/v1/applications", "GET"),
			"searchApplications": ("/api/v1/applications/search", "GET"),
			"createApplication": ("/api/v1/applications", "POST"),
			"updateApplication": ("/api/v1/applications/{id}", "PUT"),
			"deleteApplication": ("/api/v1/applications/{id}", "DELETE"),
			"getAnalyticsSummary": ("/api/v1/analytics/summary", "GET"),
			"getComprehensiveAnalytics": ("/api/v1/analytics/comprehensive-dashboard", "GET"),
			"getUserProfile": ("/api/v1/profile", "GET"),
			"updateUserProfile": ("/api/v1/profile", "PUT"),
			"getRecommendations": ("/api/v1/recommendations", "GET"),
			"getSkillGapAnalysis": ("/api/v1/skill-gap", "GET"),
			"generateContent": ("/api/v1/content/generate", "POST"),
			"uploadResume": ("/api/v1/resume/upload", "POST"),
			"getResumeParsingStatus": ("/api/v1/resume/{id}/status", "GET"),
			"parseJobDescription": ("/api/v1/jobs/parse-description", "POST"),
			"generateCoverLetter": ("/api/v1/content/cover-letter", "POST"),
			"generateResumeTailoring": ("/api/v1/content/resume-tailor", "POST"),
			"getGeneratedContent": ("/api/v1/content/{id}", "GET"),
			"updateGeneratedContent": ("/api/v1/content/{id}", "PUT"),
			"startInterviewSession": ("/api/v1/interview/start-session", "POST"),
			"submitInterviewAnswer": ("/api/v1/interview/{id}/answer", "POST"),
			"getInterviewSessionSummary": ("/api/v1/interview/{id}/summary", "GET"),
			"submitFeedback": ("/api/v1/feedback", "POST"),
			"getFeedbackSummary": ("/api/v1/feedback/summary", "GET"),
			"healthCheck": ("/api/v1/health", "GET"),
			"getNotifications": ("/api/v1/notifications", "GET"),
			"markNotificationAsRead": ("/api/v1/notifications/{id}/read", "PUT"),
			"markNotificationAsUnread": ("/api/v1/notifications/{id}/unread", "PUT"),
			"markAllNotificationsAsRead": ("/api/v1/notifications/read-all", "PUT"),
			"deleteNotification": ("/api/v1/notifications/{id}", "DELETE"),
			"deleteNotifications": ("/api/v1/notifications/bulk-delete", "POST"),
			"getNotificationPreferences": ("/api/v1/notifications/preferences", "GET"),
			"updateNotificationPreferences": ("/api/v1/notifications/preferences", "PUT"),
			"subscribeToPushNotifications": ("/api/v1/notifications/push/subscribe", "POST"),
			"unsubscribeFromPushNotifications": ("/api/v1/notifications/push/unsubscribe", "POST"),
			"login": ("/api/v1/auth/login", "POST"),
			"register": ("/api/v1/auth/register", "POST"),
		}

		if method_name in method_map:
			return method_map[method_name]

		# Try to infer from method name patterns
		if method_name.startswith("get"):
			resource = method_name[3:].lower()
			return (f"/api/v1/{resource}", "GET")
		elif method_name.startswith("create"):
			resource = method_name[6:].lower()
			return (f"/api/v1/{resource}", "POST")
		elif method_name.startswith("update"):
			resource = method_name[6:].lower()
			return (f"/api/v1/{resource}/{{id}}", "PUT")
		elif method_name.startswith("delete"):
			resource = method_name[6:].lower()
			return (f"/api/v1/{resource}/{{id}}", "DELETE")

		return (None, "GET")

	def _clean_endpoint(self, url: str) -> Optional[str]:
		"""
		Clean and normalize an endpoint URL.

		Args:
		    url: Raw URL string

		Returns:
		    Cleaned endpoint path or None
		"""
		# Remove base URL if present
		url = re.sub(r"https?://[^/]+", "", url)

		# Remove template literals
		url = re.sub(r"\$\{[^}]+\}", "{id}", url)

		# Remove query parameters
		url = url.split("?")[0]

		# Ensure it starts with /
		if not url.startswith("/"):
			url = "/" + url

		# Only return if it looks like an API endpoint
		if "/api/" in url:
			return url

		return None

	def _infer_method_from_context(self, context: str) -> str:
		"""
		Infer HTTP method from surrounding context.

		Args:
		    context: Code context

		Returns:
		    HTTP method (GET, POST, PUT, DELETE)
		"""
		context_lower = context.lower()

		if "method:" in context_lower:
			if "'post'" in context_lower or '"post"' in context_lower:
				return "POST"
			elif "'put'" in context_lower or '"put"' in context_lower:
				return "PUT"
			elif "'delete'" in context_lower or '"delete"' in context_lower:
				return "DELETE"
			elif "'patch'" in context_lower or '"patch"' in context_lower:
				return "PATCH"

		# Infer from keywords
		if any(word in context_lower for word in ["create", "add", "submit", "upload"]):
			return "POST"
		elif any(word in context_lower for word in ["update", "edit", "modify"]):
			return "PUT"
		elif any(word in context_lower for word in ["delete", "remove"]):
			return "DELETE"

		return "GET"

	def identify_feature_requirements(self) -> List[FeatureRequirement]:
		"""Derive feature requirements from the current API call set.

		Returns:
		    A list of feature requirement groupings keyed by feature name.
		"""
		# Group API calls by feature/component
		feature_map: Dict[str, Set[str]] = {}
		component_map: Dict[str, Set[str]] = {}

		for api_call in self.api_calls:
			# Extract feature from component path
			feature = self._extract_feature_from_component(api_call.component)

			if feature not in feature_map:
				feature_map[feature] = set()
				component_map[feature] = set()

			endpoint_key = f"{api_call.method} {api_call.endpoint}"
			feature_map[feature].add(endpoint_key)
			component_map[feature].add(api_call.component)

		# Create feature requirements
		self.feature_requirements = []
		for feature, endpoints in feature_map.items():
			priority = self._determine_priority(feature, endpoints)

			requirement = FeatureRequirement(
				feature_name=feature,
				required_endpoints=sorted(list(endpoints)),
				priority=priority,
				components=sorted(list(component_map[feature])),
				description=f"Feature requiring {len(endpoints)} API endpoints",
			)
			self.feature_requirements.append(requirement)

		return self.feature_requirements

	def _extract_feature_from_component(self, component: str) -> str:
		"""Derive a logical feature bucket from a component path string.

		Args:
		    component: Dotted path representing the component location.

		Returns:
		    A normalized feature name used for grouping.
		"""
		parts = component.split(".")

		# Look for feature indicators
		if "features" in parts:
			idx = parts.index("features")
			if idx + 1 < len(parts):
				return parts[idx + 1]

		if "pages" in parts:
			idx = parts.index("pages")
			if idx + 1 < len(parts):
				return parts[idx + 1]

		if "components" in parts:
			idx = parts.index("components")
			if idx + 1 < len(parts):
				return parts[idx + 1]

		# Use first meaningful part
		for part in parts:
			if part not in ["src", "lib", "hooks", "utils"]:
				return part

		return "general"

	def _determine_priority(self, feature: str, endpoints: Set[str]) -> str:
		"""Estimate the business priority for a feature cluster.

		Args:
		    feature: Feature name derived from the component path.
		    endpoints: Collection of unique HTTP method/path keys the feature invokes.

		Returns:
		    One of ``critical``, ``high``, ``medium``, or ``low``.
		"""
		# Critical features
		if feature in ["auth", "authentication", "login"]:
			return "critical"

		# High priority features
		if feature in ["jobs", "applications", "dashboard", "analytics"]:
			return "high"

		# Medium priority features
		if feature in ["notifications", "profile", "settings"]:
			return "medium"

		# Low priority for features with few endpoints
		if len(endpoints) <= 2:
			return "low"

		return "medium"

	def export_to_json(self, output_file: str) -> None:
		"""Persist scan results, feature groupings, and stats to disk.

		Args:
		    output_file: Absolute or relative path where the JSON file should be written.
		"""
		data = {
			"api_calls": [call.to_dict() for call in self.api_calls],
			"feature_requirements": [req.to_dict() for req in self.feature_requirements],
			"statistics": {
				"total_api_calls": len(self.api_calls),
				"total_features": len(self.feature_requirements),
				"unique_endpoints": len(set(f"{call.method} {call.endpoint}" for call in self.api_calls)),
			},
		}

		with open(output_file, "w", encoding="utf-8") as f:
			json.dump(data, f, indent=2)

	def get_statistics(self) -> Dict[str, Any]:
		"""Summarize API usage metrics from the latest scan.

		Returns:
		    Mapping of aggregate counts (unique endpoints, components, methods, etc.).
		"""
		unique_endpoints = set(f"{call.method} {call.endpoint}" for call in self.api_calls)
		unique_components = set(call.component for call in self.api_calls)

		method_counts = {}
		for call in self.api_calls:
			method_counts[call.method] = method_counts.get(call.method, 0) + 1

		return {
			"total_api_calls": len(self.api_calls),
			"unique_endpoints": len(unique_endpoints),
			"unique_components": len(unique_components),
			"calls_by_method": method_counts,
			"calls_by_type": {
				"direct": len([c for c in self.api_calls if c.call_type == "direct"]),
				"hook": len([c for c in self.api_calls if c.call_type == "hook"]),
				"service": len([c for c in self.api_calls if c.call_type == "service"]),
			},
		}
