from pydantic import BaseModel, constr
from typing import Optional
from datetime import datetime
from ..common.enums import EventStatus

class EventBase(BaseModel):
    name: constr(min_length=1, max_length=100)
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: constr(min_length=1, max_length=200)
    max_attendees: int

class EventCreate(EventBase):
    pass

class EventUpdate(EventBase):
    name: Optional[constr(min_length=1, max_length=100)] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[constr(min_length=1, max_length=200)] = None
    max_attendees: Optional[int] = None
    status: Optional[EventStatus] = None

class EventInDB(EventBase):
    id: int
    status: EventStatus
    created_at: datetime
    updated_at: datetime
    organizer_id: int

    class Config:
        from_attributes = True

class EventResponse(EventBase):
    id: int
    status: EventStatus
    created_at: datetime
    updated_at: datetime
    organizer_id: int

    class Config:
        from_attributes = True 