from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Annotated
from uuid import UUID
import crud
import models
import schemas
from database import engine, get_db

# Create all database tables
# This reads all models that inherit from Base and creates corresponding tables
# Only creates tables that don't exist yet (safe to run multiple times)
models.Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="Medical Imaging API",
    description="RESTful API for medical imaging studies",
    version="1.0.0",
    docs_url="/docs",   # Swagger UI documentation
    redoc_url="/redoc"  # ReDoc documentation (alternative format)
)

@app.get("/", tags=["Health"])
def read_root():
    return {"message": "Medical Imaging API is running.",
            "version": "1.0.0",
            "status": "healthy"
    }


@app.post(
    "/patients/",
    response_model=schemas.PatientResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Patients"]
)
def create_patient(
    patient: schemas.PatientCreate,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Create a new patient record.
    
    - **mrn**: Medical Record Number (unique)
    - **first_name**: Patient's first name
    - **last_name**: Patient's last name
    - **date_of_birth**: Patient's date of birth (YYYY-MM-DD)
    
    Returns the created patient record with assigned ID and timestamps.
    """
    existing_patient = crud.get_patient_by_mrn(db, patient.mrn)
    if existing_patient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Patient with MRN {patient.mrn} already exists."
        )
    
    # Create patient
    return crud.create_patient(db, patient)


# READ - Get all patients with pagination
@app.get("/patients",
         response_model=List[schemas.PatientResponse],
         status_code=status.HTTP_200_OK,
         tags=["Patients"])
def get_patients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of patients with pagination.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    
    Example: /patients?skip=10&limit=5 returns patients 11-15
    Returns a list of patient records.
    """
    if limit > 100:
        limit = 100  # Enforce maximum limit to prevent large responses
    return crud.get_patients(db, skip=skip, limit=limit)

# READ - Get single patient by ID
@app.get("/patients/{patient_id}",
         response_model=schemas.PatientResponse,
         tags=["Patients"])
def get_patient(
    uuid: UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieve a single patient by their unique ID.
    
    - **patient_id**: UUID of the patient to retrieve
    
    Returns the patient record if found.
    """
    patient = crud.get_patient(db, uuid)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {uuid} not found."
        )
    return patient

# UPDATE - Modify existing patient
@app.put("/patients/{patient_id}",
         response_model=schemas.PatientResponse,
         tags=["Patients"]
)
def update_patient(
    patient_id: UUID,
    patient_update: schemas.PatientUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing patient's information.
    
    - **patient_id**: UUID of the patient to update
    - **patient_update**: Fields to update (all optional)
    
    Returns the updated patient record.
    """
    patient = crud.update_patient(db, patient_id, patient_update)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found."
        )
    return patient

# DELETE - Remove patient
@app.delete("/patients/{patient_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            tags=["Patients"]
)
def delete_patient(
    patient_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a patient record by ID.
    
    - **patient_id**: UUID of the patient to delete
    
    Returns no content on successful deletion.
    """
    deleted = crud.delete_patient(db, patient_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found."
        )
    #  204 responses have no body, so we don't return anything
    return None

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    Catch-all error handler.
    Returns 500 Internal Server Error for unexpected exceptions.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred."}
    )