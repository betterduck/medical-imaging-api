from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime
from auth_models import UserRole

class UserCreate(BaseModel):
    email:  EmailStr = Field(
        ...,
        description="User's email address",
        examples=["john.doe@example.com"]
    )

    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        examples=["SecurePassword_#3!"]
    )

    full_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Full name of the user",
        examples=["John Doe"]
    )

    role: UserRole = Field(
        UserRole.PATIENT,
        description="Role assigned to the user"
    )

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isalpha() for char in v):
            raise ValueError('Password must contain at least one letter')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        return v
    
class UserLogin(BaseModel):
    email: EmailStr = Field(
        ...,
        description="User's email address"
    )

    password: str = Field(
        ...,
        description="User's password"
    )

class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str = Field(
        ...,
        description="JWT access token",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )

    token_type: str = Field(
        default="bearer",
        description="Type of the token (bearer for JWT)"
    )

class TokenData(BaseModel):
    """
    Schema for data extracted from JWT token.
    
    Used internally to pass decoded token data.
    Not returned to client.
    """
    user_id: UUID
    email: str
    role: UserRole

