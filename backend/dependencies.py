"""
Authentication dependencies and JWT utilities
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict

from services.auth_service import decode_access_token

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """
    Dependency to get current authenticated user from JWT token
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = int(payload.get("sub"))
    email = payload.get("email")
    
    return {
        "id": user_id,
        "email": email
    }

async def get_current_active_user(current_user: Dict = Depends(get_current_user)) -> Dict:
    """
    Dependency to ensure user is active
    """
    # Could add additional checks here (e.g., user is_active from database)
    return current_user
