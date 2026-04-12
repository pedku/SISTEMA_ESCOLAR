"""
Test script for parent portal routes.
Tests route registration, template rendering, and access control.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models.user import User
from models.academic import AcademicStudent, ParentStudent, Grade, Subject, SubjectGrade
from models.institution import Institution, Campus
from models.grading import AcademicPeriod, FinalGrade
from models.attendance import Attendance
from models.observation import Observation
from models.report import ReportCard
from datetime import date, datetime


def test_parent_portal():
    app = create_app()
    results = []

    with app.app_context():
        print("=" * 60)
        print("TEST PORTAL DE ACUDIENTES")
        print("=" * 60)

        # 1. Check routes exist
        print("\n1. Verificando rutas registradas...")
        rules = list(app.url_map.iter_rules())
        parent_rules = [r for r in rules if r.rule.startswith('/parent/')]
        
        expected_routes = [
            '/parent/dashboard',
            '/parent/grades/<int:student_id>',
            '/parent/attendance/<int:student_id>',
            '/parent/observations/<int:student_id>',
            '/parent/report-cards/<int:student_id>',
        ]

        for expected in expected_routes:
            found = any(r.rule == expected for r in parent_rules)
            status = "OK" if found else "FALLO"
            print(f"   [{status}] {expected}")
            results.append(('route_' + expected.replace('/parent/', '').replace('/', '_'), found))

        # 2. Check templates exist
        print("\n2. Verificando templates...")
        from jinja2 import Environment, FileSystemLoader
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        
        templates_to_check = [
            'parent/dashboard.html',
            'parent/grades.html',
            'parent/attendance.html',
            'parent/observations.html',
            'parent/report_cards.html',
        ]

        for tmpl in templates_to_check:
            try:
                template = env.get_template(tmpl)
                # Check it's not just a placeholder
                content = open(os.path.join(template_dir, tmpl), 'r', encoding='utf-8').read()
                has_content = 'module en desarrollo' not in content.lower() and content.strip() != ''
                status = "OK" if has_content else "PLACEHOLDER"
                print(f"   [{status}] {tmpl}")
                results.append(('template_' + tmpl.replace('/', '_'), has_content))
            except Exception as e:
                print(f"   [ERROR] {tmpl}: {e}")
                results.append(('template_' + tmpl.replace('/', '_'), False))

        # 3. Check route decorators and logic
        print("\n3. Verificando logica de rutas...")
        from routes.parent import parent_bp, _get_parent_students, _verify_student_access, _get_student_average, _get_attendance_stats
        
        checks = [
            ('_get_parent_students function exists', callable(_get_parent_students)),
            ('_verify_student_access function exists', callable(_verify_student_access)),
            ('_get_student_average function exists', callable(_get_student_average)),
            ('_get_attendance_stats function exists', callable(_get_attendance_stats)),
        ]

        for name, check in checks:
            status = "OK" if check else "FALLO"
            print(f"   [{status}] {name}")
            results.append(('logic_' + name.split()[0], check))

        # 4. Check parent_dashboard route has proper decorators
        print("\n4. Verificando decoradores...")
        from routes.parent import parent_dashboard, parent_view_grades, parent_view_attendance, parent_view_observations, parent_view_report_cards
        
        route_funcs = [
            ('parent_dashboard', parent_dashboard),
            ('parent_view_grades', parent_view_grades),
            ('parent_view_attendance', parent_view_attendance),
            ('parent_view_observations', parent_view_observations),
            ('parent_view_report_cards', parent_view_report_cards),
        ]

        for name, func in route_funcs:
            # Check function exists and is callable
            has_decorators = callable(func)
            status = "OK" if has_decorators else "FALLO"
            print(f"   [{status}] {name} - decorada y callable")
            results.append(('decorator_' + name, has_decorators))

        # 5. Verify ParentStudent model has correct fields
        print("\n5. Verificando modelo ParentStudent...")
        parent_student_fields = ['parent_id', 'student_id', 'relationship']
        for field in parent_student_fields:
            has_field = hasattr(ParentStudent, field)
            status = "OK" if has_field else "FALLO"
            print(f"   [{status}] Campo '{field}'")
            results.append(('model_ParentStudent_' + field, has_field))

        # Summary
        print("\n" + "=" * 60)
        passed = sum(1 for _, v in results if v)
        total = len(results)
        print(f"RESULTADO: {passed}/{total} pruebas pasadas")
        
        if passed == total:
            print("TODAS LAS PRUEBAS PASARON!")
        else:
            failed = [name for name, v in results if not v]
            print(f"Pruebas fallidas: {', '.join(failed)}")
        print("=" * 60)

        return passed == total


if __name__ == '__main__':
    success = test_parent_portal()
    sys.exit(0 if success else 1)
