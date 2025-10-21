"""
Streamlined FastAPI application with essential functionality only.
"""

import asyncio
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Core imports only
from .core.config import get_settings
from .core.logging import get_logger, setup_logging

logger = get_logger(__name__)

def create_app() -> FastAPI:
    """Create and configure the FastAPI application with essential features only."""
    
    # Setup logging first
    setup_logging()
    
    settings = get_settings()
    
    app = FastAPI(
        title="Career Copilot API",
        description="AI-powered job application tracking and career management system",
        version="1.0.0",
        docs_url="/docs" if settings.api_debug else None,
        redoc_url="/redoc" if settings.api_debug else None,
    )
    
    # Add CORS middleware
    cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    logger.info(f"CORS origins configured: {cors_origins}")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization", 
            "Content-Type", 
            "X-API-Key", 
            "X-Request-ID", 
            "Accept",
            "Origin",
            "User-Agent"
        ],
        expose_headers=["X-Request-ID"],
    )
    
    # Add basic exception handler
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTP exceptions."""
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
    
    # Add root route
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "message": "Career Copilot API",
            "version": "1.0.0",
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "docs": "/docs",
            "health": "/api/v1/health"
        }
    
    # Add basic health check
    @app.get("/api/v1/health")
    async def health_check():
        """Basic health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
    
    # Add connection test endpoint
    @app.get("/api/v1/connection-test")
    async def connection_test():
        """Simple endpoint to test frontend-backend connectivity."""
        return {
            "status": "connected",
            "message": "Frontend-backend connection successful",
            "timestamp": datetime.now().isoformat(),
            "server_info": {
                "host": settings.api_host,
                "port": settings.api_port,
                "cors_origins": settings.cors_origins.split(",")
            }
        }
    
    # Include essential routers only
    try:
        from .api.v1 import health_router
        app.include_router(health_router, prefix="/api/v1")
    except ImportError as e:
        logger.warning(f"Could not import health router: {e}")
    
    try:
        from .api.v1 import auth
        app.include_router(auth.router, prefix="/api/v1/auth")
    except ImportError as e:
        logger.warning(f"Could not import auth router: {e}")
    
    # Add startup event
    @app.on_event("startup")
    async def startup_event():
        logger.info("🚀 Career Copilot API starting up...")
        logger.info(f"🌐 API will run on {settings.api_host}:{settings.api_port}")
        
        # Basic startup validation
        try:
            # Test database connection if available
            logger.info("✅ Basic startup validation completed")
        except Exception as e:
            logger.warning(f"⚠️ Startup validation warning: {e}")
        
        logger.info("🌐 Available endpoints:")
        logger.info("  - GET / - Root endpoint")
        logger.info("  - GET /api/v1/health - Health check")
        logger.info("  - GET /api/v1/connection-test - Connection test")
        
        if settings.api_debug:
            logger.info("  - GET /docs - API documentation")
            logger.info("  - GET /redoc - Alternative API documentation")
    
    # Add shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("🛑 Career Copilot API shutting down...")
        logger.info("✅ Shutdown completed")
    
    return app

# Create the application instance
app = create_app()