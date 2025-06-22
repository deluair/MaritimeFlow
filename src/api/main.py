"""
Main FastAPI application for MaritimeFlow platform
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import structlog
import time
from typing import Callable

from ..core.config import settings

logger = structlog.get_logger(__name__)


def create_application() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Advanced Maritime Analytics and Supply Chain Intelligence Platform",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add middleware
    add_middleware(application)
    
    # Add routes
    add_routes(application)
    
    # Add event handlers
    add_event_handlers(application)
    
    return application


def add_middleware(app: FastAPI) -> None:
    """Add middleware to the application"""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Gzip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Custom logging middleware
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next: Callable) -> JSONResponse:
        start_time = time.time()
        
        # Log request
        logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None
        )
        
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=f"{process_time:.4f}s"
        )
        
        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


def add_routes(app: FastAPI) -> None:
    """Add API routes to the application"""
    
    from .routes import vessels
    # Optional route imports - only vessels is implemented for now
    # from .routes import ports, analytics, alerts, routes as route_router
    
    # Include route modules
    app.include_router(vessels.router, prefix="/api/v1/vessels", tags=["vessels"])
    # Additional routes can be added here when implemented
    # app.include_router(ports.router, prefix="/api/v1/ports", tags=["ports"])
    # app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
    # app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
    # app.include_router(route_router.router, prefix="/api/v1/routes", tags=["routes"])
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": settings.app_version
        }
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API information"""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "description": "Advanced Maritime Analytics and Supply Chain Intelligence Platform",
            "docs_url": "/docs",
            "health_url": "/health"
        }


def add_event_handlers(app: FastAPI) -> None:
    """Add startup and shutdown event handlers"""
    
    @app.on_event("startup")
    async def startup_event():
        """Application startup handler"""
        logger.info("Starting MaritimeFlow API server")
        logger.info(f"Debug mode: {settings.debug}")
        logger.info(f"API host: {settings.api_host}:{settings.api_port}")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Application shutdown handler"""
        logger.info("Shutting down MaritimeFlow API server")


# Global exception handler
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors"""
    logger.error(
        "Unhandled exception",
        url=str(request.url),
        method=request.method,
        error=str(exc),
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "timestamp": time.time()
        }
    )


# Create application instance
app = create_application()

# Add global exception handler
app.add_exception_handler(Exception, global_exception_handler)


def get_application() -> FastAPI:
    """Get the configured FastAPI application"""
    return app 