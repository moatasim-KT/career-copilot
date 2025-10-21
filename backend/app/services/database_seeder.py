"""
Database seeding service for populating the vector store with sample precedent clauses.

This module provides functionality to seed the ChromaDB vector store with
sample precedent clauses for job application tracking.
"""

import logging
import uuid
from datetime import datetime
from typing import List

from ..core.exceptions import VectorStoreError
from .vector_store import PrecedentClause, VectorStoreService

logger = logging.getLogger(__name__)


class DatabaseSeeder:
	"""Service for seeding the vector database with sample precedent clauses."""

	def __init__(self, vector_store: VectorStoreService):
		self.vector_store = vector_store

	def get_sample_precedent_clauses(self) -> List[PrecedentClause]:
		"""Generate sample precedent clauses for seeding the database."""
		sample_clauses = [
			# Liability and Indemnification Clauses
			PrecedentClause(
				id=str(uuid.uuid4()),
				text="The Company shall indemnify and hold harmless the Client from and against any and all claims, damages, losses, costs, and expenses (including reasonable attorneys' fees) arising out of or resulting from the Company's negligent acts or omissions in the performance of this Agreement.",
				category="indemnification",
				risk_level="Low",
				source_document="Standard Service Agreement Template",
				effectiveness_score=0.85,
				created_at=datetime.now(),
			),
			PrecedentClause(
				id=str(uuid.uuid4()),
				text="Client agrees to indemnify, defend, and hold harmless Company from any and all claims, damages, losses, and expenses, including attorney fees, arising from Client's use of the services, regardless of the cause of action or legal theory involved.",
				category="indemnification",
				risk_level="High",
				source_document="Vendor Service Agreement",
				effectiveness_score=0.95,
				created_at=datetime.now(),
			),
			PrecedentClause(
				id=str(uuid.uuid4()),
				text="Each party's liability under this Agreement shall be limited to direct damages only and shall not exceed the total amount paid under this Agreement in the twelve (12) months preceding the claim.",
				category="liability_limitation",
				risk_level="Medium",
				source_document="Software License Agreement",
				effectiveness_score=0.78,
				created_at=datetime.now(),
			),
			# Termination Clauses
			PrecedentClause(
				id=str(uuid.uuid4()),
				text="Either party may terminate this Agreement at any time, with or without cause, by providing thirty (30) days written notice to the other party.",
				category="termination",
				risk_level="Low",
				source_document="Consulting Agreement",
				effectiveness_score=0.82,
				created_at=datetime.now(),
			),
			PrecedentClause(
				id=str(uuid.uuid4()),
				text="This Agreement may be terminated immediately by Company at its sole discretion without notice or cause. Upon termination, Client shall immediately cease all use of services and pay all outstanding fees.",
				category="termination",
				risk_level="High",
				source_document="SaaS Terms of Service",
				effectiveness_score=0.92,
				created_at=datetime.now(),
			),
			# Payment and Financial Clauses
			PrecedentClause(
				id=str(uuid.uuid4()),
				text="Payment terms are Net 30 days from invoice date. Late payments shall accrue interest at the rate of 1.5% per month or the maximum rate permitted by law, whichever is less.",
				category="payment",
				risk_level="Low",
				source_document="Professional Services Agreement",
				effectiveness_score=0.75,
				created_at=datetime.now(),
			),
			PrecedentClause(
				id=str(uuid.uuid4()),
				text="All fees are non-refundable and must be paid in advance. Company reserves the right to change pricing at any time without notice. Failure to pay within 5 days results in immediate service suspension.",
				category="payment",
				risk_level="High",
				source_document="Software Subscription Agreement",
				effectiveness_score=0.88,
				created_at=datetime.now(),
			),
			# Intellectual Property Clauses
			PrecedentClause(
				id=str(uuid.uuid4()),
				text="Each party retains ownership of its pre-existing intellectual property. Any work product created jointly shall be owned equally by both parties.",
				category="intellectual_property",
				risk_level="Low",
				source_document="Joint Development Agreement",
				effectiveness_score=0.80,
				created_at=datetime.now(),
			),
			PrecedentClause(
				id=str(uuid.uuid4()),
				text="Client hereby assigns to Company all right, title, and interest in and to any intellectual property, including but not limited to ideas, concepts, processes, and discoveries, developed during the term of this Agreement.",
				category="intellectual_property",
				risk_level="High",
				source_document="Work for Hire Agreement",
				effectiveness_score=0.90,
				created_at=datetime.now(),
			),
			# Confidentiality Clauses
			PrecedentClause(
				id=str(uuid.uuid4()),
				text="Both parties agree to maintain the confidentiality of any proprietary information disclosed during the term of this Agreement and for a period of three (3) years thereafter.",
				category="confidentiality",
				risk_level="Low",
				source_document="Mutual Non-Disclosure Agreement",
				effectiveness_score=0.83,
				created_at=datetime.now(),
			),
			PrecedentClause(
				id=str(uuid.uuid4()),
				text="Recipient acknowledges that any breach of confidentiality may cause irreparable harm and agrees that Discloser shall be entitled to seek injunctive relief and monetary damages without limitation.",
				category="confidentiality",
				risk_level="Medium",
				source_document="Unilateral NDA",
				effectiveness_score=0.87,
				created_at=datetime.now(),
			),
			# Warranty and Disclaimer Clauses
			PrecedentClause(
				id=str(uuid.uuid4()),
				text="Company warrants that services will be performed in a professional and workmanlike manner in accordance with industry standards. This warranty is exclusive and in lieu of all other warranties.",
				category="warranty",
				risk_level="Low",
				source_document="Service Provider Agreement",
				effectiveness_score=0.76,
				created_at=datetime.now(),
			),
			PrecedentClause(
				id=str(uuid.uuid4()),
				text="SERVICES ARE PROVIDED 'AS IS' WITHOUT WARRANTY OF ANY KIND. COMPANY DISCLAIMS ALL WARRANTIES, EXPRESS OR IMPLIED, INCLUDING MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.",
				category="warranty",
				risk_level="High",
				source_document="Software License Terms",
				effectiveness_score=0.94,
				created_at=datetime.now(),
			),
			# Governing Law and Dispute Resolution
			PrecedentClause(
				id=str(uuid.uuid4()),
				text="This Agreement shall be governed by the laws of [State] without regard to conflict of law principles. Any disputes shall be resolved through binding arbitration in [City, State].",
				category="dispute_resolution",
				risk_level="Medium",
				source_document="Commercial Contract Template",
				effectiveness_score=0.81,
				created_at=datetime.now(),
			),
			PrecedentClause(
				id=str(uuid.uuid4()),
				text="Client waives the right to trial by jury and class action lawsuits. All disputes must be resolved individually through binding arbitration with costs borne by the losing party.",
				category="dispute_resolution",
				risk_level="High",
				source_document="Consumer Service Agreement",
				effectiveness_score=0.89,
				created_at=datetime.now(),
			),
			# Force Majeure Clauses
			PrecedentClause(
				id=str(uuid.uuid4()),
				text="Neither party shall be liable for any failure or delay in performance due to circumstances beyond its reasonable control, including acts of God, natural disasters, or government actions.",
				category="force_majeure",
				risk_level="Low",
				source_document="Supply Agreement",
				effectiveness_score=0.77,
				created_at=datetime.now(),
			),
			# Data and Privacy Clauses
			PrecedentClause(
				id=str(uuid.uuid4()),
				text="Company will process personal data in accordance with applicable privacy laws and will implement appropriate technical and organizational measures to protect such data.",
				category="data_privacy",
				risk_level="Low",
				source_document="Data Processing Agreement",
				effectiveness_score=0.84,
				created_at=datetime.now(),
			),
			PrecedentClause(
				id=str(uuid.uuid4()),
				text="Client grants Company unlimited rights to collect, use, and share any data provided, including personal information, for any business purpose without restriction or compensation.",
				category="data_privacy",
				risk_level="High",
				source_document="Data Collection Terms",
				effectiveness_score=0.91,
				created_at=datetime.now(),
			),
		]

		return sample_clauses

	def seed_database(self, reset_existing: bool = False) -> None:
		"""
		Seed the vector database with sample precedent clauses.

		Args:
		    reset_existing: If True, reset the existing collection before seeding
		"""
		try:
			if reset_existing:
				logger.info("Resetting existing vector store collection")
				self.vector_store.reset_collection()

			# Check if database already has data
			stats = self.vector_store.get_collection_stats()
			if stats["total_clauses"] > 0 and not reset_existing:
				logger.info(f"Database already contains {stats['total_clauses']} clauses. Skipping seeding.")
				return

			# Get sample clauses
			sample_clauses = self.get_sample_precedent_clauses()

			# Add clauses to vector store
			logger.info(f"Seeding database with {len(sample_clauses)} sample precedent clauses")
			self.vector_store.add_precedent_clauses(sample_clauses)

			# Log statistics
			final_stats = self.vector_store.get_collection_stats()
			logger.info(f"Database seeding completed. Total clauses: {final_stats['total_clauses']}")
			logger.info(f"Categories: {final_stats['categories']}")
			logger.info(f"Risk levels: {final_stats['risk_levels']}")

		except Exception as e:
			logger.error(f"Failed to seed database: {e!s}")
			raise VectorStoreError(f"Database seeding failed: {e!s}")

	def add_custom_clauses(self, clauses: List[dict]) -> None:
		"""
		Add custom precedent clauses to the database.

		Args:
		    clauses: List of clause dictionaries with required fields
		"""
		try:
			precedent_clauses = []
			for clause_data in clauses:
				clause = PrecedentClause(
					id=clause_data.get("id", str(uuid.uuid4())),
					text=clause_data["text"],
					category=clause_data["category"],
					risk_level=clause_data["risk_level"],
					source_document=clause_data.get("source_document", "Custom"),
					effectiveness_score=clause_data.get("effectiveness_score", 0.5),
					created_at=datetime.now(),
				)
				precedent_clauses.append(clause)

			self.vector_store.add_precedent_clauses(precedent_clauses)
			logger.info(f"Added {len(precedent_clauses)} custom precedent clauses")

		except Exception as e:
			logger.error(f"Failed to add custom clauses: {e!s}")
			raise VectorStoreError(f"Failed to add custom clauses: {e!s}")


def get_database_seeder(vector_store: VectorStoreService = None) -> DatabaseSeeder:
	"""Get a database seeder instance."""
	if vector_store is None:
		from .vector_store import get_vector_store_service

		vector_store = get_vector_store_service()

	return DatabaseSeeder(vector_store)
