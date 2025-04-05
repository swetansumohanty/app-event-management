from pydantic import BaseModel, EmailStr, constr, Field
from typing import Optional, List
from datetime import datetime

class AttendeeBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20)
    event_id: int

class AttendeeCreate(AttendeeBase):
    pass

class AttendeeUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20)
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
    check_in_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BulkCheckInRequest(BaseModel):
    event_id: int
    attendee_emails: List[EmailStr] 