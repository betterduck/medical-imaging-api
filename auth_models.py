from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid
from database import Base

class UserRole(str, enum.Enum):
    """
    Role-Based Access Control
    """
    ADMIN = "ADMIN"
    DOCTOR = "DOCTOR"
    PATIENT = "PATIENT"

class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=uuid.uuid4
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    hashed_password = Column(
        String(255),
        nullable=False,
    )

    full_name = Column(
        String(255),
        nullable=False
    )

    role = Column(
        SQLEnum(UserRole),
        nullable=False,
        index=True,
        default=UserRole.PATIENT
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    last_login = Column(
        DateTime,
        nullable=True
    )

    def __repr__(self):
        return f"<User(email={self.email}, role={self.role})>"