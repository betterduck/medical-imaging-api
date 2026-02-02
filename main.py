from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from typing import List, Annotated, Optional
from uuid import UUID
from pathlib import Path
import crud
import models
import schemas
import file_utils
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

@app.on_event("startup")
async def startup_event():
    file_utils.ensure_upload_directory()
    print(f"Upload directory ready: {file_utils.UPLOAD_DIR}")


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

@app.post(
    "/studies",
    response_model=schemas.StudyResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Studies"]
)
def create_study(
    study: schemas.StudyCreate,
    db: Session = Depends(get_db)
):
    """
    1. Check if the patient exists
    2. Create a new study linked to that patient.
    3. Return the created study record.
    """

    patient_exists = crud.get_patient(db,study.patient_id)
    if not patient_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Patient with ID {study.patient_id} does not exist."
        )
    return crud.create_study(db, study)

@app.get(
    "/studies",
    response_model=List[schemas.StudyResponse],
    tags=["Studies"]
)
def get_studies(
    db: Session=Depends(get_db),
    skip: int=0,
    limit: int=100,
    patient_id: Optional[UUID]=None,
    modality: Optional[models.StudyModality]=None,
    status: Optional[models.StudyStatus]=None
):
    if limit > 100:
        limit = 100  # Enforce maximum limit

    return crud.get_studies(
        db=db,
        skip=skip,
        limit=limit,
        patient_id=patient_id,
        modality=modality,
        status=status
    )

@app.get(
    "/studies/{study_id}",
    response_model=schemas.StudyResponse,
    tags=["Studies"]
)
def get_study(
    study_id: UUID,
    db: Session=Depends(get_db)
):
    study = crud.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study with ID {study_id} not found"
        )
    return study

@app.put(
    "/studies/{study_id}",
    response_model=schemas.StudyResponse,
    tags=["Studies"]
)
def update_study(
    study_id: UUID,
    study_update: schemas.StudyUpdate,
    db: Session=Depends(get_db)
):
    updated_study = crud.update_study(db, study_id, study_update)
    if not updated_study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study with ID {study_id} not found"
        )
    return updated_study

@app.delete(
    "/studies/{study_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Studies"])
def delete_study(
    study_id: UUID,
    db: Session=Depends(get_db)
):
    deleted = crud.delete_study(db, study_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study with ID {study_id} not found"
        )
    return None

@app.get(
    "/patients/{patient_id}/studies",
    response_model=schemas.PatientWithStudies,
    tags=["Patients"])
def get_patient_with_studies(
    patient_id: UUID,
    db: Session=Depends(get_db)
):
    patient = crud.get_patient_with_studies(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )
    return patient

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

@app.post(
    "/studies/{study_id}/images",
    response_model=schemas.ImageResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Images"]
)
async def upload_image(
    study_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    study = crud.get_study(db, study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study with ID {study_id} not found."
        )
    try:
        filename, stored_filename, file_path, file_size = await file_utils.save_upload_file(file)
    except HTTPException:
        raise  # Re-raise HTTP exceptions from file_utils

    mime_type = file_utils.validate_mime_type(open(file_path, 'rb').read(2048))

    db_image = crud.create_image(
        db,
        study_id=study_id,
        filename=filename,
        stored_filename=stored_filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=mime_type
    )
    return db_image

@app.get(
    "studies/{stud_id}/images",
    response_model=List[schemas.ImageResponse],
    tags=["Images"]
)
def get_study_images(
    study_id: UUID,
    db: Session = Depends(get_db)
):
    study = crud.get_study(db, study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study with ID {study_id} not found"
        )
    images = crud.get_study_images(db, study_id)
    return images

@app.get(
    "/studies/{study_id}/images/{image_id}/download",
    tags=["Images"]
)
async def download_image(
    study_id: UUID,
    image_id: UUID,
    db: Session = Depends(get_db)
):
    study = crud.get_study(db, study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study with ID {study_id} not found"
        )
    image = crud.get_image(db, image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID {image_id} not found"
        )
    
    if image.study_id != study_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Image with ID {image_id} does not belong to Study with ID {study_id}"
        )
    
    file_path = Path(image.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File for Image with ID {image_id} not found on server"
        )
    return FileResponse(
        path=file_path,
        media_type=image.mime_type,
        filename=image.filename
    )

@app.delete(
    "/studies/{study_id}/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Images"]
)
def delete_image(
    study_id: UUID,
    image_id: UUID,
    db: Session = Depends(get_db)
):
    study = crud.get_study(db, study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study with ID {study_id} not found"
        )
    image = crud.get_image(db, image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID {image_id} not found"
        )
    
    if image.study_id != study_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Image with ID {image_id} does not belong to Study with ID {study_id}"
        )
    
    crud.delete_image(db, image_id)
    return None
