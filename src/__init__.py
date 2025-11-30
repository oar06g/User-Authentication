from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from src.api import APIV1, templates
from src.middleware import SecurityHeadersMiddleware, RateLimitMiddleware, CSRFMiddleware
from src.exceptions import (
    AuthenticationError, ValidationError, RateLimitError,
    authentication_error_handler, validation_error_handler,
    rate_limit_error_handler, general_exception_handler
)
from src.logger import setup_logging
from src.settings import RATE_LIMIT_PER_MINUTE, RATE_LIMIT_PER_HOUR, DEBUG
import logging

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    # Setup logging
    setup_logging()
    logger.info("Starting User Authentication System")
    
    # Create FastAPI app
    app = FastAPI(
        title="User Authentication System",
        description="Secure authentication system with JWT, email verification, and password reset",
        version="1.0.0",
        debug=DEBUG
    )
    
    # Add security middleware (order matters!)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, 
                      requests_per_minute=RATE_LIMIT_PER_MINUTE,
                      requests_per_hour=RATE_LIMIT_PER_HOUR)
    # Note: CSRF middleware temporarily disabled for initial setup
    # app.add_middleware(CSRFMiddleware)
    
    # Register exception handlers
    app.add_exception_handler(AuthenticationError, authentication_error_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(RateLimitError, rate_limit_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    # index route
    @app.get("/", response_class=HTMLResponse)
    def index(request: Request): return templates.TemplateResponse("index.html", {"request": request})

    # Include routers
    app.include_router(APIV1().router)
    
    logger.info("Application initialized successfully")
    return app

def run():
    """Run the application"""
    app = create_app()
    import uvicorn
    
    logger.info("Starting uvicorn server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
