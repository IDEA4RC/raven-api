"""
Endpoints para autenticación
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app import schemas
from app.services.auth import auth_service

router = APIRouter()


@router.post("/login", response_model=Dict[str, Any])
def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    """
    Obtiene un token de acceso usando las credenciales de usuario.
    """
    try:
        result = auth_service.authenticate(form_data.username, form_data.password)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error durante la autenticación: {str(e)}"
        )


@router.post("/refresh-token", response_model=Dict[str, Any])
def refresh_token(refresh_token: str) -> Any:
    """
    Actualiza un token de acceso usando el token de actualización.
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


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(refresh_token: str) -> None:
    """
    Cierra la sesión del usuario invalidando el token.
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
