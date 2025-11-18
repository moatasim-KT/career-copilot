"""
Dashboard Layout Service
Manages customizable dashboard layouts for users
"""

import logging
from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.dashboard import DashboardLayout

logger = logging.getLogger(__name__)


class DashboardLayoutService:
	"""Service for managing dashboard layouts"""

	# Default widget configurations
	DEFAULT_WIDGETS: ClassVar[List[Dict[str, Any]]] = [
		{"id": "status-overview", "x": 0, "y": 0, "w": 6, "h": 2, "visible": True},
		{"id": "recent-jobs", "x": 6, "y": 0, "w": 6, "h": 2, "visible": True},
		{"id": "calendar", "x": 0, "y": 2, "w": 6, "h": 4, "visible": True},
		{"id": "ai-recommendations", "x": 6, "y": 2, "w": 6, "h": 4, "visible": True},
		{"id": "application-stats", "x": 0, "y": 6, "w": 4, "h": 3, "visible": True},
		{"id": "activity-timeline", "x": 4, "y": 6, "w": 4, "h": 3, "visible": True},
		{"id": "skills-progress", "x": 8, "y": 6, "w": 4, "h": 3, "visible": True},
		{"id": "goals-tracker", "x": 0, "y": 9, "w": 12, "h": 2, "visible": True},
	]

	# Widget size constraints
	WIDGET_CONSTRAINTS: ClassVar[Dict[str, Dict[str, int]]] = {
		"status-overview": {"minW": 4, "minH": 2, "maxW": 12, "maxH": 4},
		"recent-jobs": {"minW": 4, "minH": 2, "maxW": 12, "maxH": 6},
		"calendar": {"minW": 4, "minH": 3, "maxW": 12, "maxH": 8},
		"ai-recommendations": {"minW": 4, "minH": 3, "maxW": 12, "maxH": 8},
		"application-stats": {"minW": 3, "minH": 2, "maxW": 6, "maxH": 4},
		"activity-timeline": {"minW": 3, "minH": 2, "maxW": 12, "maxH": 6},
		"skills-progress": {"minW": 3, "minH": 2, "maxW": 8, "maxH": 5},
		"goals-tracker": {"minW": 6, "minH": 2, "maxW": 12, "maxH": 4},
	}

	# Responsive breakpoints configuration
	BREAKPOINTS: ClassVar[Dict[str, Dict[str, int]]] = {
		"lg": {"cols": 12, "rowHeight": 100, "width": 1200},
		"md": {"cols": 10, "rowHeight": 100, "width": 996},
		"sm": {"cols": 6, "rowHeight": 100, "width": 768},
		"xs": {"cols": 4, "rowHeight": 100, "width": 480},
		"xxs": {"cols": 2, "rowHeight": 100, "width": 0},
	}

	def __init__(self, db: Session):
		"""
		Initialize dashboard layout service.

		Args:
		    db: Database session
		"""
		self.db = db

	def get_user_layout(self, user_id: int) -> Dict[str, Any]:
		"""
		Get user's dashboard layout or return default.

		Args:
		    user_id: User ID

		Returns:
		    Dashboard layout configuration
		"""
		try:
			layout = self.db.query(DashboardLayout).filter(DashboardLayout.user_id == user_id).first()

			if layout:
				return {
					"layout": layout.layout_config,
					"updated_at": layout.updated_at.isoformat(),
				}

			# Return default layout
			return {
				"layout": {
					"widgets": self.DEFAULT_WIDGETS.copy(),
					"breakpoints": self.BREAKPOINTS,
					"constraints": self.WIDGET_CONSTRAINTS,
				},
				"updated_at": None,
			}

		except Exception as e:
			logger.error(f"Error fetching layout for user {user_id}: {e!s}")
			# Return default on error
			return {
				"layout": {
					"widgets": self.DEFAULT_WIDGETS.copy(),
					"breakpoints": self.BREAKPOINTS,
					"constraints": self.WIDGET_CONSTRAINTS,
				},
				"updated_at": None,
			}

	def save_user_layout(self, user_id: int, layout_config: Dict[str, Any]) -> DashboardLayout:
		"""
		Save user's custom dashboard layout.

		Args:
		    user_id: User ID
		    layout_config: Layout configuration dictionary

		Returns:
		    DashboardLayout object

		Raises:
		    ValueError: If layout is invalid
		"""
		try:
			# Validate layout
			self._validate_layout(layout_config)

			# Check if layout exists
			layout = self.db.query(DashboardLayout).filter(DashboardLayout.user_id == user_id).first()

			if layout:
				# Update existing
				layout.layout_config = layout_config
				layout.updated_at = datetime.utcnow()
			else:
				# Create new
				layout = DashboardLayout(
					user_id=user_id,
					layout_config=layout_config,
				)
				self.db.add(layout)

			self.db.commit()
			self.db.refresh(layout)

			logger.info(f"Saved dashboard layout for user {user_id}")
			return layout

		except ValueError:
			raise
		except Exception as e:
			self.db.rollback()
			logger.error(f"Error saving layout for user {user_id}: {e!s}")
			raise

	def reset_to_default(self, user_id: int) -> DashboardLayout:
		"""
		Reset user's dashboard to default layout.

		Args:
		    user_id: User ID

		Returns:
		    DashboardLayout object with default configuration
		"""
		try:
			default_config = {
				"widgets": self.DEFAULT_WIDGETS.copy(),
				"breakpoints": self.BREAKPOINTS,
				"constraints": self.WIDGET_CONSTRAINTS,
			}

			return self.save_user_layout(user_id, default_config)

		except Exception as e:
			logger.error(f"Error resetting layout for user {user_id}: {e!s}")
			raise

	def toggle_widget_visibility(self, user_id: int, widget_id: str, visible: bool) -> DashboardLayout:
		"""
		Toggle visibility of a specific widget.

		Args:
		    user_id: User ID
		    widget_id: Widget identifier
		    visible: New visibility state

		Returns:
		    Updated DashboardLayout object
		"""
		try:
			layout_data = self.get_user_layout(user_id)
			layout_config = layout_data["layout"]

			# Find and update widget
			widgets = layout_config.get("widgets", [])
			widget_found = False

			for widget in widgets:
				if widget["id"] == widget_id:
					widget["visible"] = visible
					widget_found = True
					break

			if not widget_found:
				raise ValueError(f"Widget {widget_id} not found")

			return self.save_user_layout(user_id, layout_config)

		except Exception as e:
			logger.error(f"Error toggling widget {widget_id} for user {user_id}: {e!s}")
			raise

	def update_widget_position(
		self,
		user_id: int,
		widget_id: str,
		x: int,
		y: int,
		w: Optional[int] = None,
		h: Optional[int] = None,
	) -> DashboardLayout:
		"""
		Update widget position and/or size.

		Args:
		    user_id: User ID
		    widget_id: Widget identifier
		    x: X position in grid
		    y: Y position in grid
		    w: Width (optional)
		    h: Height (optional)

		Returns:
		    Updated DashboardLayout object
		"""
		try:
			layout_data = self.get_user_layout(user_id)
			layout_config = layout_data["layout"]

			# Find and update widget
			widgets = layout_config.get("widgets", [])
			widget_found = False

			for widget in widgets:
				if widget["id"] == widget_id:
					widget["x"] = x
					widget["y"] = y
					if w is not None:
						widget["w"] = w
					if h is not None:
						widget["h"] = h

					# Validate against constraints
					self._validate_widget_size(widget)
					widget_found = True
					break

			if not widget_found:
				raise ValueError(f"Widget {widget_id} not found")

			return self.save_user_layout(user_id, layout_config)

		except Exception as e:
			logger.error(f"Error updating widget {widget_id} for user {user_id}: {e!s}")
			raise

	def add_custom_widget(self, user_id: int, widget_id: str, x: int, y: int, w: int, h: int) -> DashboardLayout:
		"""
		Add a new custom widget to user's dashboard.

		Args:
		    user_id: User ID
		    widget_id: Widget identifier
		    x: X position
		    y: Y position
		    w: Width
		    h: Height

		Returns:
		    Updated DashboardLayout object
		"""
		try:
			layout_data = self.get_user_layout(user_id)
			layout_config = layout_data["layout"]

			# Check if widget already exists
			widgets = layout_config.get("widgets", [])
			if any(widget["id"] == widget_id for widget in widgets):
				raise ValueError(f"Widget {widget_id} already exists")

			# Add new widget
			new_widget = {
				"id": widget_id,
				"x": x,
				"y": y,
				"w": w,
				"h": h,
				"visible": True,
			}

			widgets.append(new_widget)
			layout_config["widgets"] = widgets

			return self.save_user_layout(user_id, layout_config)

		except Exception as e:
			logger.error(f"Error adding widget {widget_id} for user {user_id}: {e!s}")
			raise

	def remove_widget(self, user_id: int, widget_id: str) -> DashboardLayout:
		"""
		Remove a widget from user's dashboard.

		Args:
		    user_id: User ID
		    widget_id: Widget identifier

		Returns:
		    Updated DashboardLayout object
		"""
		try:
			layout_data = self.get_user_layout(user_id)
			layout_config = layout_data["layout"]

			widgets = layout_config.get("widgets", [])
			original_count = len(widgets)

			# Remove widget
			widgets = [w for w in widgets if w["id"] != widget_id]

			if len(widgets) == original_count:
				raise ValueError(f"Widget {widget_id} not found")

			layout_config["widgets"] = widgets

			return self.save_user_layout(user_id, layout_config)

		except Exception as e:
			logger.error(f"Error removing widget {widget_id} for user {user_id}: {e!s}")
			raise

	def _validate_layout(self, layout_config: Dict[str, Any]) -> None:
		"""
		Validate layout configuration.

		Args:
		    layout_config: Layout configuration to validate

		Raises:
		    ValueError: If layout is invalid
		"""
		if not isinstance(layout_config, dict):
			raise ValueError("Layout config must be a dictionary")

		if "widgets" not in layout_config:
			raise ValueError("Layout config must contain 'widgets' key")

		widgets = layout_config["widgets"]
		if not isinstance(widgets, list):
			raise ValueError("Widgets must be a list")

		# Validate each widget
		for widget in widgets:
			self._validate_widget(widget)

	def _validate_widget(self, widget: Dict[str, Any]) -> None:
		"""
		Validate individual widget configuration.

		Args:
		    widget: Widget configuration

		Raises:
		    ValueError: If widget is invalid
		"""
		required_fields = ["id", "x", "y", "w", "h"]
		for field in required_fields:
			if field not in widget:
				raise ValueError(f"Widget missing required field: {field}")

		# Validate numeric fields
		if not isinstance(widget["x"], int) or widget["x"] < 0:
			raise ValueError("Widget x must be non-negative integer")
		if not isinstance(widget["y"], int) or widget["y"] < 0:
			raise ValueError("Widget y must be non-negative integer")
		if not isinstance(widget["w"], int) or widget["w"] <= 0:
			raise ValueError("Widget width must be positive integer")
		if not isinstance(widget["h"], int) or widget["h"] <= 0:
			raise ValueError("Widget height must be positive integer")

		# Validate against constraints
		self._validate_widget_size(widget)

	def _validate_widget_size(self, widget: Dict[str, Any]) -> None:
		"""
		Validate widget size against constraints.

		Args:
		    widget: Widget configuration

		Raises:
		    ValueError: If widget size violates constraints
		"""
		widget_id = widget["id"]
		constraints = self.WIDGET_CONSTRAINTS.get(widget_id)

		if not constraints:
			# No constraints for this widget, allow any size
			return

		w, h = widget["w"], widget["h"]

		if w < constraints["minW"]:
			raise ValueError(f"Widget {widget_id} width below minimum: {constraints['minW']}")
		if h < constraints["minH"]:
			raise ValueError(f"Widget {widget_id} height below minimum: {constraints['minH']}")
		if w > constraints["maxW"]:
			raise ValueError(f"Widget {widget_id} width exceeds maximum: {constraints['maxW']}")
		if h > constraints["maxH"]:
			raise ValueError(f"Widget {widget_id} height exceeds maximum: {constraints['maxH']}")

	def get_available_widgets(self) -> List[Dict[str, Any]]:
		"""
		Get list of available widgets with metadata.

		Returns:
		    List of widget metadata dictionaries
		"""
		return [
			{
				"id": "status-overview",
				"name": "Application Status",
				"description": "Overview of application statuses",
				"type": "status",
				"constraints": self.WIDGET_CONSTRAINTS["status-overview"],
			},
			{
				"id": "recent-jobs",
				"name": "Recent Job Postings",
				"description": "Latest job postings matching your profile",
				"type": "feed",
				"constraints": self.WIDGET_CONSTRAINTS["recent-jobs"],
			},
			{
				"id": "calendar",
				"name": "Upcoming Interviews",
				"description": "Calendar view of scheduled interviews",
				"type": "calendar",
				"constraints": self.WIDGET_CONSTRAINTS["calendar"],
			},
			{
				"id": "ai-recommendations",
				"name": "AI Job Matches",
				"description": "AI-powered job recommendations",
				"type": "recommendations",
				"constraints": self.WIDGET_CONSTRAINTS["ai-recommendations"],
			},
			{
				"id": "application-stats",
				"name": "Application Statistics",
				"description": "Key metrics about your applications",
				"type": "stats",
				"constraints": self.WIDGET_CONSTRAINTS["application-stats"],
			},
			{
				"id": "activity-timeline",
				"name": "Recent Activity",
				"description": "Timeline of recent application activities",
				"type": "timeline",
				"constraints": self.WIDGET_CONSTRAINTS["activity-timeline"],
			},
			{
				"id": "skills-progress",
				"name": "Skills Development",
				"description": "Track your skill development progress",
				"type": "progress",
				"constraints": self.WIDGET_CONSTRAINTS["skills-progress"],
			},
			{
				"id": "goals-tracker",
				"name": "Career Goals",
				"description": "Monitor your career goals and milestones",
				"type": "goals",
				"constraints": self.WIDGET_CONSTRAINTS["goals-tracker"],
			},
		]
