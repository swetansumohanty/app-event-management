from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ..dao.event import EventDAO
from ..dao.user import UserDAO
from ..dto.event import EventCreate, EventUpdate, EventResponse
from ..core.database import get_db
from ..common.response import AppResponse
from ..common.enums import HTTPStatus, EventStatus

class EventService:
    def __init__(self):
        self.event_dao = EventDAO()
        self.user_dao = UserDAO()

    def create_event(self, db: Session, event_in: EventCreate, organizer_id: int) -> AppResponse[EventResponse]:
        try:
            event = self.event_dao.create(db, {**event_in.model_dump(), "organizer_id": organizer_id})
            return AppResponse.success_response(
                status_code=HTTPStatus.CREATED,
                message="Event created successfully",
                data=EventResponse.model_validate(event)
            )
        except Exception as e:
            return AppResponse.error_response(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                message=f"Error creating event: {str(e)}"
            )

    def update_event(self, db: Session, event_id: int, event_in: EventUpdate, organizer_id: int) -> AppResponse[EventResponse]:
        try:
            event = self.event_dao.get_by_id(db, event_id)
            if not event:
                return AppResponse.error_response(
                    status_code=HTTPStatus.NOT_FOUND,
                    message="Event not found"
                )
            
            if event.organizer_id != organizer_id:
                return AppResponse.error_response(
                    status_code=HTTPStatus.FORBIDDEN,
                    message="Not authorized to update this event"
                )
            
            if event_in.start_time and event_in.end_time and event_in.start_time >= event_in.end_time:
                return AppResponse.error_response(
                    status_code=HTTPStatus.BAD_REQUEST,
                    message="End time must be after start time"
                )
            
            # Convert status to string value if it exists
            update_data = event_in.model_dump(exclude_unset=True)
            if 'status' in update_data:
                if isinstance(update_data['status'], EventStatus):
                    update_data['status'] = update_data['status'].value
                elif isinstance(update_data['status'], str):
                    # Validate the string value
                    valid_statuses = {'SCHEDULED', 'ONGOING', 'COMPLETED', 'CANCELED'}
                    if update_data['status'].upper() not in valid_statuses:
                        return AppResponse.error_response(
                            status_code=HTTPStatus.BAD_REQUEST,
                            message=f"Invalid status value. Must be one of: {valid_statuses}"
                        )
                    update_data['status'] = update_data['status'].upper()
            
            updated_event = self.event_dao.update(db, event_id, update_data)
            if not updated_event:
                return AppResponse.error_response(
                    status_code=HTTPStatus.NOT_FOUND,
                    message="Event not found"
                )
            return AppResponse.success_response(
                status_code=HTTPStatus.OK,
                message="Event updated successfully",
                data=EventResponse.model_validate(updated_event)
            )
        except Exception as e:
            return AppResponse.error_response(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                message=f"Error updating event: {str(e)}"
            )

    def get_event(self, db: Session, event_id: int) -> AppResponse[EventResponse]:
        try:
            event = self.event_dao.get(db, event_id)
            if not event:
                return AppResponse.error_response(
                    status_code=HTTPStatus.NOT_FOUND,
                    message="Event not found"
                )
            return AppResponse.success_response(
                status_code=HTTPStatus.OK,
                message="Event retrieved successfully",
                data=EventResponse.model_validate(event)
            )
        except Exception as e:
            return AppResponse.error_response(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                message=f"Error retrieving event: {str(e)}"
            )

    def get_events(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[EventStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> AppResponse[List[EventResponse]]:
        try:
            if status:
                events = self.event_dao.get_by_status(db, status.value, skip, limit)
            elif start_date and end_date:
                events = self.event_dao.get_by_date_range(db, start_date, end_date, skip, limit)
            else:
                events = self.event_dao.get_all(db, skip, limit)
            
            return AppResponse.success_response(
                status_code=HTTPStatus.OK,
                message="Events retrieved successfully",
                data=[EventResponse.model_validate(event) for event in events]
            )
        except Exception as e:
            return AppResponse.error_response(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                message=f"Error retrieving events: {str(e)}"
            )

    def update_event_status(self, db: Session, event_id: int, new_status: EventStatus, user_id: int) -> AppResponse[EventResponse]:
        """
        Update event status with authorization check.
        
        Args:
            db: Database session
            event_id: ID of the event to update
            new_status: New status to set
            user_id: ID of the user making the request
            
        Returns:
            AppResponse containing the updated event
        """
        try:
            # Get event and verify ownership
            event = self.event_dao.get(db, event_id)
            if not event:
                return AppResponse.error_response(
                    status_code=HTTPStatus.NOT_FOUND,
                    message="Event not found"
                )

            if event.organizer_id != user_id:
                return AppResponse.error_response(
                    status_code=HTTPStatus.FORBIDDEN,
                    message="You are not authorized to update this event"
                )

            # Validate status transition
            if not self._is_valid_status_transition(event.status, new_status):
                return AppResponse.error_response(
                    status_code=HTTPStatus.BAD_REQUEST,
                    message=f"Invalid status transition from {event.status} to {new_status}"
                )

            # Update status
            updated_event = self.event_dao.update_status(db, event_id, new_status)
            if not updated_event:
                return AppResponse.error_response(
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                    message="Failed to update event status"
                )

            return AppResponse.success_response(
                status_code=HTTPStatus.OK,
                message="Event status updated successfully",
                data=EventResponse.model_validate(updated_event)
            )

        except Exception as e:
            return AppResponse.error_response(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                message=f"Error updating event status: {str(e)}"
            )

    def _is_valid_status_transition(self, current_status: EventStatus, new_status: EventStatus) -> bool:
        valid_transitions = {
            EventStatus.SCHEDULED: [EventStatus.ONGOING, EventStatus.CANCELLED],
            EventStatus.ONGOING: [EventStatus.COMPLETED, EventStatus.CANCELLED],
            EventStatus.COMPLETED: [],
            EventStatus.CANCELLED: []
        }
        return new_status in valid_transitions.get(current_status, []) 