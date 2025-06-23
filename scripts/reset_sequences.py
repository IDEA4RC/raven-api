#!/usr/bin/env python3
"""
Script para resetear las secuencias de PostgreSQL cuando están desincronizadas.
Este script debe ejecutarse cuando se obtienen errores de violación de clave primaria.
"""

import os
import sys
import subprocess
from pathlib import Path

# Agregar el directorio padre al path para poder importar app
sys.path.append(str(Path(__file__).parent.parent))

from app.config.settings import settings


def run_sql_command(sql_command: str) -> str:
    """
    Ejecuta un comando SQL en el contenedor Docker de PostgreSQL
    """
    docker_command = [
        "docker", "exec", "-it", "raven-postgres", 
        "psql", "-U", "raven_user", "-d", "raven_db", "-c", sql_command
    ]
    
    try:
        result = subprocess.run(docker_command, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando comando SQL: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return ""


def reset_sequence(table_name: str, sequence_name: str = None) -> bool:
    """
    Resetea la secuencia de una tabla específica
    """
    if sequence_name is None:
        sequence_name = f"{table_name}_id_seq"
    
    print(f"Reseteando secuencia para tabla '{table_name}'...")
    
    # Obtener el ID máximo actual
    max_id_result = run_sql_command(f"SELECT MAX(id) FROM {table_name};")
    if not max_id_result:
        print(f"Error obteniendo MAX(id) de {table_name}")
        return False
    
    # Extraer el número del resultado
    try:
        lines = max_id_result.strip().split('\n')
        max_id_line = [line for line in lines if line.strip() and not line.startswith('-') and not line.startswith('max')][0]
        max_id = int(max_id_line.strip()) if max_id_line.strip() != '' else 0
    except (IndexError, ValueError) as e:
        print(f"Error procesando resultado MAX(id): {e}")
        max_id = 0
    
    print(f"  ID máximo actual: {max_id}")
    
    # Resetear la secuencia
    reset_result = run_sql_command(f"SELECT setval('{sequence_name}', {max_id});")
    if reset_result:
        print(f"  ✅ Secuencia '{sequence_name}' reseteada correctamente")
        return True
    else:
        print(f"  ❌ Error reseteando secuencia '{sequence_name}'")
        return False


def main():
    """
    Función principal que resetea todas las secuencias importantes
    """
    print("🔄 Iniciando reseteo de secuencias de PostgreSQL...\n")
    
    # Lista de tablas que necesitan reseteo de secuencias
    tables = [
        "workspaces",
        "permits", 
        "workspace_histories",
        "users",
        "teams",
        "user_teams",
        "organizations",
        "user_types"
    ]
    
    success_count = 0
    total_count = len(tables)
    
    for table in tables:
        if reset_sequence(table):
            success_count += 1
        print()  # Línea en blanco entre tablas
    
    print(f"📊 Resumen: {success_count}/{total_count} secuencias reseteadas correctamente")
    
    if success_count == total_count:
        print("✅ Todas las secuencias han sido reseteadas exitosamente")
        return 0
    else:
        print("⚠️ Algunas secuencias no pudieron ser reseteadas")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
