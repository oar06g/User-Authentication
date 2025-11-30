"""
Security middleware for authentication system
Includes CSRF protection, rate limiting, and security headers
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.datastructures import Headers
import time
import secrets
from collections import defaultdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent brute force attacks
    Limits requests per IP address
    """
    
    def __init__(self, app, requests_per_minute: int = 60, requests_per_hour: int = 300):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.minute_requests = defaultdict(list)
        self.hour_requests = defaultdict(list)
        self.blocked_ips = {}
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def is_rate_limited(self, ip: str) -> tuple[bool, str]:
        """Check if IP is rate limited"""
        now = datetime.now()
        
        # Check if IP is blocked
        if ip in self.blocked_ips:
            if now < self.blocked_ips[ip]:
                remaining = (self.blocked_ips[ip] - now).seconds
                return True, f"IP blocked. Try again in {remaining} seconds"
            else:
                del self.blocked_ips[ip]
        
        # Clean old requests (minute)
        minute_ago = now - timedelta(minutes=1)
        self.minute_requests[ip] = [
            req_time for req_time in self.minute_requests[ip] 
            if req_time > minute_ago
        ]
        
        # Clean old requests (hour)
        hour_ago = now - timedelta(hours=1)
        self.hour_requests[ip] = [
            req_time for req_time in self.hour_requests[ip] 
            if req_time > hour_ago
        ]
        
        # Check minute limit
        if len(self.minute_requests[ip]) >= self.requests_per_minute:
            # Block for 5 minutes
            self.blocked_ips[ip] = now + timedelta(minutes=5)
            logger.warning(f"Rate limit exceeded for IP {ip} - blocked for 5 minutes")
            return True, "Too many requests. Try again in 5 minutes"
        
        # Check hour limit
        if len(self.hour_requests[ip]) >= self.requests_per_hour:
            return True, "Hourly rate limit exceeded. Try again later"
        
        # Add current request
        self.minute_requests[ip].append(now)
        self.hour_requests[ip].append(now)
        
        return False, ""
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for static files
        if request.url.path.startswith("/static"):
            return await call_next(request)
        
        ip = self.get_client_ip(request)
        is_limited, message = self.is_rate_limited(ip)
        
        if is_limited:
            logger.warning(f"Rate limit hit for {ip}: {message}")
            return JSONResponse(
                status_code=429,
                content={"detail": message}
            )
        
        response = await call_next(request)
        return response


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware"""
    
    SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
    CSRF_COOKIE_NAME = "csrf_token"
    CSRF_HEADER_NAME = "X-CSRF-Token"
    
    async def dispatch(self, request: Request, call_next):
        # Skip CSRF for safe methods
        if request.method in self.SAFE_METHODS:
            response = await call_next(request)
            
            # Set CSRF token cookie if not present
            if self.CSRF_COOKIE_NAME not in request.cookies:
                csrf_token = secrets.token_urlsafe(32)
                response.set_cookie(
                    key=self.CSRF_COOKIE_NAME,
                    value=csrf_token,
                    httponly=True,
                    secure=True,
                    samesite="strict",
                    max_age=3600
                )
            
            return response
        
        # For unsafe methods, verify CSRF token
        cookie_token = request.cookies.get(self.CSRF_COOKIE_NAME)
        
        # Check form data first
        if request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
            form = await request.form()
            form_token = form.get("csrf_token")
        else:
            form_token = None
        
        # Check header
        header_token = request.headers.get(self.CSRF_HEADER_NAME)
        
        # Get token from either form or header
        request_token = form_token or header_token
        
        if not cookie_token or not request_token:
            logger.warning(f"CSRF token missing for {request.url.path}")
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token missing"}
            )
        
        if not secrets.compare_digest(cookie_token, request_token):
            logger.warning(f"CSRF token mismatch for {request.url.path}")
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token invalid"}
            )
        
        response = await call_next(request)
        return response


def get_csrf_token(request: Request) -> str:
    """Get CSRF token from request cookies"""
    token = request.cookies.get(CSRFMiddleware.CSRF_COOKIE_NAME)
    if not token:
        token = secrets.token_urlsafe(32)
    return token
