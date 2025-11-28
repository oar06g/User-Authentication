from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
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
