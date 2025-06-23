#!/usr/bin/env python3
"""
Script completo para gestión de migraciones y base de datos de RAVEN API
Permite ejecutar migraciones, limpiar la base de datos, y hacer backup/restore
"""

import os
import sys
import argparse
import subprocess
import psycopg2
from datetime import datetime
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.settings import settings


class DatabaseManager:
    """Gestor de base de datos para RAVEN API"""
    
    def __init__(self):
        self.db_url = settings.DATABASE_URI
        self.parse_db_url()
    
    def parse_db_url(self):
        """Parsea la URL de la base de datos"""
        # Ejemplo: postgresql://user:password@host:port/database
        if "postgresql://" in self.db_url:
            parts = self.db_url.replace("postgresql://", "").split("/")
            db_name = parts[1] if len(parts) > 1 else "raven_db"
            user_host = parts[0].split("@")
            user_pass = user_host[0].split(":")
            host_port = user_host[1].split(":") if len(user_host) > 1 else ["localhost", "5432"]
            
            self.db_config = {
                'host': host_port[0],
                'port': int(host_port[1]) if len(host_port) > 1 else 5432,
                'database': db_name,
                'user': user_pass[0],
                'password': user_pass[1] if len(user_pass) > 1 else ""
            }
        else:
            raise ValueError("Solo se soporta PostgreSQL")
    
    def run_migrations(self, direction="upgrade"):
        """Ejecuta las migraciones de Alembic"""
        print(f"🔄 Ejecutando migraciones ({direction})...")
        
        try:
            if direction == "upgrade":
                # Migrar a la última versión
                result = subprocess.run(["alembic", "upgrade", "head"], 
                                      capture_output=True, text=True)
            elif direction == "downgrade":
                # Volver a la versión anterior
                result = subprocess.run(["alembic", "downgrade", "-1"], 
                                      capture_output=True, text=True)
            else:
                raise ValueError("direction debe ser 'upgrade' o 'downgrade'")
            
            if result.returncode == 0:
                print("✅ Migraciones ejecutadas correctamente")
                print(result.stdout)
            else:
                print("❌ Error en las migraciones:")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Error ejecutando migraciones: {e}")
            return False
        
        return True
    
    def get_migration_status(self):
        """Obtiene el estado actual de las migraciones"""
        print("📊 Estado de las migraciones:")
        
        try:
            result = subprocess.run(["alembic", "current"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("Estado actual:")
                print(result.stdout)
            else:
                print("❌ Error obteniendo estado:")
                print(result.stderr)
                
            # Mostrar historial
            result = subprocess.run(["alembic", "history"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("\nHistorial de migraciones:")
                print(result.stdout)
                
        except Exception as e:
            print(f"❌ Error obteniendo estado: {e}")
    
    def create_migration(self, message):
        """Crea una nueva migración"""
        print(f"📝 Creando nueva migración: {message}")
        
        try:
            result = subprocess.run(["alembic", "revision", "--autogenerate", "-m", message], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Migración creada correctamente")
                print(result.stdout)
            else:
                print("❌ Error creando migración:")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Error creando migración: {e}")
            return False
        
        return True
    
    def clean_database(self, confirm=False):
        """Limpia completamente la base de datos"""
        if not confirm:
            response = input("⚠️ ¿Estás seguro de que quieres limpiar TODA la base de datos? (escribe 'CONFIRMAR'): ")
            if response != "CONFIRMAR":
                print("❌ Operación cancelada")
                return False
        
        print("🧹 Limpiando base de datos...")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Obtener todas las tablas
            cursor.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' AND tablename != 'alembic_version'
            """)
            tables = cursor.fetchall()
            
            # Deshabilitar restricciones de clave foránea temporalmente
            cursor.execute("SET session_replication_role = replica;")
            
            # Truncar todas las tablas
            for table in tables:
                table_name = table[0]
                print(f"  Limpiando tabla: {table_name}")
                cursor.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;")
            
            # Rehabilitar restricciones de clave foránea
            cursor.execute("SET session_replication_role = DEFAULT;")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print("✅ Base de datos limpiada correctamente")
            return True
            
        except Exception as e:
            print(f"❌ Error limpiando base de datos: {e}")
            return False
    
    def reset_database(self, confirm=False):
        """Resetea completamente la base de datos (drop + create + migrate)"""
        if not confirm:
            response = input("⚠️ ¿Estás seguro de que quieres RESETEAR completamente la base de datos? (escribe 'RESETEAR'): ")
            if response != "RESETEAR":
                print("❌ Operación cancelada")
                return False
        
        print("🔄 Reseteando base de datos...")
        
        # 1. Eliminar todas las tablas
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Eliminar todas las tablas incluyendo alembic_version
            cursor.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
            cursor.execute("GRANT ALL ON SCHEMA public TO public;")
            cursor.execute("GRANT ALL ON SCHEMA public TO " + self.db_config['user'] + ";")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print("✅ Esquema de base de datos eliminado")
            
        except Exception as e:
            print(f"❌ Error eliminando esquema: {e}")
            return False
        
        # 2. Ejecutar migraciones desde cero
        return self.run_migrations("upgrade")
    
    def backup_database(self, backup_file=None):
        """Crea un backup de la base de datos"""
        if not backup_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"backup_raven_db_{timestamp}.sql"
        
        print(f"💾 Creando backup: {backup_file}")
        
        try:
            # Usar pg_dump para crear el backup
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config['password']
            
            cmd = [
                "pg_dump",
                "-h", self.db_config['host'],
                "-p", str(self.db_config['port']),
                "-U", self.db_config['user'],
                "-d", self.db_config['database'],
                "--no-password",
                "-f", backup_file
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Backup creado: {backup_file}")
                return backup_file
            else:
                print("❌ Error creando backup:")
                print(result.stderr)
                return None
                
        except Exception as e:
            print(f"❌ Error creando backup: {e}")
            return None
    
    def restore_database(self, backup_file, confirm=False):
        """Restaura la base de datos desde un backup"""
        if not os.path.exists(backup_file):
            print(f"❌ Archivo de backup no encontrado: {backup_file}")
            return False
        
        if not confirm:
            response = input(f"⚠️ ¿Estás seguro de que quieres restaurar desde {backup_file}? (escribe 'RESTAURAR'): ")
            if response != "RESTAURAR":
                print("❌ Operación cancelada")
                return False
        
        print(f"📥 Restaurando desde: {backup_file}")
        
        # Primero limpiar la base de datos
        if not self.reset_database(confirm=True):
            return False
        
        try:
            # Usar psql para restaurar
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config['password']
            
            cmd = [
                "psql",
                "-h", self.db_config['host'],
                "-p", str(self.db_config['port']),
                "-U", self.db_config['user'],
                "-d", self.db_config['database'],
                "-f", backup_file
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Base de datos restaurada correctamente")
                return True
            else:
                print("❌ Error restaurando base de datos:")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Error restaurando base de datos: {e}")
            return False


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Gestor de base de datos RAVEN API")
    parser.add_argument("command", choices=[
        "migrate", "rollback", "status", "create", "clean", "reset", "backup", "restore"
    ], help="Comando a ejecutar")
    parser.add_argument("--message", "-m", help="Mensaje para nueva migración")
    parser.add_argument("--file", "-f", help="Archivo de backup para restaurar")
    parser.add_argument("--confirm", "-y", action="store_true", help="Confirmar operaciones peligrosas")
    
    args = parser.parse_args()
    
    db_manager = DatabaseManager()
    
    if args.command == "migrate":
        db_manager.run_migrations("upgrade")
    
    elif args.command == "rollback":
        db_manager.run_migrations("downgrade")
    
    elif args.command == "status":
        db_manager.get_migration_status()
    
    elif args.command == "create":
        if not args.message:
            print("❌ Se requiere un mensaje para la migración (--message)")
            return
        db_manager.create_migration(args.message)
    
    elif args.command == "clean":
        db_manager.clean_database(args.confirm)
    
    elif args.command == "reset":
        db_manager.reset_database(args.confirm)
    
    elif args.command == "backup":
        backup_file = db_manager.backup_database(args.file)
        if backup_file:
            print(f"📂 Backup guardado en: {os.path.abspath(backup_file)}")
    
    elif args.command == "restore":
        if not args.file:
            print("❌ Se requiere un archivo de backup (--file)")
            return
        db_manager.restore_database(args.file, args.confirm)


if __name__ == "__main__":
    main()
