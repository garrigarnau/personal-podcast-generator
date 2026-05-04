"""
Pydantic schemas for authentication endpoints.
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from uuid import UUID
from typing import Optional


class SignupRequest(BaseModel):
    """
    User signup request.

    Attributes:
        username: Unique username (3-50 characters)
        email: Valid email address
        password: Password (minimum 8 characters)
    """

    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, max_length=72, description="Password (8-72 characters)")

    @field_validator('password')
    @classmethod
    def validate_password_bytes(cls, v: str) -> str:
        """Validate password doesn't exceed bcrypt's 72-byte limit."""
        password_bytes = v.encode('utf-8')
        if len(password_bytes) > 72:
            raise ValueError(f'Password is {len(password_bytes)} bytes, must be 72 bytes or less (bcrypt limit)')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "johndoe",
                "email": "john@example.com",
                "password": "securepass123"
            }
        }
    )


class LoginRequest(BaseModel):
    """
    User login request.

    Attributes:
        username: Username or email
        password: User password
    """

    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "johndoe",
                "password": "securepass123"
            }
        }
    )


class TokenResponse(BaseModel):
    """
    JWT token response.

    Attributes:
        access_token: JWT access token
        token_type: Token type (always "bearer")
        user_id: UUID of the authenticated user
        username: Username of the authenticated user
    """

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user_id: UUID = Field(..., description="User ID")
    username: str = Field(..., description="Username")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "johndoe"
            }
        }
    )


class UserResponse(BaseModel):
    """
    User information response (without sensitive data).

    Attributes:
        id: User UUID
        username: Username
        email: Email address
        created_at: Account creation timestamp
    """

    id: UUID
    username: str
    email: str
    created_at: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "johndoe",
                "email": "john@example.com",
                "created_at": "2026-05-04T10:30:00"
            }
        }
    )


class ErrorResponse(BaseModel):
    """
    Error response.

    Attributes:
        detail: Error message
    """

    detail: str = Field(..., description="Error message")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "Username already exists"
            }
        }
    )
