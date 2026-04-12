"""
Migration script to add created_at column to campuses table.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Check if column exists
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('campuses')]
        
        if 'created_at' in columns:
            print("✓ La columna 'created_at' ya existe en la tabla 'campuses'.")
        else:
            print("Agregando columna 'created_at' a la tabla 'campuses'...")
            with db.engine.connect() as conn:
                # SQLite requires NULL default for ALTER TABLE, will be populated by model default
                conn.execute(text("ALTER TABLE campuses ADD COLUMN created_at DATETIME"))
                conn.commit()
            print("✓ Columna 'created_at' agregada exitosamente.")
        
        print("\nMigración completada.")
    except Exception as e:
        print(f"\nError durante la migración: {str(e)}")
        import traceback
        traceback.print_exc()
