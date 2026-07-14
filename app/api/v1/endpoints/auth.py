from app.core.response import api_response
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.services.auth_service import AuthService
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["Authentication"])
service = AuthService()

# --- Schemas ---
class RegisterRequest(BaseModel):
    legal_name: str 
    owner_name: str
    email: EmailStr
    phone: str | None = None
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# --- Routes ---
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    # Generate a slug from the legal name
    slug = request.legal_name.lower().replace(" ", "-")
    try:
        user = service.register_owner(
            db, 
            {"legal_name": request.legal_name, "phone": request.phone},
            {"full_name": request.owner_name, "email": request.email, "password": request.password},
            slug
        )
        db.commit()
        return api_response(
            data={"user_id": str(user.id)},
            message="Business and Owner registered successfully"
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    clean_email = request.email.strip()
    clean_password = request.password.strip()
    
    result = service.login_user(db, clean_email, clean_password)
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    
    return {
        "access_token": result["access_token"],
        "token_type": "bearer",
        "user": {
            "id": str(result["user"].id),
            "email": result["user"].email,
            "full_name": result["user"].full_name,
            "role": result["user"].role
        }
    }

@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    return api_response(
        data={
            "id": str(current_user.id),
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role
        },
        message="User retrieved successfully"
    )