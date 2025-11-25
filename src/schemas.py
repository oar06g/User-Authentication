from pydantic import BaseModel, EmailStr, Field
from datetime import date
from typing import Optional

class UserCreate(BaseModel):
    full_name: str = Field(
        ...,
        min_length=4,
        max_length=100,
        description="The full name of the user.",
    )
    username: str = Field(
        ...,
        min_length=4,
        max_length=50,
        pattern="^[a-zA-Z0-9_]+$",
        description="The unique username for the user.",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=50,
        description="The password for the user account.",
    )
    email: EmailStr = Field(
        ...,
        description="The email address of the user.",
    )

class UserLogin(BaseModel):
    username: str = Field(
        ...,
        pattern="^[a-zA-Z0-9_]+$",
        description="The username of the user.",
    )
    password: str = Field(
        ...,
        description="The password of the user.",
    )