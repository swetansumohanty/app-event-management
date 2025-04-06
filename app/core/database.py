from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from .config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the declarative base class
Base = declarative_base()

# MySQL configurations
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  
    pool_recycle=3600,   
    pool_size=5,         
    max_overflow=10,
    echo=True,  # Enable SQL query logging
    connect_args={
        "connect_timeout": 60
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Test database connection and create tables if they don't exist
def init_database():
    try:
        logger.info("Initializing database...")
        logger.info(f"Database URL: {engine.url}")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully!")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise 