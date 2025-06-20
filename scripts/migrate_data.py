#!/usr/bin/env python3
"""
Script to migrate data from SQLite to PostgreSQL
"""

import os
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

def migrate_data():
    """Migrates data from SQLite to PostgreSQL"""
    
    # Database configuration
    sqlite_db = "/home/aalonso/LST/IDEA4RC/raven-api/raven.db"
    pg_config = {
        'host': 'localhost',
        'database': 'raven_db',
        'user': 'raven_user',
        'password': 'raven_password',
        'port': 5432
    }
    
    if not os.path.exists(sqlite_db):
        print(f"SQLite database not found: {sqlite_db}")
        print("Skipping data migration...")
        return
    
    try:
        # Conectar a SQLite
        sqlite_conn = sqlite3.connect(sqlite_db)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Conectar a PostgreSQL
        pg_conn = psycopg2.connect(**pg_config)
        pg_cursor = pg_conn.cursor()
        
        print("Connected to both databases.")
        
        # Get list of SQLite tables in dependency order
        table_order = [
            'organizations',
            'user_types', 
            'teams',
            'users',
            'user_teams',
            'workspaces',
            'workspace_histories',
            'permits',
            'algorithms',
            'cohorts',
            'analyses',
            'metadata_searches',
            'cohort_algorithms',
            'cohort_results'
        ]
        
        # Get all available tables
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        available_tables = [row[0] for row in sqlite_cursor.fetchall() if row[0] != 'alembic_version']
        
        # Filter only existing tables
        tables = [table for table in table_order if table in available_tables]
        
        for table in tables:
            print(f"Migrating table: {table}")
            
            # Get data from SQLite
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                print(f"  No data in {table}")
                continue
            
            # Get column names
            sqlite_cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in sqlite_cursor.fetchall()]
            
            # Clean table in PostgreSQL
            pg_cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
            
            # Insert data into PostgreSQL
            if table == 'workspaces':
                # Handle special migration for workspaces (team_id -> team_ids)
                migrated_rows = []
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    # Convertir team_id a team_ids array
                    if 'team_id' in row_dict and row_dict['team_id'] is not None:
                        # Crear nueva fila con team_ids
                        new_row = []
                        for i, col in enumerate(columns):
                            if col == 'team_id':
                                # Saltar team_id
                                continue
                            new_row.append(row[i])
                        # Add team_ids as array
                        new_row.append([str(row_dict['team_id'])])
                        migrated_rows.append(tuple(new_row))
                    else:
                        # No team_id, add empty array
                        new_row = list(row)[:-1] if 'team_id' in columns else list(row)
                        new_row.append([])
                        migrated_rows.append(tuple(new_row))
                
                # Actualizar nombres de columnas para PostgreSQL
                pg_columns = [col for col in columns if col != 'team_id'] + ['team_ids']
                placeholders = ', '.join(['%s'] * len(pg_columns))
                insert_query = f"INSERT INTO {table} ({', '.join(pg_columns)}) VALUES ({placeholders})"
                
                pg_cursor.executemany(insert_query, migrated_rows)
            else:
                # Normal migration for other tables
                migrated_rows = []
                for row in rows:
                    # Convertir valores para compatibilidad PostgreSQL
                    converted_row = []
                    for i, (col, val) in enumerate(zip(columns, row)):
                        # Convertir booleanos para PostgreSQL
                        if table == 'users' and col == 'is_active':
                            converted_row.append(bool(val) if val is not None else None)
                        else:
                            converted_row.append(val)
                    migrated_rows.append(tuple(converted_row))
                
                placeholders = ', '.join(['%s'] * len(columns))
                insert_query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
                pg_cursor.executemany(insert_query, migrated_rows)
            
            print(f"  Migrados {len(rows)} registros")
        
        # Confirmar cambios
        pg_conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        if 'pg_conn' in locals():
            pg_conn.rollback()
    finally:
        if 'sqlite_conn' in locals():
            sqlite_conn.close()
        if 'pg_conn' in locals():
            pg_conn.close()

if __name__ == "__main__":
    migrate_data()
