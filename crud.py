# CRUD = Create, Read, Update, Delete
# Business logic for database operations

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from uuid import UUID
import models
import schemas

# CREATE - Add new patient to database
def create_patient(db: Session, patient: schemas.PatientCreate) -> models.Patient:
    """
    Create a new patient in the database.
    
    Args:
        db: Database session
        patient: PatientCreate schema with patient data
        
    Returns:
        Created Patient model instance
        
    Raises:
        IntegrityError: If MRN already exists (duplicate)
    """
    # Create new Patient instance from schema data
    # **patient.dict() unpacks the dictionary into keyword arguments
    # Example: Patient(mrn="MRN001", first_name="John", ...)
    db_patient = models.Patient(**patient.model_dump())
    
    try:
        db.add(db_patient)      # Add to database session
        db.commit()             # Save changes to database
        db.refresh(db_patient)  # Refresh to get database-generated fields (id, timestamps)
        return db_patient
    except IntegrityError:
        db.rollback()  # Undo changes if error occurs
        raise  # Re-raise the exception to be handled by the endpoint

# READ - Get all patients
def get_patients(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[models.Patient]:
    """
    Get list of patients with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
    Returns:
        List of Patient model instances
        
    Example:
        # Get first 10 patients: skip=0, limit=10
        # Get next 10 patients: skip=10, limit=10
    """
    return (db.query(models.Patient)
            .offset(skip)      # Skip first N records
            .limit(limit)      # Return max N records
            .all())            # Execute query and return all results

# READ - Get single patient by ID
def get_patient(db: Session, patient_id: UUID) -> Optional[models.Patient]:
    """
    Get a single patient by ID.
    
    Args:
        db: Database session
        patient_id: UUID of the patient
        
    Returns:
        Patient model instance if found, None otherwise
    """
    return (db.query(models.Patient)
            .filter(models.Patient.id == patient_id)  # WHERE id = patient_id
            .first())  # Return first result or None

# READ - Get patient by MRN
def get_patient_by_mrn(db: Session, mrn: str) -> Optional[models.Patient]:
    """
    Get a patient by Medical Record Number.
    
    Useful for checking if MRN already exists.
    """
    return (db.query(models.Patient)
            .filter(models.Patient.mrn == mrn)
            .first())  # Return first result or None

# UPDATE - Modify existing patient
def update_patient(
    db: Session,
    patient_id: UUID,
    patient_update: schemas.PatientUpdate
) -> Optional[models.Patient]:
    """
    Update an existing patient.
    
    Args:
        db: Database session
        patient_id: UUID of patient to update
        patient_update: PatientUpdate schema with fields to update
        
    Returns:
        Updated Patient model instance if found, None otherwise
    """
    # Get existing patient
    db_patient = get_patient(db, patient_id)
    if not db_patient:
        return None
    
    # Update only fields that were provided
    # exclude_unset=True means only include fields that were actually set
    # This allows partial updates
    patient_data = patient_update.model_dump(exclude_unset=True)
    for key, value in patient_data.items():
        setattr(db_patient, key, value)  # Update attribute

    db.commit()         # Save changes
    db.refresh(db_patient)  # Refresh to get updated data
    return db_patient
    

# DELETE - Remove patient from database
def delete_patient(db: Session, patient_id: UUID) -> bool:
    """
    Delete a patient from the database.
    
    Args:
        db: Database session
        patient_id: UUID of patient to delete
        
    Returns:
        True if deleted, False if patient not found
    """
    db_patient = get_patient(db, patient_id)
    if not db_patient:
        return False  # Patient not found
    db.delete(db_patient)  # Delete from session
    db.commit()            # Save changes
    return True