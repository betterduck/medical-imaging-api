# models.py
# Database models define the structure of our database tables

from sqlalchemy import Column, String, Date, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from database import Base

# Patient Model
# This represents the "patients" table in the database
class Patient(Base):
    """
    Patient database model.
    
    Each instance of this class represents one row in the patients table.
    SQLAlchemy automatically converts between Python objects and database rows.
    """
    
    __tablename__ = "patients"  # Name of the table in PostgreSQL
    
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