"""
Migration script to add scheduling and enrollment tables.
Run: python migrate_scheduling.py
"""

import sys
sys.path.insert(0, '.')

from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app()

def run_migration():
    """Create new tables for scheduling and enrollment system."""
    
    with app.app_context():
        print("=== Migracion: Sistema de Matricula y Horarios ===")
        print("Creando tablas nuevas...")
        
        # Create new tables
        db.create_all()
        
        # Verify tables were created
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        new_tables = [
            'classrooms',
            'student_enrollments',
            'teacher_subject_assignments',
            'schedules',
            'schedule_blocks'
        ]
        
        print("\nTablas creadas:")
        for table in new_tables:
            if table in tables:
                print(f"  [OK] {table}")
            else:
                print(f"  [FAIL] {table} - No se pudo crear")
        
        print("\n=== Migracion completada ===")
        print("Las siguientes tablas han sido creadas:")
        print("  - classrooms: Salones/Aulas por sede")
        print("  - student_enrollments: Matricula de estudiantes en materias")
        print("  - teacher_subject_assignments: Asignacion de profesores a materias")
        print("  - schedules: Horarios de clases (materia + salon + hora)")
        print("  - schedule_blocks: Bloques de tiempo para generacion de horarios")
        
        return True


if __name__ == '__main__':
    try:
        run_migration()
    except Exception as e:
        print(f"\n[ERROR] Error durante la migracion: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
