from typing import Generic, TypeVar, Optional
from pydantic import BaseModel
from .enums import HTTPStatus

T = TypeVar('T')

class AppResponse(BaseModel, Generic[T]):
    status_code: int
    success: bool
    message: str
    data: Optional[T] = None

    @staticmethod
    def success_response(*, status_code: int, message: str, data: Optional[T] = None) -> "AppResponse[T]":
        return AppResponse(
            status_code=status_code,
            success=True,
            message=message,
            data=data
        )

    @staticmethod
    def error_response(*, status_code: int, message: str) -> "AppResponse[T]":
        return AppResponse(
            status_code=status_code,
            success=False,
            message=message,
            data=None
        ) 