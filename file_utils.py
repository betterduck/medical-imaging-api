from fastapi import HTTPException, status, UploadFile
from typing import Tuple
import magic
import os
import uuid
from pathlib import Path

UPLOAD_DIR = Path(__file__).parent / "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.dcm'}
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'application/dicom'}

def ensure_upload_directory():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    if not os.access(UPLOAD_DIR, os.W_OK):
        raise PermissionError(f"Upload directory {UPLOAD_DIR} is not writable.")
    
def validate_file_extension(filename: str) -> None:
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{extension}' is not allowed."
        )
    
def validate_file_size(file_size: int) -> None:
    if file_size > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        actual_mb = file_size / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size {actual_mb:.2f} MB exceeds the maximum allowed size of {max_mb:.2f} MB."
        )
    
def validate_mime_type(file_content: bytes) -> str:
    mime = magic.from_buffer(file_content, mime=True)
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{mime}' is not allowed."
        )
    return mime

def generate_unique_filename(original_filename: str) -> str:
    extension = Path(original_filename).suffix.lower()
    unique_id = uuid.uuid4()
    return f"{unique_id}{extension}"

async def save_upload_file(upload_file: UploadFile) -> Tuple[str, str, str, int]:
    validate_file_extension(upload_file.filename)
    file_content = await upload_file.read()
    file_size = len(file_content)
    validate_file_size(file_size)
    mime_type = validate_mime_type(file_content[:2048])  # Check first 2048 bytes for MIME type
    unique_filename = generate_unique_filename(upload_file.filename)
    file_path = UPLOAD_DIR / unique_filename
    try:
        with open(file_path, 'wb') as out_file:
            out_file.write(file_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    return (
        upload_file.filename,
        unique_filename,
        str(file_path),
        file_size
    )

def delete_file(file_path: str) -> None:
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
    except Exception as e:
        print(f"Error deleting file {file_path}: {str(e)}")

