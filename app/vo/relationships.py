from sqlalchemy.orm import relationship
from .user import User
from .attendee import Attendee
from .event import Event

# User relationships
User.attendees = relationship("Attendee", back_populates="user")
User.events_organized = relationship("Event", back_populates="organizer")

# Attendee relationships
Attendee.event = relationship("Event", back_populates="attendees")
Attendee.user = relationship("User", back_populates="attendees")

# Event relationships
Event.attendees = relationship("Attendee", back_populates="event")
Event.organizer = relationship("User", back_populates="events_organized") 