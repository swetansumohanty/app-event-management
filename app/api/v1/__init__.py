from fastapi import APIRouter
from .endpoints import events, attendees, user

router = APIRouter()

router.include_router(events.router, prefix="/events", tags=["events"])
router.include_router(attendees.router, prefix="/attendees", tags=["attendees"])
router.include_router(user.router, prefix="/user", tags=["users"]) 