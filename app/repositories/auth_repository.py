from sqlalchemy.orm import Session
from app.models import User, Business, BusinessSettings
import uuid

class AuthRepository:
    def get_user_by_email(self, db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

    def create_business_and_user(
        self, 
        db: Session, 
        business_data: dict, 
        user_data: dict, 
        hashed_password: str,
        slug: str
    ) -> User:
        # 1. Create Business
        business = Business(
            legal_name=business_data["legal_name"],
            slug=slug,
            email=user_data["email"],
            phone=business_data.get("phone")
        )
        db.add(business)
        db.flush()  # Get business.id

        # 2. Create Settings
        settings = BusinessSettings(business_id=business.id)
        db.add(settings)

        # 3. Create Owner User
        user = User(
            business_id=business.id,
            full_name=user_data["full_name"],
            email=user_data["email"],
            password_hash=hashed_password,
            role="owner"
        )
        db.add(user)
        db.flush()
        return user