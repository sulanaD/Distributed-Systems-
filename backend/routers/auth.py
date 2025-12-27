"""
Authentication router
"""
from fastapi import APIRouter, HTTPException, status
from models.schemas import UserRegister, UserLogin, TokenResponse, UserResponse, ErrorResponse

from services.auth_service import create_user, authenticate_user, create_access_token

router = APIRouter()

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """Register a new user"""
    # Check if user already exists
    from services.auth_service import get_user_by_email
    existing_user = await get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = await create_user(
        email=user_data.email,
        password=user_data.password,
        first_name=user_data.first_name,
        last_name=user_data.last_name
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    # Create access token
    access_token = create_access_token(user['id'], user['email'])
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Login with email and password"""
    user = await authenticate_user(credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token = create_access_token(user['id'], user['email'])
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/logout")
async def logout():
    """Logout (client-side token removal)"""
    return {"message": "Logged out successfully"}
