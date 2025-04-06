from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.service.auth import get_current_active_user, oauth2_scheme
from app.service.attendee import AttendeeService
from app.dto.attendee import AttendeeCreate, AttendeeResponse, BulkCheckInRequest
from app.dto.user import UserResponse
from app.common.response import AppResponse
from app.common.enums import HTTPStatus
import csv
import io
from app.common.logger import logger


router = APIRouter()
attendee_service = AttendeeService()


@router.post("/", response_model=AppResponse[AttendeeResponse], status_code=HTTPStatus.CREATED.value)
async def register_attendee(
    attendee_in: AttendeeCreate,
    db: Session = Depends(get_db)
):
    logger.info(f"Registering attendee: {attendee_in}")
    response = attendee_service.register_attendee(db, attendee_in)
    if not response.success:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.message
        )
    return response

@router.post("/{attendee_id}/check-in", response_model=AppResponse[AttendeeResponse])
async def check_in_attendee(
    attendee_id: int,
    db: Session = Depends(get_db)
):
    logger.info(f"Checking in attendee: {attendee_id}")
    response = attendee_service.check_in_attendee(db, attendee_id)
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendee not found"
        )
    return AppResponse.success_response(
        status_code=status.HTTP_200_OK,
        message="Attendee checked in successfully",
        data=response
    )

@router.get("/", response_model=AppResponse[List[AttendeeResponse]], status_code=HTTPStatus.OK.value)
async def get_attendees(
    event_id: Optional[int] = None,
    email: Optional[str] = None,
    check_in_status: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List Attendees with optional filters.
    
    Parameters:
    - event_id: Filter by specific event
    - email: Filter by attendee email
    - check_in_status: Filter by check-in status (True/False)
    - skip: Number of records to skip (for pagination)
    - limit: Maximum number of records to return
    """
    logger.info(f"Getting attendees with event_id: {event_id}, email: {email}, check_in_status: {check_in_status}")
    return attendee_service.get_attendees(
        db=db,
        event_id=event_id,
        email=email,
        check_in_status=check_in_status,
        skip=skip,
        limit=limit
    )

@router.get("/event/{event_id}/checked-in", response_model=AppResponse[List[AttendeeResponse]], status_code=HTTPStatus.OK.value)
async def get_checked_in_attendees(
    event_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    logger.info(f"Getting checked-in attendees for event: {event_id}")
    attendees = attendee_service.get_checked_in_attendees(db, event_id, skip, limit)
    return AppResponse.success_response(
        status_code=status.HTTP_200_OK,
        message="Checked-in attendees retrieved successfully",
        data=attendees
    )

@router.post("/bulk-check-in", response_model=AppResponse[List[AttendeeResponse]])
async def bulk_check_in_attendees(
    event_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Bulk check-in attendees via CSV upload.
    CSV should have a single column with attendee emails.
    """
    logger.info(f"Bulk checking in attendees for event: {event_id}")
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed"
        )

    try:
        # Read CSV file
        logger.info(f"Reading CSV file: {file.filename}")
        contents = await file.read()
        csv_file = io.StringIO(contents.decode('utf-8'))
        csv_reader = csv.reader(csv_file)
        
        # Extract emails from CSV
        logger.info(f"Extracting emails from CSV")
        emails = []
        for row in csv_reader:
            if row:  # Skip empty rows
                emails.append(row[0].strip()) 

        if not emails:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid emails found in CSV"
            )

        # Create bulk check-in request
        request = BulkCheckInRequest(
            event_id=event_id,
            attendee_emails=emails
        )
        logger.info(f"Bulk check-in request: {request}")

        # Process bulk check-in
        response = attendee_service.bulk_check_in_attendees(db, request)
        logger.info(f"Bulk check-in response: {response}")
        if not response.success:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.message
            )
        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing CSV file: {str(e)}"
        ) 