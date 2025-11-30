"""
Input validation utilities for authentication system
"""
import re
from typing import Tuple, List


class PasswordValidator:
    """Password strength validation"""
    
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    
    @classmethod
    def validate(cls, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password strength
        Returns: (is_valid, list_of_errors)
        """
        errors = []
        
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters long")
        
        if len(password) > cls.MAX_LENGTH:
            errors.append(f"Password must not exceed {cls.MAX_LENGTH} characters")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Check for common patterns
        common_patterns = [
            r'(.)\1{2,}',  # Three or more repeated characters
            r'(012|123|234|345|456|567|678|789|890)',  # Sequential numbers
            r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)',  # Sequential letters
        ]
        
        for pattern in common_patterns:
            if re.search(pattern, password.lower()):
                errors.append("Password contains common patterns")
                break
        
        # Check against common passwords
        common_passwords = [
            'password', '12345678', 'qwerty', 'abc123', 'letmein',
            'admin123', 'welcome', 'monkey', '1234567890', 'password123'
        ]
        
        if password.lower() in common_passwords:
            errors.append("Password is too common")
        
        return len(errors) == 0, errors
    
    @classmethod
    def get_strength_score(cls, password: str) -> int:
        """
        Calculate password strength score (0-100)
        """
        score = 0
        
        # Length score (max 30 points)
        if len(password) >= 8:
            score += min(30, len(password) * 2)
        
        # Complexity score
        if re.search(r'[a-z]', password):
            score += 10
        if re.search(r'[A-Z]', password):
            score += 10
        if re.search(r'\d', password):
            score += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 20
        
        # Variety score
        unique_chars = len(set(password))
        score += min(20, unique_chars * 2)
        
        # Deduct for common patterns
        if re.search(r'(.)\1{2,}', password):
            score -= 10
        
        return min(100, max(0, score))


class UsernameValidator:
    """Username validation"""
    
    MIN_LENGTH = 3
    MAX_LENGTH = 50
    PATTERN = re.compile(r'^[a-zA-Z0-9_]+$')
    
    @classmethod
    def validate(cls, username: str) -> Tuple[bool, List[str]]:
        """
        Validate username
        Returns: (is_valid, list_of_errors)
        """
        errors = []
        
        if len(username) < cls.MIN_LENGTH:
            errors.append(f"Username must be at least {cls.MIN_LENGTH} characters long")
        
        if len(username) > cls.MAX_LENGTH:
            errors.append(f"Username must not exceed {cls.MAX_LENGTH} characters")
        
        if not cls.PATTERN.match(username):
            errors.append("Username can only contain letters, numbers, and underscores")
        
        # Reserved usernames
        reserved = ['admin', 'root', 'system', 'user', 'guest', 'api', 'test']
        if username.lower() in reserved:
            errors.append("This username is reserved")
        
        return len(errors) == 0, errors


class EmailValidator:
    """Email validation (additional to pydantic)"""
    
    @classmethod
    def validate(cls, email: str) -> Tuple[bool, List[str]]:
        """
        Validate email format
        Returns: (is_valid, list_of_errors)
        """
        errors = []
        
        # Basic regex pattern
        pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        if not pattern.match(email):
            errors.append("Invalid email format")
        
        # Check for disposable email domains (basic list)
        disposable_domains = [
            'tempmail.com', 'throwaway.email', '10minutemail.com',
            'guerrillamail.com', 'mailinator.com'
        ]
        
        domain = email.split('@')[-1].lower() if '@' in email else ''
        if domain in disposable_domains:
            errors.append("Disposable email addresses are not allowed")
        
        return len(errors) == 0, errors
