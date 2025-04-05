from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..vo.user import User
from .base import BaseDAO
from ..dto.user import UserCreate, UserUpdate

class UserDAO(BaseDAO[User]):
    def __init__(self):
        super().__init__(User)

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        query = select(User).where(User.email == email)
        return db.execute(query).scalar_one_or_none()

    def create_user(self, db: Session, user_in: UserCreate, hashed_password: str) -> User:
        user_data = user_in.model_dump(exclude={"password"})
        user_data["hashed_password"] = hashed_password
        return self.create(db, user_data)

    def update_user(self, db: Session, user_id: int, user_in: UserUpdate, hashed_password: Optional[str] = None) -> Optional[User]:
        user = self.get(db, user_id)
        if not user:
            return None
        
        update_data = user_in.model_dump(exclude_unset=True)
        if hashed_password:
            update_data["hashed_password"] = hashed_password
        
        return self.update(db, user, update_data) 