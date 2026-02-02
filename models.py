# Database models define the structure of our database tables

from sqlalchemy import Column, String, Date, DateTime, Text, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from database import Base
import enum

# Patient Model
# This represents the "patients" table in the database
class Patient(Base):
    """
    Patient database model.
    
    Each instance of this class represents one row in the patients table.
    SQLAlchemy automatically converts between Python objects and database rows.
    """
    
    __tablename__ = "patients"  # Name of the table in PostgreSQL

    studies = relationship(
        "Study", 
        back_populates="patient",
        cascade="all, delete-orphan")
    # cascade options:
    # - "all" = apply all cascades
    # - "delete-orphan" = delete study if removed from patient.studies list
    
    # Columns definition
    # Column() creates a database column
    # primary_key=True means this column uniquely identifies each row
    
    id = Column(
        UUID(as_uuid=True),  # UUID type - universally unique identifier
        primary_key=True,    # This is the primary key
        default=uuid.uuid4,  # Automatically generate new UUID for each patient
        nullable=False       # Can't be empty
    )
    
    # Medical Record Number - unique identifier used in hospitals
    mrn = Column(
        String(50),      # Maximum 50 characters
        unique=True,     # No two patients can have same MRN
        nullable=False,  # Required field
        index=True       # Create index for faster lookups
    )
    
    first_name = Column(
        String(100),     # Maximum 100 characters
        nullable=False   # Required
    )
    
    last_name = Column(
        String(100),
        nullable=False
    )
    
    date_of_birth = Column(
        Date,            # Stores only date, not time
        nullable=False
    )
    
    # Timestamps - track when record was created/updated
    created_at = Column(
        DateTime,
        default=datetime.utcnow,  # Automatically set to current time when created
        nullable=False
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,   # Set to current time when created
        onupdate=datetime.utcnow,  # Update to current time when record is modified
        nullable=False
    )
    
    # String representation of the object
    # Makes debugging easier - shows patient info when you print()
    def __repr__(self):
        return f"<Patient(mrn={self.mrn}, name={self.first_name} {self.last_name})>"


class StudyStatus(str, enum.Enum):
    PLANNED = "Planned"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    REVIEWED = "Reviewed"

class StudyModality(str, enum.Enum):
    CT = "CT"
    MRI = "MRI"
    XRAY = "X-Ray"
    ULTRASOUND = "Ultrasound"

class BodyPart(str, enum.Enum):
    HEAD = "Head"
    CHEST = "Chest"
    ABDOMEN = "Abdomen"
    PELVIS = "Pelvis"
    LIMBS = "Limbs"

class Study(Base):
    __tablename__ = "studies"

    patient = relationship(
        "Patient",
        back_populates="studies"
    )

    images = relationship(
        "Image",
        back_populates="study",
        cascade="all, delete-orphan"
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=uuid.uuid4
    )

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id"),
        nullable=False,
        index= True
    )

    study_date = Column(
        Date,
        nullable=False,
        index=True
    )

    modality = Column(
        SQLEnum(StudyModality),
        nullable=False,
        index=True
    )

    body_part = Column(
        SQLEnum(BodyPart),
        nullable=False,
        index=True
    )

    description = Column(
        Text,
        nullable=True
    )

    status = Column(
        SQLEnum(StudyStatus),
        nullable=False,
        default=StudyStatus.PLANNED,
        index=True
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

    def __repr__(self):
        return f"<Study(id={self.id}, modality={self.modality}, body_part={self.body_part}, status={self.status})>"