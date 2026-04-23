import pytest

def test_login_page(client):
    response = client.get('/login')
    assert response.status_code == 200

def test_protected_endpoints_redirect_without_login(client):
    endpoints = [
        '/',
        '/dashboard/root',
        '/institution/list',
        '/users/users',
        '/students/',
        '/grades/input',
        '/attendance/',
        '/report-cards/',
        '/metrics/institution'
    ]
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 302
        assert '/login' in response.headers.get('Location', '')

def test_login_success(client, init_database):
    response = client.post('/login', data={
        'username': 'root',
        'password': 'root123'
    }, follow_redirects=True)
    assert response.status_code == 200
