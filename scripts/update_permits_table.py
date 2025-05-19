#!/usr/bin/env python
"""
Script para actualizar la estructura de la tabla permits en la base de datos.
"""

import os
import sys
import sqlite3

# Obtener ruta de la base de datos
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "raven.db")
print(f"Base de datos: {db_path}")

# Conectar a la base de datos
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Verificar si la tabla permits existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='permits'")
    if not cursor.fetchone():
        print("La tabla permits no existe. Creando tabla...")
        cursor.execute("""
        CREATE TABLE permits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            permit_name VARCHAR,
            creation_date TIMESTAMP,
            validity_date TIMESTAMP,
            team_id INTEGER,
            status INTEGER,
            workspace_id INTEGER,
            update_date TIMESTAMP,
            FOREIGN KEY(team_id) REFERENCES teams(id),
            FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
        )
        """)
        print("Tabla permits creada correctamente.")
    else:
        # Verificar si las columnas workspace_id y update_date existen
        cursor.execute("PRAGMA table_info(permits)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Añadir columnas si no existen
        if 'workspace_id' not in columns:
            print("Añadiendo columna workspace_id...")
            cursor.execute("ALTER TABLE permits ADD COLUMN workspace_id INTEGER REFERENCES workspaces(id)")
        
        if 'update_date' not in columns:
            print("Añadiendo columna update_date...")
            cursor.execute("ALTER TABLE permits ADD COLUMN update_date TIMESTAMP")
        
        print("Estructura de tabla permits actualizada correctamente.")
    
    # Crear índices para mejorar el rendimiento
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_permits_workspace_id ON permits(workspace_id)")
    print("Índices creados correctamente.")
    
    # Commit de los cambios
    conn.commit()
    print("Base de datos actualizada correctamente.")

except Exception as e:
    print(f"Error: {e}")
    conn.rollback()

finally:
    # Cerrar la conexión
    conn.close()
