"""
Communicator Node for Contract Analysis Workflow

This module implements the communicator node, responsible for drafting professional
negotiation emails based on the analysis results and redline suggestions.
"""

import json
import re
from typing import Any, Dict, List, Optional

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from ..core.ai_manager import ModelType, get_ai_manager
from ..core.langsmith_integration import trace_ai_operation
from .state import ContractAnalysisState, RedlineSuggestion, WorkflowStatus, add_warning, update_state_status


class EmailTemplate:
	"""
	Email template system for consistent formatting of negotiation emails.
	"""

	# Base template for emails with redlines
	EMAIL_WITH_REDLINES_TEMPLATE = """Subject: Contract Review - Proposed Revisions for {contract_filename}

Dear [Counterparty Name],

I hope this email finds you well. I have completed my review of the {contract_filename} and would like to propose some revisions to address certain provisions that may present risks or require clarification.

{redlines_summary}

{detailed_redlines}

I believe these proposed changes will help ensure a more balanced agreement that protects both parties' interests. I would be happy to discuss these revisions at your convenience.

Please let me know if you have any questions or would like to schedule a call to review these items together.

Best regards,
[Your Name]
[Your Title]
[Your Contact Information]"""

	# Template for emails when no changes are needed
	EMAIL_NO_CHANGES_TEMPLATE = """Subject: Contract Review Complete - {contract_filename}

Dear [Counterparty Name],

I hope this email finds you well. I have completed my review of the {contract_filename} and am pleased to inform you that the contract appears to be well-drafted with no significant concerns requiring revision.

The contract terms appear balanced and appropriate for this type of agreement. I did not identify any provisions that would present material risks or require modification.

We can proceed with execution of the contract as currently drafted. Please let me know if you have any questions or if there are any other aspects you would like to discuss.

Best regards,
[Your Name]
[Your Title]
[Your Contact Information]"""

	@staticmethod
	def format_redlines_summary(redlines: List[RedlineSuggestion]) -> str:
		"""
		Create a summary of redlines for the email.

		Args:
		    redlines: List of redline suggestions

		Returns:
		    str: Formatted summary text
		"""
		if not redlines:
			return "Upon review, I found no provisions requiring revision."

		total_redlines = len(redlines)
		risk_levels = {}

		for redline in redlines:
			# Extract risk level from the redline (if available in risk_explanation)
			risk_explanation = redline.get("risk_explanation", "").lower()
			if "high risk" in risk_explanation or "high" in risk_explanation:
				risk_levels["high"] = risk_levels.get("high", 0) + 1
			elif "medium risk" in risk_explanation or "medium" in risk_explanation:
				risk_levels["medium"] = risk_levels.get("medium", 0) + 1
			else:
				risk_levels["low"] = risk_levels.get("low", 0) + 1

		summary = f"I have identified {total_redlines} provision{'s' if total_redlines != 1 else ''} that would benefit from revision"

		if risk_levels:
			risk_summary = []
			if risk_levels.get("high", 0) > 0:
				risk_summary.append(f"{risk_levels['high']} high-priority")
			if risk_levels.get("medium", 0) > 0:
				risk_summary.append(f"{risk_levels['medium']} medium-priority")
			if risk_levels.get("low", 0) > 0:
				risk_summary.append(f"{risk_levels['low']} low-priority")

			if risk_summary:
				summary += f" ({', '.join(risk_summary)} item{'s' if sum(risk_levels.values()) != 1 else ''})"

		summary += "."
		return summary

	@staticmethod
	def format_detailed_redlines(redlines: List[RedlineSuggestion]) -> str:
		"""
		Format detailed redline information for the email.

		Args:
		    redlines: List of redline suggestions

		Returns:
		    str: Formatted detailed redlines text
		"""
		if not redlines:
			return ""

		detailed_text = "PROPOSED REVISIONS:\n\n"

		for i, redline in enumerate(redlines, 1):
			detailed_text += f"{i}. "

			# Add change rationale if available
			if redline.get("change_rationale"):
				detailed_text += f"{redline['change_rationale']}\n\n"
			else:
				detailed_text += f"Risk: {redline.get('risk_explanation', 'Risk mitigation')}\n\n"

			# Handle "No change recommended" cases
			if redline["suggested_redline"].lower().strip() == "no change recommended":
				detailed_text += f'   Current Language: "{redline["original_clause"]}"\n'
				detailed_text += f"   Recommendation: No change recommended\n"
				detailed_text += f"   Rationale: {redline.get('change_rationale', 'Current language is acceptable')}\n\n"
			else:
				detailed_text += f'   Current Language: "{redline["original_clause"]}"\n'
				detailed_text += f'   Proposed Language: "{redline["suggested_redline"]}"\n\n'

		return detailed_text.strip()


class EmailDraftOutput(BaseModel):
	"""
	Represents the output structure for email draft generation.
	"""

	email_subject: str = Field(description="Professional email subject line")
	email_body: str = Field(description="Complete email body with professional formatting")
	tone_assessment: str = Field(description="Assessment of the email tone (e.g., 'professional', 'courteous', 'collaborative')")
	redlines_included: bool = Field(description="Whether the email includes redline suggestions")
	email_type: str = Field(description="Type of email: 'with_redlines' or 'no_changes'")


def validate_email_content(email_content: str) -> List[str]:
	"""
	Validate email content for professionalism and completeness.

	Args:
	    email_content: The email content to validate

	Returns:
	    List[str]: List of validation issues (empty if valid)
	"""
	issues = []

	# Check for basic email structure
	if "Subject:" not in email_content:
		issues.append("Email missing subject line")

	if "Dear" not in email_content and "Hello" not in email_content:
		issues.append("Email missing proper greeting")

	if "Best regards" not in email_content and "Sincerely" not in email_content and "Kind regards" not in email_content:
		issues.append("Email missing professional closing")

	# Check for placeholder text that should be replaced
	placeholders = ["[Counterparty Name]", "[Your Name]", "[Your Title]", "[Your Contact Information]"]
	for placeholder in placeholders:
		if placeholder in email_content:
			issues.append(f"Email contains unreplaced placeholder: {placeholder}")

	# Check for minimum length (professional emails should have substance)
	if len(email_content.strip()) < 200:
		issues.append("Email content appears too brief for professional communication")

	# Check for unprofessional language patterns
	unprofessional_patterns = [r"\b(gonna|wanna|gotta)\b", r"\b(hey|hi there)\b", r"!!!+", r"\b(awesome|cool|sweet)\b"]

	for pattern in unprofessional_patterns:
		if re.search(pattern, email_content, re.IGNORECASE):
			issues.append(f"Email contains potentially unprofessional language: {pattern}")

	return issues


def format_email_with_template(contract_filename: str, redlines: List[RedlineSuggestion], template_type: str = "auto") -> str:
	"""
	Format email using predefined templates.

	Args:
	    contract_filename: Name of the contract file
	    redlines: List of redline suggestions
	    template_type: Type of template to use ("auto", "with_redlines", "no_changes")

	Returns:
	    str: Formatted email content
	"""
	# Determine template type automatically if not specified
	if template_type == "auto":
		# Filter out "no change recommended" redlines for template selection
		actionable_redlines = [r for r in redlines if r["suggested_redline"].lower().strip() != "no change recommended"]
		template_type = "with_redlines" if actionable_redlines else "no_changes"

	if template_type == "no_changes" or not redlines:
		return EmailTemplate.EMAIL_NO_CHANGES_TEMPLATE.format(contract_filename=contract_filename)
	else:
		redlines_summary = EmailTemplate.format_redlines_summary(redlines)
		detailed_redlines = EmailTemplate.format_detailed_redlines(redlines)

		return EmailTemplate.EMAIL_WITH_REDLINES_TEMPLATE.format(
			contract_filename=contract_filename, redlines_summary=redlines_summary, detailed_redlines=detailed_redlines
		)


def _build_email_prompt(contract_filename: str, redlines: List[Dict]) -> str:
	"""Build the email generation prompt for AI analysis."""
	redlines_json = json.dumps(redlines, indent=2)

	return f"""You are a professional legal counsel drafting a negotiation email to a counterparty. 
Your task is to create a courteous, professional email that summarizes proposed contract revisions 
or confirms that no changes are needed.

Contract filename: {contract_filename}
Suggested redlines: {redlines_json}

Guidelines for the email:
1. Maintain a professional, courteous, and collaborative tone
2. Be clear and specific about proposed changes
3. Provide context for why changes are being suggested
4. If no actionable redlines exist, draft an email confirming the contract is acceptable
5. Use proper business email formatting
6. Include placeholders for names and contact information that can be customized

Generate a complete email draft in the following JSON format:
{{
  "email_subject": "Professional email subject line",
  "email_body": "Complete email body with professional formatting",
  "tone_assessment": "Assessment of the email tone (e.g., 'professional', 'courteous', 'collaborative')",
  "redlines_included": true/false,
  "email_type": "Type of email: 'with_redlines' or 'no_changes'"
}}

IMPORTANT: Respond with ONLY valid JSON in the exact format above."""


def _parse_email_response(response_content: str) -> Dict:
	"""Parse the email response from AI."""
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
		raise ValueError(f"Failed to parse email response: {e}")


def create_communicator_node() -> callable:
	"""
	Creates the communicator node function for the LangGraph workflow.

	Returns:
	    callable: The communicator node function.
	"""
	ai_manager = get_ai_manager()

	@trace_ai_operation("email_generation", "chain")
	async def communicator_node(state: ContractAnalysisState) -> ContractAnalysisState:
		"""
		Communicator node function.

		Args:
		    state: The current ContractAnalysisState.

		Returns:
		    ContractAnalysisState: The updated state with email draft.
		"""
		state = update_state_status(state, WorkflowStatus.COMMUNICATING, "communicator")

		contract_filename = state.get("contract_filename", "contract")
		suggested_redlines: List[RedlineSuggestion] = state.get("suggested_redlines", [])

		try:
			# Filter out "no change recommended" redlines for email generation
			actionable_redlines = [r for r in suggested_redlines if r["suggested_redline"].lower().strip() != "no change recommended"]

			# Determine if we should use AI or template-based approach
			use_ai = state.get("config", {}).get("use_ai_for_email", True)

			if use_ai:
				# Use AI manager to generate email
				redlines_for_ai = [
					{
						"original_clause": redline["original_clause"],
						"suggested_redline": redline["suggested_redline"],
						"risk_explanation": redline["risk_explanation"],
						"change_rationale": redline.get("change_rationale", ""),
					}
					for redline in suggested_redlines
				]

				# Build email generation prompt
				email_prompt = _build_email_prompt(contract_filename, redlines_for_ai)

				# Use AI manager for email generation
				result = await ai_manager.analyze_with_fallback(model_type=ModelType.EMAIL_DRAFTING, prompt=email_prompt, criteria="confidence")

				# Parse the response
				email_result = _parse_email_response(result.content)

				# Combine subject and body
				email_draft = f"{email_result['email_subject']}\n\n{email_result['email_body']}"

				# Validate the generated email
				validation_issues = validate_email_content(email_draft)
				if validation_issues:
					for issue in validation_issues:
						state = add_warning(state, f"Email validation issue: {issue}")

			else:
				# Use template-based approach
				email_draft = format_email_with_template(contract_filename=contract_filename, redlines=suggested_redlines, template_type="auto")

			state["email_draft"] = email_draft

			# Add success message
			if actionable_redlines:
				state = add_warning(
					state,
					f"Generated professional email draft with {len(actionable_redlines)} redline suggestion{'s' if len(actionable_redlines) != 1 else ''}",
				)
			else:
				state = add_warning(state, "Generated email draft confirming no changes needed")

		except Exception as e:
			error_msg = f"Communicator node failed: {e!s}"
			state = update_state_status(state, WorkflowStatus.FAILED, "communicator", error_msg)

			# Provide fallback email draft
			fallback_email = format_email_with_template(contract_filename=contract_filename, redlines=suggested_redlines, template_type="auto")
			state["email_draft"] = fallback_email
			state = add_warning(state, "Used fallback template due to LLM failure")

		return state

	return communicator_node


# Convenience function for standalone email generation
def generate_email_draft(
	contract_filename: str, redlines: List[RedlineSuggestion], llm: Optional[ChatOpenAI] = None, use_template: bool = False
) -> str:
	"""
	Generate an email draft outside of the workflow context.

	Args:
	    contract_filename: Name of the contract file
	    redlines: List of redline suggestions
	    llm: Optional language model for LLM-based generation
	    use_template: Whether to use template-based generation

	Returns:
	    str: Generated email draft
	"""
	if use_template or llm is None:
		return format_email_with_template(contract_filename=contract_filename, redlines=redlines, template_type="auto")
	else:
		# Create a temporary state for the communicator node
		temp_state = ContractAnalysisState(
			contract_text="",
			contract_filename=contract_filename,
			risky_clauses=[],
			overall_risk_score=None,
			suggested_redlines=redlines,
			email_draft="",
			precedent_context=[],
			status=WorkflowStatus.COMMUNICATING,
			current_node="communicator",
			processing_metadata={
				"start_time": None,
				"end_time": None,
				"processing_duration": None,
				"model_version": "1.0.0",
				"workflow_version": "1.0.0",
				"error_count": 0,
				"warnings": [],
			},
			errors=[],
			last_error=None,
			config={"use_llm_for_email": True},
		)

		communicator_func = create_communicator_node(llm)
		result_state = communicator_func(temp_state)

		return result_state["email_draft"]
