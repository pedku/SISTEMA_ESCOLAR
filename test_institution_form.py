"""Test: Formulario institution_new mantiene datos al haber errores."""
import sys
sys.path.insert(0, '.')

from app import create_app
from extensions import db
from models.institution import Institution
from models.user import User

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
    print("TEST: Persistencia de datos en formulario institución")
    print("=" * 60)

    with app.test_client() as client:
        # 1. Login como root
        rv = client.post('/login', data={
            'username': 'root',
            'password': 'root123'
        }, follow_redirects=True)
        test("Login root exitoso", rv.status_code == 200)

        # 2. GET al formulario - debe tener form_data y errors vacíos
        rv = client.get('/institution/new')
        test("GET /institution/new funciona", rv.status_code == 200)
        html = rv.data.decode('utf-8')
        test("Template renderiza sin errores", 'institutionForm' in html)

        # 3. POST sin datos del admin (debe fallar y mantener datos)
        rv = client.post('/institution/new', data={
            'name': 'Instituto Test Persistencia',
            'nit': '111.222.333-4',
            'address': 'Calle Persistencia 456',
            'phone': '6019998888',
            'email': 'test@persistencia.edu.co',
            'municipality': 'Medellín',
            'department': 'Antioquia',
            'academic_year': '2026',
            # Sin datos del admin - debe fallar
        }, follow_redirects=True)
        
        test("POST sin admin retorna error", rv.status_code == 200)
        html = rv.data.decode('utf-8')
        test("Mensaje de error presente", b'obligatorio' in rv.data or b'administrador' in rv.data)
        
        # VERIFICAR PERSISTENCIA DE DATOS
        test("Campo name mantiene valor", b'Instituto Test Persistencia' in rv.data)
        test("Campo nit mantiene valor", b'111.222.333-4' in rv.data)
        test("Campo address mantiene valor", b'Calle Persistencia 456' in rv.data)
        html_data = rv.data.decode('utf-8')
        test("Campo municipality mantiene valor", 'Medellín' in html_data)
        test("Campo department mantiene valor", 'Antioquia' in html_data)

        # 4. POST con email duplicado (debe fallar y mantener datos)
        # Primero creamos un admin para otra institución
        existing_admin = User.query.filter_by(email='existing@test.com').first()
        if not existing_admin:
            from werkzeug.security import generate_password_hash
            existing_admin = User(
                username='testexisting',
                email='existing@test.com',
                password_hash=generate_password_hash('test123'),
                first_name='Test',
                last_name='Existing',
                role='admin',
                institution_id=None,
                document_type='CC',
                document_number='0000000',
                is_active=True
            )
            db.session.add(existing_admin)
            db.session.commit()
        
        rv = client.post('/institution/new', data={
            'name': 'Instituto Test Email Dup',
            'nit': '555.666.777-8',
            'address': 'Calle Email 789',
            'phone': '6017776666',
            'email': 'test@dupemail.edu.co',
            'municipality': 'Cali',
            'department': 'Valle',
            'academic_year': '2026',
            'admin_first_name': 'Admin',
            'admin_last_name': 'Duplicado',
            'admin_document_type': 'CC',
            'admin_document': '111222333',
            'admin_email': 'existing@test.com',  # Email duplicado
        }, follow_redirects=True)
        
        test("POST con email duplicado retorna error", rv.status_code == 200)
        html_data = rv.data.decode('utf-8')
        test("Error email presente", 'ya est' in html_data.lower() or 'registrado' in html_data.lower() or 'email' in html_data.lower())
        
        # VERIFICAR PERSISTENCIA DE DATOS
        test("Campo name mantiene valor (email dup)", b'Instituto Test Email Dup' in rv.data)
        test("Campo admin_first_name mantiene valor", b'Admin' in rv.data)
        test("Campo admin_last_name mantiene valor", b'Duplicado' in rv.data)
        test("Campo municipality mantiene valor", 'Cali' in html_data)
        test("Campo admin_email mantiene valor", b'existing@test.com' in rv.data)

    print("\n" + "=" * 60)
    print(f"Resultados: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 60)
