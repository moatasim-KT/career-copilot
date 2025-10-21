"""
Compliance Checking Service
Checks contracts against regulatory requirements and standards
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ComplianceStandard(str, Enum):
	"""Compliance standards"""

	GDPR = "gdpr"
	SOX = "sox"
	HIPAA = "hipaa"
	PCI_DSS = "pci_dss"
	ISO_27001 = "iso_27001"
	CCPA = "ccpa"
	FERPA = "ferpa"


class ComplianceLevel(str, Enum):
	"""Compliance levels"""

	COMPLIANT = "compliant"
	NON_COMPLIANT = "non_compliant"
	PARTIALLY_COMPLIANT = "partially_compliant"
	NOT_APPLICABLE = "not_applicable"


@dataclass
class ComplianceCheck:
	"""Individual compliance check result"""

	standard: ComplianceStandard
	level: ComplianceLevel
	score: float
	issues: List[str]
	recommendations: List[str]
	clauses_found: List[str]
	clauses_missing: List[str]


@dataclass
class ComplianceReport:
	"""Overall compliance report"""

	contract_id: str
	contract_name: str
	overall_compliance_score: float
	checks: List[ComplianceCheck]
	generated_at: datetime
	summary: str


class ComplianceService:
	"""Service for checking contract compliance against various standards"""

	def __init__(self):
		self.settings = get_settings()

		# Define compliance patterns and requirements
		self.compliance_patterns = {
			ComplianceStandard.GDPR: {
				"data_protection": [
					r"data protection",
					r"personal data",
					r"privacy policy",
					r"data processing",
					r"consent",
					r"right to be forgotten",
					r"data portability",
				],
				"required_clauses": [
					"Data protection officer",
					"Data processing agreement",
					"Privacy notice",
					"Consent mechanism",
					"Data breach notification",
				],
			},
			ComplianceStandard.SOX: {
				"financial_controls": [r"financial reporting", r"internal controls", r"audit", r"disclosure", r"materiality", r"risk assessment"],
				"required_clauses": [
					"Financial reporting requirements",
					"Internal control framework",
					"Audit rights",
					"Disclosure obligations",
					"Materiality thresholds",
				],
			},
			ComplianceStandard.HIPAA: {
				"health_privacy": [
					r"protected health information",
					r"phi",
					r"health information",
					r"medical records",
					r"patient privacy",
					r"healthcare data",
				],
				"required_clauses": [
					"HIPAA compliance",
					"PHI protection",
					"Business associate agreement",
					"Data security safeguards",
					"Breach notification",
				],
			},
			ComplianceStandard.CCPA: {
				"consumer_privacy": [r"consumer privacy", r"personal information", r"opt-out", r"data sale", r"consumer rights", r"privacy notice"],
				"required_clauses": [
					"Consumer privacy rights",
					"Data collection notice",
					"Opt-out mechanism",
					"Data sale restrictions",
					"Consumer access rights",
				],
			},
		}

	async def check_contract_compliance(self, contract_text: str, contract_name: str, standards: List[ComplianceStandard] = None) -> ComplianceReport:
		"""Check contract compliance against specified standards"""
		try:
			if standards is None:
				standards = [ComplianceStandard.GDPR, ComplianceStandard.SOX, ComplianceStandard.HIPAA]

			checks = []
			total_score = 0.0

			for standard in standards:
				check = await self._check_standard_compliance(contract_text, standard)
				checks.append(check)
				total_score += check.score

			overall_score = total_score / len(checks) if checks else 0.0

			# Generate summary
			summary = self._generate_compliance_summary(checks, overall_score)

			return ComplianceReport(
				contract_id=f"contract_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
				contract_name=contract_name,
				overall_compliance_score=round(overall_score, 2),
				checks=checks,
				generated_at=datetime.now(),
				summary=summary,
			)

		except Exception as e:
			logger.error(f"Failed to check contract compliance: {e}")
			return self._get_empty_compliance_report(contract_name)

	async def _check_standard_compliance(self, contract_text: str, standard: ComplianceStandard) -> ComplianceCheck:
		"""Check compliance against a specific standard"""
		try:
			if standard not in self.compliance_patterns:
				return ComplianceCheck(
					standard=standard,
					level=ComplianceLevel.NOT_APPLICABLE,
					score=0.0,
					issues=[],
					recommendations=[],
					clauses_found=[],
					clauses_missing=[],
				)

			patterns = self.compliance_patterns[standard]
			clauses_found = []
			clauses_missing = []
			issues = []
			recommendations = []

			# Check for required patterns
			for category, pattern_list in patterns.items():
				if category == "required_clauses":
					continue

				for pattern in pattern_list:
					if re.search(pattern, contract_text, re.IGNORECASE):
						clauses_found.append(pattern)
					else:
						issues.append(f"Missing {category}: {pattern}")

			# Check for required clauses
			for clause in patterns.get("required_clauses", []):
				if any(keyword in contract_text.lower() for keyword in clause.lower().split()):
					clauses_found.append(clause)
				else:
					clauses_missing.append(clause)
					issues.append(f"Missing required clause: {clause}")

			# Calculate compliance score
			total_requirements = len(patterns.get("required_clauses", []))
			found_requirements = len(clauses_found)
			score = (found_requirements / total_requirements * 100) if total_requirements > 0 else 0.0

			# Determine compliance level
			if score >= 80:
				level = ComplianceLevel.COMPLIANT
			elif score >= 50:
				level = ComplianceLevel.PARTIALLY_COMPLIANT
			else:
				level = ComplianceLevel.NON_COMPLIANT

			# Generate recommendations
			recommendations = self._generate_recommendations(standard, issues, clauses_missing)

			return ComplianceCheck(
				standard=standard,
				level=level,
				score=round(score, 2),
				issues=issues,
				recommendations=recommendations,
				clauses_found=clauses_found,
				clauses_missing=clauses_missing,
			)

		except Exception as e:
			logger.error(f"Failed to check {standard} compliance: {e}")
			return ComplianceCheck(
				standard=standard,
				level=ComplianceLevel.NON_COMPLIANT,
				score=0.0,
				issues=[f"Error checking compliance: {e!s}"],
				recommendations=["Review contract manually"],
				clauses_found=[],
				clauses_missing=[],
			)

	def _generate_recommendations(self, standard: ComplianceStandard, issues: List[str], missing_clauses: List[str]) -> List[str]:
		"""Generate compliance recommendations"""
		recommendations = []

		if standard == ComplianceStandard.GDPR:
			if any("data protection" in issue.lower() for issue in issues):
				recommendations.append("Add comprehensive data protection clauses")
			if any("consent" in issue.lower() for issue in issues):
				recommendations.append("Include explicit consent mechanisms")
			if any("privacy" in issue.lower() for issue in issues):
				recommendations.append("Add detailed privacy policy references")

		elif standard == ComplianceStandard.SOX:
			if any("financial" in issue.lower() for issue in issues):
				recommendations.append("Include financial reporting requirements")
			if any("audit" in issue.lower() for issue in issues):
				recommendations.append("Add audit rights and procedures")
			if any("disclosure" in issue.lower() for issue in issues):
				recommendations.append("Include material disclosure obligations")

		elif standard == ComplianceStandard.HIPAA:
			if any("phi" in issue.lower() or "health" in issue.lower() for issue in issues):
				recommendations.append("Add PHI protection and handling requirements")
			if any("breach" in issue.lower() for issue in issues):
				recommendations.append("Include data breach notification procedures")
			if any("business associate" in issue.lower() for issue in issues):
				recommendations.append("Add business associate agreement requirements")

		# Add general recommendations for missing clauses
		for clause in missing_clauses:
			recommendations.append(f"Consider adding: {clause}")

		return recommendations

	def _generate_compliance_summary(self, checks: List[ComplianceCheck], overall_score: float) -> str:
		"""Generate compliance summary"""
		compliant_count = sum(1 for check in checks if check.level == ComplianceLevel.COMPLIANT)
		total_checks = len(checks)

		if overall_score >= 80:
			status = "Highly Compliant"
		elif overall_score >= 60:
			status = "Moderately Compliant"
		elif overall_score >= 40:
			status = "Partially Compliant"
		else:
			status = "Non-Compliant"

		return f"Contract is {status} with {compliant_count}/{total_checks} standards fully met. Overall compliance score: {overall_score:.1f}%"

	def _get_empty_compliance_report(self, contract_name: str) -> ComplianceReport:
		"""Get empty compliance report"""
		return ComplianceReport(
			contract_id="",
			contract_name=contract_name,
			overall_compliance_score=0.0,
			checks=[],
			generated_at=datetime.now(),
			summary="Unable to analyze compliance",
		)

	async def get_compliance_standards(self) -> List[Dict[str, Any]]:
		"""Get available compliance standards"""
		return [
			{
				"standard": ComplianceStandard.GDPR,
				"name": "General Data Protection Regulation",
				"description": "EU data protection and privacy regulation",
				"applicable_to": ["Data processing", "Personal information", "Privacy"],
			},
			{
				"standard": ComplianceStandard.SOX,
				"name": "Sarbanes-Oxley Act",
				"description": "US financial reporting and corporate governance",
				"applicable_to": ["Financial reporting", "Internal controls", "Audit"],
			},
			{
				"standard": ComplianceStandard.HIPAA,
				"name": "Health Insurance Portability and Accountability Act",
				"description": "US healthcare data protection regulation",
				"applicable_to": ["Healthcare data", "Medical records", "Patient information"],
			},
			{
				"standard": ComplianceStandard.CCPA,
				"name": "California Consumer Privacy Act",
				"description": "California consumer privacy protection",
				"applicable_to": ["Consumer data", "Personal information", "Privacy rights"],
			},
			{
				"standard": ComplianceStandard.PCI_DSS,
				"name": "Payment Card Industry Data Security Standard",
				"description": "Credit card data security standards",
				"applicable_to": ["Payment processing", "Credit card data", "Financial transactions"],
			},
		]

	async def generate_compliance_report(self, contract_text: str, contract_name: str, format: str = "json") -> Dict[str, Any]:
		"""Generate detailed compliance report"""
		try:
			report = await self.check_contract_compliance(contract_text, contract_name)

			if format.lower() == "pdf":
				# Generate PDF report
				return await self._generate_pdf_report(report)
			elif format.lower() == "excel":
				# Generate Excel report
				return await self._generate_excel_report(report)
			else:
				# Return JSON format
				return {
					"report": {
						"contract_id": report.contract_id,
						"contract_name": report.contract_name,
						"overall_compliance_score": report.overall_compliance_score,
						"summary": report.summary,
						"generated_at": report.generated_at.isoformat(),
						"checks": [
							{
								"standard": check.standard.value,
								"level": check.level.value,
								"score": check.score,
								"issues": check.issues,
								"recommendations": check.recommendations,
								"clauses_found": check.clauses_found,
								"clauses_missing": check.clauses_missing,
							}
							for check in report.checks
						],
					}
				}
		except Exception as e:
			logger.error(f"Failed to generate compliance report: {e}")
			return {"error": str(e)}

	async def _generate_pdf_report(self, report: ComplianceReport) -> Dict[str, Any]:
		"""Generate PDF compliance report"""
		# Implementation for PDF generation
		return {"format": "pdf", "data": "PDF report would be generated here"}

	async def _generate_excel_report(self, report: ComplianceReport) -> Dict[str, Any]:
		"""Generate Excel compliance report"""
		# Implementation for Excel generation
		return {"format": "excel", "data": "Excel report would be generated here"}
