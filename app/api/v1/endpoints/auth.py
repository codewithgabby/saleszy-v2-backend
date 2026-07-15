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

class CreateStaffRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: str = "cashier"  # cashier, manager

class UpdateStaffRequest(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    role: str | None = None
    is_active: bool | None = None

class StaffResponse(BaseModel):
    id: str
    full_name: str
    email: str
    role: str
    is_active: bool
    last_login_at: str | None = None

# --- Staff Routes ---
@router.get("/staff")
async def list_staff(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owners can manage staff")
    
    users = service.repo.get_users_by_business(db, current_user.business_id)
    return api_response(
        data=[
            {
                "id": str(u.id),
                "full_name": u.full_name,
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None
            }
            for u in users
        ],
        message=f"Retrieved {len(users)} staff members"
    )

@router.post("/staff", status_code=status.HTTP_201_CREATED)
async def create_staff(
    request: CreateStaffRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owners can create staff")
    
    # Check email
    existing = service.repo.get_user_by_email(db, request.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    hashed = service.hash_password(request.password)
    user = service.repo.create_staff(db, current_user.business_id, request.full_name, request.email, hashed, request.role)
    db.commit()
    
    return api_response(
        data={"id": str(user.id), "full_name": user.full_name, "email": user.email, "role": user.role},
        message="Staff created successfully"
    )

@router.patch("/staff/{user_id}")
async def update_staff(
    user_id: str,
    request: UpdateStaffRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owners can update staff")
    
    from uuid import UUID
    user = service.repo.get_user_by_id(db, UUID(user_id), current_user.business_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    service.repo.update_user(db, user, updates)
    db.commit()
    
    return api_response(
        data={"id": str(user.id), "full_name": user.full_name, "email": user.email, "role": user.role, "is_active": user.is_active},
        message="Staff updated"
    )

@router.delete("/staff/{user_id}")
async def deactivate_staff(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owners can deactivate staff")
    
    from uuid import UUID
    user = service.repo.get_user_by_id(db, UUID(user_id), current_user.business_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    if user.role == "owner":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate owner")
    
    service.repo.deactivate_user(db, user)
    db.commit()
    return api_response(message="Staff deactivated")    