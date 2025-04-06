import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.common.enums import HTTPStatus, UserRole
from app.core.database import get_db
from sqlalchemy.orm import Session
from app.common.logger import logger


# Override the database dependency
def override_get_db(db_session: Session):
    def _get_db():
        try:
            yield db_session
        finally:
            pass  # Don't close the session as it's managed by the fixture
    return _get_db

# Create TestClient
client = TestClient(app)

@pytest.fixture(scope="function")
def sample_user_data():
    return {
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "testpassword123",  
        "role": UserRole.ORGANIZER.value 
    }

@pytest.fixture(scope="function")
def auth_token(sample_user_data, db_session):
    # Override the database dependency for this test
    app.dependency_overrides[get_db] = override_get_db(db_session)
    
    # Create a user first
    client.post("/api/v1/user/register", json=sample_user_data)
    
    # Get token
    response = client.post(
        "/api/v1/user/login",
        data={
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
    )
    return response.json()["access_token"]

class TestUserAPI:
    def test_create_user_success(self, sample_user_data, db_session):
        # Override the database dependency for this test
        app.dependency_overrides[get_db] = override_get_db(db_session)
        
        logger.info("Starting test_create_user_success")
        response = client.post("/api/v1/user/register", json=sample_user_data)
        logger.info(f"Response: {response.json()}")
        logger.info(f"Response status code: {type(response)}")
        
        # Get the response data
        response_data = response.json()
        
        # Check status code
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response data status code: {response_data.get('status_code')}")
        assert response.status_code == HTTPStatus.CREATED.value, f"Expected status code {HTTPStatus.CREATED.value}, got {response.status_code}"
        
        # Check response structure
        assert response_data["success"] is True
        assert response_data["message"] == "User created successfully"
        
        # Check user data
        user_data = response_data["data"]
        assert user_data["email"] == sample_user_data["email"]
        assert user_data["first_name"] == sample_user_data["first_name"]
        assert user_data["last_name"] == sample_user_data["last_name"]
        assert user_data["role"] == sample_user_data["role"]
        assert "id" in user_data
        assert "password" not in user_data
        assert "hashed_password" not in user_data
        logger.info("Test test_create_user_success completed successfully")

    def test_create_user_duplicate_email(self, sample_user_data, db_session):
        # Override the database dependency for this test
        app.dependency_overrides[get_db] = override_get_db(db_session)
        
        logger.info("Starting test_create_user_duplicate_email")
        # First create a user
        client.post("/api/v1/user/register", json=sample_user_data)
        
        # Try to create another user with same email
        response = client.post("/api/v1/user/register", json=sample_user_data)
        response_data = response.json()
        logger.info(f"Response: {response.json()}")
        # Check status code
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response data status code: {response_data.get('status_code')}")
        assert response.status_code == HTTPStatus.BAD_REQUEST.value, f"Expected status code {HTTPStatus.BAD_REQUEST.value}, got {response.status_code}"
        assert response_data["detail"] == "Email already registered"
        logger.info("Test test_create_user_duplicate_email completed successfully")

    def test_create_user_invalid_email(self, sample_user_data, db_session):
        # Override the database dependency for this test
        app.dependency_overrides[get_db] = override_get_db(db_session)
        
        logger.info("Starting test_create_user_invalid_email")
        invalid_data = sample_user_data.copy()
        invalid_data["email"] = "invalid-email"
        response = client.post("/api/v1/user/register", json=invalid_data)
        assert response.status_code == 422  # Pydantic validation error
        assert "value is not a valid email address" in response.json()["detail"][0]["msg"]
        logger.info("Test test_create_user_invalid_email completed successfully")


