from fastapi import Depends, status, HTTPException, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List

import auth_schemas
import auth_models
import auth_utils
from database import get_db

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post(
    "/register",
    response_model=auth_schemas.UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
    user_data: auth_schemas.UserCreate,
    db: Session = Depends(get_db)
):
    user = db.query(auth_models.User)\
        .filter(auth_models.User.email == user_data.email)\
        .first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    print(repr(user_data.password), len(user_data.password))
    hashed_password = auth_utils.hash_password(user_data.password)
    db_user = auth_models.User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@router.post(
    "/login",
    response_model=auth_schemas.Token
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(auth_models.User)\
        .filter(auth_models.User.email == form_data.username)\
        .first()
    
    if not user or not auth_utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    access_token_expires = timedelta(minutes=auth_utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_utils.create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value
        },
        expires_delta=access_token_expires
    )

    user.last_login = datetime.utcnow()
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get(
    "/me",
    response_model=auth_schemas.UserResponse
)
def get_current_user_info(
    current_user: auth_models.User = Depends(auth_utils.get_current_user)
):
    return current_user

@router.get(
    "/users",
    response_model=List[auth_schemas.UserResponse]
)
def list_users(
    current_user: auth_models.User=Depends(auth_utils.require_role([auth_models.UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    users = db.query(auth_models.User).all()
    return users