"""
Slack Bot Commands Service for contract management operations.
Provides slash commands and interactive workflows for job application tracking.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

from ..core.logging import get_logger
from .slack_service import EnhancedSlackService, SlackMessage

logger = get_logger(__name__)


class CommandType(str, Enum):
	"""Slack command types"""

	ANALYZE = "analyze"
	STATUS = "status"
	REPORT = "report"
	HELP = "help"
	SETTINGS = "settings"


class CommandPermission(str, Enum):
	"""Command permission levels"""

	PUBLIC = "public"
	PRIVATE = "private"
	ADMIN = "admin"


@dataclass
class SlackCommand:
	"""Slack command definition"""

	name: str
	description: str
	usage: str
	permission: CommandPermission
	handler: str
	examples: List[str]


class SlackBotCommands:
	"""Slack bot commands service for contract management"""

	def __init__(self, slack_service: EnhancedSlackService):
		self.slack_service = slack_service
		self.client = slack_service.client

		# Command registry
		self.commands = {
			"analyze": SlackCommand(
				name="analyze",
				description="Analyze a contract document",
				usage="/analyze [contract_url] [options]",
				permission=CommandPermission.PRIVATE,
				handler="handle_analyze_command",
				examples=[
					"/analyze https://example.com/contract.pdf",
					"/analyze https://example.com/contract.pdf --priority high",
					"/analyze https://example.com/contract.pdf --notify #legal",
				],
			),
			"status": SlackCommand(
				name="status",
				description="Check job application tracking status",
				usage="/status [contract_id]",
				permission=CommandPermission.PUBLIC,
				handler="handle_status_command",
				examples=["/status", "/status contract_123", "/status --recent 5"],
			),
			"report": SlackCommand(
				name="report",
				description="Generate job application tracking report",
				usage="/report [contract_id] [format]",
				permission=CommandPermission.PRIVATE,
				handler="handle_report_command",
				examples=["/report contract_123", "/report contract_123 pdf", "/report contract_123 summary"],
			),
			"help": SlackCommand(
				name="help",
				description="Show available commands and usage",
				usage="/help [command]",
				permission=CommandPermission.PUBLIC,
				handler="handle_help_command",
				examples=["/help", "/help analyze", "/help status"],
			),
			"settings": SlackCommand(
				name="settings",
				description="Manage notification and analysis settings",
				usage="/settings [action] [options]",
				permission=CommandPermission.ADMIN,
				handler="handle_settings_command",
				examples=["/settings show", "/settings notifications on", "/settings channel #contracts"],
			),
			"upload": SlackCommand(
				name="upload",
				description="Upload and analyze a contract file",
				usage="/upload [file_attachment]",
				permission=CommandPermission.PRIVATE,
				handler="handle_upload_command",
				examples=["/upload (attach file)", "/upload --priority high (attach file)", "/upload --notify #legal (attach file)"],
			),
			"workflow": SlackCommand(
				name="workflow",
				description="Manage contract approval workflows",
				usage="/workflow [action] [contract_id] [options]",
				permission=CommandPermission.PRIVATE,
				handler="handle_workflow_command",
				examples=["/workflow create contract_123 @user1 @user2", "/workflow status workflow_456", "/workflow approve workflow_456"],
			),
		}

		# Command statistics
		self.command_stats = {"total_commands": 0, "by_command": {}, "by_user": {}, "errors": 0}

	async def handle_slash_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Handle incoming slash command"""
		try:
			command = payload.get("command", "").lstrip("/")
			text = payload.get("text", "").strip()
			user_id = payload.get("user_id")
			channel_id = payload.get("channel_id")

			logger.info(f"Handling slash command: /{command} from user {user_id}")

			# Update statistics
			self.command_stats["total_commands"] += 1
			self.command_stats["by_command"][command] = self.command_stats["by_command"].get(command, 0) + 1
			self.command_stats["by_user"][user_id] = self.command_stats["by_user"].get(user_id, 0) + 1

			# Check if command exists
			if command not in self.commands:
				return await self._send_error_response(f"Unknown command: /{command}. Type `/help` for available commands.")

			# Check permissions
			if not await self._check_command_permission(command, user_id, channel_id):
				return await self._send_error_response(f"You don't have permission to use the /{command} command.")

			# Route to appropriate handler
			handler_name = self.commands[command].handler
			handler = getattr(self, handler_name)

			return await handler(payload, text)

		except Exception as e:
			self.command_stats["errors"] += 1
			logger.error(f"Error handling slash command: {e}")
			return await self._send_error_response("An error occurred while processing your command. Please try again.")

	async def handle_analyze_command(self, payload: Dict[str, Any], text: str) -> Dict[str, Any]:
		"""Handle /analyze command"""
		user_id = payload.get("user_id")
		channel_id = payload.get("channel_id")

		if not text:
			return {
				"response_type": "ephemeral",
				"text": "Please provide a contract URL to analyze.",
				"blocks": [
					{
						"type": "section",
						"text": {
							"type": "mrkdwn",
							"text": "*Usage:* `/analyze <contract_url> [options]`\n\n*Examples:*\n• `/analyze https://example.com/contract.pdf`\n• `/analyze https://example.com/contract.pdf --priority high`",
						},
					}
				],
			}

		# Parse command arguments
		args = text.split()
		contract_input = args[0]
		options = self._parse_command_options(args[1:])

		# Check if input is URL or file upload
		is_url = self._is_valid_url(contract_input)
		is_file_id = contract_input.startswith("F") and len(contract_input) > 5  # Slack file ID format

		if not is_url and not is_file_id:
			return await self._send_error_response(
				"Please provide a valid contract URL or upload a file to analyze.\nUsage: `/analyze <contract_url>` or `/analyze <file_id>`"
			)

		# Start analysis process
		analysis_id = f"analysis_{datetime.now().timestamp()}"

		# Send immediate response
		response = {
			"response_type": "in_channel" if options.get("public") else "ephemeral",
			"text": f"🔍 Starting job application tracking...",
			"blocks": [
				{"type": "header", "text": {"type": "plain_text", "text": "🔍 Contract Analysis Started"}},
				{
					"type": "section",
					"fields": [
						{"type": "mrkdwn", "text": f"*Contract:* {contract_input}"},
						{"type": "mrkdwn", "text": f"*Analysis ID:* {analysis_id}"},
						{"type": "mrkdwn", "text": f"*Priority:* {options.get('priority', 'normal').title()}"},
						{"type": "mrkdwn", "text": f"*Requested by:* <@{user_id}>"},
					],
				},
				{"type": "section", "text": {"type": "mrkdwn", "text": "⏳ Analysis in progress... You'll be notified when complete."}},
			],
		}

		# Start background analysis (mock for now)
		self._bg_tasks = getattr(self, "_bg_tasks", [])
		self._bg_tasks.append(asyncio.create_task(self._simulate_contract_analysis(analysis_id, contract_input, user_id, channel_id, options)))

		return response

	async def handle_status_command(self, payload: Dict[str, Any], text: str) -> Dict[str, Any]:
		"""Handle /status command"""
		user_id = payload.get("user_id")

		# Parse arguments
		args = text.split() if text else []

		if args and not args[0].startswith("--"):
			# Specific contract status
			contract_id = args[0]
			return await self._get_contract_status(contract_id, user_id)
		else:
			# General status or recent analyses
			options = self._parse_command_options(args)
			recent_count = int(options.get("recent", 5))
			return await self._get_recent_analyses(user_id, recent_count)

	async def handle_report_command(self, payload: Dict[str, Any], text: str) -> Dict[str, Any]:
		"""Handle /report command"""
		user_id = payload.get("user_id")

		if not text:
			return await self._send_error_response("Please provide a contract ID. Usage: `/report <contract_id> [format]`")

		args = text.split()
		contract_id = args[0]
		report_format = args[1] if len(args) > 1 else "summary"

		# Generate report
		return await self._generate_contract_report(contract_id, report_format, user_id)

	async def handle_help_command(self, payload: Dict[str, Any], text: str) -> Dict[str, Any]:
		"""Handle /help command"""
		if text and text in self.commands:
			# Specific command help
			command = self.commands[text]
			return {
				"response_type": "ephemeral",
				"blocks": [
					{"type": "header", "text": {"type": "plain_text", "text": f"Help: /{command.name}"}},
					{"type": "section", "text": {"type": "mrkdwn", "text": f"*Description:* {command.description}\n*Usage:* `{command.usage}`"}},
					{"type": "section", "text": {"type": "mrkdwn", "text": "*Examples:*\n" + "\n".join([f"• `{ex}`" for ex in command.examples])}},
				],
			}
		else:
			# General help
			command_list = []
			for cmd_name, cmd in self.commands.items():
				command_list.append(f"• `/{cmd_name}` - {cmd.description}")

			return {
				"response_type": "ephemeral",
				"blocks": [
					{"type": "header", "text": {"type": "plain_text", "text": "📚 Career Copilot Bot Commands"}},
					{"type": "section", "text": {"type": "mrkdwn", "text": "*Available Commands:*\n" + "\n".join(command_list)}},
					{
						"type": "section",
						"text": {"type": "mrkdwn", "text": "💡 *Tip:* Use `/help <command>` for detailed help on a specific command."},
					},
				],
			}

	async def handle_settings_command(self, payload: Dict[str, Any], text: str) -> Dict[str, Any]:
		"""Handle /settings command"""
		user_id = payload.get("user_id")

		if not text or text == "show":
			return await self._show_user_settings(user_id)

		args = text.split()
		action = args[0]

		if action == "notifications":
			setting = args[1] if len(args) > 1 else "show"
			return await self._manage_notification_settings(user_id, setting)
		elif action == "channel":
			channel = args[1] if len(args) > 1 else None
			return await self._set_default_channel(user_id, channel)
		else:
			return await self._send_error_response(f"Unknown settings action: {action}. Use `/help settings` for usage.")

	async def handle_upload_command(self, payload: Dict[str, Any], text: str) -> Dict[str, Any]:
		"""Handle /upload command for file uploads"""
		user_id = payload.get("user_id")
		channel_id = payload.get("channel_id")

		# Parse options
		args = text.split() if text else []
		options = self._parse_command_options(args)

		# Check if there are any files in the channel recently
		# In a real implementation, you'd check for file uploads in the request
		return {
			"response_type": "ephemeral",
			"blocks": [
				{"type": "header", "text": {"type": "plain_text", "text": "📎 Contract File Upload"}},
				{
					"type": "section",
					"text": {
						"type": "mrkdwn",
						"text": "*How to upload a contract for analysis:*\n\n1. Drag and drop your contract file into this channel\n2. Add a comment with `/analyze <file_id>` to start analysis\n3. Or use the interactive buttons that appear with the file",
					},
				},
				{"type": "section", "text": {"type": "mrkdwn", "text": "*Supported formats:* PDF, DOC, DOCX\n*Max file size:* 10MB"}},
				{
					"type": "actions",
					"elements": [
						{
							"type": "button",
							"text": {"type": "plain_text", "text": "📋 Upload Guidelines"},
							"action_id": "upload_guidelines",
							"value": "show_guidelines",
						}
					],
				},
			],
		}

	async def handle_workflow_command(self, payload: Dict[str, Any], text: str) -> Dict[str, Any]:
		"""Handle /workflow command for approval workflows"""
		user_id = payload.get("user_id")
		channel_id = payload.get("channel_id")

		if not text:
			return {
				"response_type": "ephemeral",
				"text": "Please specify a workflow action.",
				"blocks": [
					{
						"type": "section",
						"text": {
							"type": "mrkdwn",
							"text": "*Workflow Commands:*\n\n• `/workflow create <contract_name> @user1 @user2` - Create approval workflow\n• `/workflow status <workflow_id>` - Check workflow status\n• `/workflow list` - List active workflows",
						},
					}
				],
			}

		args = text.split()
		action = args[0]

		if action == "create":
			return await self._handle_workflow_create(payload, args[1:])
		elif action == "status":
			return await self._handle_workflow_status(payload, args[1:])
		elif action == "list":
			return await self._handle_workflow_list(payload)
		else:
			return await self._send_error_response(f"Unknown workflow action: {action}. Use `/help workflow` for usage.")

	async def _handle_workflow_create(self, payload: Dict[str, Any], args: List[str]) -> Dict[str, Any]:
		"""Handle workflow creation"""
		if len(args) < 2:
			return await self._send_error_response("Usage: `/workflow create <contract_name> @user1 @user2 ...`")

		contract_name = args[0]
		approvers = []

		# Extract user mentions
		for arg in args[1:]:
			if arg.startswith("@"):
				# Remove @ and extract user ID (in real implementation, resolve username to ID)
				user_mention = arg[1:]
				approvers.append(user_mention)

		if not approvers:
			return await self._send_error_response("Please specify at least one approver using @username format.")

		# Create approval workflow
		try:
			result = await self.slack_service.create_approval_workflow(
				channel=payload["channel_id"], contract_name=contract_name, approvers=approvers
			)

			return {
				"response_type": "in_channel",
				"blocks": [
					{
						"type": "section",
						"text": {
							"type": "mrkdwn",
							"text": f"✅ *Approval workflow created*\n\n*Contract:* {contract_name}\n*Workflow ID:* {result['workflow_id']}\n*Approvers:* {', '.join([f'<@{user}>' for user in approvers])}",
						},
					}
				],
			}

		except Exception as e:
			return await self._send_error_response(f"Failed to create workflow: {e!s}")

	async def _handle_workflow_status(self, payload: Dict[str, Any], args: List[str]) -> Dict[str, Any]:
		"""Handle workflow status check"""
		if not args:
			return await self._send_error_response("Please provide a workflow ID.")

		workflow_id = args[0]

		# Get workflow status (mock implementation)
		workflows = getattr(self.slack_service, "_approval_workflows", {})
		workflow = workflows.get(workflow_id)

		if not workflow:
			return await self._send_error_response(f"Workflow {workflow_id} not found.")

		# Build status display
		approval_status = []
		for approver in workflow["approvers"]:
			if approver in workflow["approved_by"]:
				approval_status.append(f"✅ <@{approver}> - Approved")
			elif approver in workflow["rejected_by"]:
				approval_status.append(f"❌ <@{approver}> - Rejected")
			else:
				approval_status.append(f"⏳ <@{approver}> - Pending")

		return {
			"response_type": "ephemeral",
			"blocks": [
				{"type": "header", "text": {"type": "plain_text", "text": f"📊 Workflow Status: {workflow_id}"}},
				{
					"type": "section",
					"fields": [
						{"type": "mrkdwn", "text": f"*Contract:* {workflow['contract_name']}"},
						{"type": "mrkdwn", "text": f"*Status:* {workflow['status'].title()}"},
						{"type": "mrkdwn", "text": f"*Created:* {workflow['created_at'].strftime('%Y-%m-%d %H:%M')}"},
						{"type": "mrkdwn", "text": f"*Progress:* {len(workflow['approved_by'])}/{len(workflow['approvers'])} approved"},
					],
				},
				{"type": "section", "text": {"type": "mrkdwn", "text": "*Approval Status:*\n" + "\n".join(approval_status)}},
			],
		}

	async def _handle_workflow_list(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Handle workflow list"""
		workflows = getattr(self.slack_service, "_approval_workflows", {})

		if not workflows:
			return {"response_type": "ephemeral", "text": "No active workflows found."}

		workflow_list = []
		for workflow_id, workflow in workflows.items():
			status_emoji = {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(workflow["status"], "❓")

			workflow_list.append(f"{status_emoji} `{workflow_id}` - {workflow['contract_name']} ({workflow['status']})")

		return {
			"response_type": "ephemeral",
			"blocks": [
				{"type": "header", "text": {"type": "plain_text", "text": "📋 Active Workflows"}},
				{"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(workflow_list)}},
				{"type": "context", "elements": [{"type": "mrkdwn", "text": "Use `/workflow status <workflow_id>` for detailed information"}]},
			],
		}

	async def _simulate_contract_analysis(self, analysis_id: str, contract_input: str, user_id: str, channel_id: str, options: Dict[str, Any]):
		"""Simulate job application tracking process"""
		try:
			# Simulate analysis delay
			await asyncio.sleep(10)  # 10 seconds for demo

			# Mock analysis results
			risk_score = 6.5
			risk_level = "Medium"
			analysis_summary = "Contract analysis completed. Several clauses require attention."
			risky_clauses = [
				"Unlimited liability clause in section 4.2",
				"Automatic renewal terms in section 8.1",
				"Broad indemnification requirements",
			]
			recommendations = ["Negotiate liability cap in section 4.2", "Add termination notice period", "Review indemnification scope"]

			# Send completion notification
			contract_name = f"Contract from {contract_input}" if contract_input.startswith("http") else f"Uploaded Contract ({contract_input})"
			await self.slack_service.send_contract_analysis_notification(
				channel=channel_id,
				contract_name=contract_name,
				risk_score=risk_score,
				risk_level=risk_level,
				analysis_summary=analysis_summary,
				risky_clauses=risky_clauses,
				recommendations=recommendations,
			)

			# Send DM to requester
			await self.slack_service.send_message(
				SlackMessage(
					channel=user_id,  # DM to user
					text=f"✅ Your job application tracking is complete! Analysis ID: {analysis_id}",
					blocks=[
						{
							"type": "section",
							"text": {
								"type": "mrkdwn",
								"text": f"✅ *Analysis Complete*\n\nYour job application tracking (ID: `{analysis_id}`) has finished processing.\n\n*Risk Score:* {risk_score}/10\n*Risk Level:* {risk_level}",
							},
						},
						{
							"type": "actions",
							"elements": [
								{
									"type": "button",
									"text": {"type": "plain_text", "text": "View Results"},
									"style": "primary",
									"action_id": "view_analysis_results",
									"value": analysis_id,
								}
							],
						},
					],
				)
			)

		except Exception as e:
			logger.error(f"Error in simulated analysis: {e}")

			# Send error notification
			await self.slack_service.send_message(
				SlackMessage(
					channel=user_id,
					text=f"❌ Analysis failed for {analysis_id}",
					blocks=[
						{
							"type": "section",
							"text": {
								"type": "mrkdwn",
								"text": f"❌ *Analysis Failed*\n\nSorry, the analysis for `{analysis_id}` encountered an error.\n\nError: {e!s}",
							},
						}
					],
				)
			)

	async def _get_contract_status(self, contract_id: str, user_id: str) -> Dict[str, Any]:
		"""Get status of specific job application tracking"""
		# Mock status data
		status_data = {
			"id": contract_id,
			"status": "completed",
			"progress": 100,
			"risk_score": 6.5,
			"created_at": "2024-01-15T10:30:00Z",
			"completed_at": "2024-01-15T10:35:00Z",
		}

		return {
			"response_type": "ephemeral",
			"blocks": [
				{"type": "header", "text": {"type": "plain_text", "text": f"📊 Contract Status: {contract_id}"}},
				{
					"type": "section",
					"fields": [
						{"type": "mrkdwn", "text": f"*Status:* {status_data['status'].title()}"},
						{"type": "mrkdwn", "text": f"*Progress:* {status_data['progress']}%"},
						{"type": "mrkdwn", "text": f"*Risk Score:* {status_data['risk_score']}/10"},
						{"type": "mrkdwn", "text": f"*Created:* {status_data['created_at']}"},
					],
				},
			],
		}

	async def _get_recent_analyses(self, user_id: str, count: int) -> Dict[str, Any]:
		"""Get recent contract analyses"""
		# Mock recent analyses
		analyses = [
			{"id": "analysis_001", "status": "completed", "risk_score": 6.5, "created": "2024-01-15T10:30:00Z"},
			{"id": "analysis_002", "status": "in_progress", "risk_score": None, "created": "2024-01-15T11:00:00Z"},
			{"id": "analysis_003", "status": "completed", "risk_score": 3.2, "created": "2024-01-15T09:15:00Z"},
		]

		analysis_text = []
		for analysis in analyses[:count]:
			status_emoji = "✅" if analysis["status"] == "completed" else "⏳"
			risk_text = f" (Risk: {analysis['risk_score']}/10)" if analysis["risk_score"] else ""
			analysis_text.append(f"{status_emoji} `{analysis['id']}` - {analysis['status'].title()}{risk_text}")

		return {
			"response_type": "ephemeral",
			"blocks": [
				{"type": "header", "text": {"type": "plain_text", "text": f"📋 Recent Analyses (Last {count})"}},
				{"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(analysis_text) if analysis_text else "No recent analyses found."}},
			],
		}

	async def _generate_contract_report(self, contract_id: str, format_type: str, user_id: str) -> Dict[str, Any]:
		"""Generate job application tracking report"""
		if format_type not in ["summary", "detailed", "pdf"]:
			return await self._send_error_response(f"Invalid report format: {format_type}. Use 'summary', 'detailed', or 'pdf'.")

		return {
			"response_type": "ephemeral",
			"blocks": [
				{"type": "header", "text": {"type": "plain_text", "text": f"📄 Generating {format_type.title()} Report"}},
				{
					"type": "section",
					"text": {
						"type": "mrkdwn",
						"text": f"Generating {format_type} report for contract `{contract_id}`...\n\nYou'll receive the report shortly.",
					},
				},
				{
					"type": "actions",
					"elements": [
						{
							"type": "button",
							"text": {"type": "plain_text", "text": "Download Report"},
							"style": "primary",
							"action_id": "download_report",
							"value": f"{contract_id}_{format_type}",
						}
					],
				},
			],
		}

	async def _show_user_settings(self, user_id: str) -> Dict[str, Any]:
		"""Show user settings"""
		# Mock user settings
		settings = {"notifications": "enabled", "default_channel": "#contracts", "auto_notify": True, "report_format": "summary"}

		return {
			"response_type": "ephemeral",
			"blocks": [
				{"type": "header", "text": {"type": "plain_text", "text": "⚙️ Your Settings"}},
				{
					"type": "section",
					"fields": [
						{"type": "mrkdwn", "text": f"*Notifications:* {settings['notifications']}"},
						{"type": "mrkdwn", "text": f"*Default Channel:* {settings['default_channel']}"},
						{"type": "mrkdwn", "text": f"*Auto Notify:* {'Yes' if settings['auto_notify'] else 'No'}"},
						{"type": "mrkdwn", "text": f"*Report Format:* {settings['report_format']}"},
					],
				},
				{
					"type": "actions",
					"elements": [
						{"type": "button", "text": {"type": "plain_text", "text": "Edit Settings"}, "action_id": "edit_settings", "value": user_id}
					],
				},
			],
		}

	async def _manage_notification_settings(self, user_id: str, setting: str) -> Dict[str, Any]:
		"""Manage notification settings"""
		if setting in ["on", "enable", "enabled"]:
			status = "enabled"
			message = "✅ Notifications have been enabled."
		elif setting in ["off", "disable", "disabled"]:
			status = "disabled"
			message = "❌ Notifications have been disabled."
		else:
			return await self._send_error_response("Invalid setting. Use 'on' or 'off' to enable/disable notifications.")

		return {
			"response_type": "ephemeral",
			"text": message,
			"blocks": [
				{
					"type": "section",
					"text": {"type": "mrkdwn", "text": f"{message}\n\nYou can change this anytime with `/settings notifications <on|off>`"},
				}
			],
		}

	async def _set_default_channel(self, user_id: str, channel: str) -> Dict[str, Any]:
		"""Set default notification channel"""
		if not channel:
			return await self._send_error_response("Please specify a channel. Usage: `/settings channel #channel-name`")

		return {
			"response_type": "ephemeral",
			"text": f"✅ Default channel set to {channel}",
			"blocks": [
				{
					"type": "section",
					"text": {
						"type": "mrkdwn",
						"text": f"✅ Your default notification channel has been set to {channel}.\n\nAll future analysis notifications will be sent there unless specified otherwise.",
					},
				}
			],
		}

	def _parse_command_options(self, args: List[str]) -> Dict[str, Any]:
		"""Parse command line options"""
		options = {}
		i = 0
		while i < len(args):
			arg = args[i]
			if arg.startswith("--"):
				key = arg[2:]
				if i + 1 < len(args) and not args[i + 1].startswith("--"):
					options[key] = args[i + 1]
					i += 2
				else:
					options[key] = True
					i += 1
			else:
				i += 1
		return options

	def _is_valid_url(self, url: str) -> bool:
		"""Validate URL format"""
		return url.startswith(("http://", "https://")) and "." in url

	async def _check_command_permission(self, command: str, user_id: str, channel_id: str) -> bool:
		"""Check if user has permission to use command"""
		cmd = self.commands.get(command)
		if not cmd:
			return False

		if cmd.permission == CommandPermission.PUBLIC:
			return True
		elif cmd.permission == CommandPermission.PRIVATE:
			# Check if it's a DM or user has access
			return True  # Simplified for demo
		elif cmd.permission == CommandPermission.ADMIN:
			# Check if user is admin
			return True  # Simplified for demo

		return False

	async def _send_error_response(self, message: str) -> Dict[str, Any]:
		"""Send error response"""
		return {
			"response_type": "ephemeral",
			"text": f"❌ {message}",
			"blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": f"❌ {message}"}}],
		}

	def get_command_statistics(self) -> Dict[str, Any]:
		"""Get command usage statistics"""
		return {
			"total_commands": self.command_stats["total_commands"],
			"by_command": self.command_stats["by_command"],
			"by_user": self.command_stats["by_user"],
			"errors": self.command_stats["errors"],
			"success_rate": ((self.command_stats["total_commands"] - self.command_stats["errors"]) / self.command_stats["total_commands"] * 100)
			if self.command_stats["total_commands"] > 0
			else 0,
		}
