from sqlalchemy.orm import Session
from app.dao.user import UserDAO
from app.dto.user import UserCreate, UserResponse
from app.common.response import AppResponse
from app.common.enums import HTTPStatus
from app.service.auth import get_password_hash

class UserService:
    def __init__(self):
        self.user_dao = UserDAO()

    def register_user(self, db: Session, user_in: UserCreate) -> AppResponse[UserResponse]:
        # Check if user already exists
        if self.user_dao.get_by_email(db, email=user_in.email):
            return AppResponse.error_response(
                status_code=HTTPStatus.BAD_REQUEST,
                message="Email already registered"
            )
        
        # Create new user
        user_data = user_in.model_dump()
        user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
        user = self.user_dao.create(db, user_data)
        
        return AppResponse.success_response(
            status_code=HTTPStatus.CREATED,
            message="User created successfully",
            data=user
        )

    def get_user_by_email(self, db: Session, email: str) -> AppResponse[UserResponse]:
        user = self.user_dao.get_by_email(db, email)
        if not user:
            return AppResponse.error_response(
                status_code=HTTPStatus.NOT_FOUND,
                message="User not found"
            )
        
        return AppResponse.success_response(
            status_code=HTTPStatus.OK,
            message="User retrieved successfully",
            data=user
        ) 