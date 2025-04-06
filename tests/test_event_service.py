import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.service.event import EventService
from app.dao.event import EventDAO
from app.dao.user import UserDAO
from app.common.enums import EventStatus, HTTPStatus
from app.common.response import AppResponse
from app.dto.event import EventCreate, EventUpdate, EventResponse
from app.vo.event import Event
from app.common.logger import logger
from unittest.mock import patch
from fastapi import HTTPException, status


@pytest.fixture
def event_service():
    return EventService()

@pytest.fixture
def mock_db(mocker):
    return mocker.Mock(spec=Session)

@pytest.fixture
def mock_event_dao(mocker):
    return mocker.Mock(spec=EventDAO)

@pytest.fixture
def mock_user_dao(mocker):
    return mocker.Mock(spec=UserDAO)

@pytest.fixture
def sample_event():
    return {
        "id": 1,
        "name": "Test Event",
        "description": "Test Description",
        "start_time": datetime.now() + timedelta(days=1),
        "end_time": datetime.now() + timedelta(days=2),
        "location": "Test Location",
        "max_attendees": 100,
        "status": EventStatus.SCHEDULED,
        "organizer_id": 1,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

class TestEventService:
    @patch('datetime.datetime')
    def test_automatic_status_update_to_completed(self, mock_datetime, event_service, mock_db, mock_event_dao, sample_event):
        # Setup mock datetime
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # Setup
        past_event = sample_event.copy()
        past_event["end_time"] = mock_now - timedelta(hours=1)  # Event ended 1 hour ago
        past_event["status"] = EventStatus.ONGOING
        
        # Create a mock event object with the required attributes
        class MockEvent:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        # Create the initial event
        mock_event = MockEvent(**past_event)
        
        # Create the updated event with COMPLETED status
        updated_event_data = past_event.copy()
        updated_event_data["status"] = EventStatus.COMPLETED
        updated_event = MockEvent(**updated_event_data)
        
        # Setup the mock to return the initial event on get
        mock_event_dao.get.return_value = mock_event
        
        # Setup the mock to return the updated event on update_status
        mock_event_dao.update_status.return_value = updated_event
        
        event_service.event_dao = mock_event_dao
        
        # Test
        response = event_service.get_event(mock_db, 1)
        
        # Verify
        assert response.status_code == HTTPStatus.OK
        mock_event_dao.update_status.assert_called_once_with(
            mock_db, 1, EventStatus.COMPLETED
        )
        
        # Verify the response data has the updated status
        assert response.data.status == EventStatus.COMPLETED
        assert isinstance(response.data, Event)

    def test_invalid_status_transition(self, event_service, mock_db, mock_event_dao, sample_event):
        # Setup
        completed_event_data = sample_event.copy()
        completed_event_data["status"] = EventStatus.COMPLETED
        
        # Create a mock event object with the required attributes
        class MockEvent:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        # Create the mock event
        mock_event = MockEvent(**completed_event_data)
        
        # Setup the mock to return the event
        mock_event_dao.get.return_value = mock_event
        event_service.event_dao = mock_event_dao
        
        # Test
        response = event_service.update_event_status(
            mock_db, 1, EventStatus.ONGOING, 1
        )
        
        # Verify
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert "Invalid status transition" in response.message

    def test_update_event_with_invalid_times(self, event_service, mock_db, mock_event_dao, sample_event):
        # Setup
        # Create a mock event object with the required attributes
        class MockEvent:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        # Create the mock event
        mock_event = MockEvent(**sample_event)
        
        # Setup the mock to return the event
        mock_event_dao.get_by_id.return_value = mock_event
        event_service.event_dao = mock_event_dao
        
        # Create an update with invalid times
        update_data = EventUpdate(
            name="Updated Event",
            start_time=datetime.now() + timedelta(days=2),
            end_time=datetime.now() + timedelta(days=1),
            location="Updated Location",
            max_attendees=150
        )
        
        # Test
        response = event_service.update_event(mock_db, 1, update_data, 1)
        
        # Verify
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert "End time must be after start time" in response.message


    def test_registration_limit(self, event_service, mock_db, mock_event_dao, sample_event):
        # Setup
        from app.service.attendee import AttendeeService
        from app.dto.attendee import AttendeeCreate
        from app.dao.attendee import AttendeeDAO
        
        # Create a mock event object with the required attributes
        class MockEvent:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
                self.max_attendees = kwargs.get("max_attendees", 0)
        
        # Create a mock attendee DAO
        mock_attendee_dao = AttendeeDAO()
        
        # Create mock attendees list
        mock_attendees = []
        for i in range(sample_event["max_attendees"]):
            mock_attendees.append(MockEvent(**{
                "id": i + 1,
                "event_id": sample_event["id"],
                "first_name": f"Test{i}",
                "last_name": "User",
                "email": f"test{i}@example.com",
                "phone_number": "1234567890",
                "check_in_status": False
            }))
        
        # Create the mock event
        mock_event = MockEvent(**sample_event)
        
        # Mock the database queries
        mock_event_dao.get.return_value = mock_event
        mock_attendee_dao.get_by_event = lambda db, event_id: mock_attendees
        
        # Create attendee service with mocked DAOs
        attendee_service = AttendeeService()
        attendee_service.event_dao = mock_event_dao
        attendee_service.attendee_dao = mock_attendee_dao
        
        # Test registration attempt
        attendee_data = AttendeeCreate(
            event_id=1,
            first_name="Test",
            last_name="User",
            email="test@example.com",
            phone_number="1234567890"
        )
        response = attendee_service.register_attendee(mock_db, attendee_data)
        
        # Verify
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert "Event has reached maximum attendees" in response.message

    def test_check_in_validation(self, event_service, mock_db, mock_event_dao, mocker, sample_event):
        # Setup
        from app.service.attendee import AttendeeService
        from app.dao.attendee import AttendeeDAO
        from datetime import datetime, timedelta
        
        # Create the mock event
        scheduled_event = mocker.Mock()
        scheduled_event.status = EventStatus.ONGOING
        scheduled_event.start_time = datetime.now() + timedelta(days=1)  # Event hasn't started yet
        
        # Create a mock attendee object that matches AttendeeResponse structure
        class MockAttendee:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        # Create the mock attendee with all required fields for AttendeeResponse
        mock_now = datetime.now()
        mock_attendee = MockAttendee(
            id=1,
            event_id=1,
            first_name="Test",
            last_name="User",
            email="test@example.com",
            phone_number="1234567890",
            check_in_status=False,
            check_in_time=None,
            created_at=mock_now,
            updated_at=mock_now
        )
        
        # Create mock attendee DAO
        mock_attendee_dao = mocker.Mock(spec=AttendeeDAO)
        mock_attendee_dao.get.return_value = mock_attendee
        
        # Mock the database queries
        mock_event_dao.get.return_value = scheduled_event
        
        # Create attendee service with mocked DAOs
        attendee_service = AttendeeService()
        attendee_service.event_dao = mock_event_dao
        attendee_service.attendee_dao = mock_attendee_dao
        
        # Test check-in attempt
        with pytest.raises(HTTPException) as exc_info:
            attendee_service.check_in_attendee(mock_db, mock_attendee.id)
        
        # Verify
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Event is not ongoing" in str(exc_info.value.detail)

    def test_valid_status_transitions(self, event_service):
        # Test SCHEDULED to ONGOING
        assert event_service._is_valid_status_transition(
            EventStatus.SCHEDULED, EventStatus.ONGOING
        ) is True
        
        # Test ONGOING to COMPLETED
        assert event_service._is_valid_status_transition(
            EventStatus.ONGOING, EventStatus.COMPLETED
        ) is True
        
        # Test SCHEDULED to CANCELLED
        assert event_service._is_valid_status_transition(
            EventStatus.SCHEDULED, EventStatus.CANCELLED
        ) is True

    def test_invalid_status_transitions(self, event_service):
        # Test COMPLETED to ONGOING
        assert event_service._is_valid_status_transition(
            EventStatus.COMPLETED, EventStatus.ONGOING
        ) is False
        
        # Test CANCELLED to SCHEDULED
        assert event_service._is_valid_status_transition(
            EventStatus.CANCELLED, EventStatus.SCHEDULED
        ) is False
        
        # Test SCHEDULED to COMPLETED
        assert event_service._is_valid_status_transition(
            EventStatus.SCHEDULED, EventStatus.COMPLETED
        ) is False 