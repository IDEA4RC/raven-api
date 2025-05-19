#!/usr/bin/env python
"""
Script para crear un usuario de prueba en la base de datos.
"""

import os
import sys

# Añadir el directorio raíz del proyecto al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.models.user import User
from app.models.user_type import UserType

# Crear una sesión de base de datos
db = SessionLocal()

try:
    # Verificar si existe un tipo de usuario con permisos de administrador
    admin_type = db.query(UserType).first()
    
    # Si no existe, lo creamos
    if not admin_type:
        admin_type = UserType(
            description='Administrador del sistema',
            metadata_search=3,  # Crear
            permissions=1,      # Sí
            cohort_builder=1,   # Sí
            data_quality=2,     # Exportar
            export=4,           # Exportar
            results_report=2    # Editar
        )
        db.add(admin_type)
        db.commit()
        db.refresh(admin_type)
        print(f"Tipo de usuario administrador creado con ID: {admin_type.id}")
    else:
        print(f"Tipo de usuario administrador ya existe con ID: {admin_type.id}")
    
    # Verificar si ya existe un usuario de prueba
    test_user = db.query(User).filter(User.email=='test@example.com').first()
    
    # Si no existe, lo creamos
    if not test_user:
        test_user = User(
            email='test@example.com',
            username='test_user',
            first_name='Usuario',
            last_name='de Prueba',
            is_active=True,
            user_type_id=admin_type.id,
            keycloak_id='test-user-id'
        )
        db.add(test_user)
        db.commit()
        print(f"Usuario de prueba creado con ID: {test_user.id}")
    else:
        print(f"Usuario de prueba ya existe con ID: {test_user.id}")

except Exception as e:
    print(f"Error: {e}")
    db.rollback()

finally:
    # Cerrar la sesión
    db.close()
