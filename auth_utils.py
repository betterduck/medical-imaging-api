from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os
from database import get_db
from auth_models import User, UserRole

load_dotenv()

# Generate with openssl rand -hex 32
SECRET_KEY = os.getenv("SECRET_KEY")
# Algorithm used for signing JWT
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto" # automatically uprade old hashes
)

# Tells FastAPI where to look for the token
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login")

def hash_password(password: str) -> str:
    """
    Process:
    1. Generate random salt
    2. Combine password + salt
    3. Apply bcrypt hash function
    4. Return hash (includes salt)
    """
    return pwd_context.hash(password)

def verify_password(
    plain_password: str, 
    hashed_password: str) -> bool:
    """
    Process:
    1. Extract salt from stored hash
    2. Hash provided password with same salt
    3. Compare hashes
    """
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Process:
    1. Copy payload data
    2. Add expiration time
    3. Sign with secret key
    4. Encode as JWT string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """
    Process:
    1. Split token into header, payload, signature
    2. Recalculate signature with secret key
    3. Verify signature matches
    4. Check expiration
    5. Return payload
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
        Get current user from JWT token.
        
        FastAPI dependency that:
        1. Extracts token from Authorization header
        2. Verifies token signature
        3. Looks up user in database
        4. Returns user object
        
        Usage in endpoints:
        @app.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            # current_user is automatically populated
            return {"user": current_user.email}
        
        Args:
            token: JWT token from Authorization header
            db: Database session
            
        Returns:
            User object of authenticated user
            
        Raises:
            HTTPException 401: If token invalid or user not found
            
        Flow:
        Client request:
            GET /protected
            Authorization: Bearer eyJhbGciOi...
        
        1. oauth2_scheme extracts token from header
        2. decode_access_token verifies and decodes
        3. Query database for user
        4. Check user is active
        5. Return user object to endpoint
    """
    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
            ) 
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user

def require_role(allowed_roles: list):
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Requires roles: {allowed_roles}"
            )
        return current_user
    return role_checker