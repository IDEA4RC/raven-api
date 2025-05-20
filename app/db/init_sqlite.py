#!/usr/bin/env python
"""
Script de inicialización para RAVEN API.
Este script se ejecuta durante el arranque del contenedor para asegurar
que la base de datos está correctamente configurada.
"""

import os
import sys
import sqlite3
import traceback

def init_database():
    """
    Inicializa la base de datos, asegurando que tiene la estructura correcta.
    """
    # Obtener ruta de la base de datos (en entorno de producción está en /app/raven.db)
    db_path = "/app/raven.db"
    print(f"Base de datos: {db_path}")
    
    # Si no existe la base de datos, no podemos hacer nada
    if not os.path.exists(db_path):
        print(f"La base de datos {db_path} no existe. Se creará cuando arranque la aplicación.")
        return
    
    # Conectar a la base de datos
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Verificar si la tabla users existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("La tabla users no existe.")
            return
            
        # Verificar si las columnas existen
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Añadir columnas si no existen
        if 'keycloak_id' not in columns:
            print("Añadiendo columna keycloak_id...")
            cursor.execute("ALTER TABLE users ADD COLUMN keycloak_id VARCHAR")
            
            # Actualizar los usuarios existentes con keycloak_id simulados
            print("Actualizando usuarios existentes con valores keycloak_id predeterminados...")
            cursor.execute("SELECT id FROM users")
            user_ids = cursor.fetchall()
            
            for user_id in user_ids:
                keycloak_id = f"keycloak-id-{user_id[0]}"
                cursor.execute("UPDATE users SET keycloak_id = ? WHERE id = ?", (keycloak_id, user_id[0]))
        
        if 'first_name' not in columns:
            print("Añadiendo columna first_name...")
            cursor.execute("ALTER TABLE users ADD COLUMN first_name VARCHAR")
        
        if 'last_name' not in columns:
            print("Añadiendo columna last_name...")
            cursor.execute("ALTER TABLE users ADD COLUMN last_name VARCHAR")
        
        if 'is_active' not in columns:
            print("Añadiendo columna is_active...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1")
        
        print("Estructura de tabla users actualizada correctamente.")
        
        # Verificar si la tabla permits existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='permits'")
        if cursor.fetchone():
            # Verificar si las columnas workspace_id y update_date existen
            cursor.execute("PRAGMA table_info(permits)")
            permit_columns = [column[1] for column in cursor.fetchall()]
            
            # Añadir columnas si no existen
            if 'workspace_id' not in permit_columns:
                print("Añadiendo columna workspace_id a la tabla permits...")
                cursor.execute("ALTER TABLE permits ADD COLUMN workspace_id INTEGER REFERENCES workspaces(id)")
            
            if 'update_date' not in permit_columns:
                print("Añadiendo columna update_date a la tabla permits...")
                cursor.execute("ALTER TABLE permits ADD COLUMN update_date TIMESTAMP")
            
            print("Estructura de tabla permits actualizada correctamente.")
            
            # Crear índices para mejorar el rendimiento
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_permits_workspace_id ON permits(workspace_id)")
        
        # Crear índice para keycloak_id si no existe
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_keycloak_id ON users(keycloak_id)")
        
        # Commit de los cambios
        conn.commit()
        print("Base de datos actualizada correctamente.")
        
    except Exception as e:
        print(f"Error al actualizar la base de datos: {e}")
        print(traceback.format_exc())
        conn.rollback()
    finally:
        # Cerrar la conexión
        conn.close()

if __name__ == "__main__":
    init_database()
