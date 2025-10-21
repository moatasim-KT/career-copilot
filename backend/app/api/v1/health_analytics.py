"""
Health Analytics and Reporting API
Endpoints for health check analytics, reporting, and automation management.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse

from ...core.auth import get_current_user_or_api_key
from ...core.logging import get_logger
from ...services.health_analytics_service import get_health_analytics_service, HealthRule
from ...services.health_automation_service import get_health_automation_service

logger = get_logger(__name__)
router = APIRouter(prefix="/health/analytics", tags=["Health Analytics"])


@router.get("/summary")
async def get_health_summary(
    hours: int = Query(24, description="Hours of data to analyze"),
    current_user=Depends(get_current_user_or_api_key)
) -> JSONResponse:
    """
    Get comprehensive health summary and statistics.
    """
    try:
        analytics_service = get_health_analytics_service()
        summary = await analytics_service.get_health_summary(hours)
        
        return JSONResponse(content={
            "summary": {
                "period_start": summary.period_start.isoformat(),
                "period_end": summary.period_end.isoformat(),
                "total_checks": summary.total_checks,
                "healthy_percentage": summary.healthy_percentage,
                "degraded_percentage": summary.degraded_percentage,
                "unhealthy_percentage": summary.unhealthy_percentage,
                "average_response_time_ms": summary.average_response_time_ms,
                "trend": summary.trend.value,
                "incident_count": len(summary.incidents)
            },
            "incidents": summary.incidents
        })
        
    except Exception as e:
        logger.error(f"Failed to get health summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/availability")
async def get_availability_report(
    hours: int = Query(24, description="Hours of data to analyze"),
    current_user=Depends(get_current_user_or_api_key)
) -> JSONResponse:
    """
    Get detailed availability report with SLA metrics.
    """
    try:
        analytics_service = get_health_analytics_service()
        report = await analytics_service.get_availability_report(hours)
        
        return JSONResponse(content=report)
        
    except Exception as e:
        logger.error(f"Failed to get availability report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_performance_trends(
    hours: int = Query(24, description="Hours of data to analyze"),
    current_user=Depends(get_current_user_or_api_key)
) -> JSONResponse:
    """
    Get performance trend analysis for all components.
    """
    try:
        analytics_service = get_health_analytics_service()
        trends = await analytics_service.get_performance_trends(hours)
        
        return JSONResponse(content=trends)
        
    except Exception as e:
        logger.error(f"Failed to get performance trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/component/{component_name}")
async def get_component_analytics(
    component_name: str,
    hours: int = Query(24, description="Hours of data to analyze"),
    current_user=Depends(get_current_user_or_api_key)
) -> JSONResponse:
    """
    Get detailed analytics for a specific component.
    """
    try:
        analytics_service = get_health_analytics_service()
        analytics = await analytics_service.get_component_analytics(component_name, hours)
        
        return JSONResponse(content=analytics)
        
    except Exception as e:
        logger.error(f"Failed to get component analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
async def export_health_data(
    hours: int = Query(24, description="Hours of data to export"),
    format_type: str = Query("json", description="Export format (json)"),
    current_user=Depends(get_current_user_or_api_key)
) -> PlainTextResponse:
    """
    Export health data in specified format.
    """
    try:
        analytics_service = get_health_analytics_service()
        exported_data = await analytics_service.export_health_data(hours, format_type)
        
        filename = f"health_data_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{format_type}"
        
        return PlainTextResponse(
            content=exported_data,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Failed to export health data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/automation/status")
async def get_automation_status(
    current_user=Depends(get_current_user_or_api_key)
) -> JSONResponse:
    """
    Get health automation service status.
    """
    try:
        automation_service = get_health_automation_service()
        status = automation_service.get_rule_status()
        
        return JSONResponse(content={
            "automation_enabled": automation_service.config.enabled,
            "service_running": automation_service.running,
            "check_interval_seconds": automation_service.config.check_interval_seconds,
            "email_notifications": automation_service.config.email_notifications,
            "webhook_notifications": automation_service.config.webhook_notifications,
            "auto_remediation": automation_service.config.auto_remediation,
            "rules": status
        })
        
    except Exception as e:
        logger.error(f"Failed to get automation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/automation/rules")
async def get_automation_rules(
    current_user=Depends(get_current_user_or_api_key)
) -> JSONResponse:
    """
    Get all health automation rules.
    """
    try:
        automation_service = get_health_automation_service()
        rules = automation_service.get_rules()
        
        rules_data = []
        for rule in rules:
            rules_data.append({
                "name": rule.name,
                "condition": rule.condition,
                "duration_minutes": rule.duration_minutes,
                "actions": [action.value for action in rule.actions],
                "enabled": rule.enabled,
                "cooldown_minutes": rule.cooldown_minutes,
                "last_triggered": rule.last_triggered.isoformat() if rule.last_triggered else None
            })
        
        return JSONResponse(content={"rules": rules_data})
        
    except Exception as e:
        logger.error(f"Failed to get automation rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automation/rules")
async def create_automation_rule(
    rule_data: Dict[str, Any],
    current_user=Depends(get_current_user_or_api_key)
) -> JSONResponse:
    """
    Create a new health automation rule.
    """
    try:
        # Validate rule data
        required_fields = ["name", "condition", "duration_minutes", "actions"]
        for field in required_fields:
            if field not in rule_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Convert actions to enum values
        actions = []
        for action_str in rule_data["actions"]:
            try:
                actions.append(AutomationAction(action_str))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid action: {action_str}")
        
        # Create rule
        rule = HealthRule(
            name=rule_data["name"],
            condition=rule_data["condition"],
            duration_minutes=rule_data["duration_minutes"],
            actions=actions,
            enabled=rule_data.get("enabled", True),
            cooldown_minutes=rule_data.get("cooldown_minutes", 30)
        )
        
        automation_service = get_health_automation_service()
        automation_service.add_rule(rule)
        
        return JSONResponse(content={
            "message": "Rule created successfully",
            "rule_name": rule.name
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create automation rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/automation/rules/{rule_name}")
async def delete_automation_rule(
    rule_name: str,
    current_user=Depends(get_current_user_or_api_key)
) -> JSONResponse:
    """
    Delete a health automation rule.
    """
    try:
        automation_service = get_health_automation_service()
        success = automation_service.remove_rule(rule_name)
        
        if success:
            return JSONResponse(content={
                "message": "Rule deleted successfully",
                "rule_name": rule_name
            })
        else:
            raise HTTPException(status_code=404, detail="Rule not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete automation rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automation/start")
async def start_automation(
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user_or_api_key)
) -> JSONResponse:
    """
    Start the health automation service.
    """
    try:
        automation_service = get_health_automation_service()
        
        if automation_service.running:
            return JSONResponse(content={
                "message": "Automation service already running"
            })
        
        # Start automation service in background
        background_tasks.add_task(automation_service.start)
        
        return JSONResponse(content={
            "message": "Automation service starting"
        })
        
    except Exception as e:
        logger.error(f"Failed to start automation service: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automation/stop")
async def stop_automation(
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user_or_api_key)
) -> JSONResponse:
    """
    Stop the health automation service.
    """
    try:
        automation_service = get_health_automation_service()
        
        if not automation_service.running:
            return JSONResponse(content={
                "message": "Automation service not running"
            })
        
        # Stop automation service in background
        background_tasks.add_task(automation_service.stop)
        
        return JSONResponse(content={
            "message": "Automation service stopping"
        })
        
    except Exception as e:
        logger.error(f"Failed to stop automation service: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_health_dashboard(
    current_user=Depends(get_current_user_or_api_key)
) -> JSONResponse:
    """
    Get comprehensive health dashboard data.
    """
    try:
        analytics_service = get_health_analytics_service()
        automation_service = get_health_automation_service()
        
        # Get data for different time periods
        summary_24h = await analytics_service.get_health_summary(24)
        summary_7d = await analytics_service.get_health_summary(24 * 7)
        availability_24h = await analytics_service.get_availability_report(24)
        performance_24h = await analytics_service.get_performance_trends(24)
        automation_status = automation_service.get_rule_status()
        
        dashboard = {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "24h": {
                    "healthy_percentage": summary_24h.healthy_percentage,
                    "degraded_percentage": summary_24h.degraded_percentage,
                    "unhealthy_percentage": summary_24h.unhealthy_percentage,
                    "average_response_time_ms": summary_24h.average_response_time_ms,
                    "trend": summary_24h.trend.value,
                    "incident_count": len(summary_24h.incidents)
                },
                "7d": {
                    "healthy_percentage": summary_7d.healthy_percentage,
                    "degraded_percentage": summary_7d.degraded_percentage,
                    "unhealthy_percentage": summary_7d.unhealthy_percentage,
                    "average_response_time_ms": summary_7d.average_response_time_ms,
                    "trend": summary_7d.trend.value,
                    "incident_count": len(summary_7d.incidents)
                }
            },
            "availability": availability_24h,
            "performance": performance_24h,
            "automation": {
                "enabled": automation_service.config.enabled,
                "running": automation_service.running,
                "total_rules": automation_status["total_rules"],
                "enabled_rules": automation_status["enabled_rules"],
                "active_conditions": automation_status["active_conditions"]
            },
            "recent_incidents": summary_24h.incidents[-5:] if summary_24h.incidents else []
        }
        
        return JSONResponse(content=dashboard)
        
    except Exception as e:
        logger.error(f"Failed to get health dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))