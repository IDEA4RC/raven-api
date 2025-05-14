"""
Servicio de autenticación con Keycloak
"""

from typing import Dict, Any, Optional
import requests
from fastapi import HTTPException, status

from app.config.settings import settings
from app.utils.keycloak import keycloak_handler


class AuthService:
    """
    Servicio para manejar la autenticación con Keycloak
    """
    
    def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Autenticar un usuario contra Keycloak y obtener tokens
        """
        url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token"
        
        data = {
            "client_id": settings.KEYCLOAK_CLIENT_ID,
            "client_secret": settings.KEYCLOAK_CLIENT_SECRET,
            "grant_type": "password",
            "username": username,
            "password": password
        }
        
        try:
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                return response.json()
            else:
                detail = "Authentication failed"
                try:
                    error_json = response.json()
                    error_description = error_json.get("error_description", "")
                    if error_description:
                        detail = error_description
                except:
                    pass
                    
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=detail,
                    headers={"WWW-Authenticate": "Bearer"}
                )
        except requests.RequestException as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error connecting to authentication server: {str(e)}"
            )
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refrescar un token usando el refresh_token
        """
        url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token"
        
        data = {
            "client_id": settings.KEYCLOAK_CLIENT_ID,
            "client_secret": settings.KEYCLOAK_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        
        try:
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Error refreshing token",
                    headers={"WWW-Authenticate": "Bearer"}
                )
        except requests.RequestException as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error connecting to authentication server: {str(e)}"
            )
    
    def logout(self, refresh_token: str) -> None:
        """
        Cerrar la sesión del usuario invalidando el token
        """
        url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/logout"
        
        data = {
            "client_id": settings.KEYCLOAK_CLIENT_ID,
            "client_secret": settings.KEYCLOAK_CLIENT_SECRET,
            "refresh_token": refresh_token
        }
        
        try:
            response = requests.post(url, data=data)
            
            if response.status_code != 204 and response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error logging out"
                )
        except requests.RequestException as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error connecting to authentication server: {str(e)}"
            )


auth_service = AuthService()
