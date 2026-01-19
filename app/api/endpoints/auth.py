"""
Endpoints for authentication.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import schemas
from app.services.auth import AuthService
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.organization import Organization
from app.models.user_type import UserType

logger = logging.getLogger(__name__)

router = APIRouter()

# Create auth service instance
auth_service = AuthService()


@router.post("/login", response_model=Dict[str, Any])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """
    Authenticate user with Keycloak and return access token. If user is found, but is its first login, it will be saved in the database.
    """
    try:
        # Authenticate user with Keycloak
        if not form_data.username or not form_data.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username and password are required"
            )
        # Call the authentication service
        if not auth_service:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service is not available"
            )
        if not form_data.username.strip() or not form_data.password.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username and password cannot be empty"
            )
        result = auth_service.authenticate(form_data.username, form_data.password)
        # Get user information from Keycloak using the access token
        from app.utils.keycloak import keycloak_handler
        access_token = result.get("access_token")
        user_info = keycloak_handler.validate_token(access_token)
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudo obtener la información del usuario de Keycloak"
            )
        
        # If the user is not found in the database, create a new user
        keycloak_id = user_info.get("sub")
        if not keycloak_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ID de usuario de Keycloak no encontrado"
            )
            
        user = db.query(User).filter(User.keycloak_id == keycloak_id).first()
        org_name = user_info.get("coe_name")
        org_id = None 
        if org_name:
            org = db.query(Organization).filter(Organization.org_name == org_name).first()
            if org:
                org_id = org.id

        if not user:
            # Get default user type for new users
            default_user_type_id = None
            
            # First try to find "Usuario estándar"
            default_user_type = db.query(UserType).filter(UserType.description == "Usuario estándar").first()
            if default_user_type:
                default_user_type_id = default_user_type.id
            else:
                # If not found, try to get any available user type
                any_user_type = db.query(UserType).first()
                if any_user_type:
                    default_user_type_id = any_user_type.id
                    logger.warning(f"Using fallback user type: {any_user_type.description} (ID: {any_user_type.id})")
                else:
                    logger.warning("No user types found in database, creating user without user_type_id")
            user_info.coe_name = user_info.get("preferred_username", "unknown")
            user = User(
                keycloak_id=keycloak_id,
                username=form_data.username,
                email=user_info.get("email", ""),
                first_name=user_info.get("given_name", ""),
                last_name=user_info.get("family_name", ""),
                user_type_id=default_user_type_id,
                organization_id=org_id
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            result["keycloak_id"] = keycloak_id
        else:
            # User exists, check if any information needs to be updated
            needs_update = False
            
            # Check for changes in user information
            new_email = user_info.get("email", "")
            new_first_name = user_info.get("given_name", "")
            new_last_name = user_info.get("family_name", "")
            
            if user.email != new_email:
                user.email = new_email
                needs_update = True
            
            if user.first_name != new_first_name:
                user.first_name = new_first_name
                needs_update = True
            
            if user.last_name != new_last_name:
                user.last_name = new_last_name
                needs_update = True
            
            # Update username if it has changed
            if user.username != form_data.username:
                user.username = form_data.username
                needs_update = True
            
            # If user doesn't have a user_type_id, assign the default one
            if user.user_type_id is None:
                default_user_type = db.query(UserType).filter(UserType.description == "Usuario estándar").first()
                if not default_user_type:
                    user.user_type_id = 4  # Fallback to ID 4
                else:
                    user.user_type_id = default_user_type.id
                needs_update = True
            
            if user.organization_id != org_id:
                user.organization_id = org_id
                needs_update = True

                
            # Save changes if any updates were made
            if needs_update:
                db.commit()
                db.refresh(user)

            result["keycloak_id"] = keycloak_id
    
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error durante la autenticación: {str(e)}"
        )


@router.post("/refresh-token", response_model=Dict[str, Any])
def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Updates an access token using the refresh token.
    """
    try:
        result = auth_service.refresh_token(refresh_token)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el token: {str(e)}"
        )


@router.get("/me", response_model=schemas.User)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get current user information.
    """
    return current_user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    refresh_token: str,
    db: Session = Depends(get_db)
) -> None:
    """
    Logs out the user by invalidating the token.
    """
    try:
        auth_service.logout(refresh_token)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cerrar sesión: {str(e)}"
        )
