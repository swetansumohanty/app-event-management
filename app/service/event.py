from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ..dao.event import EventDAO
from ..dao.attendee import AttendeeDAO
from ..dto.event import EventCreate, EventUpdate, EventResponse
from ..common.enums import EventStatus
from ..core.database import get_db

class EventService:
    def __init__(self):
        self.event_dao = EventDAO()
        self.attendee_dao = AttendeeDAO()

    def create_event(self, db: Session, event_in: EventCreate, organizer_id: int) -> EventResponse:
        if event_in.start_time >= event_in.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End time must be after start time"
            )
        
        event_data = event_in.model_dump()
        event_data["organizer_id"] = organizer_id
        event = self.event_dao.create(db, event_data)
        return EventResponse.model_validate(event)

    def update_event(self, db: Session, event_id: int, event_in: EventUpdate, organizer_id: int) -> Optional[EventResponse]:
        event = self.event_dao.get_by_id(db, event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        if event.organizer_id != organizer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this event"
            )
        
        if event_in.start_time and event_in.end_time and event_in.start_time >= event_in.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End time must be after start time"
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
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid status value. Must be one of: {valid_statuses}"
                    )
                update_data['status'] = update_data['status'].upper()
        
        updated_event = self.event_dao.update(db, event_id, update_data)
        if not updated_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        return EventResponse.model_validate(updated_event)

    def get_event(self, db: Session, event_id: int) -> Optional[EventResponse]:
        event = self.event_dao.get(db, event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        return EventResponse.model_validate(event)

    def get_events(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[EventStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[EventResponse]:
        if status:
            events = self.event_dao.get_by_status(db, status, skip, limit)
        elif start_date and end_date:
            events = self.event_dao.get_by_date_range(db, start_date, end_date, skip, limit)
        else:
            events = self.event_dao.get_all(db, skip, limit)
        
        return [EventResponse.model_validate(event) for event in events]

    def update_event_status(self, db: Session, event_id: int, status: EventStatus, organizer_id: int) -> Optional[EventResponse]:
        event = self.event_dao.get(db, event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        if event.organizer_id != organizer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this event"
            )
        
        updated_event = self.event_dao.update_status(db, event_id, status)
        return EventResponse.model_validate(updated_event) if updated_event else None 