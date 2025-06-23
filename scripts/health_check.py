#!/usr/bin/env python3
"""
Script para verificar la salud e integridad de la base de datos de Raven API.
Detecta problemas comunes como valores NULL en campos obligatorios,
secuencias desincronizadas, y datos inconsistentes.
"""

import sys
import subprocess
from pathlib import Path

# Agregar el directorio padre al path para poder importar app
sys.path.append(str(Path(__file__).parent.parent))


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


def check_null_values():
    """
    Verifica si hay valores NULL en campos que deberían ser obligatorios
    """
    print("🔍 Verificando valores NULL en campos obligatorios...\n")
    
    checks = [
        ("permits", "workspace_id", "Permits sin workspace_id"),
        ("workspace_histories", "workspace_id", "Historiales sin workspace_id"),
        ("workspace_histories", "user_id", "Historiales sin user_id"),
        ("workspaces", "creator_id", "Workspaces sin creator"),
        ("permits", "status", "Permits sin estado"),
    ]
    
    issues_found = 0
    
    for table, column, description in checks:
        result = run_sql_command(f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL;")
        if result:
            try:
                lines = result.strip().split('\n')
                count_line = [line for line in lines if line.strip() and not line.startswith('-') and not line.startswith('count')][0]
                count = int(count_line.strip())
                
                if count > 0:
                    print(f"  ❌ {description}: {count} registros")
                    issues_found += 1
                else:
                    print(f"  ✅ {description}: OK")
            except (IndexError, ValueError):
                print(f"  ❓ {description}: Error verificando")
    
    return issues_found


def check_sequence_sync():
    """
    Verifica si las secuencias están sincronizadas con los datos
    """
    print("\n🔄 Verificando sincronización de secuencias...\n")
    
    tables = ["workspaces", "permits", "workspace_histories", "users", "teams"]
    issues_found = 0
    
    for table in tables:
        # Obtener el máximo ID actual
        max_id_result = run_sql_command(f"SELECT MAX(id) FROM {table};")
        # Obtener el valor actual de la secuencia
        seq_result = run_sql_command(f"SELECT last_value FROM {table}_id_seq;")
        
        if max_id_result and seq_result:
            try:
                max_id_lines = max_id_result.strip().split('\n')
                max_id_line = [line for line in max_id_lines if line.strip() and not line.startswith('-') and not line.startswith('max')][0]
                max_id = int(max_id_line.strip()) if max_id_line.strip() != '' else 0
                
                seq_lines = seq_result.strip().split('\n')
                seq_line = [line for line in seq_lines if line.strip() and not line.startswith('-') and not line.startswith('last_value')][0]
                seq_value = int(seq_line.strip())
                
                if max_id > seq_value:
                    print(f"  ❌ {table}: MAX(id)={max_id}, secuencia={seq_value} (desincronizada)")
                    issues_found += 1
                else:
                    print(f"  ✅ {table}: MAX(id)={max_id}, secuencia={seq_value} (OK)")
                    
            except (IndexError, ValueError) as e:
                print(f"  ❓ {table}: Error verificando secuencia - {e}")
        else:
            print(f"  ❓ {table}: No se pudo verificar")
    
    return issues_found


def check_foreign_keys():
    """
    Verifica la integridad de las claves foráneas
    """
    print("\n🔗 Verificando integridad de claves foráneas...\n")
    
    checks = [
        ("permits", "workspace_id", "workspaces", "id", "Permits con workspace_id inválido"),
        ("workspace_histories", "workspace_id", "workspaces", "id", "Historiales con workspace_id inválido"),
        ("workspace_histories", "user_id", "users", "id", "Historiales con user_id inválido"),
        ("workspaces", "creator_id", "users", "id", "Workspaces con creator_id inválido"),
    ]
    
    issues_found = 0
    
    for table, fk_column, ref_table, ref_column, description in checks:
        query = f"""
        SELECT COUNT(*) FROM {table} t1 
        LEFT JOIN {ref_table} t2 ON t1.{fk_column} = t2.{ref_column} 
        WHERE t1.{fk_column} IS NOT NULL AND t2.{ref_column} IS NULL;
        """
        result = run_sql_command(query)
        
        if result:
            try:
                lines = result.strip().split('\n')
                count_line = [line for line in lines if line.strip() and not line.startswith('-') and not line.startswith('count')][0]
                count = int(count_line.strip())
                
                if count > 0:
                    print(f"  ❌ {description}: {count} registros")
                    issues_found += 1
                else:
                    print(f"  ✅ {description}: OK")
            except (IndexError, ValueError):
                print(f"  ❓ {description}: Error verificando")
    
    return issues_found


def main():
    """
    Función principal que ejecuta todas las verificaciones
    """
    print("🏥 Verificación de salud de la base de datos Raven API\n")
    print("=" * 60)
    
    total_issues = 0
    
    # Ejecutar verificaciones
    total_issues += check_null_values()
    total_issues += check_sequence_sync()
    total_issues += check_foreign_keys()
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 Resumen de la verificación:")
    
    if total_issues == 0:
        print("✅ ¡La base de datos está en perfecto estado!")
        print("   No se encontraron problemas de integridad.")
        return 0
    else:
        print(f"⚠️  Se encontraron {total_issues} problemas en la base de datos.")
        print("   Revisa los detalles arriba y considera ejecutar:")
        print("   - scripts/reset_sequences.py (para problemas de secuencias)")
        print("   - Limpieza manual de datos inconsistentes")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
