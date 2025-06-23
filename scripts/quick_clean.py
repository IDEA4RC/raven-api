#!/usr/bin/env python3
"""
Script rápido para vaciar la base de datos manteniendo la estructura
"""

import sys
import psycopg2
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.settings import settings


def parse_database_url(db_url):
    """Parsea la URL de la base de datos"""
    if "postgresql://" in db_url:
        parts = db_url.replace("postgresql://", "").split("/")
        db_name = parts[1] if len(parts) > 1 else "raven_db"
        user_host = parts[0].split("@")
        user_pass = user_host[0].split(":")
        host_port = user_host[1].split(":") if len(user_host) > 1 else ["localhost", "5432"]
        
        return {
            'host': host_port[0],
            'port': int(host_port[1]) if len(host_port) > 1 else 5432,
            'database': db_name,
            'user': user_pass[0],
            'password': user_pass[1] if len(user_pass) > 1 else ""
        }
    else:
        raise ValueError("Solo se soporta PostgreSQL")


def truncate_all_tables():
    """Vacía todas las tablas de la base de datos"""
    db_config = parse_database_url(settings.DATABASE_URI)
    
    print("🧹 Vaciando todas las tablas de la base de datos...")
    print(f"🔗 Conectando a: {db_config['host']}:{db_config['port']}/{db_config['database']}")
    
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Obtener todas las tablas excepto alembic_version
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename != 'alembic_version'
            ORDER BY tablename
        """)
        tables = cursor.fetchall()
        
        if not tables:
            print("ℹ️ No se encontraron tablas para limpiar")
            return
        
        print(f"📋 Encontradas {len(tables)} tablas:")
        for table in tables:
            print(f"  - {table[0]}")
        
        print("\n🔄 Limpiando tablas...")
        
        # Deshabilitar restricciones de clave foránea temporalmente
        cursor.execute("SET session_replication_role = replica;")
        
        # Truncar todas las tablas
        for table in tables:
            table_name = table[0]
            print(f"  🧹 Limpiando: {table_name}")
            cursor.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;")
        
        # Rehabilitar restricciones de clave foránea
        cursor.execute("SET session_replication_role = DEFAULT;")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Base de datos limpiada correctamente")
        print("ℹ️ La estructura de las tablas se ha mantenido")
        
    except Exception as e:
        print(f"❌ Error limpiando base de datos: {e}")
        sys.exit(1)


def show_table_counts():
    """Muestra el conteo de registros en cada tabla"""
    db_config = parse_database_url(settings.DATABASE_URI)
    
    print("📊 Conteo de registros por tabla:")
    print("=================================")
    
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Obtener todas las tablas
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            ORDER BY tablename
        """)
        tables = cursor.fetchall()
        
        total_records = 0
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            total_records += count
            print(f"  {table_name:<20}: {count:>6} registros")
        
        print(f"\n📈 Total de registros: {total_records}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error obteniendo conteos: {e}")
        sys.exit(1)


def main():
    """Función principal"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "count":
            show_table_counts()
        elif command == "clean":
            # Mostrar estado actual
            show_table_counts()
            print()
            
            # Confirmar limpieza
            response = input("⚠️ ¿Estás seguro de que quieres vaciar TODAS las tablas? (escribe 'SI'): ")
            if response == "SI":
                truncate_all_tables()
                print()
                show_table_counts()
            else:
                print("❌ Operación cancelada")
        else:
            print("❌ Comando no reconocido")
            print("Uso: python scripts/quick_clean.py [count|clean]")
    else:
        print("🔧 Script de limpieza rápida de base de datos")
        print("===========================================")
        print()
        print("Comandos disponibles:")
        print("  count - Mostrar conteo de registros por tabla")
        print("  clean - Vaciar todas las tablas (mantiene estructura)")
        print()
        print("Uso:")
        print("  python scripts/quick_clean.py count")
        print("  python scripts/quick_clean.py clean")


if __name__ == "__main__":
    main()
