from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, func
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
    verified = Column(Boolean, default=False)  # False for unverified, True for verified
    role = Column(String(50), default='user')  # 'user' or 'admin'

    email_verifications = relationship(
        "EmailVerifications", 
        back_populates="user",
        cascade="all, delete-orphan"
    )

class EmailVerifications(Base):
    __tablename__ = 'email_verifications'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token = Column(String(255), nullable=False, unique=True)
    token_exp = Column(Integer, nullable=False)  # Expiration time in UNIX timestamp
    is_used = Column(Boolean, default=False, nullable=False)  # False for unused, True for used
    created_at = Column(Integer, nullable=False, default=lambda: int(time.time()))
    
    user = relationship("User", back_populates="email_verifications")

