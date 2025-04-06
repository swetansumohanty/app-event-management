import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.main import app
from app.common.enums import HTTPStatus, EventStatus
from app.dto.event import EventCreate, EventUpdate
from app.common.logger import logger
from app.core.database import SessionLocal, Base, engine
from sqlalchemy.orm import Session
from app.core.database import get_db
from unittest.mock import patch

# Create all tables
Base.metadata.create_all(bind=engine)

# Create TestClient
client = TestClient(app)

@pytest.fixture(scope="function")
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def sample_event_data():
    # Use actual datetime objects
    now = datetime.now()
    return {
        "name": "Test Event",
        "description": "Test Description",
        "start_time": (now + timedelta(days=1)).isoformat(),
        "end_time": (now + timedelta(days=2)).isoformat(),
        "location": "Test Location",
        "max_attendees": 100
    }

@pytest.fixture(scope="function")
def sample_user_data():
    return {
        "email": "test3@example.com",
        "name": "Event Organizer",
        "password": "testpassword123"
    }

class TestEventAPI:
    @patch('datetime.datetime')
    def test_create_event_success(self, mock_datetime, db_session, sample_event_data, sample_user_data):
        # Set up mock datetime
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # Override the database dependency
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Login user to get bearer token
        logger.info(f"Logging in user with data: {sample_user_data}")
        login_response = client.post(
            "/api/v1/user/login",
            data={
                "email": sample_user_data["email"],
                "password": sample_user_data["password"]
            }
        )
        logger.info(f"Login response: {login_response.json()}")
        assert login_response.status_code == HTTPStatus.OK.value
        token = login_response.json()["access_token"]
        
        # Create event with bearer token
        event_data = {
            "name": sample_event_data["name"],
            "description": sample_event_data["description"],
            "start_time": sample_event_data["start_time"],
            "end_time": sample_event_data["end_time"],
            "location": sample_event_data["location"],
            "max_attendees": sample_event_data["max_attendees"]
        }
        
        logger.info(f"Creating event with data: {event_data}")
        response = client.post(
            "/api/v1/events/",
            json=event_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        logger.info(f"Event creation response: {response.json()}")
        assert response.status_code == HTTPStatus.CREATED.value, f"Expected status code 201, got {response.status_code}. Response: {response.json()}"
        data = response.json()["data"]
        assert data["name"] == sample_event_data["name"]
        assert data["status"] == EventStatus.SCHEDULED.value

    @patch('datetime.datetime')
    def test_get_event_success(self, mock_datetime, db_session, sample_event_data, sample_user_data):
        # Set up mock datetime
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # Override the database dependency
        def override_get_db():
            try:
                yield db_session
            finally:
                db_session.rollback()
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Login user to get bearer token
        login_response = client.post(
            "/api/v1/user/login",
            data={
                "email": sample_user_data["email"],
                "password": sample_user_data["password"]
            }
        )
        assert login_response.status_code == HTTPStatus.OK.value
        token = login_response.json()["access_token"]
        
        # Create event with bearer token
        event_response = client.post(
            "/api/v1/events/",
            json=sample_event_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        logger.info(f"Event Creation Response: {event_response.json()}") 
        assert event_response.status_code == HTTPStatus.CREATED.value


    @patch('datetime.datetime')
    def test_update_event_success(self, mock_datetime, db_session, sample_event_data, sample_user_data):
        # Set up mock datetime
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # Override the database dependency
        def override_get_db():
            try:
                yield db_session
            finally:
                db_session.rollback()
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Login user to get bearer token
        login_response = client.post(
            "/api/v1/user/login",
            data={
                "email": sample_user_data["email"],
                "password": sample_user_data["password"]
            }
        )
        assert login_response.status_code == HTTPStatus.OK.value
        token = login_response.json()["access_token"]
        
        # Create event with bearer token
        event_response = client.post(
            "/api/v1/events/",
            json=sample_event_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        logger.info(f"Response: {event_response.json()}") 
        assert event_response.status_code == HTTPStatus.CREATED.value
        event_data = event_response.json()["data"]
        event_id = event_data["id"]
        
        # Update event
        update_data = {
            "name": "Updated Event",
            "location": "New Location"
        }
        response = client.put(
            f"/api/v1/events/{event_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == HTTPStatus.OK.value
        data = response.json()["data"]
        assert data["name"] == update_data["name"]
        assert data["location"] == update_data["location"]

    @patch('datetime.datetime')
    def test_update_event_unauthorized(self, mock_datetime, db_session, sample_event_data, sample_user_data):
        # Set up mock datetime
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # Override the database dependency
        def override_get_db():
            try:
                yield db_session
            finally:
                db_session.rollback()
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Login user to get bearer token
        login_response = client.post(
            "/api/v1/user/login",
            data={
                "email": sample_user_data["email"],
                "password": sample_user_data["password"]
            }
        )
        logger.info(f"Login response: {login_response.json()}")
        assert login_response.status_code == HTTPStatus.OK.value
        token = login_response.json()["access_token"]
        
        # Create event with bearer token
        event_response = client.post(
            "/api/v1/events/",
            json=sample_event_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        logger.info(f"Response: {event_response.json()}") 
        assert event_response.status_code == HTTPStatus.CREATED.value
        event_data = event_response.json()["data"]
        event_id = event_data["id"]
        
        # Try to update with different user (using invalid token)
        update_data = {"name": "Updated Event"}
        response = client.put(
            f"/api/v1/events/{event_id}",
            json=update_data,
            headers={"Authorization": "Bearer invalid_token"}
        )
        logger.info(f"Updated Response: {response.json()}")
        assert response.status_code == HTTPStatus.UNAUTHORIZED.value
        assert "Could not validate credentials" in response.json()["detail"]

    @patch('datetime.datetime')
    def test_update_event_status_success(self, mock_datetime, db_session, sample_event_data, sample_user_data):
        # Set up mock datetime
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # Override the database dependency
        def override_get_db():
            try:
                yield db_session
            finally:
                db_session.rollback()
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Login user to get bearer token
        login_response = client.post(
            "/api/v1/user/login",
            data={
                "email": sample_user_data["email"],
                "password": sample_user_data["password"]
            }
        )
        assert login_response.status_code == HTTPStatus.OK.value
        token = login_response.json()["access_token"]
        
        # Create event with bearer token
        event_response = client.post(
            "/api/v1/events/",
            json=sample_event_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        logger.info(f"Event Response: {event_response.json()}") 
        assert event_response.status_code == HTTPStatus.CREATED.value
        event_data = event_response.json()["data"]
        event_id = event_data["id"]
        
        # Update status using query parameter
        response = client.patch(
            f"/api/v1/events/{event_id}/status?status={EventStatus.ONGOING.value}",
            headers={"Authorization": f"Bearer {token}"}
        )
        logger.info(f"Update Status Response: {response.json()}")
        assert response.status_code == HTTPStatus.OK.value
        data = response.json()["data"]
        assert data["status"] == EventStatus.ONGOING.value

    @patch('datetime.datetime')
    def test_update_event_status_invalid_transition(self, mock_datetime, db_session, sample_event_data, sample_user_data):
        # Set up mock datetime
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # Override the database dependency
        def override_get_db():
            try:
                yield db_session
            finally:
                db_session.rollback()
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Login user to get bearer token
        login_response = client.post(
            "/api/v1/user/login",
            data={
                "email": sample_user_data["email"],
                "password": sample_user_data["password"]
            }
        )
        assert login_response.status_code == HTTPStatus.OK.value
        token = login_response.json()["access_token"]
        
        # Create event with bearer token
        event_response = client.post(
            "/api/v1/events/",
            json=sample_event_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        logger.info(f"Event Response: {event_response.json()}") 
        assert event_response.status_code == HTTPStatus.CREATED.value
        event_data = event_response.json()["data"]
        event_id = event_data["id"]
        
        # Try invalid status transition (SCHEDULED to COMPLETED) using query parameter
        response = client.patch(
            f"/api/v1/events/{event_id}/status?status={EventStatus.COMPLETED.value}",
            headers={"Authorization": f"Bearer {token}"}
        )
        logger.info(f"Update Status Response: {response.json()}") 
        assert response.status_code == HTTPStatus.BAD_REQUEST.value
        assert "Invalid status transition" in response.json()["detail"] 