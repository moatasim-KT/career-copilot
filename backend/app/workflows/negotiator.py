"""
Negotiator Node for Contract Analysis Workflow

This module implements the negotiator node, responsible for generating redline
suggestions and alternative language for identified risky clauses.
"""

import json
from typing import Any, Dict, List, Literal, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

from ..core.ai_manager import ModelType, get_ai_manager
from ..core.langsmith_integration import trace_ai_operation
from .state import ContractAnalysisState, RedlineSuggestion, RiskLevel, RiskyClause, WorkflowStatus, add_warning, update_state_status


def _validate_risk_mitigation(redline_suggestion: RedlineSuggestion) -> bool:
	"""
	Validate if a redline suggestion effectively mitigates the identified risk.

	Args:
	    redline_suggestion: The redline suggestion to validate

	Returns:
	    bool: True if the redline mitigates risk, False otherwise
	"""
	# Simple validation logic - in a real implementation, this could be more sophisticated
	original = redline_suggestion["original_clause"].lower()
	suggested = redline_suggestion["suggested_redline"].lower()

	# If no change is recommended, consider it as not mitigating risk
	if suggested == "no change recommended":
		return False

	# Check for common risk mitigation patterns
	risk_mitigation_indicators = [
		"limited to",
		"except for",
		"excluding",
		"provided that",
		"subject to",
		"with the exception of",
		"solely",
		"only",
		"reasonable",
		"material",
		"written notice",
		"prior approval",
	]

	# If the suggested text contains risk mitigation language that wasn't in original
	for indicator in risk_mitigation_indicators:
		if indicator in suggested and indicator not in original:
			return True

	# If the suggested text is significantly different (indicating substantial changes)
	if len(suggested) > len(original) * 1.2:  # 20% longer suggests additions
		return True

	return False


class ClauseNegotiationOutput(BaseModel):
	"""
	Represents the output structure for a single clause negotiation.
	"""

	original_clause: str = Field(description="The original text of the risky clause.")
	suggested_redline: str = Field(
		description="The suggested alternative language or redline for the clause. If no change is recommended, this should be 'No change recommended'."
	)
	change_rationale: str = Field(description="Explanation for the suggested change or why no change is recommended.")
	risk_mitigated: bool = Field(description="True if the suggested redline mitigates the identified risk, False otherwise.")
	risk_level_after_redline: Optional[RiskLevel] = Field(
		default=None,
		description="The estimated risk level of the clause after applying the suggested redline. Only applicable if risk_mitigated is True.",
	)


class NegotiationOutput(BaseModel):
	"""
	Represents the overall output structure for the negotiator node.
	"""

	negotiated_clauses: List[ClauseNegotiationOutput] = Field(description="A list of negotiation outputs for each risky clause.")


def _build_negotiation_prompt(risky_clauses: List[Dict]) -> str:
	"""Build the negotiation prompt for AI analysis."""
	clauses_json = json.dumps(risky_clauses, indent=2)

	return f"""You are an expert legal counsel specializing in contract negotiation. 
Your task is to review identified risky clauses in a contract and propose 
redline suggestions or alternative language to mitigate the risks. 
For each risky clause, you must provide an original clause, a suggested redline, 
a rationale for the change, and indicate if the risk is mitigated.

If no change is recommended, state 'No change recommended' in the suggested_redline field 
and provide a clear explanation in the change_rationale.

The identified risky clauses are as follows:
{clauses_json}

Provide your output in the following JSON format:
{{
  "negotiated_clauses": [
    {{
      "original_clause": "exact text of the risky clause",
      "suggested_redline": "suggested alternative language or 'No change recommended'",
      "change_rationale": "explanation for the suggested change",
      "risk_mitigated": true/false,
      "risk_level_after_redline": "Low/Medium/High" (if risk_mitigated is true)
    }}
  ]
}}

IMPORTANT: Respond with ONLY valid JSON in the exact format above."""


def _parse_negotiation_response(response_content: str) -> Dict:
	"""Parse the negotiation response from AI."""
	import json

	try:
		# Clean up response if it's wrapped in markdown
		response_content = response_content.strip()
		if response_content.startswith("```json"):
			start = response_content.find("```json") + 7
			end = response_content.find("```", start)
			if end != -1:
				response_content = response_content[start:end].strip()
		elif response_content.startswith("```"):
			start = response_content.find("```") + 3
			end = response_content.find("```", start)
			if end != -1:
				response_content = response_content[start:end].strip()

		return json.loads(response_content)
	except json.JSONDecodeError as e:
		raise ValueError(f"Failed to parse negotiation response: {e}")


def create_negotiator_node() -> callable:
	"""
	Creates the negotiator node function for the LangGraph workflow.

	Returns:
	    callable: The negotiator node function.
	"""
	ai_manager = get_ai_manager()

	@trace_ai_operation("contract_negotiation", "chain")
	async def negotiator_node(state: ContractAnalysisState) -> ContractAnalysisState:
		"""
		Negotiator node function.

		Args:
		    state: The current ContractAnalysisState.

		Returns:
		    ContractAnalysisState: The updated state with suggested redlines.
		"""
		state = update_state_status(state, WorkflowStatus.NEGOTIATING, "negotiator")
		risky_clauses: List[RiskyClause] = state.get("risky_clauses", [])
		suggested_redlines: List[RedlineSuggestion] = []

		if not risky_clauses:
			state = add_warning(state, "No risky clauses found for negotiation.")
			state["suggested_redlines"] = []
			return state

		try:
			# Convert risky clauses to a format suitable for the AI prompt
			risky_clauses_for_ai = [
				{
					"clause_text": clause["clause_text"],
					"risk_explanation": clause["risk_explanation"],
					"risk_level": clause["risk_level"].value,
					"clause_index": clause["clause_index"],
				}
				for clause in risky_clauses
			]

			# Build negotiation prompt
			negotiation_prompt = _build_negotiation_prompt(risky_clauses_for_ai)

			# Use AI manager for negotiation with fallback
			result = await ai_manager.analyze_with_fallback(model_type=ModelType.REDLINE_GENERATION, prompt=negotiation_prompt, criteria="confidence")

			# Parse the response
			negotiation_results = _parse_negotiation_response(result.content)

			for result in negotiation_results["negotiated_clauses"]:
				# Find the matching risky clause
				matching_clause = None
				for clause in risky_clauses:
					if clause["clause_text"] == result["original_clause"]:
						matching_clause = clause
						break

				if matching_clause is None:
					state = add_warning(
						state, f"Original clause '{result['original_clause']}' not found in risky clauses. Skipping redline suggestion."
					)
					continue

				redline_suggestion = RedlineSuggestion(
					original_clause=result["original_clause"],
					suggested_redline=result["suggested_redline"],
					risk_explanation=matching_clause["risk_explanation"],
					clause_index=matching_clause["clause_index"],
					change_rationale=result["change_rationale"],
				)
				suggested_redlines.append(redline_suggestion)

			# Validate risk mitigation for generated redlines
			validated_redlines = []
			for redline in suggested_redlines:
				# Add risk mitigation validation
				is_risk_mitigated = _validate_risk_mitigation(redline)
				redline["risk_mitigated"] = is_risk_mitigated
				validated_redlines.append(redline)

			state["suggested_redlines"] = validated_redlines
			state = update_state_status(state, WorkflowStatus.NEGOTIATING, "negotiator", f"Generated {len(validated_redlines)} redline suggestions.")

		except Exception as e:
			error_msg = f"Negotiator node failed: {e!s}"
			state = update_state_status(state, WorkflowStatus.FAILED, "negotiator", error_msg)
			state["suggested_redlines"] = []  # Ensure redlines are empty on failure

		return state

	return negotiator_node
