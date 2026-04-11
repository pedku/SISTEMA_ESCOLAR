"""
Database initialization script with seed data.
Creates default institution, users, subjects, periods, and evaluation criteria.
"""

from datetime import datetime, date
from app import create_app
from extensions import db
from models.user import User
from models.institution import Institution, Campus
from models.academic import Grade, Subject, SubjectGrade, AcademicStudent
from models.grading import AcademicPeriod, GradeCriteria
from models.achievement import Achievement
from werkzeug.security import generate_password_hash


def init_db():
    """Initialize database with seed data."""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if data already exists
        if Institution.query.first():
            print("Database already contains data. Skipping initialization.")
            return
        
        print("Initializing database with seed data...")
        
        # Create root user
        root_user = User(
            username='root',
            email='root@sige.edu.co',
            first_name='Administrador',
            last_name='Root',
            document_type='CC',
            document_number='0000000000',
            role='root',
            is_active=True
        )
        root_user.set_password('root123')
        db.session.add(root_user)
        
        # Create admin user
        admin_user = User(
            username='admin',
            email='admin@sige.edu.co',
            first_name='Administrador',
            last_name='Institución',
            document_type='CC',
            document_number='0000000001',
            role='admin',
            is_active=True
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        
        # Create coordinator user
        coordinator_user = User(
            username='coordinator',
            email='coordinator@sige.edu.co',
            first_name='Coordinador',
            last_name='Académico',
            document_type='CC',
            document_number='0000000002',
            role='coordinator',
            is_active=True
        )
        coordinator_user.set_password('coord123')
        db.session.add(coordinator_user)
        
        # Create teacher user
        teacher_user = User(
            username='teacher',
            email='teacher@sige.edu.co',
            first_name='Profesor',
            last_name='Ejemplo',
            document_type='CC',
            document_number='0000000003',
            role='teacher',
            is_active=True
        )
        teacher_user.set_password('teacher123')
        db.session.add(teacher_user)
        
        db.session.commit()
        
        # Create institution
        institution = Institution(
            name='Institución Educativa Ejemplo',
            nit='900123456-7',
            address='Calle Principal #10-20',
            phone='6012345678',
            email='contacto@ieejemplo.edu.co',
            municipality='Municipio Ejemplo',
            department='Departamento',
            resolution='Resolución No. 1234 de 2020',
            academic_year='2026'
        )
        db.session.add(institution)
        db.session.commit()
        
        # Create campuses
        campus1 = Campus(
            institution_id=institution.id,
            name='Sede Principal',
            code='001',
            address='Calle Principal #10-20',
            jornada='completa',
            active=True
        )
        campus2 = Campus(
            institution_id=institution.id,
            name='Sede Secundaria',
            code='002',
            address='Carrera 5 #8-15',
            jornada='mañana',
            active=True
        )
        db.session.add_all([campus1, campus2])
        db.session.commit()
        
        # Create subjects
        subjects_data = [
            ('Matemáticas', 'MAT'),
            ('Español y Literatura', 'ESP'),
            ('Ciencias Naturales', 'CNAT'),
            ('Ciencias Sociales', 'CSOC'),
            ('Inglés', 'ING'),
            ('Educación Física', 'EDFIS'),
            ('Educación Artística', 'EDART'),
            ('Ética y Valores', 'ETICA'),
            ('Tecnología e Informática', 'TECNO'),
            ('Religión', 'RELIG'),
        ]
        
        subjects = []
        for name, code in subjects_data:
            subject = Subject(name=name, code=code)
            subjects.append(subject)
            db.session.add(subject)
        
        db.session.commit()
        
        # Create grades
        grades_data = [
            ('6-1', campus1.id, teacher_user.id),
            ('7-1', campus1.id, teacher_user.id),
            ('8-1', campus1.id, None),
            ('9-1', campus1.id, None),
            ('10-1', campus1.id, None),
            ('11-1', campus1.id, None),
        ]
        
        grades = []
        for name, campus_id, director_id in grades_data:
            grade = Grade(
                name=name,
                campus_id=campus_id,
                director_id=director_id,
                academic_year='2026',
                max_students=40
            )
            grades.append(grade)
            db.session.add(grade)
        
        db.session.commit()
        
        # Create academic periods
        periods_data = [
            ('Primer Periodo', 'P1', date(2026, 2, 2), date(2026, 4, 17), True, 1),
            ('Segundo Periodo', 'P2', date(2026, 4, 20), date(2026, 6, 19), False, 2),
            ('Tercer Periodo', 'P3', date(2026, 7, 6), date(2026, 9, 11), False, 3),
            ('Cuarto Periodo', 'P4', date(2026, 9, 14), date(2026, 11, 20), False, 4),
        ]
        
        periods = []
        for name, short_name, start, end, is_active, order in periods_data:
            period = AcademicPeriod(
                institution_id=institution.id,
                name=name,
                short_name=short_name,
                start_date=start,
                end_date=end,
                is_active=is_active,
                academic_year='2026',
                order=order
            )
            periods.append(period)
            db.session.add(period)
        
        db.session.commit()
        
        # Create evaluation criteria
        criteria_data = [
            ('Seguimiento', 20.0, 'Tareas, quizzes, participación diaria', 1),
            ('Formativo', 20.0, 'Trabajos, proyectos formativos', 2),
            ('Cognitivo', 30.0, 'Pruebas escritas, evaluaciones de conocimiento', 3),
            ('Procedimental', 30.0, 'Prácticas, aplicaciones, trabajos en clase', 4),
        ]
        
        criteria = []
        for name, weight, desc, order in criteria_data:
            criterion = GradeCriteria(
                institution_id=institution.id,
                name=name,
                weight=weight,
                description=desc,
                order=order
            )
            criteria.append(criterion)
            db.session.add(criterion)
        
        db.session.commit()
        
        # Create achievements
        achievements_data = [
            ('Superador', 'Subió 1.0 punto o más entre periodos', '📈', 
             'Mejorar nota en 1.0+ puntos entre periodos consecutivos', 'mejora'),
            ('Excelencia', 'Nota promedio >= 4.5 en el periodo', '⭐', 
             'Alcanzar promedio de 4.5 o superior en un periodo', 'académico'),
            ('Asistencia Perfecta', 'Sin inasistencias en el periodo', '✅', 
             'No tener ninguna inasistencia injustificada en el periodo', 'asistencia'),
            ('Todo Terreno', 'Todas las materias ganadas en el periodo', '🏅', 
             'Aprobar todas las asignaturas en un periodo', 'académico'),
            ('Resiliente', 'Recuperó una materia perdida', '💪', 
             'Lograr aprobar una materia que tenía perdida', 'académico'),
            ('Constancia', '3 periodos seguidos con promedio >= 4.0', '🔥', 
             'Mantener promedio de 4.0 o más durante 3 periodos consecutivos', 'académico'),
        ]
        
        achievements = []
        for name, desc, icon, criteria_text, category in achievements_data:
            achievement = Achievement(
                name=name,
                description=desc,
                icon=icon,
                criteria=criteria_text,
                category=category,
                is_active=True
            )
            achievements.append(achievement)
            db.session.add(achievement)
        
        db.session.commit()
        
        print("Database initialized successfully!")
        print("\nDefault users created:")
        print("  - Root: username=root, password=root123")
        print("  - Admin: username=admin, password=admin123")
        print("  - Coordinator: username=coordinator, password=coord123")
        print("  - Teacher: username=teacher, password=teacher123")
        print(f"\nInstitution: {institution.name}")
        print(f"Campuses: {campus1.name}, {campus2.name}")
        print(f"Subjects: {len(subjects)}")
        print(f"Grades: {len(grades)}")
        print(f"Periods: {len(periods)}")
        print(f"Criteria: {len(criteria)}")
        print(f"Achievements: {len(achievements)}")


if __name__ == '__main__':
    init_db()
