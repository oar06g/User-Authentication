"""
Structured logging configuration for authentication system
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime


def setup_logging():
    """Configure application logging"""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'app.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # File handler for errors only
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'error.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    # Security audit log
    security_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'security.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    security_handler.setLevel(logging.INFO)
    security_handler.setFormatter(detailed_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    
    # Configure security logger
    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.INFO)
    security_logger.addHandler(security_handler)
    security_logger.propagate = False
    
    # Suppress noisy loggers
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    
    return root_logger


def get_security_logger():
    """Get security audit logger"""
    return logging.getLogger('security')


class SecurityAudit:
    """Security audit logging helper"""
    
    @staticmethod
    def log_login_attempt(username: str, ip: str, success: bool, reason: str = ""):
        """Log login attempt"""
        logger = get_security_logger()
        status = "SUCCESS" if success else "FAILED"
        msg = f"Login {status} - Username: {username}, IP: {ip}"
        if reason:
            msg += f", Reason: {reason}"
        
        if success:
            logger.info(msg)
        else:
            logger.warning(msg)
    
    @staticmethod
    def log_registration(username: str, email: str, ip: str, success: bool):
        """Log user registration"""
        logger = get_security_logger()
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"Registration {status} - Username: {username}, Email: {email}, IP: {ip}")
    
    @staticmethod
    def log_password_reset_request(email: str, ip: str):
        """Log password reset request"""
        logger = get_security_logger()
        logger.info(f"Password reset requested - Email: {email}, IP: {ip}")
    
    @staticmethod
    def log_password_change(username: str, ip: str, method: str = "reset"):
        """Log password change"""
        logger = get_security_logger()
        logger.info(f"Password changed - Username: {username}, Method: {method}, IP: {ip}")
    
    @staticmethod
    def log_email_verification(email: str, success: bool):
        """Log email verification"""
        logger = get_security_logger()
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"Email verification {status} - Email: {email}")
    
    @staticmethod
    def log_logout(username: str, ip: str):
        """Log user logout"""
        logger = get_security_logger()
        logger.info(f"Logout - Username: {username}, IP: {ip}")
    
    @staticmethod
    def log_account_lockout(username: str, ip: str, duration: int):
        """Log account lockout"""
        logger = get_security_logger()
        logger.warning(f"Account locked - Username: {username}, IP: {ip}, Duration: {duration}min")
    
    @staticmethod
    def log_suspicious_activity(activity: str, ip: str, details: str = ""):
        """Log suspicious activity"""
        logger = get_security_logger()
        msg = f"Suspicious activity - Type: {activity}, IP: {ip}"
        if details:
            msg += f", Details: {details}"
        logger.warning(msg)
