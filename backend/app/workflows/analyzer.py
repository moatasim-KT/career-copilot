"""
Analyzer Agent Node for Contract Risk Analysis

This module implements the analyzer node that uses AI models with RAG
to identify risky clauses in contracts and classify their risk levels.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from ..core.ai_manager import ModelType, get_ai_manager
from ..core.config import get_settings
from ..core.exceptions import ErrorCategory, ErrorSeverity, ExternalServiceError, ValidationError, WorkflowExecutionError
from ..core.langsmith_integration import trace_ai_operation
from ..services.mock_vector_store import MockPrecedentClause, get_mock_vector_store_service
from ..services.vector_store import PrecedentClause, get_vector_store_service
from .state import ContractAnalysisState, RiskLevel, RiskyClause, WorkflowStatus, update_state_status

logger = logging.getLogger(__name__)


class ClauseAnalysis(BaseModel):
	"""Structured output model for individual clause analysis."""

	clause_text: str = Field(description="The exact text of the risky clause")
	risk_explanation: str = Field(description="Detailed explanation of why this clause is risky")
	risk_level: RiskLevel = Field(description="Risk level classification: Low, Medium, or High")
	clause_index: int = Field(description="Index/position of the clause in the contract")
	legal_concerns: List[str] = Field(description="Specific legal concerns identified")
	business_impact: str = Field(description="Potential business impact of this clause")


class ContractRiskAnalysis(BaseModel):
	"""Structured output model for complete job application tracking."""

	risky_clauses: List[ClauseAnalysis] = Field(description="List of identified risky clauses")
	overall_risk_score: float = Field(description="Overall risk score from 0.0 to 10.0", ge=0.0, le=10.0)
	analysis_summary: str = Field(description="Summary of the overall analysis")
	recommendations: List[str] = Field(description="High-level recommendations for the contract")
	metadata: Dict[str, Any] = Field(default_factory=dict, description="Analysis metadata")


class ContractAnalyzer:
	"""Contract analyzer using AI models with RAG capabilities."""

	def __init__(self):
		self.settings = get_settings()
		self.ai_manager = get_ai_manager()

		# Try to use real vector store, fallback to mock if OpenAI API key is not available
		try:
			self.vector_store = get_vector_store_service()
			self.use_mock_store = False
		except Exception as e:
			logger.warning(f"Failed to initialize ChromaDB, using mock store: {e}")
			self.vector_store = get_mock_vector_store_service()
			self.use_mock_store = True

	@trace_ai_operation("contract_analysis", "chain")
	async def analyze_contract(self, contract_text: str, contract_filename: str) -> ContractRiskAnalysis:
		"""
		Analyze a contract for risky clauses using AI models with RAG.

		Args:
		    contract_text: The contract text to analyze
		    contract_filename: Name of the contract file for context

		Returns:
		    ContractRiskAnalysis: Structured analysis results
		"""
		try:
			# Step 1: Retrieve relevant precedent clauses
			precedent_context = await self._retrieve_precedent_context(contract_text)

			# Step 2: Prepare the analysis prompt
			analysis_prompt = self._build_analysis_prompt(contract_text, contract_filename, precedent_context)

			# Step 3: Use AI manager for analysis with fallback
			analysis_result = await self._perform_ai_analysis(analysis_prompt)

			# Step 4: Enhance with precedent references
			enhanced_result = self._enhance_with_precedent_references(analysis_result, precedent_context)

			logger.info(f"Contract analysis completed: {len(enhanced_result.risky_clauses)} risky clauses found")
			return enhanced_result

		except Exception as e:
			logger.error(f"Contract analysis failed: {e!s}")
			raise WorkflowExecutionError(f"Contract analysis failed: {e!s}", category=ErrorCategory.WORKFLOW, severity=ErrorSeverity.HIGH)

	async def _retrieve_precedent_context(self, contract_text: str, max_precedents: int = 10) -> List[PrecedentClause]:
		"""
		Retrieve relevant precedent clauses using semantic search.

		Args:
		    contract_text: Contract text to find similar precedents for
		    max_precedents: Maximum number of precedents to retrieve

		Returns:
		    List[PrecedentClause]: Relevant precedent clauses
		"""
		try:
			# Extract key phrases for better search
			key_phrases = self._extract_key_phrases(contract_text)

			# Search for similar clauses using the first key phrase
			if key_phrases:
				search_query = key_phrases[0]
				precedents = self.vector_store.search_similar_clauses(query_text=search_query, n_results=max_precedents)

				# Convert mock precedents to real precedents if using mock store
				if self.use_mock_store:
					real_precedents = []
					for mock_precedent in precedents:
						real_precedent = PrecedentClause(
							id=mock_precedent.id,
							text=mock_precedent.text,
							category=mock_precedent.category,
							risk_level=mock_precedent.risk_level,
							source_document=mock_precedent.source_document,
							effectiveness_score=mock_precedent.effectiveness_score,
							created_at=datetime.fromisoformat(mock_precedent.created_at),
						)
						real_precedents.append(real_precedent)
					precedents = real_precedents

				logger.debug(f"Retrieved {len(precedents)} precedent clauses")
				return precedents
			else:
				logger.debug("No key phrases extracted, skipping precedent search")
				return []

		except Exception as e:
			logger.warning(f"Failed to retrieve precedent context: {e!s}")
			return []  # Continue without precedents if retrieval fails

	def _extract_key_phrases(self, contract_text: str) -> List[str]:
		"""
		Extract key phrases from contract text for precedent search.

		Args:
		    contract_text: Contract text to extract phrases from

		Returns:
		    List[str]: Key phrases for search
		"""
		# Simple implementation - in production, could use more sophisticated NLP
		# Split into sentences and take those with legal keywords
		legal_keywords = [
			"liability",
			"indemnification",
			"termination",
			"breach",
			"damages",
			"warranty",
			"confidentiality",
			"intellectual property",
			"payment",
			"force majeure",
			"governing law",
			"dispute resolution",
			"arbitration",
		]

		sentences = contract_text.split(".")
		key_phrases = []

		for sentence in sentences:
			sentence = sentence.strip()
			if len(sentence) > 50 and any(keyword in sentence.lower() for keyword in legal_keywords):
				key_phrases.append(sentence[:200])  # Limit phrase length
				if len(key_phrases) >= 10:
					break

		# If no key phrases found, use first few sentences
		if not key_phrases:
			key_phrases = [s.strip() for s in sentences[:5] if len(s.strip()) > 50]

		return key_phrases

	async def _perform_ai_analysis(self, analysis_prompt: str) -> ContractRiskAnalysis:
		"""
		Perform AI analysis using the AI manager with fallback.

		Args:
		    analysis_prompt: The complete analysis prompt

		Returns:
		    ContractRiskAnalysis: Parsed analysis results
		"""
		try:
			# Prepare messages for LangChain
			messages = [SystemMessage(content=self._get_system_prompt()), HumanMessage(content=analysis_prompt)]

			# Use AI manager with fallback for job application tracking
			result = await self.ai_manager.analyze_with_fallback(
				model_type=ModelType.CONTRACT_ANALYSIS, prompt=analysis_prompt, criteria="confidence"
			)

			# Parse the response
			analysis_result = self._parse_analysis_response(result.content)

			# Add metadata from AI manager
			analysis_result.metadata = {
				"model_used": result.model_used,
				"confidence_score": result.confidence_score,
				"processing_time": result.processing_time,
				"token_usage": result.token_usage,
				"cost": result.cost,
			}

			return analysis_result

		except Exception as e:
			logger.error(f"AI analysis failed: {e!s}")
			raise WorkflowExecutionError(f"AI analysis failed: {e!s}", category=ErrorCategory.WORKFLOW, severity=ErrorSeverity.HIGH)

	def _get_system_prompt(self) -> str:
		"""Get the system prompt for job application tracking."""
		return """You are an expert legal analyst specializing in contract risk assessment. Your task is to analyze contracts and identify potentially risky clauses that could expose the client to legal or financial liability.

Key responsibilities:
1. Identify clauses that pose legal, financial, or operational risks
2. Classify risk levels as Low, Medium, or High based on potential impact
3. Provide clear explanations of why each clause is risky
4. Consider both legal precedents and business implications
5. Focus on actionable insights for legal professionals

Risk Level Guidelines:
- HIGH: Clauses that could result in significant financial loss, legal liability, or operational disruption
- MEDIUM: Clauses with moderate risk that should be reviewed and potentially modified
- LOW: Clauses with minor concerns that are worth noting but may be acceptable

IMPORTANT: You must respond with ONLY valid JSON matching this exact schema:
{
  "risky_clauses": [
    {
      "clause_text": "exact text of the risky clause",
      "risk_explanation": "detailed explanation of why this clause is risky",
      "risk_level": "Low/Medium/High",
      "clause_index": 1,
      "legal_concerns": ["list of specific legal concerns"],
      "business_impact": "potential business impact description"
    }
  ],
  "overall_risk_score": 5.5,
  "analysis_summary": "summary of the overall analysis",
  "recommendations": ["list of high-level recommendations"]
}

Do not include any text before or after the JSON. Be thorough but focus on genuinely risky clauses rather than standard legal language."""

	def _build_analysis_prompt(self, contract_text: str, contract_filename: str, precedents: List[PrecedentClause]) -> str:
		"""
		Build the analysis prompt with contract text and precedent context.

		Args:
		    contract_text: Contract text to analyze
		    contract_filename: Name of the contract file
		    precedents: Relevant precedent clauses

		Returns:
		    str: Complete analysis prompt
		"""
		precedent_context = ""
		if precedents:
			precedent_context = "\n\nRELEVANT PRECEDENT CLAUSES FOR REFERENCE:\n"
			for i, precedent in enumerate(precedents[:5], 1):  # Limit to top 5
				precedent_context += f"\n{i}. Risk Level: {precedent.risk_level}\n"
				precedent_context += f"   Category: {precedent.category}\n"
				precedent_context += f"   Text: {precedent.text[:300]}...\n"
				precedent_context += f"   Source: {precedent.source_document}\n"

		prompt = f"""Please analyze the following contract for risky clauses:

CONTRACT FILENAME: {contract_filename}

CONTRACT TEXT:
{contract_text}

{precedent_context}

Please provide a comprehensive risk analysis in JSON format. For each risky clause identified:

1. Extract the exact clause text
2. Explain the specific risks and legal concerns
3. Assign appropriate risk level (Low/Medium/High)
4. Describe potential business impact
5. Reference relevant precedents when applicable

Focus on clauses that could create liability, financial exposure, or operational constraints. Consider:
- Indemnification and liability provisions
- Termination and breach clauses
- Payment and penalty terms
- Intellectual property assignments
- Confidentiality obligations
- Governing law and dispute resolution
- Force majeure and risk allocation
- Warranty and representation clauses

Provide an overall risk score (0-10) and actionable recommendations.

IMPORTANT: Respond with ONLY valid JSON in this exact format:
{{
  "risky_clauses": [
    {{
      "clause_text": "exact text of the risky clause",
      "risk_explanation": "detailed explanation of why this clause is risky",
      "risk_level": "Low/Medium/High",
      "clause_index": 1,
      "legal_concerns": ["list of specific legal concerns"],
      "business_impact": "potential business impact description"
    }}
  ],
  "overall_risk_score": 5.5,
  "analysis_summary": "summary of the overall analysis",
  "recommendations": ["list of high-level recommendations"]
}}"""

		return prompt

	def _parse_analysis_response(self, response_content: str) -> ContractRiskAnalysis:
		"""
		Parse and validate the LLM response.

		Args:
		    response_content: JSON response from OpenAI

		Returns:
		    ContractRiskAnalysis: Parsed and validated analysis
		"""
		try:
			# Debug: Log the actual response content
			logger.info(f"AI Response content: {response_content[:500]}...")

			# Check if response is empty
			if not response_content or not response_content.strip():
				logger.error("Empty response from AI model")
				raise WorkflowExecutionError("Empty response from AI model", category=ErrorCategory.WORKFLOW, severity=ErrorSeverity.HIGH)

			# Try to extract JSON from response if it's wrapped in other text
			response_content = response_content.strip()
			if response_content.startswith("```json"):
				# Extract JSON from markdown code block
				start = response_content.find("```json") + 7
				end = response_content.find("```", start)
				if end != -1:
					response_content = response_content[start:end].strip()
			elif response_content.startswith("```"):
				# Extract JSON from generic code block
				start = response_content.find("```") + 3
				end = response_content.find("```", start)
				if end != -1:
					response_content = response_content[start:end].strip()

			# Parse JSON response
			response_data = json.loads(response_content)

			# Validate and create structured response
			analysis = ContractRiskAnalysis(**response_data)

			return analysis

		except json.JSONDecodeError as e:
			logger.error(f"Failed to parse JSON response: {e!s}")
			logger.error(f"Response content: {response_content}")
			raise WorkflowExecutionError(f"Invalid JSON response from analysis: {e!s}", category=ErrorCategory.WORKFLOW, severity=ErrorSeverity.HIGH)
		except Exception as e:
			logger.error(f"Failed to validate analysis response: {e!s}")
			raise WorkflowExecutionError(f"Invalid analysis response structure: {e!s}", category=ErrorCategory.WORKFLOW, severity=ErrorSeverity.HIGH)

	def _enhance_with_precedent_references(self, analysis: ContractRiskAnalysis, precedents: List[PrecedentClause]) -> ContractRiskAnalysis:
		"""
		Enhance analysis results with precedent references.

		Args:
		    analysis: Original analysis results
		    precedents: Available precedent clauses

		Returns:
		    ContractRiskAnalysis: Enhanced analysis with precedent references
		"""
		if not precedents:
			return analysis

		# Create a mapping of precedent text to precedent info for quick lookup
		precedent_map = {precedent.text[:100]: precedent for precedent in precedents}

		# For each risky clause, try to find the most relevant precedent
		for clause_analysis in analysis.risky_clauses:
			best_precedent = self._find_best_precedent_match(clause_analysis.clause_text, precedents)

			if best_precedent:
				# Add precedent reference to the clause analysis
				# Note: We'll store this in the precedent_reference field when converting to RiskyClause
				clause_analysis.risk_explanation += (
					f"\n\nRelevant Precedent: {best_precedent.source_document} - {best_precedent.category} (Risk: {best_precedent.risk_level})"
				)

		return analysis

	def _find_best_precedent_match(self, clause_text: str, precedents: List[PrecedentClause]) -> Optional[PrecedentClause]:
		"""
		Find the best matching precedent for a given clause.

		Args:
		    clause_text: Text of the risky clause
		    precedents: Available precedent clauses

		Returns:
		    Optional[PrecedentClause]: Best matching precedent or None
		"""
		if not precedents:
			return None

		# Simple similarity matching - in production, could use more sophisticated methods
		best_match = None
		best_score = 0

		clause_words = set(clause_text.lower().split())

		for precedent in precedents:
			precedent_words = set(precedent.text.lower().split())

			# Calculate Jaccard similarity
			intersection = len(clause_words.intersection(precedent_words))
			union = len(clause_words.union(precedent_words))

			if union > 0:
				similarity = intersection / union
				if similarity > best_score:
					best_score = similarity
					best_match = precedent

		# Only return if similarity is above threshold
		return best_match if best_score > 0.1 else None


async def analyzer_node(state: ContractAnalysisState) -> ContractAnalysisState:
	"""
	Analyzer node implementation for the LangGraph workflow.

	Args:
	    state: Current workflow state

	Returns:
	    ContractAnalysisState: Updated state with analysis results
	"""
	try:
		# Update status
		state = update_state_status(state, WorkflowStatus.ANALYZING, "analyzer")

		# Initialize analyzer
		analyzer = ContractAnalyzer()

		# Perform analysis
		analysis_result = await analyzer.analyze_contract(state["contract_text"], state["contract_filename"])

		# Convert analysis results to workflow state format
		risky_clauses = []
		precedent_context = []

		for i, clause_analysis in enumerate(analysis_result.risky_clauses):
			# Extract precedent reference if present
			precedent_ref = None
			risk_explanation = clause_analysis.risk_explanation

			if "Relevant Precedent:" in risk_explanation:
				parts = risk_explanation.split("Relevant Precedent:")
				risk_explanation = parts[0].strip()
				precedent_ref = parts[1].strip() if len(parts) > 1 else None

			risky_clause = RiskyClause(
				clause_text=clause_analysis.clause_text,
				risk_explanation=risk_explanation,
				risk_level=clause_analysis.risk_level,
				precedent_reference=precedent_ref,
				clause_index=clause_analysis.clause_index,
			)
			risky_clauses.append(risky_clause)

			# Add to precedent context for later use
			if precedent_ref:
				precedent_context.append(precedent_ref)

		# Update state with results
		state["risky_clauses"] = risky_clauses
		state["overall_risk_score"] = analysis_result.overall_risk_score
		state["precedent_context"] = precedent_context

		# Add analysis metadata
		state["processing_metadata"]["warnings"].append(f"Analysis completed: {len(risky_clauses)} risky clauses identified")

		logger.info(f"Analyzer node completed: {len(risky_clauses)} risky clauses found")

		return state

	except Exception as e:
		from ..core.exceptions import ErrorCategory, ErrorSeverity, ExternalServiceError, ValidationError, WorkflowExecutionError

		# Handle specific error types with proper error classification
		error_str = str(e).lower()

		if "openai" in error_str or "api" in error_str or "rate limit" in error_str:
			workflow_error = ExternalServiceError(f"AI service error during analysis: {e}", service_name="openai", cause=e)
		elif "timeout" in error_str or "timed out" in error_str:
			workflow_error = ExternalServiceError(f"Analysis timed out: {e}", service_name="openai", cause=e)
		elif "validation" in error_str or "invalid" in error_str:
			workflow_error = ValidationError(f"Input validation failed during analysis: {e}", cause=e)
		elif "memory" in error_str or "resource" in error_str:
			workflow_error = WorkflowExecutionError(
				f"Resource exhaustion during analysis: {e}", cause=e, category=ErrorCategory.WORKFLOW, severity=ErrorSeverity.HIGH
			)
		else:
			workflow_error = WorkflowExecutionError(f"Analyzer node failed: {e}", category=ErrorCategory.WORKFLOW, severity=ErrorSeverity.HIGH)

		error_msg = str(workflow_error)
		logger.error(f"Analyzer node failed: {error_msg}", exc_info=True)

		# Update state with error information
		state = update_state_status(state, WorkflowStatus.FAILED, "analyzer", error_msg)
		state["last_error"] = error_msg

		# Increment error count
		processing_metadata = state.get("processing_metadata", {})
		processing_metadata["error_count"] = processing_metadata.get("error_count", 0) + 1
		state["processing_metadata"] = processing_metadata

		return state
