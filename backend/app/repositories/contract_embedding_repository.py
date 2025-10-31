"""
Repository for managing contract embeddings in the database.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from ..core.logging import get_logger
from ..models.database_models import ContractEmbedding, SimilaritySearchLog, ContractAnalysis
from .base_repository import BaseRepository

logger = get_logger(__name__)


class ContractEmbeddingRepository(BaseRepository[ContractEmbedding]):
	"""Repository for contract embedding operations."""

	def __init__(self, db: Session):
		super().__init__(ContractEmbedding, db)

	async def create_embedding_record(
		self,
		contract_analysis_id: UUID,
		embedding_id: str,
		chunk_index: int,
		chunk_text: str,
		chunk_size: int,
		total_chunks: int,
		embedding_model: str = "text-embedding-ada-002",
		processing_time_ms: Optional[float] = None,
		contract_type: Optional[str] = None,
		risk_level: Optional[str] = None,
		jurisdiction: Optional[str] = None,
		contract_category: Optional[str] = None,
		parties: Optional[List[str]] = None,
		key_terms: Optional[List[str]] = None,
		metadata: Optional[Dict[str, Any]] = None,
	) -> ContractEmbedding:
		"""Create a new contract embedding record."""
		try:
			embedding_record = ContractEmbedding(
				contract_analysis_id=contract_analysis_id,
				embedding_id=embedding_id,
				chunk_index=chunk_index,
				chunk_text=chunk_text,
				chunk_size=chunk_size,
				total_chunks=total_chunks,
				embedding_model=embedding_model,
				processing_time_ms=processing_time_ms,
				contract_type=contract_type,
				risk_level=risk_level,
				jurisdiction=jurisdiction,
				contract_category=contract_category,
				parties=parties or [],
				key_terms=key_terms or [],
				additional_metadata=metadata or {},
			)

			return await self.create(embedding_record)

		except Exception as e:
			logger.error(f"Failed to create embedding record: {e}")
			raise

	async def get_embeddings_by_contract(self, contract_analysis_id: UUID) -> List[ContractEmbedding]:
		"""Get all embeddings for a specific job application tracking."""
		try:
			return await self.get_multi(filters={"contract_analysis_id": contract_analysis_id}, order_by="chunk_index")

		except Exception as e:
			logger.error(f"Failed to get embeddings for contract {contract_analysis_id}: {e}")
			raise

	async def get_embedding_by_id(self, embedding_id: str) -> Optional[ContractEmbedding]:
		"""Get embedding by ChromaDB embedding ID."""
		try:
			return await self.get_by_field("embedding_id", embedding_id)

		except Exception as e:
			logger.error(f"Failed to get embedding {embedding_id}: {e}")
			raise

	async def delete_embeddings_by_contract(self, contract_analysis_id: UUID) -> int:
		"""Delete all embeddings for a specific job application tracking."""
		try:
			embeddings = await self.get_embeddings_by_contract(contract_analysis_id)

			for embedding in embeddings:
				await self.delete(embedding.id)

			logger.info(f"Deleted {len(embeddings)} embeddings for contract {contract_analysis_id}")
			return len(embeddings)

		except Exception as e:
			logger.error(f"Failed to delete embeddings for contract {contract_analysis_id}: {e}")
			raise

	async def get_embeddings_by_type(self, contract_type: str, limit: int = 100) -> List[ContractEmbedding]:
		"""Get embeddings by contract type."""
		try:
			return await self.get_multi(filters={"contract_type": contract_type}, limit=limit, order_by="created_at")

		except Exception as e:
			logger.error(f"Failed to get embeddings by type {contract_type}: {e}")
			raise

	async def get_embeddings_by_risk_level(self, risk_level: str, limit: int = 100) -> List[ContractEmbedding]:
		"""Get embeddings by risk level."""
		try:
			return await self.get_multi(filters={"risk_level": risk_level}, limit=limit, order_by="created_at")

		except Exception as e:
			logger.error(f"Failed to get embeddings by risk level {risk_level}: {e}")
			raise

	async def get_embeddings_by_jurisdiction(self, jurisdiction: str, limit: int = 100) -> List[ContractEmbedding]:
		"""Get embeddings by jurisdiction."""
		try:
			return await self.get_multi(filters={"jurisdiction": jurisdiction}, limit=limit, order_by="created_at")

		except Exception as e:
			logger.error(f"Failed to get embeddings by jurisdiction {jurisdiction}: {e}")
			raise

	async def search_embeddings(
		self,
		contract_types: Optional[List[str]] = None,
		risk_levels: Optional[List[str]] = None,
		jurisdictions: Optional[List[str]] = None,
		contract_categories: Optional[List[str]] = None,
		limit: int = 100,
		offset: int = 0,
	) -> List[ContractEmbedding]:
		"""Search embeddings with multiple filters."""
		try:
			query = self.db.query(ContractEmbedding)

			# Apply filters
			if contract_types:
				query = query.filter(ContractEmbedding.contract_type.in_(contract_types))

			if risk_levels:
				query = query.filter(ContractEmbedding.risk_level.in_(risk_levels))

			if jurisdictions:
				query = query.filter(ContractEmbedding.jurisdiction.in_(jurisdictions))

			if contract_categories:
				query = query.filter(ContractEmbedding.contract_category.in_(contract_categories))

			# Apply ordering, limit, and offset
			query = query.order_by(desc(ContractEmbedding.created_at))
			query = query.offset(offset).limit(limit)

			return query.all()

		except Exception as e:
			logger.error(f"Failed to search embeddings: {e}")
			raise

	async def get_embedding_statistics(self) -> Dict[str, Any]:
		"""Get statistics about stored embeddings."""
		try:
			# Total embeddings count
			total_embeddings = await self.count()

			# Unique contracts count
			unique_contracts = self.db.query(func.count(func.distinct(ContractEmbedding.contract_analysis_id))).scalar()

			# Average chunks per contract
			avg_chunks = 0.0
			if unique_contracts > 0:
				avg_chunks = total_embeddings / unique_contracts

			# Contract type distribution
			contract_type_stats = (
				self.db.query(ContractEmbedding.contract_type, func.count(ContractEmbedding.id).label("count"))
				.filter(ContractEmbedding.contract_type.isnot(None))
				.group_by(ContractEmbedding.contract_type)
				.all()
			)

			# Risk level distribution
			risk_level_stats = (
				self.db.query(ContractEmbedding.risk_level, func.count(ContractEmbedding.id).label("count"))
				.filter(ContractEmbedding.risk_level.isnot(None))
				.group_by(ContractEmbedding.risk_level)
				.all()
			)

			# Jurisdiction distribution
			jurisdiction_stats = (
				self.db.query(ContractEmbedding.jurisdiction, func.count(ContractEmbedding.id).label("count"))
				.filter(ContractEmbedding.jurisdiction.isnot(None))
				.group_by(ContractEmbedding.jurisdiction)
				.all()
			)

			# Average processing time
			avg_processing_time = (
				self.db.query(func.avg(ContractEmbedding.processing_time_ms)).filter(ContractEmbedding.processing_time_ms.isnot(None)).scalar() or 0.0
			)

			return {
				"total_embeddings": total_embeddings,
				"unique_contracts": unique_contracts,
				"average_chunks_per_contract": round(avg_chunks, 2),
				"average_processing_time_ms": round(float(avg_processing_time), 2),
				"contract_type_distribution": {stat.contract_type: stat.count for stat in contract_type_stats},
				"risk_level_distribution": {stat.risk_level: stat.count for stat in risk_level_stats},
				"jurisdiction_distribution": {stat.jurisdiction: stat.count for stat in jurisdiction_stats},
				"last_updated": datetime.now(timezone.utc).isoformat(),
			}

		except Exception as e:
			logger.error(f"Failed to get embedding statistics: {e}")
			raise

	async def cleanup_orphaned_embeddings(self) -> int:
		"""Clean up embeddings that no longer have associated contract analyses."""
		try:
			# Find embeddings without valid contract analyses
			orphaned_query = self.db.query(ContractEmbedding).filter(~ContractEmbedding.contract_analysis_id.in_(self.db.query(ContractAnalysis.id)))

			orphaned_embeddings = orphaned_query.all()

			# Delete orphaned embeddings
			for embedding in orphaned_embeddings:
				await self.delete(embedding.id)

			logger.info(f"Cleaned up {len(orphaned_embeddings)} orphaned embeddings")
			return len(orphaned_embeddings)

		except Exception as e:
			logger.error(f"Failed to cleanup orphaned embeddings: {e}")
			raise


class SimilaritySearchLogRepository(BaseRepository[SimilaritySearchLog]):
	"""Repository for similarity search log operations."""

	def __init__(self, db: Session):
		super().__init__(SimilaritySearchLog, db)

	async def log_search(
		self,
		user_id: Optional[UUID],
		query_text: str,
		search_type: str,
		similarity_threshold: float,
		max_results: int,
		results_count: int,
		search_time_ms: float,
		metadata_filters: Optional[Dict[str, Any]] = None,
		contract_types: Optional[List[str]] = None,
		risk_levels: Optional[List[str]] = None,
		jurisdictions: Optional[List[str]] = None,
		top_similarity_score: Optional[float] = None,
		embedding_time_ms: Optional[float] = None,
		session_id: Optional[str] = None,
		request_id: Optional[str] = None,
		ip_address: Optional[str] = None,
	) -> SimilaritySearchLog:
		"""Log a similarity search operation."""
		try:
			search_log = SimilaritySearchLog(
				user_id=user_id,
				query_text=query_text,
				search_type=search_type,
				similarity_threshold=similarity_threshold,
				max_results=max_results,
				results_count=results_count,
				search_time_ms=search_time_ms,
				metadata_filters=metadata_filters or {},
				contract_types=contract_types or [],
				risk_levels=risk_levels or [],
				jurisdictions=jurisdictions or [],
				top_similarity_score=top_similarity_score,
				embedding_time_ms=embedding_time_ms,
				session_id=session_id,
				request_id=request_id,
				ip_address=ip_address,
			)

			return await self.create(search_log)

		except Exception as e:
			logger.error(f"Failed to log similarity search: {e}")
			raise

	async def get_search_analytics(self, user_id: Optional[UUID] = None, search_type: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
		"""Get analytics for similarity searches."""
		try:
			# Base query
			query = self.db.query(SimilaritySearchLog)

			# Apply filters
			if user_id:
				query = query.filter(SimilaritySearchLog.user_id == user_id)

			if search_type:
				query = query.filter(SimilaritySearchLog.search_type == search_type)

			# Date filter
			cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
			query = query.filter(SimilaritySearchLog.created_at >= cutoff_date)

			searches = query.all()

			if not searches:
				return {
					"total_searches": 0,
					"average_search_time_ms": 0.0,
					"average_results_count": 0.0,
					"search_type_distribution": {},
					"performance_metrics": {},
				}

			# Calculate metrics
			total_searches = len(searches)
			avg_search_time = sum(s.search_time_ms for s in searches) / total_searches
			avg_results = sum(s.results_count for s in searches) / total_searches

			# Search type distribution
			search_type_dist = {}
			for search in searches:
				search_type_dist[search.search_type] = search_type_dist.get(search.search_type, 0) + 1

			# Performance metrics
			search_times = [s.search_time_ms for s in searches]
			performance_metrics = {
				"min_search_time_ms": min(search_times),
				"max_search_time_ms": max(search_times),
				"median_search_time_ms": sorted(search_times)[len(search_times) // 2],
				"p95_search_time_ms": sorted(search_times)[int(len(search_times) * 0.95)],
			}

			return {
				"total_searches": total_searches,
				"average_search_time_ms": round(avg_search_time, 2),
				"average_results_count": round(avg_results, 2),
				"search_type_distribution": search_type_dist,
				"performance_metrics": performance_metrics,
				"period_days": days,
				"generated_at": datetime.now(timezone.utc).isoformat(),
			}

		except Exception as e:
			logger.error(f"Failed to get search analytics: {e}")
			raise
