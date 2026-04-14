"""Test: AJAX endpoint para generar usernames."""
import sys
sys.path.insert(0, '.')

from app import create_app
from extensions import db
from models.user import User
from werkzeug.security import generate_password_hash

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
    print("TEST: AJAX Generate Username Endpoint")
    print("=" * 60)

    with app.test_client() as client:
        # 1. Login como root
        rv = client.post('/login', data={
            'username': 'root',
            'password': 'root123'
        }, follow_redirects=True)
        test("Login root exitoso", rv.status_code == 200)

        # 2. Sin autenticación - debe redirigir
        with app.test_client() as unauth_client:
            rv = unauth_client.get('/users/users/api/generate-username?first_name=Juan&last_name=Perez')
            test("Sin auth redirige a login", rv.status_code in (301, 302, 401))

        # 3. Sin parametros - debe dar error
        rv = client.get('/users/users/api/generate-username')
        test("Sin parametros retorna error", rv.status_code == 200)
        import json
        data = json.loads(rv.data)
        test("Error en respuesta", 'error' in data)

        # 4. Con nombre y apellido - primera vez
        rv = client.get('/users/users/api/generate-username?first_name=Juan&last_name=Perez')
        data = json.loads(rv.data)
        test("Username generado", 'username' in data)
        test("Formato correcto (jperez1)", data.get('username') == 'jperez1' if 'username' in data else False)
        print(f"     → Username generado: {data.get('username', 'N/A')}")

        # 5. Crear usuario jperez1 y verificar que el siguiente es jperez2
        from models.user import User
        existing = User.query.filter_by(username='jperez1').first()
        if not existing:
            new_user = User(
                username='jperez1',
                email='jperez1@test.com',
                password_hash=generate_password_hash('test123'),
                first_name='Juan',
                last_name='Perez',
                role='viewer',
                is_active=True
            )
            db.session.add(new_user)
            db.session.commit()

        rv = client.get('/users/users/api/generate-username?first_name=Juan&last_name=Perez')
        data = json.loads(rv.data)
        test("Siguiente username es jperez2", data.get('username') == 'jperez2')
        print(f"     → Username después de crear jperez1: {data.get('username', 'N/A')}")

        # 6. Crear jperez2 y verificar jperez3
        new_user2 = User(
            username='jperez2',
            email='jperez2@test.com',
            password_hash=generate_password_hash('test123'),
            first_name='Juan',
            last_name='Perez',
            role='viewer',
            is_active=True
        )
        db.session.add(new_user2)
        db.session.commit()

        rv = client.get('/users/users/api/generate-username?first_name=Juan&last_name=Perez')
        data = json.loads(rv.data)
        test("Siguiente username es jperez3", data.get('username') == 'jperez3')
        print(f"     → Username después de crear jperez2: {data.get('username', 'N/A')}")

        # 7. Nombre diferente - debe generar username diferente
        rv = client.get('/users/users/api/generate-username?first_name=Maria&last_name=Garcia')
        data = json.loads(rv.data)
        test("Username diferente para Maria Garcia", data.get('username') == 'mgarcia1')
        print(f"     → Username para Maria Garcia: {data.get('username', 'N/A')}")

    print("\n" + "=" * 60)
    print(f"Resultados: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 60)
