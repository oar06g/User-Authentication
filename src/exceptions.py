"""
Custom exceptions and error handlers for authentication system
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import logging

logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="templates")


class AuthenticationError(Exception):
    """Base authentication exception"""
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class InvalidCredentialsError(AuthenticationError):
    """Invalid username or password"""
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message, status_code=401)


class AccountLockedError(AuthenticationError):
    """Account is locked due to too many failed attempts"""
    def __init__(self, locked_until: int):
        from datetime import datetime
        unlock_time = datetime.fromtimestamp(locked_until).strftime('%Y-%m-%d %H:%M:%S')
        message = f"Account is locked until {unlock_time}"
        super().__init__(message, status_code=423)


class EmailNotVerifiedError(AuthenticationError):
    """Email address not verified"""
    def __init__(self, message: str = "Email address not verified"):
        super().__init__(message, status_code=403)


class TokenExpiredError(AuthenticationError):
    """Token has expired"""
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message, status_code=401)


class TokenInvalidError(AuthenticationError):
    """Token is invalid"""
    def __init__(self, message: str = "Invalid token"):
        super().__init__(message, status_code=401)


class ValidationError(Exception):
    """Input validation error"""
    def __init__(self, errors: list):
        self.errors = errors
        super().__init__("; ".join(errors))


class RateLimitError(Exception):
    """Rate limit exceeded"""
    def __init__(self, message: str = "Rate limit exceeded"):
        self.message = message
        super().__init__(self.message)


async def authentication_error_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors"""
    logger.warning(f"Authentication error: {exc.message} - Path: {request.url.path}")
    
    # For HTML requests, redirect to login
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authentication Error</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }}
                    .error-box {{
                        background: white;
                        padding: 2rem;
                        border-radius: 1rem;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                        text-align: center;
                        max-width: 400px;
                    }}
                    h1 {{ color: #e74c3c; margin-bottom: 1rem; }}
                    p {{ color: #555; margin-bottom: 1.5rem; }}
                    a {{
                        display: inline-block;
                        padding: 0.75rem 1.5rem;
                        background: #667eea;
                        color: white;
                        text-decoration: none;
                        border-radius: 0.5rem;
                        transition: 0.3s;
                    }}
                    a:hover {{ background: #5568d3; }}
                </style>
            </head>
            <body>
                <div class="error-box">
                    <h1>Authentication Required</h1>
                    <p>{exc.message}</p>
                    <a href="/api/v1/login">Go to Login</a>
                </div>
            </body>
            </html>
            """,
            status_code=exc.status_code
        )
    
    # For API requests, return JSON
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc.errors} - Path: {request.url.path}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": exc.errors}
    )


async def rate_limit_error_handler(request: Request, exc: RateLimitError):
    """Handle rate limit errors"""
    logger.warning(f"Rate limit exceeded: {request.client.host if request.client else 'unknown'}")
    
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": exc.message}
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error: {str(exc)} - Path: {request.url.path}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )
