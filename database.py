from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment variable
# os.getenv() reads from .env file
DATABASE_URL = os.getenv("DATABASE_URL")

# Create database engine
# Engine is the connection to the database
# echo=True prints all SQL queries (useful for debugging)
engine = create_engine(
    DATABASE_URL,
    echo=True  # Set to False in production to reduce logs
)

# SessionLocal is a class that creates database sessions
# A session is like a "workspace" for database operations
# You open a session, do some work, then close it
SessionLocal = sessionmaker(
    autocommit=False,  # Don't auto-commit changes (we'll do it manually)
    autoflush=False,   # Don't auto-flush changes
    bind=engine        # Bind to our database engine
)

# Base class for all our database models
# All database tables will inherit from this
Base = declarative_base()

# Dependency function to get database session
# This will be used in FastAPI endpoints
def get_db():
    """
    Creates a new database session for each request.
    Automatically closes the session when done.
    
    Usage in FastAPI:
    @app.get("/patients")
    def get_patients(db: Session = Depends(get_db)):
        # db is now a database session
        patients = db.query(Patient).all()
        return patients
    """
    db = SessionLocal()  # Create new session
    try:
        yield db  # Provide session to the endpoint
    finally:
        db.close()  # Always close session when done (even if error occurs)