"""Test: Template grades/summary.html funciona correctamente."""
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
    print("TEST: grades/summary.html Template")
    print("=" * 60)

    with app.test_client() as client:
        # Login como root
        rv = client.post('/login', data={
            'username': 'root',
            'password': 'root123'
        }, follow_redirects=True)
        test("Login root exitoso", rv.status_code == 200)

        # Probar que el template existe y se puede renderizar (aunque sea sin datos)
        # Usar IDs que no existen para verificar que la ruta responde
        rv = client.get('/grades/summary/99999/99999', follow_redirects=True)
        test("Ruta /grades/summary existe (redirect si no hay datos)", rv.status_code == 200)

        # Verificar que el template file existe
        import os
        template_path = os.path.join(app.root_path, 'templates', 'grades', 'summary.html')
        test("Template file existe", os.path.exists(template_path))

        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            test("Template tiene stat cards", 'Promedio General' in content)
            test("Template tiene tasa aprobación", 'Tasa Aprobación' in content or 'Tasa de Aprobaci' in content)
            test("Template tiene tabla resumen", 'summaryTable' in content)
            test("Template tiene gráfico distribución", 'distributionChart' in content)
            test("Template tiene estadísticas por criterio", 'Criterio' in content)
            test("Template tiene DataTables en español", 'es-ES' in content)
            test("Template tiene botón volver", 'Volver' in content)
            test("Template tiene empty state", 'No hay calificaciones' in content)
            test("Template tiene badges de desempeño", 'grade-superior' in content and 'grade-bajo' in content)
            test("Template usa Bootstrap 5", 'class="card shadow-sm"' in content or 'shadow-sm' in content)

    print("\n" + "=" * 60)
    print(f"Resultados: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 60)
