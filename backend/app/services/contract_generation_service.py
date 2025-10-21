"""
Contract Generation Service
Generates contracts based on templates and requirements
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from jinja2 import Environment, FileSystemLoader, Template

logger = logging.getLogger(__name__)


class ContractType(str, Enum):
	"""Contract types"""

	SERVICE_AGREEMENT = "service_agreement"
	EMPLOYMENT_CONTRACT = "employment_contract"
	NDA = "nda"
	SOFTWARE_LICENSE = "software_license"
	PARTNERSHIP_AGREEMENT = "partnership_agreement"
	LEASE_AGREEMENT = "lease_agreement"
	PURCHASE_ORDER = "purchase_order"
	MASTER_SERVICE_AGREEMENT = "master_service_agreement"


class ContractStatus(str, Enum):
	"""Contract generation status"""

	DRAFT = "draft"
	REVIEW = "review"
	APPROVED = "approved"
	FINAL = "final"


@dataclass
class ContractTemplate:
	"""Contract template"""

	template_id: str
	name: str
	contract_type: ContractType
	description: str
	template_content: str
	variables: List[str]
	created_at: datetime
	updated_at: datetime


@dataclass
class ContractGenerationRequest:
	"""Contract generation request"""

	request_id: str
	contract_type: ContractType
	variables: Dict[str, Any]
	custom_requirements: List[str]
	status: ContractStatus
	created_at: datetime
	generated_content: Optional[str] = None


@dataclass
class GeneratedContract:
	"""Generated contract"""

	contract_id: str
	contract_name: str
	contract_type: ContractType
	content: str
	variables_used: Dict[str, Any]
	risk_score: float
	compliance_notes: List[str]
	generated_at: datetime
	status: ContractStatus


class ContractGenerationService:
	"""Service for generating contracts from templates"""

	def __init__(self):
		self.templates: Dict[str, ContractTemplate] = {}
		self.generation_requests: Dict[str, ContractGenerationRequest] = {}
		self.generated_contracts: Dict[str, GeneratedContract] = {}
		self._initialize_templates()

	def _initialize_templates(self):
		"""Initialize contract templates"""
		self.templates = {
			"service_agreement_001": ContractTemplate(
				template_id="service_agreement_001",
				name="Standard Service Agreement",
				contract_type=ContractType.SERVICE_AGREEMENT,
				description="Basic service agreement template",
				template_content=self._get_service_agreement_template(),
				variables=["client_name", "service_provider", "service_description", "payment_terms", "duration"],
				created_at=datetime.now(),
				updated_at=datetime.now(),
			),
			"nda_001": ContractTemplate(
				template_id="nda_001",
				name="Non-Disclosure Agreement",
				contract_type=ContractType.NDA,
				description="Standard NDA template",
				template_content=self._get_nda_template(),
				variables=["disclosing_party", "receiving_party", "confidential_information", "duration"],
				created_at=datetime.now(),
				updated_at=datetime.now(),
			),
			"employment_contract_001": ContractTemplate(
				template_id="employment_contract_001",
				name="Employment Contract",
				contract_type=ContractType.EMPLOYMENT_CONTRACT,
				description="Standard employment contract template",
				template_content=self._get_employment_contract_template(),
				variables=["employee_name", "employer_name", "position", "salary", "start_date", "benefits"],
				created_at=datetime.now(),
				updated_at=datetime.now(),
			),
		}

	def _get_service_agreement_template(self) -> str:
		"""Get service agreement template"""
		return """
SERVICE AGREEMENT

This Service Agreement ("Agreement") is entered into on {{ effective_date }} between {{ client_name }} ("Client") and {{ service_provider }} ("Service Provider").

1. SERVICES
Service Provider agrees to provide the following services: {{ service_description }}

2. PAYMENT TERMS
Client agrees to pay Service Provider {{ payment_amount }} {{ payment_frequency }} for the services provided.

3. TERM
This Agreement shall commence on {{ start_date }} and continue for {{ duration }} unless terminated earlier in accordance with this Agreement.

4. TERMINATION
Either party may terminate this Agreement with {{ notice_period }} written notice.

5. CONFIDENTIALITY
Both parties agree to maintain the confidentiality of any proprietary information disclosed during the course of this Agreement.

6. LIMITATION OF LIABILITY
Service Provider's liability shall be limited to the total amount paid by Client under this Agreement.

7. GOVERNING LAW
This Agreement shall be governed by the laws of {{ governing_law }}.

IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first written above.

Client: _________________     Service Provider: _________________
Date: _________________       Date: _________________
        """

	def _get_nda_template(self) -> str:
		"""Get NDA template"""
		return """
NON-DISCLOSURE AGREEMENT

This Non-Disclosure Agreement ("Agreement") is entered into on {{ effective_date }} between {{ disclosing_party }} ("Disclosing Party") and {{ receiving_party }} ("Receiving Party").

1. CONFIDENTIAL INFORMATION
The term "Confidential Information" means all information disclosed by Disclosing Party to Receiving Party, including but not limited to: {{ confidential_information }}

2. OBLIGATIONS
Receiving Party agrees to:
a) Hold all Confidential Information in strict confidence
b) Not disclose Confidential Information to any third party
c) Use Confidential Information solely for the purpose of {{ purpose }}

3. DURATION
This Agreement shall remain in effect for {{ duration }} from the date of execution.

4. RETURN OF INFORMATION
Upon termination of this Agreement, Receiving Party shall return all Confidential Information to Disclosing Party.

5. REMEDIES
The parties acknowledge that any breach of this Agreement would cause irreparable harm and that monetary damages would be inadequate.

IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first written above.

Disclosing Party: _________________     Receiving Party: _________________
Date: _________________                Date: _________________
        """

	def _get_employment_contract_template(self) -> str:
		"""Get employment contract template"""
		return """
EMPLOYMENT CONTRACT

This Employment Contract ("Contract") is entered into on {{ effective_date }} between {{ employer_name }} ("Employer") and {{ employee_name }} ("Employee").

1. POSITION
Employee shall serve as {{ position }} and shall perform such duties as may be assigned by Employer.

2. COMPENSATION
Employee shall receive a salary of {{ salary }} per {{ pay_period }}, payable {{ payment_schedule }}.

3. BENEFITS
Employee shall be entitled to the following benefits: {{ benefits }}

4. START DATE
Employee's employment shall commence on {{ start_date }}.

5. WORK SCHEDULE
Employee shall work {{ work_schedule }} hours per week.

6. TERMINATION
Either party may terminate this employment relationship with {{ notice_period }} written notice.

7. CONFIDENTIALITY
Employee agrees to maintain the confidentiality of all proprietary information of Employer.

8. NON-COMPETE
Employee agrees not to compete with Employer for {{ non_compete_period }} after termination of employment.

IN WITNESS WHEREOF, the parties have executed this Contract as of the date first written above.

Employer: _________________     Employee: _________________
Date: _________________        Date: _________________
        """

	async def generate_contract(
		self, contract_type: ContractType, variables: Dict[str, Any], custom_requirements: List[str] = None, template_id: Optional[str] = None
	) -> GeneratedContract:
		"""Generate a contract from template"""
		try:
			# Find appropriate template
			template = await self._find_template(contract_type, template_id)
			if not template:
				raise ValueError(f"No template found for contract type: {contract_type}")

			# Validate required variables
			missing_vars = await self._validate_variables(template, variables)
			if missing_vars:
				raise ValueError(f"Missing required variables: {missing_vars}")

			# Generate contract content
			content = await self._render_template(template, variables, custom_requirements)

			# Generate contract ID and name
			contract_id = f"contract_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
			contract_name = f"{contract_type.value.replace('_', ' ').title()} - {variables.get('client_name', 'Unknown')}"

			# Analyze generated contract for risk and compliance
			risk_score = await self._analyze_generated_contract(content)
			compliance_notes = await self._check_generated_contract_compliance(content)

			# Create generated contract
			generated_contract = GeneratedContract(
				contract_id=contract_id,
				contract_name=contract_name,
				contract_type=contract_type,
				content=content,
				variables_used=variables,
				risk_score=risk_score,
				compliance_notes=compliance_notes,
				generated_at=datetime.now(),
				status=ContractStatus.DRAFT,
			)

			self.generated_contracts[contract_id] = generated_contract

			logger.info(f"Generated contract {contract_id} of type {contract_type}")
			return generated_contract

		except Exception as e:
			logger.error(f"Failed to generate contract: {e}")
			raise

	async def _find_template(self, contract_type: ContractType, template_id: Optional[str] = None) -> Optional[ContractTemplate]:
		"""Find appropriate template"""
		if template_id and template_id in self.templates:
			return self.templates[template_id]

		# Find template by contract type
		for template in self.templates.values():
			if template.contract_type == contract_type:
				return template

		return None

	async def _validate_variables(self, template: ContractTemplate, variables: Dict[str, Any]) -> List[str]:
		"""Validate that all required variables are provided"""
		missing_vars = []
		for var in template.variables:
			if var not in variables or not variables[var]:
				missing_vars.append(var)
		return missing_vars

	async def _render_template(self, template: ContractTemplate, variables: Dict[str, Any], custom_requirements: List[str] = None) -> str:
		"""Render template with variables"""
		try:
			# Create Jinja2 environment
			env = Environment()
			template_obj = env.from_string(template.template_content)

			# Add default values for common variables
			default_vars = {
				"effective_date": datetime.now().strftime("%B %d, %Y"),
				"start_date": datetime.now().strftime("%B %d, %Y"),
				"governing_law": "State of California",
				"notice_period": "30 days",
				"duration": "12 months",
				"payment_frequency": "monthly",
				"pay_period": "year",
				"payment_schedule": "bi-weekly",
				"work_schedule": "40",
				"non_compete_period": "12 months",
				"purpose": "evaluation of potential business relationship",
			}

			# Merge variables with defaults
			all_vars = {**default_vars, **variables}

			# Render template
			content = template_obj.render(**all_vars)

			# Apply custom requirements if provided
			if custom_requirements:
				content = await self._apply_custom_requirements(content, custom_requirements)

			return content

		except Exception as e:
			logger.error(f"Failed to render template: {e}")
			raise

	async def _apply_custom_requirements(self, content: str, requirements: List[str]) -> str:
		"""Apply custom requirements to contract content"""
		# This is a simplified implementation
		# In production, you'd have more sophisticated requirement processing

		for requirement in requirements:
			if "liability" in requirement.lower():
				# Add liability clause if not present
				if "limitation of liability" not in content.lower():
					content += (
						"\n\n8. LIMITATION OF LIABILITY\nService Provider's liability shall be limited to the total amount paid under this Agreement."
					)

			if "indemnification" in requirement.lower():
				# Add indemnification clause
				if "indemnification" not in content.lower():
					content += "\n\n9. INDEMNIFICATION\nClient agrees to indemnify and hold harmless Service Provider from any claims arising from Client's use of the services."

			if "force majeure" in requirement.lower():
				# Add force majeure clause
				if "force majeure" not in content.lower():
					content += "\n\n10. FORCE MAJEURE\nNeither party shall be liable for any failure to perform due to circumstances beyond their reasonable control."

		return content

	async def _analyze_generated_contract(self, content: str) -> float:
		"""Analyze generated contract for risk"""
		risk_score = 5.0  # Base risk score

		# Check for high-risk clauses
		if "limitation of liability" in content.lower():
			risk_score -= 1.0
		if "indemnification" in content.lower():
			risk_score += 1.0
		if "force majeure" in content.lower():
			risk_score += 0.5
		if "termination" in content.lower():
			risk_score += 0.5

		# Check contract length (longer contracts may be riskier)
		if len(content) > 5000:
			risk_score += 1.0
		elif len(content) < 1000:
			risk_score += 0.5

		return max(0.0, min(10.0, risk_score))

	async def _check_generated_contract_compliance(self, content: str) -> List[str]:
		"""Check generated contract for compliance issues"""
		compliance_notes = []

		# Check for required clauses
		if "governing law" not in content.lower():
			compliance_notes.append("Consider adding governing law clause")

		if "confidentiality" not in content.lower():
			compliance_notes.append("Consider adding confidentiality clause")

		if "termination" not in content.lower():
			compliance_notes.append("Consider adding termination clause")

		# Check for GDPR compliance if personal data is mentioned
		if any(word in content.lower() for word in ["personal data", "privacy", "data protection"]):
			if "data protection" not in content.lower():
				compliance_notes.append("Consider adding GDPR compliance clause for data protection")

		return compliance_notes

	async def get_available_templates(self) -> List[Dict[str, Any]]:
		"""Get available contract templates"""
		return [
			{
				"template_id": template.template_id,
				"name": template.name,
				"contract_type": template.contract_type.value,
				"description": template.description,
				"variables": template.variables,
				"created_at": template.created_at.isoformat(),
			}
			for template in self.templates.values()
		]

	async def get_contract_types(self) -> List[Dict[str, Any]]:
		"""Get available contract types"""
		return [
			{
				"type": contract_type.value,
				"name": contract_type.value.replace("_", " ").title(),
				"description": f"Generate {contract_type.value.replace('_', ' ')} contracts",
			}
			for contract_type in ContractType
		]

	async def get_generated_contract(self, contract_id: str) -> Optional[GeneratedContract]:
		"""Get generated contract by ID"""
		return self.generated_contracts.get(contract_id)

	async def update_contract_status(self, contract_id: str, status: ContractStatus) -> bool:
		"""Update contract status"""
		if contract_id in self.generated_contracts:
			self.generated_contracts[contract_id].status = status
			return True
		return False

	async def export_contract(self, contract_id: str, format: str = "txt") -> Dict[str, Any]:
		"""Export contract in various formats"""
		contract = self.generated_contracts.get(contract_id)
		if not contract:
			return {"error": "Contract not found"}

		if format.lower() == "pdf":
			# In production, use a PDF generation library
			return {"format": "pdf", "content": "PDF content would be generated here", "contract_id": contract_id}
		elif format.lower() == "docx":
			# In production, use a DOCX generation library
			return {"format": "docx", "content": "DOCX content would be generated here", "contract_id": contract_id}
		else:
			return {
				"format": "txt",
				"content": contract.content,
				"contract_id": contract_id,
				"contract_name": contract.contract_name,
				"generated_at": contract.generated_at.isoformat(),
			}

	async def get_generation_statistics(self) -> Dict[str, Any]:
		"""Get contract generation statistics"""
		total_generated = len(self.generated_contracts)
		by_type = {}
		by_status = {}

		for contract in self.generated_contracts.values():
			# Count by type
			contract_type = contract.contract_type.value
			by_type[contract_type] = by_type.get(contract_type, 0) + 1

			# Count by status
			status = contract.status.value
			by_status[status] = by_status.get(status, 0) + 1

		return {
			"total_generated": total_generated,
			"by_type": by_type,
			"by_status": by_status,
			"templates_available": len(self.templates),
			"contract_types_available": len(ContractType),
		}
