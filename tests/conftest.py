import os
import sys
import pytest
from datetime import datetime
from sqlalchemy import create_engine, inspect, event, MetaData
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.core.config import settings

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import all models to ensure their tables are created
from app.vo.user import User
from app.vo.attendee import Attendee
from app.vo.event import Event

# Create test database URL
TEST_DATABASE_URL = "mysql+pymysql://root:root@db:3306/test_event_management"

@pytest.fixture(scope="session", autouse=True)
def test_engine():
    """Create test database engine and tables"""
    # Create engine
    engine = create_engine(
        TEST_DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=5,
        max_overflow=10,
        echo=True
    )
    
    # Create database if it doesn't exist
    with engine.connect() as conn:
        conn.execute("CREATE DATABASE IF NOT EXISTS test_event_management")
        conn.execute("USE test_event_management")
    
    # Create all tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Verify tables were created
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Created tables: {tables}")
    
    yield engine
    
    # Clean up
    Base.metadata.drop_all(bind=engine)
    with engine.connect() as conn:
        conn.execute("DROP DATABASE IF EXISTS test_event_management")

@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create a fresh database session for each test"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(autouse=True)
def mock_datetime_now(monkeypatch):
    """Mock datetime.now() for consistent testing"""
    class MockDatetime:
        @classmethod
        def now(cls):
            return datetime(2024, 4, 5, 12, 0, 0)
    
    monkeypatch.setattr("datetime.datetime", MockDatetime)