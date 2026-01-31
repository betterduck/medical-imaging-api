# schemas.py
# Pydantic models for request/response validation

from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime
from uuid import UUID
from typing import Optional

# Base schema with common fields
class PatientBase(BaseModel):
    """
    Base schema with fields common to all patient operations.
    Other schemas inherit from this to avoid repeating fields.
    """
    mrn: str = Field(
        ...,  # ... means required field
        min_length=1,
        max_length=50,
        description="Medical Record Number",
        examples=["MRN001234"]  # Example for API documentation
    )
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        examples=["John"]
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        examples=["Doe"]
    )
    date_of_birth: date = Field(
        ...,
        description="Patient's date of birth",
        examples=["1980-05-15"]
    )
    
    # Custom validator to ensure date of birth is not in the future
    @field_validator('date_of_birth')
    @classmethod
    def validate_dob(cls, v):
        """
        Validates that date of birth is not in the future.
        Pydantic calls this automatically when validating data.
        """
        if v > date.today():
            raise ValueError('Date of birth cannot be in the future')
        return v

# Schema for creating a new patient
# Inherits all fields from PatientBase
class PatientCreate(PatientBase):
    """
    Schema for creating a new patient.
    Used when client sends POST request to create patient.
    
    Example request body:
    {
        "mrn": "MRN001234",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1980-05-15"
    }
    """
    pass  # No additional fields needed

# Schema for updating a patient
# All fields are optional (user can update just one field)
class PatientUpdate(BaseModel):
    """
    Schema for updating an existing patient.
    All fields optional - client can update any combination.
    
    Example request body (update only name):
    {
        "first_name": "Jane"
    }
    """
    mrn: Optional[str] = Field(None, min_length=1, max_length=50)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    date_of_birth: Optional[date] = None

# Schema for patient response (what API returns)
# Includes database-generated fields like id, created_at
class PatientResponse(PatientBase):
    """
    Schema for patient response.
    Used when API returns patient data to client.
    Includes all fields from PatientBase plus database-generated fields.
    
    Example response:
    {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "mrn": "MRN001234",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1980-05-15",
        "created_at": "2026-01-29T10:30:00",
        "updated_at": "2026-01-29T10:30:00"
    }
    """
    id: UUID  # Database-generated UUID
    created_at: datetime  # Automatically set by database
    updated_at: datetime  # Automatically updated by database
    
    # Tell Pydantic to work with SQLAlchemy models
    class Config:
        from_attributes = True  # Allows: PatientResponse.from_orm(db_patient)