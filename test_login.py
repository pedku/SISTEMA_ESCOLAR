"""
Test page to diagnose the 500 error.
"""

from app import create_app, db
from models.user import User
from flask_login import login_user

app = create_app()

with app.app_context():
    # Test 1: Check if root user exists
    root = User.query.filter_by(username='root').first()
    if root:
        print("✅ Root user exists")
        print(f"   - Username: {root.username}")
        print(f"   - Role: {root.role}")
        print(f"   - Email: {root.email}")
        print(f"   - Password check: {root.check_password('root123')}")
    else:
        print("❌ Root user does NOT exist")
    
    # Test 2: Check all users
    print("\n📋 All users:")
    users = User.query.all()
    for user in users:
        print(f"   - {user.username} ({user.role}) - Active: {user.is_active}")
    
    # Test 3: Check dashboard routes
    print("\n🔍 Testing routes:")
    with app.test_client() as client:
        # Test login page
        resp = client.get('/login')
        print(f"   GET /login: {resp.status_code}")
        
        # Test dashboard (should redirect to login)
        resp = client.get('/')
        print(f"   GET /: {resp.status_code} (redirect to login)")
        
        # Test login with root
        with client.session_transaction() as sess:
            pass  # Initialize session
        
        # Get CSRF token
        resp = client.get('/login')
        
        # Extract CSRF token from form (simplified test without CSRF)
        resp = client.post('/login', data={
            'username': 'root',
            'password': 'root123',
            'csrf_token': 'test-token'  # Will be ignored in test mode
        }, follow_redirects=True, headers={'X-CSRFToken': 'test'})
        print(f"   POST /login (root): {resp.status_code}")
        
        if resp.status_code == 200:
            print("   ✅ Login successful")
            # Check where it redirected
            print(f"   📍 Final URL: {resp.request.path}")
        else:
            print(f"   ❌ Login failed")

print("\n✅ Test completed")
