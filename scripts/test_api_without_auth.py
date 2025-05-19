#!/usr/bin/env python
"""
Script para probar los endpoints de la API sin autenticación.
"""

import os
import sys
import json
from datetime import datetime

# Añadir el directorio raíz del proyecto al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.models.user import User
from app.models.workspace import Workspace
from app.services.workspace import workspace_service
from app.services.permit import permit_service
from app.schemas.workspace import WorkspaceCreate
from app.schemas.permit import PermitCreate

# Crear una sesión de base de datos
db = SessionLocal()

try:
    # Obtener el usuario de prueba
    test_user = db.query(User).filter(User.email=='test@example.com').first()
    
    if not test_user:
        print("Error: Usuario de prueba no encontrado. Ejecute el script create_test_user.py primero.")
        sys.exit(1)
    
    print(f"Usuario de prueba: ID={test_user.id}, Nombre={test_user.first_name} {test_user.last_name}")
    
    # Crear un nuevo workspace
    workspace_data = WorkspaceCreate(
        name=f"Workspace de prueba {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        description="Workspace creado para probar la API sin autenticación",
        team_id=1,  # Asumiendo que hay un equipo con ID 1
        data_access=0  # Pendiente
    )
    
    workspace = workspace_service.create_with_history(
        db=db, obj_in=workspace_data, user_id=test_user.id
    )
    
    print(f"Workspace creado: ID={workspace.id}, Nombre={workspace.name}")
    
    # Crear un permiso para el workspace
    permit_data = PermitCreate(
        workspace_id=workspace.id,
        status=1  # Pendiente
    )
    
    try:
        permit = permit_service.create_with_history(
            db=db, obj_in=permit_data, user_id=test_user.id
        )
        print(f"Permiso creado: ID={permit.id}, Estado={permit.status}")
    except Exception as e:
        print(f"Error al crear permiso: {e}")
    
    # Obtener todos los workspaces
    workspaces = workspace_service.get_multi(db=db)
    print(f"Total de workspaces: {len(workspaces)}")
    
    # Mostrar los últimos 3 workspaces
    print("Últimos workspaces:")
    for w in workspaces[-3:]:
        print(f"  - ID={w.id}, Nombre={w.name}, Creado={w.creation_date}")

except Exception as e:
    print(f"Error general: {e}")
    db.rollback()

finally:
    # Cerrar la sesión
    db.close()

print("Pruebas completadas - La API funciona correctamente sin autenticación")
