"""
Test integral del sistema SIGE - Verifica que todas las rutas y templates funcionen.
"""
import sys
sys.path.insert(0, '.')

from app import create_app
from extensions import db

app = create_app()
passed = 0
failed = 0
errors = []

def test(name, condition, detail=''):
    global passed, failed
    if condition:
        print(f"  [PASS] {name}")
        passed += 1
    else:
        msg = f"[FAIL] {name}"
        if detail:
            msg += f" - {detail}"
        print(f"  {msg}")
        failed += 1
        errors.append(msg)

with app.app_context():
    print("\n" + "=" * 60)
    print("=== SIGE - Test Integral de Rutas y Templates ===")
    print("=" * 60)

    # 1. Verificar blueprints registrados
    print("\n--- Blueprints Registrados ---")
    expected_blueprints = [
        'auth', 'dashboard', 'institution', 'students', 'grades',
        'report_cards', 'attendance', 'observations', 'users',
        'metrics', 'alerts', 'achievements', 'parent', 'qr',
        'scheduling'
    ]
    registered = list(app.blueprints.keys())
    for bp in expected_blueprints:
        test(f"Blueprint '{bp}'", bp in registered, f"Registrados: {', '.join(registered[:5])}...")

    # 2. Verificar rutas críticas de scheduling
    print("\n--- Rutas de Scheduling ---")
    with app.test_client() as client:
        scheduling_routes = [
            '/scheduling/enrollments',
            '/scheduling/enrollments/new',
            '/scheduling/assignments',
            '/scheduling/assignments/new',
            '/scheduling/subject-grades',
            '/scheduling/subject-grades/new',
            '/scheduling/classrooms',
            '/scheduling/classrooms/new',
            '/scheduling/schedules',
            '/scheduling/schedules/generate',
            '/scheduling/blocks',
            '/scheduling/blocks/new',
        ]
        for route in scheduling_routes:
            resp = client.get(route, follow_redirects=False)
            test(f"GET {route}", resp.status_code in (200, 301, 302, 401), f"Status: {resp.status_code}")

    # 3. Verificar rutas de institution
    print("\n--- Rutas de Institution ---")
    with app.test_client() as client:
        inst_routes = [
            '/institution/new',
            '/institution/list',
            '/institution/campuses',
            '/institution/campuses/new',
            '/institution/grades',
            '/institution/subjects',
            '/institution/periods',
            '/institution/criteria',
        ]
        for route in inst_routes:
            resp = client.get(route, follow_redirects=False)
            test(f"GET {route}", resp.status_code in (200, 301, 302, 401), f"Status: {resp.status_code}")

    # 4. Verificar rutas de students
    print("\n--- Rutas de Students ---")
    with app.test_client() as client:
        student_routes = [
            '/students/',
            '/students/new',
            '/students/upload',
        ]
        for route in student_routes:
            resp = client.get(route, follow_redirects=False)
            test(f"GET {route}", resp.status_code in (200, 301, 302, 401), f"Status: {resp.status_code}")

    # 5. Verificar rutas de users
    print("\n--- Rutas de Users ---")
    with app.test_client() as client:
        user_routes = [
            '/users/users',
            '/users/users/new',
        ]
        for route in user_routes:
            resp = client.get(route, follow_redirects=False)
            test(f"GET {route}", resp.status_code in (200, 301, 302, 401), f"Status: {resp.status_code}")

    # 6. Verificar templates existentes
    print("\n--- Templates Existentes ---")
    import os
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    critical_templates = [
        'base.html',
        'institution/institution_form.html',
        'scheduling/enrollments/list.html',
        'scheduling/enrollments/form.html',
        'scheduling/assignments/list.html',
        'scheduling/assignments/form.html',
        'scheduling/subject_grades/list.html',
        'scheduling/subject_grades/form.html',
        'scheduling/classrooms/list.html',
        'scheduling/classrooms/form.html',
        'scheduling/schedules/list.html',
        'scheduling/schedules/generate.html',
        'scheduling/blocks/list.html',
        'scheduling/blocks/form.html',
        'users/list.html',
        'users/create.html',
        'students/list.html',
        'dashboard/admin.html',
        'dashboard/coordinator.html',
    ]
    for tmpl in critical_templates:
        path = os.path.join(template_dir, tmpl)
        test(f"Template '{tmpl}'", os.path.exists(path))

    # 7. Verificar que no hay url_for rotos en templates de scheduling
    print("\n--- Verificar url_for en templates de Scheduling ---")
    import re
    scheduling_templates = [
        'scheduling/enrollments/list.html',
        'scheduling/enrollments/form.html',
        'scheduling/assignments/list.html',
        'scheduling/assignments/form.html',
        'scheduling/subject_grades/list.html',
        'scheduling/subject_grades/form.html',
        'scheduling/classrooms/list.html',
        'scheduling/classrooms/form.html',
        'scheduling/schedules/list.html',
        'scheduling/schedules/generate.html',
        'scheduling/blocks/list.html',
        'scheduling/blocks/form.html',
    ]
    
    for tmpl in scheduling_templates:
        path = os.path.join(template_dir, tmpl)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Buscar url_for con endpoint incorrecto
            bad_patterns = [
                r"students\.student_list",
                r"students\.profile.*student_id=",
            ]
            for pattern in bad_patterns:
                matches = re.findall(pattern, content)
                test(f"{tmpl} - sin '{pattern}'", len(matches) == 0, f"Encontrados: {matches}")

print("\n" + "=" * 60)
print(f"Resultados: {passed} passed, {failed} failed, {passed+failed} total")
if errors:
    print("\nErrores encontrados:")
    for e in errors:
        print(f"  - {e}")
print("=" * 60)
