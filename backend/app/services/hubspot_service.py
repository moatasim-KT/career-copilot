"""
HubSpot Integration Service
Integrates with HubSpot CRM for contact and deal management
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import httpx

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class HubSpotObjectType(str, Enum):
	"""HubSpot object types"""

	CONTACT = "contacts"
	DEAL = "deals"
	COMPANY = "companies"
	TICKET = "tickets"
	TASK = "tasks"


@dataclass
class HubSpotContact:
	"""HubSpot contact data"""

	contact_id: Optional[str] = None
	email: str = ""
	first_name: str = ""
	last_name: str = ""
	company: str = ""
	phone: str = ""
	job_title: str = ""
	properties: Dict[str, Any] = None


@dataclass
class HubSpotDeal:
	"""HubSpot deal data"""

	deal_id: Optional[str] = None
	deal_name: str = ""
	deal_stage: str = ""
	amount: float = 0.0
	close_date: Optional[datetime] = None
	pipeline_id: str = "default"
	properties: Dict[str, Any] = None


@dataclass
class HubSpotCompany:
	"""HubSpot company data"""

	company_id: Optional[str] = None
	name: str = ""
	domain: str = ""
	industry: str = ""
	city: str = ""
	state: str = ""
	country: str = ""
	properties: Dict[str, Any] = None


class HubSpotService:
	"""Service for HubSpot CRM integration"""

	def __init__(self):
		self.settings = get_settings()
		self.api_key = getattr(self.settings, "hubspot_api_key", "")
		self.base_url = "https://api.hubapi.com"
		self.enabled = getattr(self.settings, "hubspot_enabled", False)

		logger.info(f"HubSpot service initialized: enabled={self.enabled}")

	async def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
		"""Make API request to HubSpot"""
		try:
			if not self.enabled or not self.api_key:
				raise ValueError("HubSpot not enabled or API key missing")

			url = f"{self.base_url}{endpoint}"
			headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

			async with httpx.AsyncClient() as client:
				response = await client.request(method, url, headers=headers, json=data, params=params)
				response.raise_for_status()
				return response.json()

		except Exception as e:
			logger.error(f"HubSpot API request failed: {e}")
			raise

	async def create_contact(self, contact: HubSpotContact) -> Optional[str]:
		"""Create a new contact in HubSpot"""
		try:
			properties = {
				"email": contact.email,
				"firstname": contact.first_name,
				"lastname": contact.last_name,
				"company": contact.company,
				"phone": contact.phone,
				"jobtitle": contact.job_title,
			}

			# Add custom properties
			if contact.properties:
				properties.update(contact.properties)

			data = {"properties": properties}

			response = await self._make_request("POST", "/crm/v3/objects/contacts", data)

			if "id" in response:
				logger.info(f"Created HubSpot contact: {response['id']}")
				return response["id"]
			else:
				logger.error(f"Failed to create contact: {response}")
				return None

		except Exception as e:
			logger.error(f"Failed to create HubSpot contact: {e}")
			return None

	async def get_contact(self, contact_id: str) -> Optional[HubSpotContact]:
		"""Get contact by ID"""
		try:
			response = await self._make_request("GET", f"/crm/v3/objects/contacts/{contact_id}")

			if "properties" in response:
				props = response["properties"]
				return HubSpotContact(
					contact_id=response.get("id"),
					email=props.get("email", ""),
					first_name=props.get("firstname", ""),
					last_name=props.get("lastname", ""),
					company=props.get("company", ""),
					phone=props.get("phone", ""),
					job_title=props.get("jobtitle", ""),
					properties=props,
				)
			return None

		except Exception as e:
			logger.error(f"Failed to get HubSpot contact: {e}")
			return None

	async def search_contacts(self, query: str, limit: int = 10) -> List[HubSpotContact]:
		"""Search contacts"""
		try:
			params = {"q": query, "limit": limit, "properties": "email,firstname,lastname,company,phone,jobtitle"}

			response = await self._make_request("GET", "/crm/v3/objects/contacts/search", params=params)

			contacts = []
			if "results" in response:
				for result in response["results"]:
					props = result.get("properties", {})
					contacts.append(
						HubSpotContact(
							contact_id=result.get("id"),
							email=props.get("email", ""),
							first_name=props.get("firstname", ""),
							last_name=props.get("lastname", ""),
							company=props.get("company", ""),
							phone=props.get("phone", ""),
							job_title=props.get("jobtitle", ""),
							properties=props,
						)
					)

			return contacts

		except Exception as e:
			logger.error(f"Failed to search HubSpot contacts: {e}")
			return []

	async def create_deal(self, deal: HubSpotDeal) -> Optional[str]:
		"""Create a new deal in HubSpot"""
		try:
			properties = {"dealname": deal.deal_name, "dealstage": deal.deal_stage, "amount": str(deal.amount), "pipeline": deal.pipeline_id}

			if deal.close_date:
				properties["closedate"] = deal.close_date.isoformat()

			# Add custom properties
			if deal.properties:
				properties.update(deal.properties)

			data = {"properties": properties}

			response = await self._make_request("POST", "/crm/v3/objects/deals", data)

			if "id" in response:
				logger.info(f"Created HubSpot deal: {response['id']}")
				return response["id"]
			else:
				logger.error(f"Failed to create deal: {response}")
				return None

		except Exception as e:
			logger.error(f"Failed to create HubSpot deal: {e}")
			return None

	async def get_deal(self, deal_id: str) -> Optional[HubSpotDeal]:
		"""Get deal by ID"""
		try:
			response = await self._make_request("GET", f"/crm/v3/objects/deals/{deal_id}")

			if "properties" in response:
				props = response["properties"]
				close_date = None
				if props.get("closedate"):
					close_date = datetime.fromisoformat(props["closedate"].replace("Z", "+00:00"))

				return HubSpotDeal(
					deal_id=response.get("id"),
					deal_name=props.get("dealname", ""),
					deal_stage=props.get("dealstage", ""),
					amount=float(props.get("amount", 0)),
					close_date=close_date,
					pipeline_id=props.get("pipeline", "default"),
					properties=props,
				)
			return None

		except Exception as e:
			logger.error(f"Failed to get HubSpot deal: {e}")
			return None

	async def update_deal_stage(self, deal_id: str, new_stage: str) -> bool:
		"""Update deal stage"""
		try:
			data = {"properties": {"dealstage": new_stage}}

			response = await self._make_request("PATCH", f"/crm/v3/objects/deals/{deal_id}", data)

			if "id" in response:
				logger.info(f"Updated deal {deal_id} stage to {new_stage}")
				return True
			return False

		except Exception as e:
			logger.error(f"Failed to update deal stage: {e}")
			return False

	async def create_company(self, company: HubSpotCompany) -> Optional[str]:
		"""Create a new company in HubSpot"""
		try:
			properties = {
				"name": company.name,
				"domain": company.domain,
				"industry": company.industry,
				"city": company.city,
				"state": company.state,
				"country": company.country,
			}

			# Add custom properties
			if company.properties:
				properties.update(company.properties)

			data = {"properties": properties}

			response = await self._make_request("POST", "/crm/v3/objects/companies", data)

			if "id" in response:
				logger.info(f"Created HubSpot company: {response['id']}")
				return response["id"]
			else:
				logger.error(f"Failed to create company: {response}")
				return None

		except Exception as e:
			logger.error(f"Failed to create HubSpot company: {e}")
			return None

	async def associate_contact_with_deal(self, contact_id: str, deal_id: str) -> bool:
		"""Associate contact with deal"""
		try:
			data = {"inputs": [{"from": {"id": contact_id}, "to": {"id": deal_id}, "type": "contact_to_deal"}]}

			response = await self._make_request("PUT", "/crm/v3/objects/contacts/associations", data)

			if "results" in response and len(response["results"]) > 0:
				logger.info(f"Associated contact {contact_id} with deal {deal_id}")
				return True
			return False

		except Exception as e:
			logger.error(f"Failed to associate contact with deal: {e}")
			return False

	async def create_contract_deal(
		self, contract_name: str, contract_value: float, contact_email: str, risk_score: float, contract_type: str = "Contract"
	) -> Optional[str]:
		"""Create a deal for job application tracking"""
		try:
			# First, try to find existing contact
			contacts = await self.search_contacts(contact_email, limit=1)
			contact_id = None

			if contacts:
				contact_id = contacts[0].contact_id
			else:
				# Create new contact if not found
				contact = HubSpotContact(email=contact_email, first_name="Contract", last_name="Client")
				contact_id = await self.create_contact(contact)

			if not contact_id:
				logger.error("Failed to find or create contact")
				return None

			# Determine deal stage based on risk score
			if risk_score >= 7.0:
				deal_stage = "contract_review_high_risk"
			elif risk_score >= 4.0:
				deal_stage = "contract_review_medium_risk"
			else:
				deal_stage = "contract_review_low_risk"

			# Create deal
			deal = HubSpotDeal(
				deal_name=f"{contract_type}: {contract_name}",
				deal_stage=deal_stage,
				amount=contract_value,
				close_date=datetime.now() + timedelta(days=30),  # 30 days from now
				properties={
					"contract_type": contract_type,
					"risk_score": str(risk_score),
					"contract_name": contract_name,
					"analysis_date": datetime.now().isoformat(),
				},
			)

			deal_id = await self.create_deal(deal)

			if deal_id and contact_id:
				# Associate contact with deal
				await self.associate_contact_with_deal(contact_id, deal_id)

			return deal_id

		except Exception as e:
			logger.error(f"Failed to create contract deal: {e}")
			return None

	async def update_deal_with_analysis_results(self, deal_id: str, analysis_results: Dict[str, Any]) -> bool:
		"""Update deal with job application tracking results"""
		try:
			properties = {
				"contract_analysis_completed": "true",
				"risk_score": str(analysis_results.get("risk_score", 0)),
				"risk_level": analysis_results.get("risk_level", "Unknown"),
				"analysis_date": datetime.now().isoformat(),
				"risky_clauses_count": str(len(analysis_results.get("risky_clauses", []))),
				"compliance_score": str(analysis_results.get("compliance_score", 0)),
			}

			# Add specific risk details
			if "risky_clauses" in analysis_results:
				risky_clauses = analysis_results["risky_clauses"]
				if risky_clauses:
					properties["top_risk_areas"] = ", ".join([clause.get("risk_type", "Unknown") for clause in risky_clauses[:3]])

			data = {"properties": properties}

			response = await self._make_request("PATCH", f"/crm/v3/objects/deals/{deal_id}", data)

			if "id" in response:
				logger.info(f"Updated deal {deal_id} with analysis results")
				return True
			return False

		except Exception as e:
			logger.error(f"Failed to update deal with analysis results: {e}")
			return False

	async def get_deal_pipelines(self) -> List[Dict[str, Any]]:
		"""Get available deal pipelines"""
		try:
			response = await self._make_request("GET", "/crm/v3/pipelines/deals")

			pipelines = []
			if "results" in response:
				for pipeline in response["results"]:
					pipelines.append(
						{
							"pipeline_id": pipeline.get("id"),
							"label": pipeline.get("label"),
							"stages": [
								{"stage_id": stage.get("id"), "label": stage.get("label"), "display_order": stage.get("displayOrder")}
								for stage in pipeline.get("stages", [])
							],
						}
					)

			return pipelines

		except Exception as e:
			logger.error(f"Failed to get deal pipelines: {e}")
			return []

	async def get_contact_properties(self) -> List[Dict[str, Any]]:
		"""Get available contact properties"""
		try:
			response = await self._make_request("GET", "/crm/v3/properties/contacts")

			properties = []
			if "results" in response:
				for prop in response["results"]:
					properties.append(
						{
							"name": prop.get("name"),
							"label": prop.get("label"),
							"type": prop.get("type"),
							"field_type": prop.get("fieldType"),
							"description": prop.get("description"),
						}
					)

			return properties

		except Exception as e:
			logger.error(f"Failed to get contact properties: {e}")
			return []

	async def test_connection(self) -> Dict[str, Any]:
		"""Test HubSpot connection"""
		try:
			if not self.enabled:
				return {"success": False, "message": "HubSpot not enabled", "error": "Service disabled"}

			if not self.api_key:
				return {"success": False, "message": "HubSpot API key missing", "error": "No API key configured"}

			# Test with a simple API call
			response = await self._make_request("GET", "/crm/v3/objects/contacts", params={"limit": 1})

			if "results" in response:
				return {"success": True, "message": "HubSpot connection successful", "service": "HubSpot", "authenticated": True}
			else:
				return {"success": False, "message": "HubSpot connection failed", "error": "Invalid API response"}

		except Exception as e:
			return {"success": False, "message": f"HubSpot connection test failed: {e!s}", "error": str(e)}

	async def get_integration_stats(self) -> Dict[str, Any]:
		"""Get integration statistics"""
		try:
			# Get counts of different objects
			contacts_response = await self._make_request("GET", "/crm/v3/objects/contacts", params={"limit": 1})
			deals_response = await self._make_request("GET", "/crm/v3/objects/deals", params={"limit": 1})
			companies_response = await self._make_request("GET", "/crm/v3/objects/companies", params={"limit": 1})

			return {
				"contacts_count": contacts_response.get("total", 0),
				"deals_count": deals_response.get("total", 0),
				"companies_count": companies_response.get("total", 0),
				"last_sync": datetime.now().isoformat(),
				"status": "connected" if self.enabled else "disabled",
			}

		except Exception as e:
			logger.error(f"Failed to get integration stats: {e}")
			return {"contacts_count": 0, "deals_count": 0, "companies_count": 0, "last_sync": None, "status": "error"}
