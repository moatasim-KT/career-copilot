"""
Report generation service for creating analysis reports.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ..core.logging import get_logger

logger = get_logger(__name__)


class ReportGenerationService:
	"""Service for generating various types of reports."""

	def __init__(self):
		pass

	async def generate_analysis_report(self, analysis_data: Dict[str, Any], output_format: str = "pdf") -> Dict[str, Any]:
		"""Generate an analysis report."""
		try:
			logger.info(f"Generating analysis report in {output_format} format")

			# Extract key information from analysis data
			contract_name = analysis_data.get("contract_filename", "Unknown Contract")
			risk_score = analysis_data.get("risk_score", 0.0)
			risky_clauses = analysis_data.get("risky_clauses", [])
			recommendations = analysis_data.get("recommendations", [])

			# Generate report content
			report_content = {
				"title": f"Contract Analysis Report - {contract_name}",
				"generated_at": datetime.now(timezone.utc).isoformat(),
				"summary": {
					"contract_name": contract_name,
					"risk_score": risk_score,
					"total_risky_clauses": len(risky_clauses),
					"total_recommendations": len(recommendations),
				},
				"risk_assessment": {"overall_score": risk_score, "risk_level": self._get_risk_level(risk_score), "risky_clauses": risky_clauses},
				"recommendations": recommendations,
				"output_format": output_format,
			}

			# For now, return the structured data
			# In a real implementation, this would generate actual PDF/DOCX files
			if output_format == "pdf":
				report_content["file_path"] = f"/reports/{contract_name}_analysis.pdf"
			elif output_format == "docx":
				report_content["file_path"] = f"/reports/{contract_name}_analysis.docx"

			logger.info(f"Analysis report generated successfully for {contract_name}")
			return report_content

		except Exception as e:
			logger.error(f"Failed to generate analysis report: {e}", exc_info=True)
			raise

	async def generate_batch_report(self, batch_data: Dict[str, Any], output_format: str = "pdf") -> Dict[str, Any]:
		"""Generate a batch processing report."""
		try:
			logger.info(f"Generating batch report in {output_format} format")

			batch_id = batch_data.get("batch_id", "Unknown Batch")
			total_items = batch_data.get("total_items", 0)
			successful_items = batch_data.get("successful_items", 0)
			failed_items = batch_data.get("failed_items", 0)

			# Generate report content
			report_content = {
				"title": f"Batch Processing Report - {batch_id}",
				"generated_at": datetime.now(timezone.utc).isoformat(),
				"summary": {
					"batch_id": batch_id,
					"total_items": total_items,
					"successful_items": successful_items,
					"failed_items": failed_items,
					"success_rate": (successful_items / total_items * 100) if total_items > 0 else 0,
				},
				"results": batch_data.get("results", []),
				"errors": batch_data.get("errors", []),
				"output_format": output_format,
			}

			# For now, return the structured data
			if output_format == "pdf":
				report_content["file_path"] = f"/reports/batch_{batch_id}_report.pdf"
			elif output_format == "docx":
				report_content["file_path"] = f"/reports/batch_{batch_id}_report.docx"

			logger.info(f"Batch report generated successfully for {batch_id}")
			return report_content

		except Exception as e:
			logger.error(f"Failed to generate batch report: {e}", exc_info=True)
			raise

	def _get_risk_level(self, risk_score: float) -> str:
		"""Get risk level based on score."""
		if risk_score >= 8.0:
			return "Critical"
		elif risk_score >= 6.0:
			return "High"
		elif risk_score >= 4.0:
			return "Medium"
		else:
			return "Low"


# Global service instance
_report_generation_service: Optional[ReportGenerationService] = None


def get_report_generation_service() -> ReportGenerationService:
	"""Get the global report generation service instance."""
	global _report_generation_service
	if _report_generation_service is None:
		_report_generation_service = ReportGenerationService()
	return _report_generation_service


async def generate_analysis_report(analysis_result: Dict[str, Any], filename: str) -> Dict[str, Any]:
	"""Helper function to generate analysis report."""
	service = get_report_generation_service()
	return await service.generate_analysis_report(analysis_result)
