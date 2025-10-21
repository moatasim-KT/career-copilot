"""
Real-time Analysis Status API Endpoints

This module provides WebSocket and Server-Sent Events (SSE) endpoints for real-time
progress updates, agent-level progress tracking, estimated time remaining calculation,
and cancellation support for job application tracking workflows.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request, Query
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from ...core.auth import get_current_user
from ...core.exceptions import WorkflowExecutionError, ErrorCategory, ErrorSeverity
from ...models.database_models import User
from ...models.agent_models import (
    AgentState,
    WorkflowState,
    WorkflowProgress,
    get_workflow_progress_manager,
    AgentProgressMetrics
)
from ...agents.orchestration_service import get_orchestration_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis-status"])


class AnalysisStatusResponse(BaseModel):
    """Response model for analysis status."""
    
    analysis_id: str
    workflow_id: str
    status: str
    progress_percentage: float
    current_stage: str
    current_agent: Optional[str]
    
    # Agent details
    total_agents: int
    completed_agents: int
    failed_agents: int
    running_agents: int
    
    # Timing information
    start_time: str
    estimated_completion_time: Optional[str]
    elapsed_time: float
    estimated_remaining_time: Optional[float]
    
    # Cancellation support
    can_cancel: bool
    cancellation_reason: Optional[str]
    
    # Error information
    error_message: Optional[str]
    
    # Agent-level progress
    agent_progress: Dict[str, Dict[str, Any]]


class AgentProgressDetail(BaseModel):
    """Detailed agent progress information."""
    
    agent_name: str
    state: str
    progress_percentage: float
    current_operation: str
    start_time: Optional[str]
    end_time: Optional[str]
    execution_time: Optional[float]
    estimated_completion_time: Optional[str]
    error_message: Optional[str]
    retry_count: int
    token_usage: Optional[int]
    cost: Optional[float]


class CancellationRequest(BaseModel):
    """Request model for analysis cancellation."""
    
    reason: Optional[str] = Field(None, description="Reason for cancellation")
    force: bool = Field(False, description="Force cancellation even if not recommended")


class ConnectionManager:
    """Enhanced connection manager for WebSocket and SSE connections."""
    
    def __init__(self):
        self.websocket_connections: Dict[str, Set[WebSocket]] = {}
        self.sse_connections: Dict[str, Set] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        self.heartbeat_interval = 30  # seconds
        self._heartbeat_task: Optional[asyncio.Task] = None
        
    async def connect_websocket(self, websocket: WebSocket, analysis_id: str, user_id: str):
        """Connect WebSocket for analysis updates."""
        await websocket.accept()
        
        if analysis_id not in self.websocket_connections:
            self.websocket_connections[analysis_id] = set()
        
        self.websocket_connections[analysis_id].add(websocket)
        
        # Store connection metadata
        connection_id = f"ws_{analysis_id}_{user_id}_{id(websocket)}"
        self.connection_metadata[connection_id] = {
            "type": "websocket",
            "analysis_id": analysis_id,
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "websocket": websocket
        }
        
        logger.info(f"WebSocket connected for analysis {analysis_id} by user {user_id}")
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "analysis_id": analysis_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return connection_id
    
    def disconnect_websocket(self, websocket: WebSocket, analysis_id: str):
        """Disconnect WebSocket."""
        if analysis_id in self.websocket_connections:
            self.websocket_connections[analysis_id].discard(websocket)
            if not self.websocket_connections[analysis_id]:
                del self.websocket_connections[analysis_id]
        
        # Clean up metadata
        to_remove = []
        for conn_id, metadata in self.connection_metadata.items():
            if metadata.get("websocket") == websocket:
                to_remove.append(conn_id)
        
        for conn_id in to_remove:
            del self.connection_metadata[conn_id]
        
        logger.info(f"WebSocket disconnected for analysis {analysis_id}")
    
    async def broadcast_to_analysis(self, analysis_id: str, message: Dict[str, Any]):
        """Broadcast message to all connections for an analysis."""
        message["timestamp"] = datetime.utcnow().isoformat()
        
        # Broadcast to WebSocket connections
        if analysis_id in self.websocket_connections:
            disconnected = set()
            for websocket in self.websocket_connections[analysis_id].copy():
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send WebSocket message: {e}")
                    disconnected.add(websocket)
            
            # Remove disconnected WebSockets
            for websocket in disconnected:
                self.websocket_connections[analysis_id].discard(websocket)
        
        # Broadcast to SSE connections would be handled separately
        # as SSE connections are managed differently
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        total_ws = sum(len(connections) for connections in self.websocket_connections.values())
        
        return {
            "total_websocket_connections": total_ws,
            "active_analyses": list(self.websocket_connections.keys()),
            "connection_count_by_analysis": {
                analysis_id: len(connections) 
                for analysis_id, connections in self.websocket_connections.items()
            }
        }


# Global connection manager
connection_manager = ConnectionManager()


@router.websocket("/ws/{analysis_id}")
async def websocket_analysis_status(
    websocket: WebSocket,
    analysis_id: str,
    user_id: str = Query(..., description="User ID for authentication")
):
    """
    WebSocket endpoint for real-time analysis progress updates.
    
    Provides:
    - Real-time progress updates
    - Agent-level progress tracking
    - Estimated time remaining
    - Error notifications
    - Cancellation support
    """
    connection_id = None
    
    try:
        # Connect WebSocket
        connection_id = await connection_manager.connect_websocket(websocket, analysis_id, user_id)
        
        # Get workflow progress manager
        workflow_manager = get_workflow_progress_manager()
        
        # Send initial status
        workflow = workflow_manager.get_workflow(analysis_id)
        if workflow:
            initial_status = await _get_detailed_analysis_status(analysis_id, workflow)
            await websocket.send_json({
                "type": "initial_status",
                "data": initial_status.dict()
            })
        else:
            await websocket.send_json({
                "type": "error",
                "message": f"Analysis {analysis_id} not found"
            })
            return
        
        # Main message loop
        update_interval = 2.0  # seconds
        last_update = datetime.utcnow()
        
        while True:
            try:
                # Check for incoming messages (non-blocking)
                message = await asyncio.wait_for(websocket.receive_json(), timeout=0.1)
                await _handle_websocket_message(websocket, analysis_id, message, user_id)
            except asyncio.TimeoutError:
                # No message received, continue with periodic updates
                pass
            except Exception as e:
                logger.error(f"Error receiving WebSocket message: {e}")
                break
            
            # Send periodic updates
            now = datetime.utcnow()
            if (now - last_update).total_seconds() >= update_interval:
                workflow = workflow_manager.get_workflow(analysis_id)
                if workflow:
                    current_status = await _get_detailed_analysis_status(analysis_id, workflow)
                    
                    await websocket.send_json({
                        "type": "progress_update",
                        "data": current_status.dict()
                    })
                    
                    # Check if analysis is finished
                    if workflow.workflow_state in [
                        WorkflowState.COMPLETED, 
                        WorkflowState.FAILED, 
                        WorkflowState.CANCELLED
                    ]:
                        await websocket.send_json({
                            "type": "analysis_finished",
                            "final_status": workflow.workflow_state.value,
                            "data": current_status.dict()
                        })
                        break
                
                last_update = now
            
            # Small sleep to prevent busy waiting
            await asyncio.sleep(0.1)
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for analysis {analysis_id}")
    except Exception as e:
        logger.error(f"WebSocket error for analysis {analysis_id}: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Connection error: {str(e)}"
            })
        except:
            pass
    finally:
        if connection_id:
            connection_manager.disconnect_websocket(websocket, analysis_id)


async def _handle_websocket_message(
    websocket: WebSocket, 
    analysis_id: str, 
    message: Dict[str, Any], 
    user_id: str
):
    """Handle incoming WebSocket messages."""
    message_type = message.get("type")
    
    if message_type == "ping":
        # Respond to ping with pong
        await websocket.send_json({
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    elif message_type == "request_update":
        # Client requesting immediate update
        workflow_manager = get_workflow_progress_manager()
        workflow = workflow_manager.get_workflow(analysis_id)
        
        if workflow:
            current_status = await _get_detailed_analysis_status(analysis_id, workflow)
            await websocket.send_json({
                "type": "progress_update",
                "data": current_status.dict()
            })
    
    elif message_type == "cancel_analysis":
        # Client requesting analysis cancellation
        try:
            reason = message.get("data", {}).get("reason", "User requested cancellation")
            force = message.get("data", {}).get("force", False)
            
            success = await _cancel_analysis(analysis_id, reason, force, user_id)
            
            await websocket.send_json({
                "type": "cancel_response",
                "success": success,
                "message": "Analysis cancellation requested" if success else "Failed to cancel analysis"
            })
        except Exception as e:
            await websocket.send_json({
                "type": "cancel_response",
                "success": False,
                "message": f"Cancellation error: {str(e)}"
            })
    
    elif message_type == "get_agent_details":
        # Client requesting detailed agent information
        agent_name = message.get("data", {}).get("agent_name")
        if agent_name:
            agent_details = await _get_agent_details(analysis_id, agent_name)
            await websocket.send_json({
                "type": "agent_details",
                "agent_name": agent_name,
                "data": agent_details
            })


@router.get("/sse/{analysis_id}")
async def sse_analysis_status(
    request: Request,
    analysis_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Server-Sent Events (SSE) endpoint for real-time analysis progress updates.
    
    Alternative to WebSocket for clients that prefer SSE.
    """
    
    async def event_generator():
        """Generate SSE events for analysis progress."""
        workflow_manager = get_workflow_progress_manager()
        last_update = datetime.utcnow()
        update_interval = 3.0  # seconds (slightly longer than WebSocket)
        
        # Send initial status
        workflow = workflow_manager.get_workflow(analysis_id)
        if not workflow:
            yield {
                "event": "error",
                "data": json.dumps({"message": f"Analysis {analysis_id} not found"})
            }
            return
        
        initial_status = await _get_detailed_analysis_status(analysis_id, workflow)
        yield {
            "event": "initial_status",
            "data": json.dumps(initial_status.dict())
        }
        
        # Send periodic updates
        while True:
            try:
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info(f"SSE client disconnected for analysis {analysis_id}")
                    break
                
                now = datetime.utcnow()
                if (now - last_update).total_seconds() >= update_interval:
                    workflow = workflow_manager.get_workflow(analysis_id)
                    if workflow:
                        current_status = await _get_detailed_analysis_status(analysis_id, workflow)
                        
                        yield {
                            "event": "progress_update",
                            "data": json.dumps(current_status.dict())
                        }
                        
                        # Check if analysis is finished
                        if workflow.workflow_state in [
                            WorkflowState.COMPLETED, 
                            WorkflowState.FAILED, 
                            WorkflowState.CANCELLED
                        ]:
                            yield {
                                "event": "analysis_finished",
                                "data": json.dumps({
                                    "final_status": workflow.workflow_state.value,
                                    "analysis": current_status.dict()
                                })
                            }
                            break
                    
                    last_update = now
                
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"SSE error for analysis {analysis_id}: {e}")
                yield {
                    "event": "error",
                    "data": json.dumps({"message": f"Stream error: {str(e)}"})
                }
                break
    
    return EventSourceResponse(event_generator())


@router.get("/status/{analysis_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    analysis_id: str,
    current_user: User = Depends(get_current_user)
) -> AnalysisStatusResponse:
    """
    Get current analysis status (REST endpoint).
    
    Provides detailed status information including:
    - Overall progress and current stage
    - Agent-level progress details
    - Timing information and estimates
    - Cancellation capabilities
    """
    workflow_manager = get_workflow_progress_manager()
    workflow = workflow_manager.get_workflow(analysis_id)
    
    if not workflow:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis {analysis_id} not found"
        )
    
    return await _get_detailed_analysis_status(analysis_id, workflow)


@router.post("/cancel/{analysis_id}")
async def cancel_analysis(
    analysis_id: str,
    cancellation_request: CancellationRequest,
    current_user: User = Depends(get_current_user)
) -> JSONResponse:
    """
    Cancel a running analysis.
    
    Supports:
    - Graceful cancellation with reason
    - Force cancellation for stuck analyses
    - User tracking for audit purposes
    """
    try:
        success = await _cancel_analysis(
            analysis_id, 
            cancellation_request.reason or "User requested cancellation",
            cancellation_request.force,
            current_user.username
        )
        
        if success:
            # Broadcast cancellation to all connected clients
            await connection_manager.broadcast_to_analysis(analysis_id, {
                "type": "analysis_cancelled",
                "reason": cancellation_request.reason,
                "cancelled_by": current_user.username
            })
            
            return JSONResponse(
                status_code=200,
                content={
                    "message": f"Analysis {analysis_id} has been cancelled",
                    "analysis_id": analysis_id,
                    "cancelled_at": datetime.utcnow().isoformat(),
                    "cancelled_by": current_user.username,
                    "reason": cancellation_request.reason
                }
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to cancel analysis {analysis_id}"
            )
    
    except Exception as e:
        logger.error(f"Error cancelling analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel analysis: {str(e)}"
        )


@router.get("/agent/{analysis_id}/{agent_name}", response_model=AgentProgressDetail)
async def get_agent_progress(
    analysis_id: str,
    agent_name: str,
    current_user: User = Depends(get_current_user)
) -> AgentProgressDetail:
    """
    Get detailed progress information for a specific agent.
    
    Provides:
    - Current agent state and progress
    - Execution timing and estimates
    - Resource usage (tokens, cost)
    - Error information and retry count
    """
    workflow_manager = get_workflow_progress_manager()
    workflow = workflow_manager.get_workflow(analysis_id)
    
    if not workflow:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis {analysis_id} not found"
        )
    
    if agent_name not in workflow.agent_progress:
        raise HTTPException(
            status_code=404,
            detail=f"Agent {agent_name} not found in analysis {analysis_id}"
        )
    
    agent_metrics = workflow.agent_progress[agent_name]
    
    return AgentProgressDetail(
        agent_name=agent_metrics.agent_name,
        state=agent_metrics.state.value,
        progress_percentage=agent_metrics.progress_percentage,
        current_operation=agent_metrics.current_operation,
        start_time=agent_metrics.start_time.isoformat() if agent_metrics.start_time else None,
        end_time=agent_metrics.end_time.isoformat() if agent_metrics.end_time else None,
        execution_time=agent_metrics.execution_time,
        estimated_completion_time=agent_metrics.estimated_completion_time.isoformat() if agent_metrics.estimated_completion_time else None,
        error_message=agent_metrics.error_message,
        retry_count=agent_metrics.retry_count,
        token_usage=None,  # Would be populated from agent execution data
        cost=None  # Would be populated from agent execution data
    )


@router.get("/connections/stats")
async def get_connection_stats(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get statistics about active connections."""
    return connection_manager.get_connection_stats()


async def _get_detailed_analysis_status(
    analysis_id: str, 
    workflow: WorkflowProgress
) -> AnalysisStatusResponse:
    """Get detailed analysis status from workflow progress."""
    
    # Calculate elapsed time
    elapsed_time = (datetime.utcnow() - workflow.start_time).total_seconds()
    
    # Calculate estimated remaining time
    estimated_remaining_time = None
    if workflow.overall_progress_percentage > 0:
        estimated_total_time = elapsed_time / (workflow.overall_progress_percentage / 100.0)
        estimated_remaining_time = max(0, estimated_total_time - elapsed_time)
    
    # Determine if analysis can be cancelled
    can_cancel = workflow.workflow_state in [WorkflowState.RUNNING, WorkflowState.INITIALIZED]
    
    # Build agent progress details
    agent_progress = {}
    for agent_name, metrics in workflow.agent_progress.items():
        agent_progress[agent_name] = {
            "state": metrics.state.value,
            "progress_percentage": round(metrics.progress_percentage, 2),
            "current_operation": metrics.current_operation,
            "start_time": metrics.start_time.isoformat() if metrics.start_time else None,
            "end_time": metrics.end_time.isoformat() if metrics.end_time else None,
            "execution_time": metrics.execution_time,
            "estimated_completion_time": metrics.estimated_completion_time.isoformat() if metrics.estimated_completion_time else None,
            "error_message": metrics.error_message,
            "retry_count": metrics.retry_count
        }
    
    return AnalysisStatusResponse(
        analysis_id=analysis_id,
        workflow_id=workflow.workflow_id,
        status=workflow.workflow_state.value,
        progress_percentage=round(workflow.overall_progress_percentage, 2),
        current_stage=workflow.current_stage,
        current_agent=workflow.current_agent,
        total_agents=workflow.total_agents,
        completed_agents=workflow.completed_agents,
        failed_agents=workflow.failed_agents,
        running_agents=workflow.running_agents,
        start_time=workflow.start_time.isoformat(),
        estimated_completion_time=workflow.estimated_completion_time.isoformat() if workflow.estimated_completion_time else None,
        elapsed_time=elapsed_time,
        estimated_remaining_time=estimated_remaining_time,
        can_cancel=can_cancel,
        cancellation_reason=None,
        error_message=workflow.error_message,
        agent_progress=agent_progress
    )


async def _cancel_analysis(
    analysis_id: str, 
    reason: str, 
    force: bool, 
    user_id: str
) -> bool:
    """Cancel an analysis workflow."""
    try:
        workflow_manager = get_workflow_progress_manager()
        workflow = workflow_manager.get_workflow(analysis_id)
        
        if not workflow:
            logger.warning(f"Cannot cancel analysis {analysis_id}: not found")
            return False
        
        # Check if analysis can be cancelled
        if not force and workflow.workflow_state not in [WorkflowState.RUNNING, WorkflowState.INITIALIZED]:
            logger.warning(f"Cannot cancel analysis {analysis_id}: state is {workflow.workflow_state.value}")
            return False
        
        # Cancel the workflow
        success = workflow_manager.cancel_workflow(analysis_id)
        
        if success:
            logger.info(f"Analysis {analysis_id} cancelled by user {user_id}: {reason}")
            
            # Try to cancel at orchestration level if available
            try:
                orchestration_service = get_orchestration_service()
                await orchestration_service.cancel_workflow(analysis_id)
            except Exception as e:
                logger.warning(f"Failed to cancel at orchestration level: {e}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error cancelling analysis {analysis_id}: {e}")
        return False


async def _get_agent_details(analysis_id: str, agent_name: str) -> Dict[str, Any]:
    """Get detailed information about a specific agent."""
    workflow_manager = get_workflow_progress_manager()
    workflow = workflow_manager.get_workflow(analysis_id)
    
    if not workflow or agent_name not in workflow.agent_progress:
        return {}
    
    agent_metrics = workflow.agent_progress[agent_name]
    
    return {
        "agent_name": agent_metrics.agent_name,
        "state": agent_metrics.state.value,
        "progress_percentage": agent_metrics.progress_percentage,
        "current_operation": agent_metrics.current_operation,
        "start_time": agent_metrics.start_time.isoformat() if agent_metrics.start_time else None,
        "end_time": agent_metrics.end_time.isoformat() if agent_metrics.end_time else None,
        "execution_time": agent_metrics.execution_time,
        "estimated_completion_time": agent_metrics.estimated_completion_time.isoformat() if agent_metrics.estimated_completion_time else None,
        "error_message": agent_metrics.error_message,
        "retry_count": agent_metrics.retry_count,
        "health_status": "healthy" if agent_metrics.state == AgentState.RUNNING else "idle"
    }


# Broadcast function for external use
async def broadcast_analysis_update(analysis_id: str, update_data: Dict[str, Any]):
    """Broadcast analysis update to all connected clients."""
    await connection_manager.broadcast_to_analysis(analysis_id, {
        "type": "progress_update",
        "data": update_data
    })


# Function to notify analysis completion
async def notify_analysis_completion(analysis_id: str, final_status: str, results: Dict[str, Any]):
    """Notify all connected clients of analysis completion."""
    await connection_manager.broadcast_to_analysis(analysis_id, {
        "type": "analysis_finished",
        "final_status": final_status,
        "results": results
    })


# Function to notify analysis error
async def notify_analysis_error(analysis_id: str, error_message: str, error_details: Dict[str, Any]):
    """Notify all connected clients of analysis error."""
    await connection_manager.broadcast_to_analysis(analysis_id, {
        "type": "analysis_error",
        "error_message": error_message,
        "error_details": error_details
    })