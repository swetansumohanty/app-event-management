from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.service.auth import (
    verify_password,
    create_access_token,
    get_current_active_user,
    oauth2_scheme
)
from app.dto.user import UserCreate, UserResponse, Token
from app.service.user import UserService
from app.common.response import AppResponse

router = APIRouter()
user_service = UserService()

@router.post("/register", response_model=AppResponse[UserResponse])
async def register(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    response = user_service.register_user(db, user_in)
    if not response.success:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.message
        )
    return response

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    response = user_service.get_user_by_email(db, form_data.username)
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = response.data
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=AppResponse[UserResponse])
async def get_current_user_endpoint(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user = await get_current_active_user(db, token)
    return AppResponse.success(
        status_code=status.HTTP_200_OK,
        message="User retrieved successfully",
        data=user
    ) 