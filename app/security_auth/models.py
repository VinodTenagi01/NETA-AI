"""
Pydantic models for authentication requests and responses.
These are data validation schemas, not ORM models.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegisterRequest(BaseModel):
    """User registration request."""
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=255)
    phone: Optional[str] = Field(None, max_length=15)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "John Doe",
                "email": "john@example.com",
                "password": "SecurePass123!",
                "phone": "+919876543210"
            }
        }
    )


class UserLoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str = Field(..., min_length=1)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "john@example.com",
                "password": "SecurePass123!"
            }
        }
    )


class TokenRefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    )


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=255)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "old_password": "OldPass123!",
                "new_password": "NewPass456!"
            }
        }
    )


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int  # seconds

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "Bearer",
                "expires_in": 900
            }
        }
    )


class UserResponse(BaseModel):
    """User profile response (public fields only)."""
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    mfa_enabled: bool
    last_login: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "john@example.com",
                "full_name": "John Doe",
                "role": "campaign_manager",
                "is_active": True,
                "mfa_enabled": False,
                "last_login": "2026-05-23T10:30:00Z",
                "created_at": "2026-05-20T08:00:00Z"
            }
        }
    )


class CurrentUserResponse(UserResponse):
    """Current authenticated user response (includes zone)."""
    zone_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class TokenData(BaseModel):
    """Internal JWT token payload."""
    user_id: str
    email: Optional[str] = None
    role: Optional[str] = None
    exp: int  # expiration timestamp
    iat: int  # issued at timestamp
    type: str = "access"  # "access" or "refresh"
