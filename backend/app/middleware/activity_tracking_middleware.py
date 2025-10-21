"""
Activity Tracking Middleware for Career Co-Pilot System
Automatically tracks user activities for analytics purposes
"""

import logging
from datetime import datetime
from typing import Callable, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.analytics_data_collection_service import analytics_data_collection_service

logger = logging.getLogger(__name__)


class ActivityTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically track user activities for analytics"""
    
    def __init__(self, app, track_all_requests: bool = False):
        super().__init__(app)
        self.track_all_requests = track_all_requests
        
        # Define which endpoints to track and their activity types
        self.tracked_endpoints = {
            # Job-related activities
            '/api/v1/jobs': 'job_view',
            '/api/v1/jobs/': 'job_detail_view',
            '/api/v1/applications': 'application_action',
            '/api/v1/recommendations': 'recommendation_view',
            
            # Analytics activities
            '/api/v1/analytics/': 'analytics_view',
            '/api/v1/skill-gap': 'skill_analysis_view',
            '/api/v1/market-trends': 'market_analysis_view',
            
            # Profile activities
            '/api/v1/profile': 'profile_action',
            '/api/v1/users/': 'user_action',
            
            # Dashboard activities
            '/api/v1/dashboard': 'dashboard_view',
            
            # Search activities
            '/api/v1/saved-searches': 'search_action',
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and track user activity if applicable"""
        start_time = datetime.utcnow()
        
        # Process the request
        response = await call_next(request)
        
        # Track activity after successful request
        if response.status_code < 400:  # Only track successful requests
            await self._track_activity(request, response, start_time)
        
        return response
    
    async def _track_activity(self, request: Request, response: Response, start_time: datetime):
        """Track user activity based on request details"""
        try:
            # Get user ID from request state (set by auth middleware)
            user_id = getattr(request.state, 'user_id', None)
            if not user_id:
                return  # No user to track
            
            # Determine activity type
            activity_type = self._determine_activity_type(request)
            if not activity_type and not self.track_all_requests:
                return  # Not a tracked endpoint
            
            # Prepare activity metadata
            metadata = self._prepare_activity_metadata(request, response, start_time)
            
            # Track the activity
            db = next(get_db())
            try:
                analytics_data_collection_service.track_user_activity(
                    db, user_id, activity_type or 'general_activity', metadata
                )
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to track user activity: {e}")
            # Don't let tracking errors affect the main request
    
    def _determine_activity_type(self, request: Request) -> str:
        """Determine activity type based on request path and method"""
        path = request.url.path
        method = request.method
        
        # Check exact matches first
        if path in self.tracked_endpoints:
            return self.tracked_endpoints[path]
        
        # Check partial matches
        for endpoint_pattern, activity_type in self.tracked_endpoints.items():
            if path.startswith(endpoint_pattern):
                # Customize activity type based on HTTP method
                if method == 'POST':
                    return f"{activity_type}_create"
                elif method == 'PUT' or method == 'PATCH':
                    return f"{activity_type}_update"
                elif method == 'DELETE':
                    return f"{activity_type}_delete"
                else:
                    return activity_type
        
        # Special cases based on path patterns
        if '/jobs/' in path and path.endswith('/apply'):
            return 'job_application'
        elif '/jobs/' in path and '/status' in path:
            return 'job_status_update'
        elif '/analytics/' in path:
            return 'analytics_view'
        elif '/recommendations' in path:
            return 'recommendation_view'
        
        return None
    
    def _prepare_activity_metadata(self, request: Request, response: Response, start_time: datetime) -> Dict[str, Any]:
        """Prepare metadata for activity tracking"""
        end_time = datetime.utcnow()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        metadata = {
            'method': request.method,
            'path': request.url.path,
            'status_code': response.status_code,
            'duration_ms': round(duration_ms, 2),
            'user_agent': request.headers.get('user-agent', ''),
            'ip_address': self._get_client_ip(request),
            'timestamp': start_time.isoformat()
        }
        
        # Add query parameters (excluding sensitive data)
        if request.query_params:
            safe_params = {}
            for key, value in request.query_params.items():
                # Exclude potentially sensitive parameters
                if key.lower() not in ['password', 'token', 'key', 'secret']:
                    safe_params[key] = value
            if safe_params:
                metadata['query_params'] = safe_params
        
        # Add request body size if available
        if hasattr(request, 'body'):
            try:
                body_size = len(request.body) if request.body else 0
                metadata['request_body_size'] = body_size
            except:
                pass
        
        return metadata
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded headers first (for load balancers/proxies)
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        return request.client.host if request.client else 'unknown'


def create_activity_tracking_middleware(track_all_requests: bool = False):
    """Factory function to create activity tracking middleware"""
    def middleware_factory(app):
        return ActivityTrackingMiddleware(app, track_all_requests)
    return middleware_factory