from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, declarative_base
import time

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    fullname = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    verified = Column(Boolean, default=False)
    role = Column(String(50), default='user')
    transaction_token = Column(String(150), unique=True, nullable=False)
    
    # Account lockout fields
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(Integer, nullable=True)  # Unix timestamp
    last_login = Column(Integer, nullable=True)  # Unix timestamp
    created_at = Column(Integer, nullable=False, default=lambda: int(time.time()))

    email_verifications = relationship(
        "EmailVerifications",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    password_resets = relationship(
        "PasswordReset",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    audit_logs = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class EmailVerifications(Base):
    __tablename__ = 'email_verifications'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token = Column(String(255), nullable=False, unique=True)
    token_exp = Column(Integer, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(Integer, nullable=False, default=lambda: int(time.time()))
    
    user = relationship("User", back_populates="email_verifications")


class PasswordReset(Base):
    __tablename__ = 'password_reset'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token = Column(String(255), nullable=False, unique=True)
    token_exp = Column(Integer, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(Integer, nullable=False, default=lambda: int(time.time()))

    user = relationship("User", back_populates="password_resets")


class AuditLog(Base):
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    action = Column(String(100), nullable=False)  # login, logout, password_change, etc.
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False)  # success, failed
    details = Column(Text, nullable=True)
    created_at = Column(Integer, nullable=False, default=lambda: int(time.time()))
    
    user = relationship("User", back_populates="audit_logs")
