"""Job Description Parser Service - Stub"""

import logging

logger = logging.getLogger(__name__)


class JobDescriptionParserService:
	"""Temporary stub for JobDescriptionParserService"""

	def __init__(self):
		logger.info("JobDescriptionParserService initialized (stub)")

	async def parse(self, job_description: str):
		"""Parse job description"""
		return {"title": "Unknown", "requirements": [], "skills": [], "raw_text": job_description}
