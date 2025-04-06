import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.main import app
from app.common.enums import HTTPStatus, EventStatus
from app.dto.attendee import AttendeeCreate, BulkCheckInRequest
from app.common.logger import logger
from app.core.database import SessionLocal, Base, engine
from sqlalchemy.orm import Session
from app.core.database import get_db
from unittest.mock import patch
import io
import csv
import uuid

# Create all tables
Base.metadata.create_all(bind=engine)

# Create TestClient
client = TestClient(app)

def generate_unique_email(base_email="goutam24"):
    """Generate a unique email using UUID"""
    unique_id = str(uuid.uuid4())[:8]
    return f"{base_email}_{unique_id}@prajapat.com"

@pytest.fixture(scope="function")
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def sample_event_data():
    return {
        "name": "Test Event",
        "description": "Test Description",
        "start_time": (datetime.now() + timedelta(days=1)).isoformat(),
        "end_time": (datetime.now() + timedelta(days=2)).isoformat(),
        "location": "Test Location",
        "max_attendees": 100
    }

@pytest.fixture
def sample_organizer_data():
    return {
        "email": "organizer@example.com",
        "name": "Event Organizer",
        "password": "testpassword123"
    }

@pytest.fixture
def sample_attendee_data():
    return {
        "first_name": "goutam",
        "last_name": "prajapat",
        "email": generate_unique_email(),
        "phone_number": "8899778877",
        "event_id": None  # This will be set in the test
    }

class TestAttendeeAPI:
    @patch('datetime.datetime')
    def test_register_attendee_success(self, mock_datetime, db_session, sample_event_data, sample_organizer_data, sample_attendee_data):
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
        
        # Login organizer to get bearer token
        login_response = client.post(
            "/api/v1/user/login",
            data={
                "email": sample_organizer_data["email"],
                "password": sample_organizer_data["password"]
            }
        )
        logger.info(f"Login Response: {login_response.json()}")
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
        
        # Update attendee data with event_id
        attendee_data = sample_attendee_data.copy()
        attendee_data["event_id"] = event_id
        
        # Register attendee
        response = client.post(
            "/api/v1/attendees/",
            json=attendee_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        logger.info(f"Attendee Response: {response.json()}")
        assert response.status_code == HTTPStatus.CREATED.value
        data = response.json()["data"]
        assert data["email"] == attendee_data["email"]
        assert data["first_name"] == attendee_data["first_name"]
        assert data["last_name"] == attendee_data["last_name"]
        assert data["phone_number"] == attendee_data["phone_number"]
        assert data["event_id"] == event_id

    @patch('datetime.datetime')
    def test_get_attendees(self, mock_datetime, db_session, sample_event_data, sample_organizer_data, sample_attendee_data):
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
        
        # Login organizer to get bearer token
        login_response = client.post(
            "/api/v1/user/login",
            data={
                "email": sample_organizer_data["email"],
                "password": sample_organizer_data["password"]
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
        assert event_response.status_code == HTTPStatus.CREATED.value
        event_data = event_response.json()["data"]
        event_id = event_data["id"]
        
        # Register attendee
        attendee_data = sample_attendee_data.copy()
        attendee_data["event_id"] = event_id
        client.post(
            "/api/v1/attendees/",
            json=attendee_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Get attendees with filters
        response = client.get(
            "/api/v1/attendees/",
            params={
                "event_id": event_id,
                "email": attendee_data["email"],
                "check_in_status": False,
                "skip": 0,
                "limit": 100
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == HTTPStatus.OK.value
        data = response.json()["data"]
        assert len(data) > 0
        assert data[0]["email"] == attendee_data["email"]

    @patch('datetime.datetime')
    def test_get_checked_in_attendees(self, mock_datetime, db_session, sample_event_data, sample_organizer_data, sample_attendee_data):
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
        
        # Login organizer to get bearer token
        login_response = client.post(
            "/api/v1/user/login",
            data={
                "email": sample_organizer_data["email"],
                "password": sample_organizer_data["password"]
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
        assert event_response.status_code == HTTPStatus.CREATED.value
        event_data = event_response.json()["data"]
        event_id = event_data["id"]
        
        # Register attendee with unique email
        attendee_data = sample_attendee_data.copy()
        attendee_data["event_id"] = event_id
        attendee_data["email"] = generate_unique_email()  # Generate new unique email
        attendee_response = client.post(
            "/api/v1/attendees/",
            json=attendee_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert attendee_response.status_code == HTTPStatus.CREATED.value
        attendee_id = attendee_response.json()["data"]["id"]
        
        # Update event status to ONGOING
        response = client.patch(
            f"/api/v1/events/{event_id}/status?status={EventStatus.ONGOING.value}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == HTTPStatus.OK.value
        
        # Check in attendee
        response = client.post(
            f"/api/v1/attendees/{attendee_id}/check-in",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == HTTPStatus.OK.value
        
        # Get checked-in attendees
        response = client.get(
            f"/api/v1/attendees/event/{event_id}/checked-in",
            params={"skip": 0, "limit": 100},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == HTTPStatus.OK.value
        data = response.json()["data"]
        assert len(data) > 0
        assert data[0]["email"] == attendee_data["email"]
        assert data[0]["check_in_status"] is True

    @patch('datetime.datetime')
    def test_bulk_check_in_attendees(self, mock_datetime, db_session, sample_event_data, sample_organizer_data, sample_attendee_data):
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
        
        # Login organizer to get bearer token
        login_response = client.post(
            "/api/v1/user/login",
            data={
                "email": sample_organizer_data["email"],
                "password": sample_organizer_data["password"]
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
        assert event_response.status_code == HTTPStatus.CREATED.value
        event_data = event_response.json()["data"]
        event_id = event_data["id"]
        
        # Register multiple attendees with unique emails
        attendees = []
        for i in range(3):
            attendee_data = sample_attendee_data.copy()
            attendee_data["email"] = generate_unique_email(f"attendee{i}")  # Generate unique email for each attendee
            attendee_data["event_id"] = event_id
            response = client.post(
                "/api/v1/attendees/",
                json=attendee_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == HTTPStatus.CREATED.value
            attendees.append(response.json()["data"])
        
        # Update event status to ONGOING
        response = client.patch(
            f"/api/v1/events/{event_id}/status?status={EventStatus.ONGOING.value}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == HTTPStatus.OK.value
        
        # Create CSV file for bulk check-in
        string_buffer = io.StringIO()
        csv_writer = csv.writer(string_buffer)
        for attendee in attendees:
            csv_writer.writerow([attendee["email"]])
        csv_content = string_buffer.getvalue().encode('utf-8')
        csv_data = io.BytesIO(csv_content)
        csv_data.seek(0)
        
        # Perform bulk check-in
        files = {
            "file": ("attendees.csv", csv_data, "text/csv")
        }
        response = client.post(
            f"/api/v1/attendees/bulk-check-in?event_id={event_id}",
            files=files,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == HTTPStatus.OK.value
        data = response.json()["data"]
        assert len(data) == len(attendees)
        for attendee in data:
            assert attendee["check_in_status"] is True

    @patch('datetime.datetime')
    def test_register_attendee_duplicate(self, mock_datetime, db_session, sample_event_data, sample_organizer_data, sample_attendee_data):
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
        
        # Login organizer to get bearer token
        login_response = client.post(
            "/api/v1/user/login",
            data={
                "email": sample_organizer_data["email"],
                "password": sample_organizer_data["password"]
            }
        )
        logger.info(f"Login Response: {login_response.json()}")
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
        
        # Update attendee data with event_id
        attendee_data = sample_attendee_data.copy()
        attendee_data["event_id"] = event_id
        
        # Register attendee first time
        response = client.post(
            "/api/v1/attendees/",
            json=attendee_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        logger.info(f"First Registration Response: {response.json()}")
        assert response.status_code == HTTPStatus.CREATED.value
        
        # Try to register the same attendee again
        response = client.post(
            "/api/v1/attendees/",
            json=attendee_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        logger.info(f"Duplicate Registration Response: {response.json()}")
        assert response.status_code == HTTPStatus.BAD_REQUEST.value
        assert "Attendee already registered for this event" in response.json()["detail"] 