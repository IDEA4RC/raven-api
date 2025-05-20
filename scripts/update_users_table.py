#!/usr/bin/env python
"""
Script para actualizar la estructura de la tabla users en la base de datos.
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
    # Verificar si la tabla users existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        print("La tabla users no existe.")
    else:
        # Verificar si las columnas existen
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Añadir columnas si no existen
        if 'keycloak_id' not in columns:
            print("Añadiendo columna keycloak_id...")
            cursor.execute("ALTER TABLE users ADD COLUMN keycloak_id VARCHAR UNIQUE")
            
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
            cursor.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
        
        print("Estructura de tabla users actualizada correctamente.")
    
    # Crear índice para keycloak_id si no existe
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_keycloak_id ON users(keycloak_id)")
    print("Índice para keycloak_id creado correctamente.")
    
    # Commit de los cambios
    conn.commit()
    print("Base de datos actualizada correctamente.")
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    # Cerrar la conexión
    conn.close()
