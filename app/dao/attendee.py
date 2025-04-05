from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..vo.attendee import Attendee
from .base import BaseDAO
from ..dto.attendee import AttendeeCreate, AttendeeUpdate
from ..vo.event import Event
from ..vo.user import User

class AttendeeDAO(BaseDAO[Attendee]):
    def __init__(self):
        super().__init__(Attendee)

    def get_attendees(
        self,
        db: Session,
        event_id: Optional[int] = None,
        email: Optional[str] = None,
        check_in_status: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Attendee]:
        """
        Get attendees with optional filters.
        
        Args:
            db: Database session
            event_id: Optional event ID to filter by
            email: Optional email to filter by
            check_in_status: Optional check-in status to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of attendees matching the filters
        """
        query = db.query(Attendee)
        
        if event_id is not None:
            query = query.filter(Attendee.event_id == event_id)
        if email is not None:
            query = query.filter(Attendee.email == email)
        if check_in_status is not None:
            query = query.filter(Attendee.check_in_status == check_in_status)
            
        return query.offset(skip).limit(limit).all()

    def get_by_event(
        self, 
        db: Session, 
        event_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Attendee]:
        return db.query(Attendee).filter(Attendee.event_id == event_id).offset(skip).limit(limit).all()

    def get_by_email(self, db: Session, email: str) -> Optional[Attendee]:
        return db.query(Attendee).filter(Attendee.email == email).first()

    def get_checked_in_attendees(self, db: Session, event_id: int, skip: int = 0, limit: int = 100) -> List[Attendee]:
        return db.query(Attendee).filter(
            and_(Attendee.event_id == event_id, Attendee.check_in_status == True)
        ).offset(skip).limit(limit).all()

    def check_in_attendee(self, db: Session, attendee_id: int) -> Optional[Attendee]:
        attendee = db.query(Attendee).filter(Attendee.id == attendee_id).first()
        if attendee:
            attendee.check_in_status = True
            db.commit()
            db.refresh(attendee)
        return attendee

    def get_by_id(self, db: Session, attendee_id: int) -> Optional[Attendee]:
        return db.query(Attendee).filter(Attendee.id == attendee_id).first()

    def get_by_event_and_user(self, db: Session, event_id: int, user_id: int) -> Optional[Attendee]:
        return db.query(Attendee).filter(
            and_(Attendee.event_id == event_id, Attendee.user_id == user_id)
        ).first()

    def create(self, db: Session, attendee_data: dict) -> Attendee:
        attendee = Attendee(**attendee_data)
        db.add(attendee)
        db.commit()
        db.refresh(attendee)
        return attendee

    def update(self, db: Session, attendee_id: int, attendee_data: dict) -> Optional[Attendee]:
        attendee = self.get_by_id(db, attendee_id)
        if attendee:
            for key, value in attendee_data.items():
                setattr(attendee, key, value)
            db.commit()
            db.refresh(attendee)
        return attendee

    def delete(self, db: Session, attendee_id: int) -> bool:
        attendee = self.get_by_id(db, attendee_id)
        if attendee:
            db.delete(attendee)
            db.commit()
            return True
        return False 