from jose import jwt
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.core.config import settings
from app.repositories.auth_repository import AuthRepository
from app.models import User
import bcrypt
import uuid

class AuthService:
    def __init__(self):
        self.repo = AuthRepository()

    def hash_password(self, password: str) -> str:
        # Hash using modern bcrypt
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )

    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    def create_refresh_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    def register_owner(self, db: Session, business_data: dict, user_data: dict, slug: str) -> User:
        # Check if email exists
        if self.repo.get_user_by_email(db, user_data["email"]):
            raise ValueError("Email already registered")
        
        hashed = self.hash_password(user_data["password"])
        return self.repo.create_business_and_user(db, business_data, user_data, hashed, slug)

    def login_user(self, db: Session, email: str, password: str) -> dict | None:
        user = self.repo.get_user_by_email(db, email)
        if not user or not self.verify_password(password, user.password_hash):
            return None
        return {"user": user, "access_token": self.create_access_token({"sub": str(user.id)})}