"""
Enhanced Slack Service with comprehensive integration capabilities.
Provides robust Slack integration with notifications, interactive components, and bot commands.
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field, validator
from slack_sdk.errors import SlackApiError
from slack_sdk.signature import SignatureVerifier
from slack_sdk.web.async_client import AsyncWebClient

from ..core.exceptions import EmailServiceError, ErrorCategory, ErrorSeverity
from ..core.logging import get_logger

logger = get_logger(__name__)


class SlackMessageType(str, Enum):
	"""Slack message types"""

	TEXT = "text"
	BLOCKS = "blocks"
	ATTACHMENTS = "attachments"
	INTERACTIVE = "interactive"


class SlackPriority(str, Enum):
	"""Slack message priority levels"""

	CRITICAL = "critical"
	HIGH = "high"
	NORMAL = "normal"
	LOW = "low"


class SlackChannelType(str, Enum):
	"""Slack channel types"""

	PUBLIC = "public_channel"
	PRIVATE = "private_channel"
	DM = "im"
	GROUP_DM = "mpim"


@dataclass
class SlackRateLimiter:
	"""Slack API rate limiter"""

	requests: List[datetime] = field(default_factory=list)
	tier1_limit: int = 1  # 1 per minute for Tier 1
	tier2_limit: int = 20  # 20 per minute for Tier 2
	tier3_limit: int = 50  # 50 per minute for Tier 3
	tier4_limit: int = 100  # 100 per minute for Tier 4


class SlackConfiguration(BaseModel):
	"""Slack service configuration"""

	bot_token: str = Field(..., description="Slack bot token")
	app_token: Optional[str] = Field(None, description="Slack app token for socket mode")
	signing_secret: str = Field(..., description="Slack signing secret")
	verification_token: Optional[str] = Field(None, description="Slack verification token")

	# Rate limiting
	rate_limit_tier: int = Field(3, description="API rate limit tier (1-4)")
	max_retries: int = Field(3, description="Maximum retry attempts")
	retry_delay: float = Field(1.0, description="Base retry delay in seconds")

	# Features
	enable_interactive_components: bool = Field(True, description="Enable interactive components")
	enable_slash_commands: bool = Field(True, description="Enable slash commands")
	enable_events: bool = Field(True, description="Enable event subscriptions")
	enable_analytics: bool = Field(True, description="Enable analytics tracking")

	# Security
	enable_signature_verification: bool = Field(True, description="Enable request signature verification")
	allowed_channels: Optional[List[str]] = Field(None, description="Allowed channel IDs")
	allowed_users: Optional[List[str]] = Field(None, description="Allowed user IDs")

	@validator("rate_limit_tier")
	def validate_tier(cls, v):
		if not 1 <= v <= 4:
			raise ValueError("Rate limit tier must be between 1 and 4")
		return v


class SlackMessage(BaseModel):
	"""Enhanced Slack message model"""

	channel: str = Field(..., description="Channel ID or name")
	text: Optional[str] = Field(None, description="Message text")
	blocks: Optional[List[Dict[str, Any]]] = Field(None, description="Block Kit blocks")
	attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Message attachments")

	# Message options
	thread_ts: Optional[str] = Field(None, description="Thread timestamp for replies")
	reply_broadcast: bool = Field(False, description="Broadcast reply to channel")
	unfurl_links: bool = Field(True, description="Unfurl links")
	unfurl_media: bool = Field(True, description="Unfurl media")

	# Metadata
	priority: SlackPriority = Field(SlackPriority.NORMAL, description="Message priority")
	message_type: SlackMessageType = Field(SlackMessageType.TEXT, description="Message type")
	metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

	# Interactive components
	callback_id: Optional[str] = Field(None, description="Callback ID for interactive components")

	@validator("attachments")
	def validate_content(cls, v, values):
		# At least one content field must be provided
		if not any([values.get("text"), values.get("blocks"), v]):
			raise ValueError("At least one of text, blocks, or attachments must be provided")
		return v


class SlackUser(BaseModel):
	"""Slack user model"""

	id: str = Field(..., description="User ID")
	name: str = Field(..., description="Username")
	real_name: Optional[str] = Field(None, description="Real name")
	email: Optional[str] = Field(None, description="Email address")
	is_bot: bool = Field(False, description="Is bot user")
	is_admin: bool = Field(False, description="Is admin user")
	timezone: Optional[str] = Field(None, description="User timezone")


class SlackChannel(BaseModel):
	"""Slack channel model"""

	id: str = Field(..., description="Channel ID")
	name: str = Field(..., description="Channel name")
	is_channel: bool = Field(True, description="Is public channel")
	is_group: bool = Field(False, description="Is private channel")
	is_im: bool = Field(False, description="Is direct message")
	is_archived: bool = Field(False, description="Is archived")
	members: List[str] = Field(default_factory=list, description="Channel members")


class EnhancedSlackService:
	"""Enhanced Slack service with comprehensive integration capabilities"""

	def __init__(self, config: SlackConfiguration):
		self.config = config
		self.client = AsyncWebClient(token=config.bot_token)
		self.signature_verifier = SignatureVerifier(config.signing_secret) if config.enable_signature_verification else None

		# Rate limiting
		self.rate_limiter = SlackRateLimiter()
		self._set_rate_limits()

		# Caches
		self.user_cache: Dict[str, SlackUser] = {}
		self.channel_cache: Dict[str, SlackChannel] = {}

		# Analytics
		self.message_stats = {"total_sent": 0, "total_failed": 0, "by_channel": {}, "by_priority": {}, "by_type": {}}

		self.is_initialized = False

	def _set_rate_limits(self):
		"""Set rate limits based on tier"""
		limits = {1: 1, 2: 20, 3: 50, 4: 100}
		self.rate_limiter.tier1_limit = limits.get(self.config.rate_limit_tier, 50)

	async def initialize(self):
		"""Initialize the Slack service"""
		logger.info("Initializing Enhanced Slack service...")

		try:
			# Test authentication
			auth_response = await self.client.auth_test()
			logger.info(f"Slack authentication successful for bot: {auth_response['user']}")

			# Load initial data
			await self._load_channels()
			await self._load_users()

			self.is_initialized = True
			logger.info("Enhanced Slack service initialized successfully")

		except SlackApiError as e:
			logger.error(f"Slack authentication failed: {e}")
			raise EmailServiceError(f"Slack initialization failed: {e}")

	async def send_message(self, message: SlackMessage) -> Dict[str, Any]:
		"""Send a message to Slack"""
		if not self.is_initialized:
			await self.initialize()

		# Check rate limits
		if not await self._check_rate_limits():
			raise EmailServiceError("Slack API rate limit exceeded", category=ErrorCategory.RATE_LIMIT, severity=ErrorSeverity.HIGH)

		# Validate channel access
		if not await self._validate_channel_access(message.channel):
			raise EmailServiceError(
				f"Access denied to channel: {message.channel}", category=ErrorCategory.AUTHORIZATION, severity=ErrorSeverity.MEDIUM
			)

		try:
			# Send message with retry logic
			result = await self._send_with_retry(message)

			# Update analytics
			await self._update_message_stats(message, True)

			return {
				"success": True,
				"message_ts": result["ts"],
				"channel": result["channel"],
				"permalink": await self._get_permalink(result["channel"], result["ts"]),
				"timestamp": datetime.now().isoformat(),
			}

		except Exception as e:
			await self._update_message_stats(message, False)
			logger.error(f"Failed to send Slack message: {e}")
			raise EmailServiceError(f"Slack message delivery failed: {e}", category=ErrorCategory.EXTERNAL_SERVICE, severity=ErrorSeverity.HIGH)

	async def _send_with_retry(self, message: SlackMessage) -> Dict[str, Any]:
		"""Send message with retry logic"""
		last_exception = None

		for attempt in range(self.config.max_retries + 1):
			try:
				return await self._send_message_internal(message)

			except SlackApiError as e:
				last_exception = e

				# Check if error is retryable
				if e.response["error"] in ["rate_limited", "timeout", "internal_error"]:
					if attempt < self.config.max_retries:
						delay = self.config.retry_delay * (2**attempt)

						# Handle rate limiting with proper delay
						if e.response["error"] == "rate_limited":
							retry_after = e.response.get("headers", {}).get("Retry-After", delay)
							delay = max(delay, float(retry_after))

						logger.warning(f"Slack API error, retrying in {delay}s: {e}")
						await asyncio.sleep(delay)
						continue

				# Non-retryable error
				raise

			except Exception as e:
				last_exception = e
				if attempt < self.config.max_retries:
					delay = self.config.retry_delay * (2**attempt)
					logger.warning(f"Slack send attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
					await asyncio.sleep(delay)
				else:
					logger.error(f"All {self.config.max_retries + 1} Slack send attempts failed")

		raise last_exception

	async def _send_message_internal(self, message: SlackMessage) -> Dict[str, Any]:
		"""Internal Slack message sending logic"""
		# Prepare message payload
		payload = {"channel": message.channel, "unfurl_links": message.unfurl_links, "unfurl_media": message.unfurl_media}

		# Add content based on message type
		if message.text:
			payload["text"] = message.text

		if message.blocks:
			payload["blocks"] = message.blocks

		if message.attachments:
			payload["attachments"] = message.attachments

		# Add thread information
		if message.thread_ts:
			payload["thread_ts"] = message.thread_ts
			payload["reply_broadcast"] = message.reply_broadcast

		# Send message
		response = await self.client.chat_postMessage(**payload)

		# Update rate limiter
		await self._update_rate_limiter()

		return response.data

	async def send_contract_analysis_notification(
		self,
		channel: str,
		contract_name: str,
		risk_score: float,
		risk_level: str,
		analysis_summary: str,
		risky_clauses: List[str],
		recommendations: List[str],
	) -> Dict[str, Any]:
		"""Send job application tracking notification with rich formatting"""

		# Determine color based on risk score
		color = "#36a64f"  # Green
		if risk_score >= 7:
			color = "#ff0000"  # Red
		elif risk_score >= 4:
			color = "#ffaa00"  # Orange

		# Create rich message blocks
		blocks = [
			{"type": "header", "text": {"type": "plain_text", "text": f"📋 Contract Analysis Complete: {contract_name}"}},
			{
				"type": "section",
				"fields": [{"type": "mrkdwn", "text": f"*Risk Score:* {risk_score}/10"}, {"type": "mrkdwn", "text": f"*Risk Level:* {risk_level}"}],
			},
			{"type": "section", "text": {"type": "mrkdwn", "text": f"*Summary:* {analysis_summary}"}},
		]

		# Add risky clauses if any
		if risky_clauses:
			clause_text = "\n".join([f"• {clause}" for clause in risky_clauses[:5]])
			if len(risky_clauses) > 5:
				clause_text += f"\n... and {len(risky_clauses) - 5} more"

			blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*⚠️ Risky Clauses:*\n{clause_text}"}})

		# Add recommendations
		if recommendations:
			rec_text = "\n".join([f"• {rec}" for rec in recommendations[:3]])
			if len(recommendations) > 3:
				rec_text += f"\n... and {len(recommendations) - 3} more"

			blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*💡 Recommendations:*\n{rec_text}"}})

		# Add action buttons
		blocks.append(
			{
				"type": "actions",
				"elements": [
					{
						"type": "button",
						"text": {"type": "plain_text", "text": "View Full Report"},
						"style": "primary",
						"action_id": "view_report",
						"value": contract_name,
					},
					{"type": "button", "text": {"type": "plain_text", "text": "Download PDF"}, "action_id": "download_pdf", "value": contract_name},
				],
			}
		)

		message = SlackMessage(
			channel=channel,
			blocks=blocks,
			message_type=SlackMessageType.BLOCKS,
			priority=SlackPriority.HIGH if risk_score >= 7 else SlackPriority.NORMAL,
			callback_id="contract_analysis",
			metadata={"contract_name": contract_name, "risk_score": risk_score, "analysis_type": "contract_analysis"},
		)

		return await self.send_message(message)

	async def send_risk_alert(
		self, channel: str, contract_name: str, risk_score: float, urgent_clauses: List[str], alert_level: str = "HIGH"
	) -> Dict[str, Any]:
		"""Send high-priority risk alert"""

		emoji = "🚨" if alert_level == "CRITICAL" else "⚠️"

		blocks = [
			{"type": "header", "text": {"type": "plain_text", "text": f"{emoji} {alert_level} RISK ALERT"}},
			{"type": "section", "text": {"type": "mrkdwn", "text": f"*Contract:* {contract_name}\n*Risk Score:* {risk_score}/10"}},
			{
				"type": "section",
				"text": {"type": "mrkdwn", "text": "*Urgent Issues Detected:*\n" + "\n".join([f"• {clause}" for clause in urgent_clauses])},
			},
			{"type": "section", "text": {"type": "mrkdwn", "text": "*🔴 Immediate action required*"}},
			{
				"type": "actions",
				"elements": [
					{
						"type": "button",
						"text": {"type": "plain_text", "text": "Review Now"},
						"style": "danger",
						"action_id": "review_urgent",
						"value": contract_name,
					},
					{"type": "button", "text": {"type": "plain_text", "text": "Escalate"}, "action_id": "escalate_risk", "value": contract_name},
				],
			},
		]

		message = SlackMessage(
			channel=channel,
			blocks=blocks,
			message_type=SlackMessageType.BLOCKS,
			priority=SlackPriority.CRITICAL,
			callback_id="risk_alert",
			metadata={"contract_name": contract_name, "risk_score": risk_score, "alert_level": alert_level, "analysis_type": "risk_alert"},
		)

		return await self.send_message(message)

	async def upload_file_to_channel(
		self,
		channel: str,
		file_path: str,
		filename: str,
		title: Optional[str] = None,
		initial_comment: Optional[str] = None,
		thread_ts: Optional[str] = None,
	) -> Dict[str, Any]:
		"""Upload a file to a Slack channel with optional threading"""
		try:
			if not self.is_initialized:
				await self.initialize()

			# Prepare file upload payload
			with open(file_path, "rb") as file_content:
				files = {"file": (filename, file_content, "application/octet-stream")}

				data = {
					"channels": channel,
					"filename": filename,
					"title": title or filename,
					"initial_comment": initial_comment or f"📎 Uploaded: {filename}",
				}

				# Add thread timestamp if provided
				if thread_ts:
					data["thread_ts"] = thread_ts

				headers = {"Authorization": f"Bearer {self.config.bot_token}"}

				# Upload file using files.upload API
				async with httpx.AsyncClient(timeout=30.0) as client:
					response = await client.post("https://slack.com/api/files.upload", headers=headers, data=data, files=files)

					result = response.json()

					if result.get("ok"):
						file_info = result.get("file", {})
						return {
							"success": True,
							"file_id": file_info.get("id"),
							"file_url": file_info.get("url_private"),
							"permalink": file_info.get("permalink"),
							"timestamp": datetime.now().isoformat(),
						}
					else:
						raise SlackApiError(f"File upload failed: {result.get('error')}")

		except Exception as e:
			logger.error(f"Failed to upload file to Slack: {e}")
			raise EmailServiceError(f"Slack file upload failed: {e}", category=ErrorCategory.EXTERNAL_SERVICE, severity=ErrorSeverity.HIGH)

	async def upload_contract_file(
		self, channel: str, contract_file_path: str, contract_name: str, analysis_summary: Optional[str] = None, thread_ts: Optional[str] = None
	) -> Dict[str, Any]:
		"""Upload contract file with analysis context"""
		try:
			# Create initial comment with analysis context
			comment_parts = [f"📋 *Contract Upload: {contract_name}*"]

			if analysis_summary:
				comment_parts.append(f"📊 *Analysis Summary:* {analysis_summary}")

			comment_parts.extend(
				["", "Use the buttons below to interact with this contract:", "• 🔍 Analyze contract", "• 📄 Generate report", "• ⚠️ Check for risks"]
			)

			initial_comment = "\n".join(comment_parts)

			# Upload the file
			upload_result = await self.upload_file_to_channel(
				channel=channel,
				file_path=contract_file_path,
				filename=f"{contract_name}.pdf",
				title=f"Contract: {contract_name}",
				initial_comment=initial_comment,
				thread_ts=thread_ts,
			)

			# Send interactive message with action buttons
			if upload_result["success"]:
				await self.send_contract_action_buttons(
					channel=channel, contract_name=contract_name, file_id=upload_result["file_id"], thread_ts=thread_ts
				)

			return upload_result

		except Exception as e:
			logger.error(f"Failed to upload contract file: {e}")
			raise EmailServiceError(f"Contract file upload failed: {e}", category=ErrorCategory.EXTERNAL_SERVICE, severity=ErrorSeverity.HIGH)

	async def send_contract_action_buttons(self, channel: str, contract_name: str, file_id: str, thread_ts: Optional[str] = None) -> Dict[str, Any]:
		"""Send interactive action buttons for contract operations"""
		blocks = [
			{"type": "section", "text": {"type": "mrkdwn", "text": f"🔧 *Contract Actions for {contract_name}*\nChoose an action to perform:"}},
			{
				"type": "actions",
				"elements": [
					{
						"type": "button",
						"text": {"type": "plain_text", "text": "🔍 Analyze Contract"},
						"style": "primary",
						"action_id": "analyze_contract",
						"value": f"{contract_name}|{file_id}",
					},
					{
						"type": "button",
						"text": {"type": "plain_text", "text": "📄 Generate Report"},
						"action_id": "generate_report",
						"value": f"{contract_name}|{file_id}",
					},
					{
						"type": "button",
						"text": {"type": "plain_text", "text": "⚠️ Risk Assessment"},
						"style": "danger",
						"action_id": "risk_assessment",
						"value": f"{contract_name}|{file_id}",
					},
				],
			},
			{
				"type": "actions",
				"elements": [
					{
						"type": "button",
						"text": {"type": "plain_text", "text": "✅ Approve Contract"},
						"style": "primary",
						"action_id": "approve_contract",
						"value": f"{contract_name}|{file_id}",
						"confirm": {
							"title": {"type": "plain_text", "text": "Confirm Approval"},
							"text": {"type": "mrkdwn", "text": f"Are you sure you want to approve *{contract_name}*?"},
							"confirm": {"type": "plain_text", "text": "Yes, Approve"},
							"deny": {"type": "plain_text", "text": "Cancel"},
						},
					},
					{
						"type": "button",
						"text": {"type": "plain_text", "text": "❌ Reject Contract"},
						"style": "danger",
						"action_id": "reject_contract",
						"value": f"{contract_name}|{file_id}",
						"confirm": {
							"title": {"type": "plain_text", "text": "Confirm Rejection"},
							"text": {"type": "mrkdwn", "text": f"Are you sure you want to reject *{contract_name}*?"},
							"confirm": {"type": "plain_text", "text": "Yes, Reject"},
							"deny": {"type": "plain_text", "text": "Cancel"},
						},
					},
					{
						"type": "button",
						"text": {"type": "plain_text", "text": "📝 Request Changes"},
						"action_id": "request_changes",
						"value": f"{contract_name}|{file_id}",
					},
				],
			},
		]

		message = SlackMessage(
			channel=channel,
			blocks=blocks,
			message_type=SlackMessageType.BLOCKS,
			priority=SlackPriority.NORMAL,
			thread_ts=thread_ts,
			callback_id="contract_actions",
			metadata={"contract_name": contract_name, "file_id": file_id, "action_type": "contract_workflow"},
		)

		return await self.send_message(message)

	async def create_approval_workflow(
		self, channel: str, contract_name: str, approvers: List[str], approval_deadline: Optional[datetime] = None, thread_ts: Optional[str] = None
	) -> Dict[str, Any]:
		"""Create an approval workflow with multiple approvers"""
		try:
			# Create approval tracking
			workflow_id = f"approval_{datetime.now().timestamp()}"

			# Format approvers list
			approver_mentions = " ".join([f"<@{user_id}>" for user_id in approvers])

			# Create deadline text
			deadline_text = ""
			if approval_deadline:
				deadline_text = f"\n⏰ *Deadline:* {approval_deadline.strftime('%Y-%m-%d %H:%M')}"

			blocks = [
				{"type": "header", "text": {"type": "plain_text", "text": f"📋 Approval Required: {contract_name}"}},
				{
					"type": "section",
					"text": {
						"type": "mrkdwn",
						"text": f"*Approvers:* {approver_mentions}{deadline_text}\n\n*Status:* Pending approval from all parties",
					},
				},
				{
					"type": "section",
					"text": {"type": "mrkdwn", "text": "*Approval Progress:*\n" + "\n".join([f"⏳ <@{user_id}> - Pending" for user_id in approvers])},
				},
				{
					"type": "actions",
					"elements": [
						{
							"type": "button",
							"text": {"type": "plain_text", "text": "✅ Approve"},
							"style": "primary",
							"action_id": "workflow_approve",
							"value": f"{workflow_id}|{contract_name}",
						},
						{
							"type": "button",
							"text": {"type": "plain_text", "text": "❌ Reject"},
							"style": "danger",
							"action_id": "workflow_reject",
							"value": f"{workflow_id}|{contract_name}",
						},
						{
							"type": "button",
							"text": {"type": "plain_text", "text": "💬 Add Comment"},
							"action_id": "workflow_comment",
							"value": f"{workflow_id}|{contract_name}",
						},
					],
				},
			]

			message = SlackMessage(
				channel=channel,
				blocks=blocks,
				message_type=SlackMessageType.BLOCKS,
				priority=SlackPriority.HIGH,
				thread_ts=thread_ts,
				callback_id="approval_workflow",
				metadata={
					"workflow_id": workflow_id,
					"contract_name": contract_name,
					"approvers": approvers,
					"deadline": approval_deadline.isoformat() if approval_deadline else None,
					"workflow_type": "approval",
				},
			)

			result = await self.send_message(message)

			# Store workflow state (in production, use database)
			self._approval_workflows = getattr(self, "_approval_workflows", {})
			self._approval_workflows[workflow_id] = {
				"contract_name": contract_name,
				"approvers": approvers,
				"approved_by": [],
				"rejected_by": [],
				"comments": [],
				"status": "pending",
				"created_at": datetime.now(),
				"deadline": approval_deadline,
				"message_ts": result.get("message_ts"),
				"channel": channel,
			}

			return {"success": True, "workflow_id": workflow_id, "message_ts": result.get("message_ts")}

		except Exception as e:
			logger.error(f"Failed to create approval workflow: {e}")
			raise EmailServiceError(f"Approval workflow creation failed: {e}", category=ErrorCategory.EXTERNAL_SERVICE, severity=ErrorSeverity.HIGH)

	async def handle_interactive_component(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Handle interactive component interactions"""
		try:
			action_id = payload.get("actions", [{}])[0].get("action_id")
			user_id = payload.get("user", {}).get("id")
			channel_id = payload.get("channel", {}).get("id")

			logger.info(f"Handling interactive component: {action_id} from user {user_id}")

			# Original handlers
			if action_id == "view_report":
				return await self._handle_view_report(payload)
			elif action_id == "download_pdf":
				return await self._handle_download_pdf(payload)
			elif action_id == "review_urgent":
				return await self._handle_review_urgent(payload)
			elif action_id == "escalate_risk":
				return await self._handle_escalate_risk(payload)

			# New contract action handlers
			elif action_id == "analyze_contract":
				return await self._handle_analyze_contract(payload)
			elif action_id == "generate_report":
				return await self._handle_generate_report(payload)
			elif action_id == "risk_assessment":
				return await self._handle_risk_assessment(payload)
			elif action_id == "approve_contract":
				return await self._handle_approve_contract(payload)
			elif action_id == "reject_contract":
				return await self._handle_reject_contract(payload)
			elif action_id == "request_changes":
				return await self._handle_request_changes(payload)

			# Workflow handlers
			elif action_id == "workflow_approve":
				return await self._handle_workflow_approve(payload)
			elif action_id == "workflow_reject":
				return await self._handle_workflow_reject(payload)
			elif action_id == "workflow_comment":
				return await self._handle_workflow_comment(payload)

			else:
				return {"status": "ignored", "message": f"Unknown action: {action_id}"}

		except Exception as e:
			logger.error(f"Error handling interactive component: {e}")
			return {"status": "error", "message": str(e)}

	async def _handle_view_report(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Handle view report button click"""
		contract_name = payload.get("actions", [{}])[0].get("value")
		user_id = payload.get("user", {}).get("id")

		# Send ephemeral message with report link
		await self.client.chat_postEphemeral(
			channel=payload["channel"]["id"],
			user=user_id,
			text=f"📊 Opening detailed report for *{contract_name}*...",
			blocks=[
				{
					"type": "section",
					"text": {"type": "mrkdwn", "text": f"📊 *Report for {contract_name}*\n\nClick the link below to view the full analysis report:"},
					"accessory": {
						"type": "button",
						"text": {"type": "plain_text", "text": "Open Report"},
						"url": f"https://app.contractanalyzer.com/reports/{contract_name}",
						"style": "primary",
					},
				}
			],
		)

		return {"status": "success", "action": "view_report"}

	async def _handle_download_pdf(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Handle download PDF button click"""
		contract_name = payload.get("actions", [{}])[0].get("value")
		user_id = payload.get("user", {}).get("id")

		# Send ephemeral message with download link
		await self.client.chat_postEphemeral(
			channel=payload["channel"]["id"],
			user=user_id,
			text=f"📄 Preparing PDF download for *{contract_name}*...",
			blocks=[
				{
					"type": "section",
					"text": {
						"type": "mrkdwn",
						"text": f"📄 *PDF Report for {contract_name}*\n\nYour PDF report is being generated. You'll receive a download link shortly.",
					},
				}
			],
		)

		return {"status": "success", "action": "download_pdf"}

	async def _handle_review_urgent(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Handle review urgent button click"""
		contract_name = payload.get("actions", [{}])[0].get("value")
		user_id = payload.get("user", {}).get("id")

		# Update original message to show it's being reviewed
		await self.client.chat_update(
			channel=payload["channel"]["id"],
			ts=payload["message"]["ts"],
			blocks=payload["message"]["blocks"]
			+ [{"type": "context", "elements": [{"type": "mrkdwn", "text": f"👤 <@{user_id}> is reviewing this contract"}]}],
		)

		return {"status": "success", "action": "review_urgent"}

	async def _handle_escalate_risk(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Handle escalate risk button click"""
		contract_name = payload.get("actions", [{}])[0].get("value")
		user_id = payload.get("user", {}).get("id")

		# Send escalation notification to management channel
		escalation_channel = "#contract-management"  # Configure as needed

		await self.send_message(
			SlackMessage(
				channel=escalation_channel,
				blocks=[
					{"type": "header", "text": {"type": "plain_text", "text": "🚨 RISK ESCALATION"}},
					{
						"type": "section",
						"text": {
							"type": "mrkdwn",
							"text": f"*Contract:* {contract_name}\n*Escalated by:* <@{user_id}>\n*Reason:* High-risk contract requires management review",
						},
					},
				],
				priority=SlackPriority.CRITICAL,
			)
		)

		return {"status": "success", "action": "escalate_risk"}

	async def _handle_analyze_contract(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Handle analyze contract button click"""
		action_value = payload.get("actions", [{}])[0].get("value", "")
		_contract_name, _file_id = action_value.split("|", 1) if "|" in action_value else (action_value, "")
		user_id = payload.get("user", {}).get("id")

		# Send immediate response
		await self.client.chat_postEphemeral(
			channel=payload["channel"]["id"],
			user=user_id,
			text=f"🔍 Starting analysis for *{contract_name}*...",
			blocks=[
				{
					"type": "section",
					"text": {
						"type": "mrkdwn",
						"text": f"🔍 *Analysis Started*\n\nAnalyzing contract: *{contract_name}*\n\nThis may take a few minutes. You'll be notified when complete.",
					},
				}
			],
		)

		# Start background analysis (mock for now)
		self._bg_tasks = getattr(self, "_bg_tasks", [])
		self._bg_tasks.append(
			asyncio.create_task(self._simulate_contract_analysis_from_button(contract_name, file_id, user_id, payload["channel"]["id"]))
		)

		return {"status": "success", "action": "analyze_contract"}

	async def _handle_generate_report(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Handle generate report button click"""
		action_value = payload.get("actions", [{}])[0].get("value", "")
		_contract_name, _file_id = action_value.split("|", 1) if "|" in action_value else (action_value, "")
		user_id = payload.get("user", {}).get("id")

		await self.client.chat_postEphemeral(
			channel=payload["channel"]["id"],
			user=user_id,
			text=f"📄 Generating report for *{contract_name}*...",
			blocks=[
				{
					"type": "section",
					"text": {
						"type": "mrkdwn",
						"text": f"📄 *Report Generation*\n\nGenerating comprehensive report for: *{contract_name}*\n\nYou'll receive a download link shortly.",
					},
				}
			],
		)

		return {"status": "success", "action": "generate_report"}

	async def _handle_risk_assessment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Handle risk assessment button click"""
		action_value = payload.get("actions", [{}])[0].get("value", "")
		_contract_name, _file_id = action_value.split("|", 1) if "|" in action_value else (action_value, "")
		user_id = payload.get("user", {}).get("id")

		await self.client.chat_postEphemeral(
			channel=payload["channel"]["id"],
			user=user_id,
			text=f"⚠️ Performing risk assessment for *{contract_name}*...",
			blocks=[
				{
					"type": "section",
					"text": {
						"type": "mrkdwn",
						"text": f"⚠️ *Risk Assessment*\n\nAnalyzing risks for: *{contract_name}*\n\nScanning for potential issues and compliance concerns...",
					},
				}
			],
		)

		return {"status": "success", "action": "risk_assessment"}

	async def _handle_approve_contract(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Handle approve contract button click"""
		action_value = payload.get("actions", [{}])[0].get("value", "")
		_contract_name, _file_id = action_value.split("|", 1) if "|" in action_value else (action_value, "")
		user_id = payload.get("user", {}).get("id")

		# Update original message to show approval
		await self.client.chat_update(
			channel=payload["channel"]["id"],
			ts=payload["message"]["ts"],
			blocks=payload["message"]["blocks"]
			+ [
				{
					"type": "section",
					"text": {"type": "mrkdwn", "text": f"✅ *APPROVED* by <@{user_id}> at {datetime.now().strftime('%Y-%m-%d %H:%M')}"},
				},
				{"type": "context", "elements": [{"type": "mrkdwn", "text": "Contract has been approved and is ready for execution."}]},
			],
		)

		# Send notification to relevant channels
		await self.send_message(
			SlackMessage(
				channel="#contract-approvals",  # Configure as needed
				blocks=[
					{"type": "header", "text": {"type": "plain_text", "text": "✅ Contract Approved"}},
					{
						"type": "section",
						"text": {
							"type": "mrkdwn",
							"text": f"*Contract:* {contract_name}\n*Approved by:* <@{user_id}>\n*Status:* Ready for execution",
						},
					},
				],
				priority=SlackPriority.HIGH,
			)
		)

		return {"status": "success", "action": "approve_contract"}

	async def _handle_reject_contract(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Handle reject contract button click"""
		action_value = payload.get("actions", [{}])[0].get("value", "")
		_contract_name, _file_id = action_value.split("|", 1) if "|" in action_value else (action_value, "")
		user_id = payload.get("user", {}).get("id")

		# Update original message to show rejection
		await self.client.chat_update(
			channel=payload["channel"]["id"],
			ts=payload["message"]["ts"],
			blocks=payload["message"]["blocks"]
			+ [
				{
					"type": "section",
					"text": {"type": "mrkdwn", "text": f"❌ *REJECTED* by <@{user_id}> at {datetime.now().strftime('%Y-%m-%d %H:%M')}"},
				},
				{"type": "context", "elements": [{"type": "mrkdwn", "text": "Contract has been rejected. Please review and address concerns."}]},
			],
		)

		return {"status": "success", "action": "reject_contract"}

	async def _handle_request_changes(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Handle request changes button click"""
		action_value = payload.get("actions", [{}])[0].get("value", "")
		contract_name, file_id = action_value.split("|", 1) if "|" in action_value else (action_value, "")
		user_id = payload.get("user", {}).get("id")

		# Open modal for change request details
		await self.client.views_open(
			trigger_id=payload["trigger_id"],
			view={
				"type": "modal",
				"callback_id": "change_request_modal",
				"title": {"type": "plain_text", "text": "Request Changes"},
				"submit": {"type": "plain_text", "text": "Submit Request"},
				"close": {"type": "plain_text", "text": "Cancel"},
				"blocks": [
					{
						"type": "section",
						"text": {"type": "mrkdwn", "text": f"*Contract:* {contract_name}\n\nPlease describe the changes you'd like to request:"},
					},
					{
						"type": "input",
						"block_id": "change_description",
						"element": {
							"type": "plain_text_input",
							"action_id": "description",
							"multiline": True,
							"placeholder": {"type": "plain_text", "text": "Describe the specific changes needed..."},
						},
						"label": {"type": "plain_text", "text": "Change Description"},
					},
					{
						"type": "input",
						"block_id": "priority_level",
						"element": {
							"type": "static_select",
							"action_id": "priority",
							"placeholder": {"type": "plain_text", "text": "Select priority level"},
							"options": [
								{"text": {"type": "plain_text", "text": "Low - Minor adjustments"}, "value": "low"},
								{"text": {"type": "plain_text", "text": "Medium - Moderate changes"}, "value": "medium"},
								{"text": {"type": "plain_text", "text": "High - Significant revisions"}, "value": "high"},
							],
						},
						"label": {"type": "plain_text", "text": "Priority Level"},
					},
				],
				"private_metadata": json.dumps(
					{
						"contract_name": contract_name,
						"file_id": file_id,
						"channel_id": payload["channel"]["id"],
						"message_ts": payload["message"]["ts"],
					}
				),
			},
		)

		return {"status": "success", "action": "request_changes"}

	async def _handle_workflow_approve(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Handle workflow approval"""
		action_value = payload.get("actions", [{}])[0].get("value", "")
		workflow_id, _contract_name = action_value.split("|", 1) if "|" in action_value else (action_value, "")
		user_id = payload.get("user", {}).get("id")

		# Get workflow state
		workflows = getattr(self, "_approval_workflows", {})
		workflow = workflows.get(workflow_id)

		if not workflow:
			return {"status": "error", "message": "Workflow not found"}

		# Check if user is authorized to approve
		if user_id not in workflow["approvers"]:
			await self.client.chat_postEphemeral(
				channel=payload["channel"]["id"], user=user_id, text="❌ You are not authorized to approve this contract."
			)
			return {"status": "error", "message": "Unauthorized"}

		# Check if already approved by this user
		if user_id in workflow["approved_by"]:
			await self.client.chat_postEphemeral(
				channel=payload["channel"]["id"], user=user_id, text="Info: You have already approved this contract."
			)
			return {"status": "success", "message": "Already approved"}

		# Add approval
		workflow["approved_by"].append(user_id)

		# Check if all approvals received
		all_approved = len(workflow["approved_by"]) == len(workflow["approvers"])

		# Update workflow status
		if all_approved:
			workflow["status"] = "approved"

		# Update message with current status
		await self._update_workflow_message(workflow_id, workflow)

		return {"status": "success", "action": "workflow_approve", "all_approved": all_approved}

	async def _handle_workflow_reject(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Handle workflow rejection"""
		action_value = payload.get("actions", [{}])[0].get("value", "")
		workflow_id, _contract_name = action_value.split("|", 1) if "|" in action_value else (action_value, "")
		user_id = payload.get("user", {}).get("id")

		# Get workflow state
		workflows = getattr(self, "_approval_workflows", {})
		workflow = workflows.get(workflow_id)

		if not workflow:
			return {"status": "error", "message": "Workflow not found"}

		# Add rejection
		workflow["rejected_by"].append(user_id)
		workflow["status"] = "rejected"

		# Update message
		await self._update_workflow_message(workflow_id, workflow)

		return {"status": "success", "action": "workflow_reject"}

	async def _handle_workflow_comment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Handle workflow comment"""
		action_value = payload.get("actions", [{}])[0].get("value", "")
		workflow_id, contract_name = action_value.split("|", 1) if "|" in action_value else (action_value, "")

		# Open modal for comment
		await self.client.views_open(
			trigger_id=payload["trigger_id"],
			view={
				"type": "modal",
				"callback_id": "workflow_comment_modal",
				"title": {"type": "plain_text", "text": "Add Comment"},
				"submit": {"type": "plain_text", "text": "Add Comment"},
				"close": {"type": "plain_text", "text": "Cancel"},
				"blocks": [
					{
						"type": "input",
						"block_id": "comment_text",
						"element": {
							"type": "plain_text_input",
							"action_id": "comment",
							"multiline": True,
							"placeholder": {"type": "plain_text", "text": "Add your comment about this contract..."},
						},
						"label": {"type": "plain_text", "text": "Comment"},
					}
				],
				"private_metadata": json.dumps({"workflow_id": workflow_id, "contract_name": contract_name}),
			},
		)

		return {"status": "success", "action": "workflow_comment"}

	async def _simulate_contract_analysis_from_button(self, contract_name: str, file_id: str, user_id: str, channel_id: str):
		"""Simulate job application tracking from button click"""
		try:
			# Simulate analysis delay
			await asyncio.sleep(5)  # 5 seconds for demo

			# Mock analysis results
			risk_score = 7.2
			risk_level = "High"
			analysis_summary = "Analysis complete. Several high-risk clauses identified requiring immediate attention."
			risky_clauses = [
				"Unlimited liability clause in section 4.2",
				"Automatic renewal without notice in section 8.1",
				"Broad indemnification requirements in section 6.3",
			]
			recommendations = [
				"Negotiate liability cap in section 4.2",
				"Add 30-day termination notice requirement",
				"Limit indemnification scope to direct damages",
			]

			# Send completion notification
			await self.send_contract_analysis_notification(
				channel=channel_id,
				contract_name=contract_name,
				risk_score=risk_score,
				risk_level=risk_level,
				analysis_summary=analysis_summary,
				risky_clauses=risky_clauses,
				recommendations=recommendations,
			)

		except Exception as e:
			logger.error(f"Error in simulated analysis: {e}")

			# Send error notification
			await self.send_message(
				SlackMessage(
					channel=channel_id,
					text=f"❌ Analysis failed for {contract_name}",
					blocks=[
						{
							"type": "section",
							"text": {
								"type": "mrkdwn",
								"text": f"❌ *Analysis Failed*\n\nSorry, the analysis for *{contract_name}* encountered an error.\n\nError: {e!s}",
							},
						}
					],
				)
			)

	async def _update_workflow_message(self, workflow_id: str, workflow: Dict[str, Any]):
		"""Update workflow message with current status"""
		try:
			# Build approval status
			approval_status = []
			for approver in workflow["approvers"]:
				if approver in workflow["approved_by"]:
					approval_status.append(f"✅ <@{approver}> - Approved")
				elif approver in workflow["rejected_by"]:
					approval_status.append(f"❌ <@{approver}> - Rejected")
				else:
					approval_status.append(f"⏳ <@{approver}> - Pending")

			# Determine overall status
			if workflow["status"] == "approved":
				status_text = "✅ *Status:* APPROVED - All parties have approved"
				status_color = "good"
			elif workflow["status"] == "rejected":
				status_text = "❌ *Status:* REJECTED - Contract has been rejected"
				status_color = "danger"
			else:
				status_text = "*Status:* Pending approval from all parties"
				status_color = "warning"

			# Update message
			blocks = [
				{"type": "header", "text": {"type": "plain_text", "text": f"📋 Approval Required: {workflow['contract_name']}"}},
				{"type": "section", "text": {"type": "mrkdwn", "text": f"{status_text}\n\n*Approval Progress:*\n" + "\n".join(approval_status)}},
			]

			# Add action buttons only if still pending
			if workflow["status"] == "pending":
				blocks.append(
					{
						"type": "actions",
						"elements": [
							{
								"type": "button",
								"text": {"type": "plain_text", "text": "✅ Approve"},
								"style": "primary",
								"action_id": "workflow_approve",
								"value": f"{workflow_id}|{workflow['contract_name']}",
							},
							{
								"type": "button",
								"text": {"type": "plain_text", "text": "❌ Reject"},
								"style": "danger",
								"action_id": "workflow_reject",
								"value": f"{workflow_id}|{workflow['contract_name']}",
							},
							{
								"type": "button",
								"text": {"type": "plain_text", "text": "💬 Add Comment"},
								"action_id": "workflow_comment",
								"value": f"{workflow_id}|{workflow['contract_name']}",
							},
						],
					}
				)

			await self.client.chat_update(channel=workflow["channel"], ts=workflow["message_ts"], blocks=blocks)

		except Exception as e:
			logger.error(f"Error updating workflow message: {e}")

	async def _check_rate_limits(self) -> bool:
		"""Check Slack API rate limits"""
		current_time = datetime.now()
		minute_ago = current_time - timedelta(minutes=1)

		# Clean old requests
		self.rate_limiter.requests = [req_time for req_time in self.rate_limiter.requests if req_time > minute_ago]

		# Check limit based on tier
		limit = getattr(self.rate_limiter, f"tier{self.config.rate_limit_tier}_limit", 50)

		if len(self.rate_limiter.requests) >= limit:
			return False

		return True

	async def _update_rate_limiter(self):
		"""Update rate limiter with current request"""
		self.rate_limiter.requests.append(datetime.now())

	async def _validate_channel_access(self, channel: str) -> bool:
		"""Validate access to channel"""
		if self.config.allowed_channels:
			return channel in self.config.allowed_channels
		return True

	async def _load_channels(self):
		"""Load and cache channel information"""
		try:
			response = await self.client.conversations_list(types="public_channel,private_channel", limit=1000)

			for channel_data in response["channels"]:
				channel = SlackChannel(
					id=channel_data["id"],
					name=channel_data["name"],
					is_channel=channel_data.get("is_channel", False),
					is_group=channel_data.get("is_group", False),
					is_archived=channel_data.get("is_archived", False),
				)
				self.channel_cache[channel.id] = channel
				self.channel_cache[f"#{channel.name}"] = channel

			logger.info(f"Loaded {len(self.channel_cache)} channels")

		except SlackApiError as e:
			logger.error(f"Failed to load channels: {e}")

	async def _load_users(self):
		"""Load and cache user information"""
		try:
			response = await self.client.users_list(limit=1000)

			for user_data in response["members"]:
				if not user_data.get("deleted", False):
					user = SlackUser(
						id=user_data["id"],
						name=user_data["name"],
						real_name=user_data.get("real_name"),
						email=user_data.get("profile", {}).get("email"),
						is_bot=user_data.get("is_bot", False),
						is_admin=user_data.get("is_admin", False),
						timezone=user_data.get("tz"),
					)
					self.user_cache[user.id] = user

			logger.info(f"Loaded {len(self.user_cache)} users")

		except SlackApiError as e:
			logger.error(f"Failed to load users: {e}")

	async def _get_permalink(self, channel: str, message_ts: str) -> str:
		"""Get permalink for a message"""
		try:
			response = await self.client.chat_getPermalink(channel=channel, message_ts=message_ts)
			return response["permalink"]
		except SlackApiError:
			return f"https://slack.com/app_redirect?channel={channel}"

	async def _update_message_stats(self, message: SlackMessage, success: bool):
		"""Update message statistics"""
		if success:
			self.message_stats["total_sent"] += 1
		else:
			self.message_stats["total_failed"] += 1

		# Update by channel
		channel = message.channel
		if channel not in self.message_stats["by_channel"]:
			self.message_stats["by_channel"][channel] = {"sent": 0, "failed": 0}

		if success:
			self.message_stats["by_channel"][channel]["sent"] += 1
		else:
			self.message_stats["by_channel"][channel]["failed"] += 1

		# Update by priority
		priority = message.priority.value
		if priority not in self.message_stats["by_priority"]:
			self.message_stats["by_priority"][priority] = {"sent": 0, "failed": 0}

		if success:
			self.message_stats["by_priority"][priority]["sent"] += 1
		else:
			self.message_stats["by_priority"][priority]["failed"] += 1

		# Update by type
		msg_type = message.message_type.value
		if msg_type not in self.message_stats["by_type"]:
			self.message_stats["by_type"][msg_type] = {"sent": 0, "failed": 0}

		if success:
			self.message_stats["by_type"][msg_type]["sent"] += 1
		else:
			self.message_stats["by_type"][msg_type]["failed"] += 1

	async def get_analytics(self) -> Dict[str, Any]:
		"""Get Slack integration analytics"""
		total_messages = self.message_stats["total_sent"] + self.message_stats["total_failed"]
		success_rate = (self.message_stats["total_sent"] / total_messages * 100) if total_messages > 0 else 0

		return {
			"overview": {
				"total_sent": self.message_stats["total_sent"],
				"total_failed": self.message_stats["total_failed"],
				"success_rate": round(success_rate, 2),
				"channels_active": len(self.message_stats["by_channel"]),
				"users_cached": len(self.user_cache),
			},
			"by_channel": self.message_stats["by_channel"],
			"by_priority": self.message_stats["by_priority"],
			"by_type": self.message_stats["by_type"],
			"rate_limiting": {
				"tier": self.config.rate_limit_tier,
				"current_requests": len(self.rate_limiter.requests),
				"limit": getattr(self.rate_limiter, f"tier{self.config.rate_limit_tier}_limit", 50),
			},
			"timestamp": datetime.now().isoformat(),
		}

	async def get_health_status(self) -> Dict[str, Any]:
		"""Get service health status"""
		try:
			# Test API connection
			auth_response = await self.client.auth_test()

			return {
				"healthy": True,
				"service": "enhanced_slack",
				"bot_user": auth_response.get("user"),
				"team": auth_response.get("team"),
				"rate_limiting": {"tier": self.config.rate_limit_tier, "current_requests": len(self.rate_limiter.requests)},
				"caches": {"users": len(self.user_cache), "channels": len(self.channel_cache)},
				"features": {
					"interactive_components": self.config.enable_interactive_components,
					"slash_commands": self.config.enable_slash_commands,
					"events": self.config.enable_events,
					"analytics": self.config.enable_analytics,
				},
				"timestamp": datetime.now().isoformat(),
			}

		except Exception as e:
			return {"healthy": False, "service": "enhanced_slack", "error": str(e), "timestamp": datetime.now().isoformat()}

	async def shutdown(self):
		"""Shutdown Slack service"""
		logger.info("Shutting down Enhanced Slack service...")

		# Clear caches
		self.user_cache.clear()
		self.channel_cache.clear()

		# Close client connections
		if hasattr(self.client, "close"):
			await self.client.close()

		logger.info("Enhanced Slack service shutdown completed")
