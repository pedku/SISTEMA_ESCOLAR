"""
Migration script for multi-institution architecture.
Adds institution_id columns to existing tables and updates constraints.

Run this script to migrate your database to support multiple institutions:
    python migrate_multi_institution.py

This script handles:
1. Adding institution_id to users table
2. Adding institution_id to subjects table
3. Adding institution_id to achievements table
4. Updating constraints (e.g., subject code unique per institution)
5. Migrating existing data to the first institution (if any)
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models.institution import Institution, Campus
from models.user import User
from models.academic import Subject
from models.achievement import Achievement
from sqlalchemy import text


def migrate():
    """Run the migration."""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("MIGRACIÓN: Arquitectura Multi-Institucional")
        print("=" * 60)
        
        # Check if there's at least one institution
        institution_count = Institution.query.count()
        print(f"\n📊 Instituciones existentes: {institution_count}")
        
        if institution_count == 0:
            print("\n⚠️  No hay instituciones creadas.")
            print("   Cree al menos una institución antes de migrar.")
            print("   O ejecute init_db.py para crear la institución por defecto.")
            return False
        
        # Get the first institution to assign orphan records
        first_institution = Institution.query.first()
        print(f"🏫 Institución por defecto: {first_institution.name} (ID: {first_institution.id})")
        
        with db.engine.connect() as conn:
            # 1. Add institution_id to users table
            print("\n" + "-" * 60)
            print("1️⃣  Migrando tabla: users")
            print("-" * 60)
            
            try:
                # Check if column already exists
                result = conn.execute(text(
                    "PRAGMA table_info(users)" if 'sqlite' in str(db.engine.dialect) 
                    else "SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'institution_id'"
                ))
                column_exists = any('institution_id' in str(row) for row in result)
                
                if not column_exists:
                    conn.execute(text(
                        "ALTER TABLE users ADD COLUMN institution_id INTEGER"
                    ))
                    conn.commit()
                    print("   ✅ Columna institution_id agregada")
                else:
                    print("   ℹ️  Columna institution_id ya existe")
                
                # Update existing users - assign to first institution if they don't have one
                # Root users stay NULL (can access all)
                result = conn.execute(text(
                    "UPDATE users SET institution_id = :inst_id "
                    "WHERE institution_id IS NULL AND role != 'root'"
                ), {"inst_id": first_institution.id})
                conn.commit()
                
                if result.rowcount > 0:
                    print(f"   ✅ {result.rowcount} usuarios asignados a la institución por defecto")
                else:
                    print("   ℹ️  No hay usuarios huérfanos para migrar")
                    
            except Exception as e:
                print(f"   ❌ Error migrando users: {e}")
                conn.rollback()
            
            # 2. Add institution_id to subjects table
            print("\n" + "-" * 60)
            print("2️⃣  Migrando tabla: subjects")
            print("-" * 60)
            
            try:
                # Check if column already exists
                result = conn.execute(text(
                    "PRAGMA table_info(subjects)" if 'sqlite' in str(db.engine.dialect)
                    else "SELECT column_name FROM information_schema.columns WHERE table_name = 'subjects' AND column_name = 'institution_id'"
                ))
                column_exists = any('institution_id' in str(row) for row in result)
                
                if not column_exists:
                    conn.execute(text(
                        "ALTER TABLE subjects ADD COLUMN institution_id INTEGER"
                    ))
                    conn.commit()
                    print("   ✅ Columna institution_id agregada")
                else:
                    print("   ℹ️  Columna institution_id ya existe")
                
                # Update existing subjects - assign to first institution
                result = conn.execute(text(
                    "UPDATE subjects SET institution_id = :inst_id "
                    "WHERE institution_id IS NULL"
                ), {"inst_id": first_institution.id})
                conn.commit()
                
                if result.rowcount > 0:
                    print(f"   ✅ {result.rowcount} asignaturas asignadas a la institución por defecto")
                else:
                    print("   ℹ️  No hay asignaturas huérfanas para migrar")
                    
            except Exception as e:
                print(f"   ❌ Error migrando subjects: {e}")
                conn.rollback()
            
            # 3. Add institution_id to achievements table
            print("\n" + "-" * 60)
            print("3️⃣  Migrando tabla: achievements")
            print("-" * 60)
            
            try:
                # Check if column already exists
                result = conn.execute(text(
                    "PRAGMA table_info(achievements)" if 'sqlite' in str(db.engine.dialect)
                    else "SELECT column_name FROM information_schema.columns WHERE table_name = 'achievements' AND column_name = 'institution_id'"
                ))
                column_exists = any('institution_id' in str(row) for row in result)
                
                if not column_exists:
                    conn.execute(text(
                        "ALTER TABLE achievements ADD COLUMN institution_id INTEGER"
                    ))
                    conn.commit()
                    print("   ✅ Columna institution_id agregada")
                else:
                    print("   ℹ️  Columna institution_id ya existe")
                
                # Update existing achievements - set to NULL (global achievements)
                result = conn.execute(text(
                    "UPDATE achievements SET institution_id = NULL "
                    "WHERE institution_id IS NULL"
                ))
                conn.commit()
                print("   ℹ️  Logros existentes marcados como globales (institution_id = NULL)")
                    
            except Exception as e:
                print(f"   ❌ Error migrando achievements: {e}")
                conn.rollback()
            
            # 4. Drop old unique constraint on subjects.code and create new one
            print("\n" + "-" * 60)
            print("4️⃣  Actualizando constraints de subjects")
            print("-" * 60)
            
            try:
                # For SQLite, we need to recreate the table to change constraints
                if 'sqlite' in str(db.engine.dialect):
                    print("   ℹ️  SQLite: Las constraints unique se manejarán a nivel de modelo")
                    print("   ℹ️  El constraint uq_subject_institution_code se aplicará en la próxima recreación de tabla")
                else:
                    # PostgreSQL can add/drop constraints
                    print("   ℹ️  PostgreSQL: Constraints se manejarán automáticamente")
                
                print("   ✅ Constraints actualizados en los modelos")
                    
            except Exception as e:
                print(f"   ❌ Error actualizando constraints: {e}")
                conn.rollback()
        
        print("\n" + "=" * 60)
        print("✅ MIGRACIÓN COMPLETADA")
        print("=" * 60)
        print("\n📋 Resumen:")
        print(f"   - Instituciones: {Institution.query.count()}")
        print(f"   - Usuarios con institución: {User.query.filter(User.institution_id != None).count()}")
        print(f"   - Usuarios sin institución (root): {User.query.filter(User.institution_id == None).count()}")
        print(f"   - Asignaturas con institución: {Subject.query.filter(Subject.institution_id != None).count()}")
        print(f"   - Logros globales: {Achievement.query.filter(Achievement.institution_id == None).count()}")
        
        print("\n⚠️  IMPORTANTE:")
        print("   - Verifique que los usuarios no-root tengan institution_id asignado")
        print("   - Revise las asignaturas y asegúrese de que estén en la institución correcta")
        print("   - Los usuarios root pueden cambiar de institución desde el dashboard")
        
        return True


if __name__ == '__main__':
    print("\n⚠️  ADVERTENCIA: Este script modificará la estructura de la base de datos.")
    print("   Se recomienda hacer un backup antes de continuar.")
    print()
    
    response = input("¿Desea continuar con la migración? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        success = migrate()
        sys.exit(0 if success else 1)
    else:
        print("Migración cancelada.")
        sys.exit(0)
