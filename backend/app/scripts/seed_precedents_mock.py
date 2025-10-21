#!/usr/bin/env python3
"""
Mock seed ChromaDB with sample precedent clauses for job application tracking.

This script populates the vector store with realistic legal precedent clauses
without requiring OpenAI API key for testing purposes.
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.logging import get_logger

logger = get_logger(__name__)


def get_sample_precedents() -> list[dict]:
	"""Get sample precedent clauses for seeding the database."""
	return [
		# Liability and Indemnification Clauses
		{
			"id": "liab_001",
			"text": "The Company shall indemnify, defend, and hold harmless the Client from and against any and all claims, damages, losses, costs, and expenses (including reasonable attorneys' fees) arising out of or relating to the Company's performance of services under this Agreement, except to the extent such claims arise from the Client's negligence or willful misconduct.",
			"category": "Liability and Indemnification",
			"risk_level": "High",
			"source_document": "Standard Service Agreement Template",
			"effectiveness_score": 0.8,
			"created_at": datetime.now(timezone.utc).isoformat(),
		},
		{
			"id": "liab_002",
			"text": "Each party shall be liable only for direct damages arising from a material breach of this Agreement, and in no event shall either party be liable for indirect, incidental, special, consequential, or punitive damages, regardless of the form of action.",
			"category": "Liability and Indemnification",
			"risk_level": "Low",
			"source_document": "Balanced Liability Clause Template",
			"effectiveness_score": 0.9,
			"created_at": datetime.now(timezone.utc).isoformat(),
		},
		{
			"id": "liab_003",
			"text": "The Client agrees to indemnify and hold harmless the Company from any claims arising from the Client's use of the deliverables, including but not limited to intellectual property infringement claims.",
			"category": "Liability and Indemnification",
			"risk_level": "High",
			"source_document": "Client-Favorable Service Agreement",
			"effectiveness_score": 0.7,
			"created_at": datetime.now(timezone.utc).isoformat(),
		},
		# Termination Clauses
		{
			"id": "term_001",
			"text": "Either party may terminate this Agreement immediately upon written notice if the other party materially breaches any provision of this Agreement and fails to cure such breach within thirty (30) days after receipt of written notice specifying the breach.",
			"category": "Termination",
			"risk_level": "Low",
			"source_document": "Standard Termination Clause",
			"effectiveness_score": 0.9,
			"created_at": datetime.now(timezone.utc).isoformat(),
		},
		{
			"id": "term_002",
			"text": "The Company may terminate this Agreement at any time with or without cause upon thirty (30) days written notice to the Client. The Client may only terminate for cause as specified in Section X.",
			"category": "Termination",
			"risk_level": "High",
			"source_document": "One-Sided Termination Clause",
			"effectiveness_score": 0.6,
			"created_at": datetime.now(timezone.utc).isoformat(),
		},
		{
			"id": "term_003",
			"text": "This Agreement shall continue in effect until terminated by either party upon ninety (90) days written notice. Upon termination, all outstanding obligations shall survive for a period of one (1) year.",
			"category": "Termination",
			"risk_level": "Medium",
			"source_document": "Long-Term Service Agreement",
			"effectiveness_score": 0.8,
			"created_at": datetime.now(timezone.utc).isoformat(),
		},
		# Payment and Pricing Clauses
		{
			"id": "pay_001",
			"text": "Payment shall be due within thirty (30) days of invoice date. Late payments shall incur interest at the rate of 1.5% per month or the maximum rate allowed by law, whichever is less.",
			"category": "Payment and Pricing",
			"risk_level": "Low",
			"source_document": "Standard Payment Terms",
			"effectiveness_score": 0.9,
			"created_at": datetime.now(timezone.utc).isoformat(),
		},
		{
			"id": "pay_002",
			"text": "All fees are non-refundable and non-cancellable once paid. The Client shall be responsible for all costs of collection, including reasonable attorneys' fees.",
			"category": "Payment and Pricing",
			"risk_level": "High",
			"source_document": "Non-Refundable Payment Clause",
			"effectiveness_score": 0.5,
			"created_at": datetime.now(timezone.utc).isoformat(),
		},
		{
			"id": "pay_003",
			"text": "The Company reserves the right to increase fees upon ninety (90) days written notice. The Client may terminate this Agreement if it objects to any fee increase.",
			"category": "Payment and Pricing",
			"risk_level": "Medium",
			"source_document": "Flexible Pricing Clause",
			"effectiveness_score": 0.7,
			"created_at": datetime.now(timezone.utc).isoformat(),
		},
		# Intellectual Property Clauses
		{
			"id": "ip_001",
			"text": "All intellectual property rights in the deliverables shall remain with the Company. The Client shall receive a non-exclusive, non-transferable license to use the deliverables for its internal business purposes only.",
			"category": "Intellectual Property",
			"risk_level": "High",
			"source_document": "Company-Owned IP Clause",
			"effectiveness_score": 0.6,
			"created_at": datetime.now(timezone.utc).isoformat(),
		},
		{
			"id": "ip_002",
			"text": "All work product, inventions, and intellectual property created in connection with this Agreement shall be owned by the Client. The Company hereby assigns all such rights to the Client.",
			"category": "Intellectual Property",
			"risk_level": "Low",
			"source_document": "Client-Owned IP Clause",
			"effectiveness_score": 0.9,
			"created_at": datetime.now(timezone.utc).isoformat(),
		},
		{
			"id": "ip_003",
			"text": "Each party shall retain ownership of its pre-existing intellectual property. Any jointly developed intellectual property shall be owned jointly by both parties.",
			"category": "Intellectual Property",
			"risk_level": "Low",
			"source_document": "Joint IP Ownership Clause",
			"effectiveness_score": 0.8,
			"created_at": datetime.now(timezone.utc).isoformat(),
		},
		# Confidentiality Clauses
		{
			"id": "conf_001",
			"text": "Each party shall maintain the confidentiality of all confidential information disclosed by the other party and shall not disclose such information to any third party without the disclosing party's prior written consent.",
			"category": "Confidentiality",
			"risk_level": "Low",
			"source_document": "Standard Confidentiality Clause",
			"effectiveness_score": 0.9,
			"created_at": datetime.now(timezone.utc).isoformat(),
		},
		{
			"id": "conf_002",
			"text": "The Client's confidential information shall be protected for a period of five (5) years after termination of this Agreement. The Company's confidential information shall be protected indefinitely.",
			"category": "Confidentiality",
			"risk_level": "High",
			"source_document": "Unequal Confidentiality Clause",
			"effectiveness_score": 0.4,
			"created_at": datetime.now(timezone.utc).isoformat(),
		},
		{
			"id": "conf_003",
			"text": "Confidential information shall not include information that is publicly available, independently developed, or rightfully received from a third party without confidentiality restrictions.",
			"category": "Confidentiality",
			"risk_level": "Low",
			"source_document": "Balanced Confidentiality Clause",
			"effectiveness_score": 0.9,
			"created_at": datetime.now(timezone.utc).isoformat(),
		},
		# Force Majeure Clauses
		{
			"id": "fm_001",
			"text": "Neither party shall be liable for any failure or delay in performance due to circumstances beyond its reasonable control, including but not limited to acts of God, natural disasters, war, terrorism, or government actions.",
			"category": "Force Majeure",
			"risk_level": "Low",
			"source_document": "Standard Force Majeure Clause",
			"effectiveness_score": 0.9,
			"created_at": datetime.now(timezone.utc).isoformat(),
		},
		{
			"id": "fm_002",
			"text": "The Company shall not be liable for any delays or failures due to force majeure events. The Client shall remain liable for all payments regardless of force majeure events affecting the Company.",
			"category": "Force Majeure",
			"risk_level": "High",
			"source_document": "One-Sided Force Majeure Clause",
			"effectiveness_score": 0.3,
			"created_at": datetime.now(timezone.utc).isoformat(),
		},
		# Governing Law and Dispute Resolution
		{
			"id": "gov_001",
			"text": "This Agreement shall be governed by the laws of [State/Country]. Any disputes shall be resolved through binding arbitration in accordance with the rules of the American Arbitration Association.",
			"category": "Governing Law and Dispute Resolution",
			"risk_level": "Low",
			"source_document": "Standard Arbitration Clause",
			"effectiveness_score": 0.8,
			"created_at": datetime.now(timezone.utc).isoformat(),
		},
		{
			"id": "gov_002",
			"text": "This Agreement shall be governed by the laws of [Company's State]. Any disputes shall be resolved exclusively in the courts of [Company's State], and the Client consents to personal jurisdiction in such courts.",
			"category": "Governing Law and Dispute Resolution",
			"risk_level": "High",
			"source_document": "Company-Favorable Jurisdiction Clause",
			"effectiveness_score": 0.5,
			"created_at": datetime.now(timezone.utc).isoformat(),
		},
		# Warranty Clauses
		{
			"id": "warr_001",
			"text": "The Company warrants that the services will be performed in a professional and workmanlike manner in accordance with industry standards. This warranty is the Company's sole warranty and is in lieu of all other warranties, express or implied.",
			"category": "Warranties",
			"risk_level": "Low",
			"source_document": "Standard Service Warranty",
			"effectiveness_score": 0.8,
			"created_at": datetime.now(timezone.utc).isoformat(),
		},
		{
			"id": "warr_002",
			"text": "The Company makes no warranties, express or implied, regarding the deliverables or services. All warranties are disclaimed to the maximum extent permitted by law.",
			"category": "Warranties",
			"risk_level": "High",
			"source_document": "No Warranty Clause",
			"effectiveness_score": 0.2,
			"created_at": datetime.now(timezone.utc).isoformat(),
		},
		{
			"id": "warr_003",
			"text": "The Company warrants that the deliverables will be free from material defects for a period of one (1) year from delivery. The Client's sole remedy for breach of this warranty is repair or replacement of the defective deliverables.",
			"category": "Warranties",
			"risk_level": "Low",
			"source_document": "Limited Warranty Clause",
			"effectiveness_score": 0.9,
			"created_at": datetime.now(timezone.utc).isoformat(),
		},
		# Limitation of Liability Clauses
		{
			"id": "lim_001",
			"text": "In no event shall either party's total liability exceed the total amount paid by the Client under this Agreement in the twelve (12) months preceding the event giving rise to the claim.",
			"category": "Limitation of Liability",
			"risk_level": "Low",
			"source_document": "Standard Liability Cap",
			"effectiveness_score": 0.8,
			"created_at": datetime.now(timezone.utc).isoformat(),
		},
		{
			"id": "lim_002",
			"text": "The Company's total liability shall not exceed the fees paid by the Client. The Client's liability shall not be limited and shall include all damages, including consequential and punitive damages.",
			"category": "Limitation of Liability",
			"risk_level": "High",
			"source_document": "Unequal Liability Limitation",
			"effectiveness_score": 0.3,
			"created_at": datetime.now(timezone.utc).isoformat(),
		},
		{
			"id": "lim_003",
			"text": "Neither party shall be liable for any indirect, incidental, special, or consequential damages, including but not limited to loss of profits, data, or business opportunities.",
			"category": "Limitation of Liability",
			"risk_level": "Low",
			"source_document": "Mutual Consequential Damages Exclusion",
			"effectiveness_score": 0.9,
			"created_at": datetime.now(timezone.utc).isoformat(),
		},
	]


async def seed_mock_vector_store():
	"""Seed a mock vector store with sample precedent clauses."""
	try:
		logger.info("Starting to seed mock vector store with precedent clauses...")

		# Get sample precedents
		precedents = get_sample_precedents()

		# Create a simple JSON file to store the precedents
		import json
		import os

		# Ensure the data directory exists
		data_dir = Path("data/chroma")
		data_dir.mkdir(parents=True, exist_ok=True)

		# Save precedents to a JSON file
		precedents_file = data_dir / "precedents.json"
		with open(precedents_file, "w") as f:
			json.dump(precedents, f, indent=2)

		logger.info(f"Successfully seeded mock vector store with {len(precedents)} precedent clauses")
		logger.info(f"Precedents saved to: {precedents_file}")

		# Print summary
		categories = {}
		risk_levels = {}
		for precedent in precedents:
			category = precedent["category"]
			risk_level = precedent["risk_level"]
			categories[category] = categories.get(category, 0) + 1
			risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1

		logger.info(f"Categories: {categories}")
		logger.info(f"Risk levels: {risk_levels}")

		return True

	except Exception as e:
		logger.error(f"Failed to seed mock vector store: {e}")
		return False


async def main():
	"""Main function to run the seeding process."""
	logger.info("Mock Vector Store Precedent Seeding Script")
	logger.info("=" * 50)

	success = await seed_mock_vector_store()

	if success:
		logger.info("✅ Mock seeding completed successfully!")
		return 0
	else:
		logger.error("❌ Mock seeding failed!")
		return 1


if __name__ == "__main__":
	exit_code = asyncio.run(main())
	sys.exit(exit_code)
