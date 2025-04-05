from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from ..vo.event import Event
from .base import BaseDAO
from ..dto.event import EventCreate, EventUpdate
from ..common.enums import EventStatus

class EventDAO(BaseDAO[Event]):
    def __init__(self):
        super().__init__(Event)

    def get_by_organizer(self, db: Session, organizer_id: int, skip: int = 0, limit: int = 100) -> List[Event]:
        return db.query(Event).filter(Event.organizer_id == organizer_id).offset(skip).limit(limit).all()

    def get_by_status(self, db: Session, status: str, skip: int = 0, limit: int = 100) -> List[Event]:
        return db.query(Event).filter(Event.status == status).offset(skip).limit(limit).all()

    def get_upcoming_events(self, db: Session, skip: int = 0, limit: int = 100) -> List[Event]:
        return db.query(Event).filter(Event.start_time > datetime.utcnow()).offset(skip).limit(limit).all()

    def get_past_events(self, db: Session, skip: int = 0, limit: int = 100) -> List[Event]:
        return db.query(Event).filter(Event.end_time < datetime.utcnow()).offset(skip).limit(limit).all()

    def get_by_id(self, db: Session, event_id: int) -> Optional[Event]:
        return db.query(Event).filter(Event.id == event_id).first()

    def create(self, db: Session, event_data: dict) -> Event:
        event = Event(**event_data)
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    def update(self, db: Session, event_id: int, event_data: dict) -> Optional[Event]:
        event = self.get_by_id(db, event_id)
        if event:
            for key, value in event_data.items():
                setattr(event, key, value)
            db.commit()
            db.refresh(event)
        return event

    def delete(self, db: Session, event_id: int) -> bool:
        event = self.get_by_id(db, event_id)
        if event:
            db.delete(event)
            db.commit()
            return True
        return False

    def get_by_date_range(self, db: Session, start_date: datetime, end_date: datetime, skip: int = 0, limit: int = 100) -> List[Event]:
        return db.query(Event).filter(
            Event.start_time >= start_date,
            Event.end_time <= end_date
        ).offset(skip).limit(limit).all()

    def update_status(self, db: Session, event_id: int, status: EventStatus) -> Optional[Event]:
        event = self.get_by_id(db, event_id)
        if not event:
            return None
        event.status = status
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    def get_available_events(self, db: Session, skip: int = 0, limit: int = 100) -> List[Event]:
        return db.query(Event).filter(
            Event.status == EventStatus.SCHEDULED,
            Event.start_time > datetime.utcnow()
        ).offset(skip).limit(limit).all() 