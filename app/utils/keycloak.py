"""
Utilidades para la integración con Keycloak
"""

import json
import logging
from typing import Dict, Optional, Any, List

import requests
from fastapi import HTTPException, status

from app.config.settings import settings


logger = logging.getLogger(__name__)


class KeycloakHandler:
    """
    Clase para manejar operaciones con Keycloak
    """
    
    def __init__(self):
        """Inicializar el manejador de Keycloak"""
        self.server_url = settings.KEYCLOAK_SERVER_URL
        self.realm_name = settings.KEYCLOAK_REALM
        self.client_id = settings.KEYCLOAK_CLIENT_ID
        self.client_secret = settings.KEYCLOAK_CLIENT_SECRET
        self.admin_username = settings.KEYCLOAK_ADMIN_USERNAME
        self.admin_password = settings.KEYCLOAK_ADMIN_PASSWORD
        self.admin_token = None
        
    def _get_admin_token(self) -> Optional[str]:
        """
        Obtiene un token de administrador para realizar operaciones en Keycloak
        """
        url = f"{self.server_url}/realms/master/protocol/openid-connect/token"
        data = {
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": self.admin_username,
            "password": self.admin_password
        }
        
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.admin_token = token_data.get("access_token")
            return self.admin_token
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al obtener el token de administrador: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de un usuario por su ID
        """
        if not self.admin_token:
            self._get_admin_token()
            
        url = f"{self.server_url}/admin/realms/{self.realm_name}/users/{user_id}"
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al obtener usuario por ID: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[List[Dict[str, Any]]]:
        """
        Busca un usuario por email
        """
        if not self.admin_token:
            self._get_admin_token()
            
        url = f"{self.server_url}/admin/realms/{self.realm_name}/users"
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        params = {"email": email, "exact": "true"}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al obtener usuario por email: {e}")
            return None
    
    def create_user(
        self, 
        username: str, 
        email: str, 
        password: str, 
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        enabled: bool = True
    ) -> Optional[str]:
        """
        Crea un usuario en Keycloak
        """
        if not self.admin_token:
            self._get_admin_token()
            
        url = f"{self.server_url}/admin/realms/{self.realm_name}/users"
        headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "username": username,
            "email": email,
            "enabled": enabled,
            "credentials": [
                {
                    "type": "password",
                    "value": password,
                    "temporary": False
                }
            ]
        }
        
        if first_name:
            payload["firstName"] = first_name
            
        if last_name:
            payload["lastName"] = last_name
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            # Keycloak devuelve el ID en la ubicación de la respuesta
            location = response.headers.get("Location")
            if location:
                user_id = location.split("/")[-1]
                return user_id
            
            # Si no podemos extraer la ID, busquemos al usuario por correo electrónico
            users = self.get_user_by_email(email)
            if users and len(users) > 0:
                return users[0].get("id")
                
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al crear usuario: {e}")
            return None
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Valida un token y devuelve la información del usuario
        """
        url = f"{self.server_url}/realms/{self.realm_name}/protocol/openid-connect/userinfo"
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al validar token: {e}")
            return None


keycloak_handler = KeycloakHandler()