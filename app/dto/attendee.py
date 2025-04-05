from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import datetime

class AttendeeBase(BaseModel):
    first_name: constr(min_length=1, max_length=50)
    last_name: constr(min_length=1, max_length=50)
    email: EmailStr
    phone_number: Optional[str] = None
    event_id: int

class AttendeeCreate(AttendeeBase):
    pass

class AttendeeUpdate(AttendeeBase):
    first_name: Optional[constr(min_length=1, max_length=50)] = None
    last_name: Optional[constr(min_length=1, max_length=50)] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    event_id: Optional[int] = None
    check_in_status: Optional[bool] = None

class AttendeeInDB(AttendeeBase):
    id: int
    check_in_status: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AttendeeResponse(AttendeeBase):
    id: int
    check_in_status: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 