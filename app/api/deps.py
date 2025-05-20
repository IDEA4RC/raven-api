"""
Dependencies for the API endpoints.
"""

from typing import Generator, Optional, Dict, Any

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session
import requests

from app import models, schemas
from app.config.settings import settings
from app.db.session import SessionLocal
from app.utils.security import ALGORITHM
from app.utils.keycloak import keycloak_handler

# COMENTED FOR TESTING - Start
"""
# Keycloack has its own token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token")
"""
# COMENTED FOR TESTING - End

# In testing mode, we create an OAuth2PasswordBearer that does not require a token
# Any value can be passed as a token or it can be left empty
class DummyOAuth2PasswordBearer:
    async def __call__(self, request: Request) -> str:
        return "dummy_token"

oauth2_scheme = DummyOAuth2PasswordBearer()


def get_db() -> Generator:
    """
    Get database session.
    """
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> models.User:
    """
    TESTING MODE: Returns an admin user without verifying authentication.
    Original: Get current user from token using Keycloak.
    """
    # COMENTED FOR TESTING - Start
    """
    try:
        # Validamos el token con Keycloak
        user_info = keycloak_handler.validate_token(token)
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authentication credentials",
            )
        
        # Obtenemos el ID de Keycloak del usuario
        keycloak_id = user_info.get("sub")
        if not keycloak_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not extract user ID from token",
            )
        
        # Buscamos el usuario en nuestra base de datos usando el ID de Keycloak
        user = db.query(models.User).filter(models.User.keycloak_id == keycloak_id).first()
        if not user:
            # Podríamos crear automáticamente el usuario si no existe,
            # pero vamos a requerir registro manual por ahora
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="User not found in system"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Inactive user"
    """
    # COMENTED FOR TESTING - End

    # In testing mode, we look for the first active admin user in the database
    user = db.query(models.User).filter(models.User.is_active == True).first()

    # If no users are found, we could return an error or create one
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="No users found in system. Please seed the database."
        )
    
    return user

    # COMENTED FOR TESTING - Start
    """
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Could not validate credentials: {str(e)}",
        )
    """
    # COMENTED FOR TESTING - End