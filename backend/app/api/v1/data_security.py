"""
API endpoints for data compression and encryption management
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.data_migration_service import DataMigrationService
from app.services.crypto_service import crypto_service
from app.services.compression_service import compression_service
from app.core.config import settings

# NOTE: This file has been converted to use AsyncSession.
# Database queries need to be converted to async: await db.execute(select(...)) instead of db.query(...)

router = APIRouter(prefix="/data-security", tags=["data-security"])


@router.get("/status")
async def get_security_status(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
	"""Get current data security and compression status"""

	migration_service = DataMigrationService(db)
	status = migration_service.get_migration_status()

	return {
		"encryption_enabled": settings.ENCRYPT_FILES and settings.ENCRYPT_USER_DATA,
		"compression_enabled": settings.ENABLE_COMPRESSION,
		"migration_status": status,
		"settings": {
			"encrypt_files": settings.ENCRYPT_FILES,
			"encrypt_user_data": settings.ENCRYPT_USER_DATA,
			"enable_compression": settings.ENABLE_COMPRESSION,
			"auto_select_compression": settings.AUTO_SELECT_COMPRESSION,
			"compression_level": settings.COMPRESSION_LEVEL,
			"min_compression_size": settings.MIN_COMPRESSION_SIZE,
		},
	}


@router.post("/migrate/encryption")
async def migrate_to_encryption(
	background_tasks: BackgroundTasks, batch_size: int = 100, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
	"""Start migration to encrypt existing data"""

	if not settings.ENCRYPT_USER_DATA and not settings.ENCRYPT_FILES:
		raise HTTPException(status_code=400, detail="Encryption is not enabled in settings")

	migration_service = DataMigrationService(db)

	# Run migration in background
	def run_migration():
		user_stats = migration_service.migrate_user_profiles_to_encryption(batch_size)
		doc_stats = migration_service.migrate_documents_to_compression_encryption(batch_size // 2)

		# Log results (in production, you might want to store this in database)
		print(f"Encryption migration completed:")
		print(f"Users: {user_stats}")
		print(f"Documents: {doc_stats}")

	background_tasks.add_task(run_migration)

	return {
		"message": "Encryption migration started in background",
		"batch_size": batch_size,
		"estimated_time": "5-15 minutes depending on data size",
	}


@router.post("/migrate/compression")
async def migrate_to_compression(
	background_tasks: BackgroundTasks, batch_size: int = 100, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
	"""Start migration to compress existing data"""

	if not settings.ENABLE_COMPRESSION:
		raise HTTPException(status_code=400, detail="Compression is not enabled in settings")

	migration_service = DataMigrationService(db)

	# Run migration in background
	def run_migration():
		doc_stats = migration_service.migrate_documents_to_compression_encryption(batch_size)
		job_stats = migration_service.migrate_job_descriptions_to_compression(batch_size * 2)

		# Log results
		print(f"Compression migration completed:")
		print(f"Documents: {doc_stats}")
		print(f"Jobs: {job_stats}")

	background_tasks.add_task(run_migration)

	return {
		"message": "Compression migration started in background",
		"batch_size": batch_size,
		"estimated_time": "10-30 minutes depending on data size",
	}


@router.post("/rollback/encryption")
async def rollback_encryption(
	background_tasks: BackgroundTasks, batch_size: int = 100, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
	"""Rollback encryption migration (decrypt data back to plaintext)"""

	migration_service = DataMigrationService(db)

	# Run rollback in background
	def run_rollback():
		stats = migration_service.rollback_encryption_migration(batch_size)
		print(f"Encryption rollback completed: {stats}")

	background_tasks.add_task(run_rollback)

	return {
		"message": "Encryption rollback started in background",
		"batch_size": batch_size,
		"warning": "This will decrypt all encrypted data back to plaintext",
	}


@router.get("/test/encryption")
async def test_encryption(
	test_data: str = "Hello, World! This is a test of the encryption system.", current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
	"""Test encryption and decryption functionality"""

	try:
		# Test text encryption
		encrypted_text = crypto_service.encrypt_text(test_data)
		decrypted_text = crypto_service.decrypt_text(encrypted_text)

		# Test JSON encryption
		test_json = {"message": test_data, "timestamp": "2024-01-20T10:00:00Z"}
		encrypted_json = crypto_service.encrypt_json(test_json)
		decrypted_json = crypto_service.decrypt_json(encrypted_json)

		# Test file encryption
		test_file_data = test_data.encode()
		encrypted_file = crypto_service.encrypt_file(test_file_data)
		decrypted_file = crypto_service.decrypt_file(encrypted_file)

		return {
			"status": "success",
			"text_encryption": {
				"original": test_data,
				"encrypted_length": len(encrypted_text),
				"decrypted": decrypted_text,
				"match": test_data == decrypted_text,
			},
			"json_encryption": {
				"original": test_json,
				"encrypted_length": len(encrypted_json),
				"decrypted": decrypted_json,
				"match": test_json == decrypted_json,
			},
			"file_encryption": {
				"original_size": len(test_file_data),
				"encrypted_size": len(encrypted_file),
				"decrypted_size": len(decrypted_file),
				"match": test_file_data == decrypted_file,
			},
		}

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Encryption test failed: {e!s}")


@router.get("/test/compression")
async def test_compression(
	test_data: str = "This is a test string for compression. " * 100, current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
	"""Test compression and decompression functionality"""

	try:
		test_bytes = test_data.encode()

		# Test different compression algorithms
		results = {}

		from app.services.compression_service import CompressionType

		algorithms = [CompressionType.GZIP, CompressionType.ZLIB, CompressionType.BZ2, CompressionType.LZMA]

		for algorithm in algorithms:
			compressed_data, comp_type = compression_service.compress_data(test_bytes, algorithm)
			decompressed_data = compression_service.decompress_data(compressed_data, comp_type)
			stats = compression_service.get_compression_stats(test_bytes, compressed_data, comp_type)

			results[algorithm.value] = {
				"original_size": len(test_bytes),
				"compressed_size": len(compressed_data),
				"compression_ratio": stats["compression_ratio"],
				"space_saved_percent": stats["space_saved_percent"],
				"decompression_match": test_bytes == decompressed_data,
			}

		# Test automatic best compression selection
		best_compressed, best_type, best_stats = compression_service.find_best_compression(test_bytes)

		return {"status": "success", "algorithm_comparison": results, "best_compression": {"algorithm": best_type.value, "stats": best_stats}}

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Compression test failed: {e!s}")


@router.get("/analytics")
async def get_security_analytics(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
	"""Get analytics on data security and compression effectiveness"""

	migration_service = DataMigrationService(db)
	status = migration_service.get_migration_status()

	# Calculate additional metrics
	total_files = status["documents"]["total"]
	encrypted_files = status["documents"]["encrypted"]
	compressed_files = status["documents"]["compressed"]

	security_score = 0
	if total_files > 0:
		security_score = ((encrypted_files + compressed_files) / (total_files * 2)) * 100

	return {
		"security_overview": status,
		"security_score": round(security_score, 1),
		"recommendations": _generate_security_recommendations(status),
		"space_efficiency": {
			"total_space_saved": status["space_savings"],
			"average_compression_ratio": _calculate_average_compression_ratio(db),
			"most_compressible_types": _get_most_compressible_file_types(db),
		},
	}


def _generate_security_recommendations(status: Dict[str, Any]) -> list:
	"""Generate security recommendations based on current status"""
	recommendations = []

	docs = status["documents"]
	users = status["users"]

	if docs["encryption_percentage"] < 100:
		recommendations.append(
			{
				"type": "encryption",
				"priority": "high",
				"message": f"Only {docs['encryption_percentage']:.1f}% of documents are encrypted. Consider running encryption migration.",
			}
		)

	if docs["compression_percentage"] < 50:
		recommendations.append(
			{
				"type": "compression",
				"priority": "medium",
				"message": f"Only {docs['compression_percentage']:.1f}% of documents are compressed. Enable compression to save storage space.",
			}
		)

	if users["encryption_percentage"] < 100:
		recommendations.append(
			{
				"type": "user_data",
				"priority": "high",
				"message": f"Only {users['encryption_percentage']:.1f}% of user profiles are encrypted. Consider running user data encryption migration.",
			}
		)

	if status["space_savings"]["total_mb_saved"] > 100:
		recommendations.append(
			{
				"type": "success",
				"priority": "info",
				"message": f"Great! You've saved {status['space_savings']['total_mb_saved']} MB through compression.",
			}
		)

	return recommendations


def _calculate_average_compression_ratio(db: Session) -> float:
	"""Calculate average compression ratio across all compressed documents"""
	from sqlalchemy import select, text

	result = db.execute(
		text("""
        SELECT AVG(CAST(compression_ratio AS FLOAT)) as avg_ratio
        FROM documents 
        WHERE is_compressed = 'true' AND compression_ratio IS NOT NULL
    """)
	).scalar()

	return round(result or 0, 4)


def _get_most_compressible_file_types(db: Session) -> list:
	"""Get file types that compress best"""
	from sqlalchemy import text

	results = db.execute(
		text("""
        SELECT 
            mime_type,
            AVG(CAST(compression_ratio AS FLOAT)) as avg_compression_ratio,
            COUNT(*) as file_count
        FROM documents 
        WHERE is_compressed = 'true' AND compression_ratio IS NOT NULL
        GROUP BY mime_type
        HAVING COUNT(*) >= 2
        ORDER BY avg_compression_ratio DESC
        LIMIT 5
    """)
	).fetchall()

	return [{"mime_type": row[0], "average_compression_ratio": round(row[1], 4), "file_count": row[2]} for row in results]
