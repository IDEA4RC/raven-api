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
    MODO PRUEBAS: Devuelve un token ficticio sin verificar credenciales.
    Original: Obtiene un token de acceso usando las credenciales de usuario.
    """
    # COMENTADO PARA PRUEBAS - Inicio
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
    """
    # COMENTADO PARA PRUEBAS - Fin
    
    # En modo pruebas, devolvemos un token de acceso ficticio
    return {
        "access_token": "dummy_access_token_for_testing",
        "token_type": "bearer",
        "refresh_token": "dummy_refresh_token_for_testing",
        "expires_in": 3600,
        "scope": "openid profile email"
    }


@router.post("/refresh-token", response_model=Dict[str, Any])
def refresh_token(refresh_token: str) -> Any:
    """
    MODO PRUEBAS: Devuelve un token ficticio sin verificar el refresh_token.
    Original: Actualiza un token de acceso usando el token de actualización.
    """
    # COMENTADO PARA PRUEBAS - Inicio
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
    """
    # COMENTADO PARA PRUEBAS - Fin
    
    # En modo pruebas, devolvemos un token de acceso ficticio nuevo
    return {
        "access_token": "new_dummy_access_token_for_testing",
        "token_type": "bearer",
        "refresh_token": "new_dummy_refresh_token_for_testing",
        "expires_in": 3600,
        "scope": "openid profile email"
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(refresh_token: str) -> None:
    """
    MODO PRUEBAS: No hace nada, simplemente devuelve éxito.
    Original: Cierra la sesión del usuario invalidando el token.
    """
    # COMENTADO PARA PRUEBAS - Inicio
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
    """
    # COMENTADO PARA PRUEBAS - Fin
    
    # En modo pruebas, no hacemos nada, simplemente devolvemos éxito
    return None
