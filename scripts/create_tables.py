#!/usr/bin/env python3
"""
Script para crear las tablas de PostgreSQL directamente
"""

import os
import sys

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from app.models.base import Base
from app.config.settings import settings

# Importar todos los modelos para que se registren
from app.models.organization import Organization
from app.models.user_type import UserType
from app.models.user import User
from app.models.team import Team
from app.models.user_team import UserTeam
from app.models.workspace import Workspace
from app.models.workspace_history import WorkspaceHistory
from app.models.permit import Permit
from app.models.algorithm import Algorithm
from app.models.analysis import Analysis
from app.models.cohort import Cohort
from app.models.cohort_algorithm import CohortAlgorithm
from app.models.cohort_result import CohortResult
from app.models.metadata_search import MetadataSearch

def create_tables():
    """Crear todas las tablas en PostgreSQL"""
    print("🔨 Creando tablas en PostgreSQL...")
    
    # Usar la configuración de PostgreSQL
    database_uri = "postgresql://raven_user:raven_password@localhost:5432/raven_db"
    
    try:
        engine = create_engine(database_uri, pool_pre_ping=True)
        
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        
        print("✅ Tablas creadas exitosamente en PostgreSQL")
        
        # Verificar las tablas creadas
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"📋 Tablas creadas ({len(tables)}):")
        for table in sorted(tables):
            print(f"   - {table}")
            
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = create_tables()
    sys.exit(0 if success else 1)
