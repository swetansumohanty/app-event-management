from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.service.auth import get_current_active_user, oauth2_scheme
from app.service.event import EventService
from app.dto.event import EventCreate, EventUpdate, EventResponse
from app.dto.user import UserResponse
from app.common.enums import EventStatus

router = APIRouter()
event_service = EventService()

@router.post("/", response_model=EventResponse)
async def create_event(
    event_in: EventCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    current_user = await get_current_active_user(db, token)
    return event_service.create_event(db, event_in, current_user.id)

@router.get("/", response_model=List[EventResponse])
async def get_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[EventStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    return event_service.get_events(db, skip, limit, status, start_date, end_date)

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    db: Session = Depends(get_db)
):
    return event_service.get_event(db, event_id)

@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_in: EventUpdate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    current_user = await get_current_active_user(db, token)
    return event_service.update_event(db, event_id, event_in, current_user.id)

@router.patch("/{event_id}/status", response_model=EventResponse)
async def update_event_status(
    event_id: int,
    status: EventStatus,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    current_user = await get_current_active_user(db, token)
    return event_service.update_event_status(db, event_id, status, current_user.id) 