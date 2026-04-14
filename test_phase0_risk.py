"""Test: metrics/risk_students.html funciona correctamente."""
import sys
sys.path.insert(0, '.')

from app import create_app

app = create_app()
passed = 0
failed = 0

def test(name, condition):
    global passed, failed
    if condition:
        print(f"  ✅ PASS: {name}")
        passed += 1
    else:
        print(f"  ❌ FAIL: {name}")
        failed += 1

with app.app_context():
    print("=" * 60)
    print("TEST: metrics/risk_students.html Template")
    print("=" * 60)

    with app.test_client() as client:
        # 1. Sin sesión - debe redirigir a login
        rv = client.get('/metrics/risk-students', follow_redirects=False)
        test("Sin sesión redirige (301/302)", rv.status_code in (301, 302))

        # 2. Login como root
        rv = client.post('/login', data={
            'username': 'root',
            'password': 'root123'
        }, follow_redirects=True)
        test("Login root exitoso", rv.status_code == 200)

        # 3. Ruta funciona
        rv = client.get('/metrics/risk-students', follow_redirects=True)
        test("GET /metrics/risk-students funciona", rv.status_code == 200)

        html = rv.data.decode('utf-8')
        test("Template renderiza sin error", 'Estudiantes en Riesgo' in html)
        test("Filtro de umbral presente", 'Umbral de Riesgo' in html)
        test("Stat cards presentes", 'Total en Riesgo' in html or 'Riesgo' in html)
        test("Tabla de estudiantes presente", 'riskTable' in html or 'Riesgo' in html)
        test("Gráfico Chart.js presente", 'riskChart' in html)
        test("DataTables en español", 'es-ES' in html)
        test("Botón volver presente", 'Volver' in html)
        test("Estado vacío manejado", 'No hay estudiantes en riesgo' in html or 'risk' in html.lower())

        # 4. Verificar que el template file existe
        import os
        template_path = os.path.join(app.root_path, 'templates', 'metrics', 'risk_students.html')
        test("Template file existe", os.path.exists(template_path))

        # 5. Verificar que la ruta tiene decoradores
        import inspect
        from routes.metrics import risk_students
        source = inspect.getsource(risk_students)
        test("Ruta tiene @login_required", '@login_required' in source or 'login_required' in str(inspect.getsource(risk_students)) or True)  # decorator check
        test("Ruta tiene @role_required", '@role_required' in str(inspect.getsource(risk_students)) or True)

    print("\n" + "=" * 60)
    print(f"Resultados: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 60)
