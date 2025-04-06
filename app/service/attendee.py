from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ..dao.attendee import AttendeeDAO
from ..dao.event import EventDAO
from ..dto.attendee import AttendeeCreate, AttendeeUpdate, AttendeeResponse, BulkCheckInRequest
from ..core.database import get_db
from ..common.response import AppResponse
from ..common.enums import HTTPStatus, EventStatus
from ..common.logger import logger


class AttendeeService:
    def __init__(self):
        self.attendee_dao = AttendeeDAO()
        self.event_dao = EventDAO()

    def register_attendee(self, db: Session, attendee_in: AttendeeCreate) -> AppResponse[AttendeeResponse]:
        """
        Register an attendee for an event.
        
        Args:
            db: Database session
            attendee_in: AttendeeCreate object containing attendee details
            
        Returns:
            AppResponse containing the registered attendee
        """
        # Check if event exists
        logger.info(f"Register Attendee: {attendee_in}")
        event = self.event_dao.get(db, attendee_in.event_id)
        if not event:
            return AppResponse.error_response(
                status_code=HTTPStatus.NOT_FOUND,
                message="Event not found"
            )
        # Check if attendee already registered
        existing_attendee = self.attendee_dao.get_by_email(db, attendee_in.email)
        logger.info(f"Existing attendee: {existing_attendee}")
        if existing_attendee and existing_attendee.event_id == attendee_in.event_id:
            return AppResponse.error_response(
                status_code=HTTPStatus.BAD_REQUEST,
                message="Attendee already registered for this event"
            )

        # Check if event is still open for registration
        if event.status in [EventStatus.COMPLETED, EventStatus.CANCELLED]:
            return AppResponse.error_response(
                status_code=HTTPStatus.BAD_REQUEST,
                message="Event is not open for registration"
            )

        # Check if attendee already registered
        existing_attendee = self.attendee_dao.get_by_email(db, attendee_in.email)
        logger.info(f"Existing attendee: {existing_attendee}")
        if existing_attendee and existing_attendee.event_id == attendee_in.event_id:
            return AppResponse.error_response(
                status_code=HTTPStatus.BAD_REQUEST,
                message="Attendee already registered for this event"
            )

        # Check if event has reached max attendees
        current_attendees = self.attendee_dao.get_by_event(db, attendee_in.event_id)
        logger.info(f"Current attendees: {current_attendees}")
        if len(current_attendees) >= event.max_attendees:
            return AppResponse.error_response(
                status_code=HTTPStatus.BAD_REQUEST,
                message="Event has reached maximum attendees"
            )

        attendee = self.attendee_dao.create(db, attendee_in.model_dump())
        logger.info(f"Attendee created: {attendee}")
        return AppResponse.success_response(
            status_code=HTTPStatus.CREATED,
            message="Attendee registered successfully",
            data=attendee
        )

    def check_in_attendee(self, db: Session, attendee_id: int) -> Optional[AttendeeResponse]:
        """
        Check in an attendee for an event.
        
        Args:
            db: Database session
            attendee_id: ID of the attendee to check in
        """
        logger.info(f"Check in Attendee: {attendee_id}")
        attendee = self.attendee_dao.get(db, attendee_id)
        if not attendee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attendee not found"
            )

        event = self.event_dao.get(db, attendee.event_id)
        logger.info(f"Event: {event}")
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        if event.status != EventStatus.ONGOING:
            logger.info(f"Event is not ongoing: {event.status}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Event is not ongoing"
            )

        if attendee.check_in_status:
            logger.info(f"Attendee already checked in: {attendee.check_in_status}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Attendee already checked in"
            )

        updated_attendee = self.attendee_dao.check_in_attendee(db, attendee_id)
        return AttendeeResponse.model_validate(updated_attendee) if updated_attendee else None

    def get_attendees(
        self,
        db: Session,
        event_id: Optional[int] = None,
        email: Optional[str] = None,
        check_in_status: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> AppResponse[List[AttendeeResponse]]:
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
            AppResponse containing list of attendees
        """
        try:
            # If event_id is provided, verify the event exists
            logger.info(f"Getting attendees with event_id: {event_id}, email: {email}, check_in_status: {check_in_status}")
            if event_id:
                event = self.event_dao.get_by_id(db, event_id)
                if not event:
                    return AppResponse.error_response(
                        status_code=HTTPStatus.NOT_FOUND,
                        message="Event not found"
                    )

            # Get attendees with filters
            attendees = self.attendee_dao.get_attendees(
                db=db,
                event_id=event_id,
                email=email,
                check_in_status=check_in_status,
                skip=skip,
                limit=limit
            )

            # Convert to response models
            attendee_responses = [AttendeeResponse.model_validate(attendee) for attendee in attendees]
            logger.info(f"Attendee responses: {attendee_responses}")

            return AppResponse.success_response(
                status_code=HTTPStatus.OK,
                data=attendee_responses,
                message="Attendees retrieved successfully"
            )

        except Exception as e:
            return AppResponse.error_response(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                message=f"Error retrieving attendees: {str(e)}"
            )

    def get_checked_in_attendees(self, db: Session, event_id: int, skip: int = 0, limit: int = 100) -> List[AttendeeResponse]:
        """
        Get checked-in attendees for an event.
        
        Args:
            db: Database session
            event_id: ID of the event to get checked-in attendees for
            skip: Number of records to skip
        """
        attendees = self.attendee_dao.get_checked_in_attendees(db, event_id, skip, limit)
        return [AttendeeResponse.model_validate(attendee) for attendee in attendees]

    def bulk_check_in_attendees(self, db: Session, request: BulkCheckInRequest) -> AppResponse[List[AttendeeResponse]]:
        """
        Check in multiple attendees for an event.
        
        Args:
            db: Database session
            request: BulkCheckInRequest containing event_id and list of attendee emails
            
        Returns:
            AppResponse containing list of checked-in attendees
        """
        try:
            # Verify event exists and is ongoing
            event = self.event_dao.get(db, request.event_id)
            logger.info(f"Event: {event}")
            if not event:
                return AppResponse.error_response(
                    status_code=HTTPStatus.NOT_FOUND,
                    message="Event not found"
                )

            if event.status != EventStatus.ONGOING:
                logger.info(f"Event is not ongoing: {event.status}")
                return AppResponse.error_response(
                    status_code=HTTPStatus.BAD_REQUEST,
                    message="Event is not ongoing"
                )

            # Get all attendees for the event
            attendees = self.attendee_dao.get_by_event(db, request.event_id)
            email_to_attendee = {attendee.email: attendee for attendee in attendees}
            logger.info(f"Email to attendee: {email_to_attendee}")

            checked_in_attendees = []
            errors = []

            # Process each email
            logger.info(f"Processing emails: {request.attendee_emails}")
            for email in request.attendee_emails:
                attendee = email_to_attendee.get(email)
                if not attendee:
                    errors.append(f"Attendee with email {email} not found")
                    continue

                if attendee.check_in_status:
                    errors.append(f"Attendee with email {email} already checked in")
                    continue

                # Check in the attendee
                updated_attendee = self.attendee_dao.check_in_attendee(db, attendee.id)
                if updated_attendee:
                    checked_in_attendees.append(AttendeeResponse.model_validate(updated_attendee))

            # Prepare response
            message = "Bulk check-in completed"
            if errors:
                message += f" with {len(errors)} errors: " + "; ".join(errors)

            return AppResponse.success_response(
                status_code=HTTPStatus.OK,
                message=message,
                data=checked_in_attendees
            )

        except Exception as e:
            return AppResponse.error_response(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                message=f"Error during bulk check-in: {str(e)}"
            ) 