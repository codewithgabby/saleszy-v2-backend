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
    
    def get_users_by_business(self, db: Session, business_id: uuid.UUID) -> list[User]:
        return db.query(User).filter(User.business_id == business_id, User.is_active == True).all()

    def get_user_by_id(self, db: Session, user_id: uuid.UUID, business_id: uuid.UUID) -> User | None:
        return db.query(User).filter(User.id == user_id, User.business_id == business_id).first()

    def create_staff(self, db: Session, business_id: uuid.UUID, full_name: str, email: str, password_hash: str, role: str = "cashier") -> User:
        user = User(
            business_id=business_id,
            full_name=full_name,
            email=email,
            password_hash=password_hash,
            role=role
        )
        db.add(user)
        db.flush()
        return user

    def update_user(self, db: Session, user: User, updates: dict) -> User:
        for key, value in updates.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        db.flush()
        return user

    def deactivate_user(self, db: Session, user: User) -> User:
        user.is_active = False
        db.flush()
        return user