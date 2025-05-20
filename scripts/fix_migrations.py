#!/usr/bin/env python
"""
Script de recuperación para garantizar que todas las migraciones de Alembic
se apliquen correctamente.

Este script verifica la estructura de la base de datos y establece el estado correcto
para las migraciones de Alembic.
"""

import os
import sys
import sqlite3
import logging
from typing import List, Optional, Tuple
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text, MetaData, Table, Column, String

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Añadir la ruta del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.settings import settings
from app.db.session import engine, SessionLocal
from app.models import Base

def get_alembic_heads() -> List[str]:
    """Obtener las revisiones finales (heads) de Alembic"""
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    return script.get_heads()

def get_current_revision() -> Optional[str]:
    """Obtener la revisión actual en la base de datos"""
    try:
        conn = engine.connect()
        context = MigrationContext.configure(conn)
        current_rev = context.get_current_revision()
        conn.close()
        return current_rev
    except Exception as e:
        logger.error(f"Error al obtener la revisión actual: {e}")
        return None

def check_alembic_version_table() -> bool:
    """Comprobar si existe la tabla alembic_version"""
    try:
        inspector = inspect(engine)
        return 'alembic_version' in inspector.get_table_names()
    except Exception as e:
        logger.error(f"Error al verificar la tabla alembic_version: {e}")
        return False

def create_alembic_version_table() -> bool:
    """Crear la tabla alembic_version si no existe"""
    try:
        metadata = MetaData()
        Table('alembic_version', metadata,
              Column('version_num', String(32), primary_key=True))
        metadata.create_all(engine)
        return True
    except Exception as e:
        logger.error(f"Error al crear la tabla alembic_version: {e}")
        return False

def set_alembic_version(revision: str) -> bool:
    """Establecer la versión actual de Alembic en la base de datos"""
    try:
        conn = engine.connect()
        conn.execute(text(f"DELETE FROM alembic_version"))
        conn.execute(text(f"INSERT INTO alembic_version (version_num) VALUES ('{revision}')"))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error al establecer la versión de Alembic: {e}")
        return False

def check_user_table_columns() -> List[str]:
    """Verificar las columnas existentes en la tabla users"""
    inspector = inspect(engine)
    if 'users' in inspector.get_table_names():
        return [col['name'] for col in inspector.get_columns('users')]
    return []

def main():
    """Función principal"""
    logger.info("Iniciando verificación y recuperación de migraciones...")
    
    # Comprobar la tabla users y sus columnas
    user_columns = check_user_table_columns()
    logger.info(f"Columnas actuales en la tabla users: {user_columns}")
    
    keycloak_id_exists = 'keycloak_id' in user_columns
    logger.info(f"Columna keycloak_id existe: {keycloak_id_exists}")
    
    # Verificar tabla alembic_version
    alembic_table_exists = check_alembic_version_table()
    logger.info(f"Tabla alembic_version existe: {alembic_table_exists}")
    
    # Obtener la revisión actual
    current_rev = get_current_revision()
    logger.info(f"Revisión actual: {current_rev}")
    
    # Obtener la última revisión disponible
    heads = get_alembic_heads()
    latest_head = heads[0] if heads else None
    logger.info(f"Revisión más reciente disponible: {latest_head}")
    
    # Si no existe la tabla alembic_version, crearla
    if not alembic_table_exists:
        logger.info("Creando tabla alembic_version...")
        create_alembic_version_table()
    
    # Determinar qué revisión establecer basado en el estado de la base de datos
    target_revision = None
    
    if not user_columns:
        # La tabla users no existe - necesitamos aplicar todas las migraciones
        logger.info("La tabla users no existe - se aplicarán todas las migraciones")
        target_revision = None  # Aplicar todas las migraciones
    elif keycloak_id_exists:
        # La columna keycloak_id ya existe - establecer a la última revisión
        logger.info("La columna keycloak_id ya existe - estableciendo a la última revisión")
        target_revision = latest_head
    else:
        # La tabla users existe pero sin keycloak_id - establecer a la revisión anterior a add_keycloak_id
        logger.info("La tabla users existe pero sin keycloak_id - aplicando migraciones pendientes")
        target_revision = None  # Aplicar migraciones pendientes
    
    # Si se determina una revisión objetivo, establecerla
    if target_revision:
        logger.info(f"Estableciendo revisión Alembic a: {target_revision}")
        if set_alembic_version(target_revision):
            logger.info(f"Revisión establecida correctamente a {target_revision}")
        else:
            logger.error("Error al establecer la revisión")
    else:
        logger.info("Se aplicarán todas las migraciones pendientes")
    
    logger.info("Verificación y recuperación de migraciones completada")

if __name__ == "__main__":
    main()
