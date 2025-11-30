from fastapi import Request, Depends, HTTPException
from src.models import User
from src.config import get_db
from sqlalchemy.orm import Session
from src.auth import decode_token
from src.exceptions import AuthenticationError, InvalidCredentialsError
import time
import logging

logger = logging.getLogger(__name__)

def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Get current authenticated user from JWT token"""
    token = request.cookies.get("access_token")
    if not token:
        logger.warning(f"No access token found - IP: {get_client_ip(request)}")
        raise AuthenticationError("Not authenticated")
    
    try:
        payload = decode_token(token)
        transtoken = payload.get("transtoken")
    except Exception as e:
        logger.warning(f"Invalid token - IP: {get_client_ip(request)}, Error: {str(e)}")
        raise AuthenticationError("Invalid token")
    
    user = db.query(User).filter(User.transaction_token == transtoken).first()
    if not user:
        logger.warning(f"User not found for token - IP: {get_client_ip(request)}")
        raise AuthenticationError("User not found")
    
    return user

def check_account_lockout(user: User) -> bool:
    """Check if user account is locked"""
    if user.locked_until and user.locked_until > int(time.time()):
        return True
    elif user.locked_until and user.locked_until <= int(time.time()):
        # Unlock account if lockout period has passed
        user.locked_until = None
        user.failed_login_attempts = 0
    return False

def record_failed_login(user: User, db: Session, max_attempts: int = 5):
    """Record failed login attempt and lock account if necessary"""
    user.failed_login_attempts += 1
    
    if user.failed_login_attempts >= max_attempts:
        # Lock account for 15 minutes
        lockout_duration = 15 * 60
        user.locked_until = int(time.time()) + lockout_duration
        logger.warning(f"Account locked - Username: {user.username}, Attempts: {user.failed_login_attempts}")
    
    db.commit()

def reset_failed_login_attempts(user: User, db: Session):
    """Reset failed login attempts after successful login"""
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = int(time.time())
    db.commit()