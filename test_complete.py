"""
Comprehensive test suite for SIGE.
Tests all modules and functionality to ensure everything works correctly.
"""

import sys
import unittest
from app import create_app
from extensions import db
from models.user import User
from models.institution import Institution, Campus
from models.academic import Grade, Subject, AcademicStudent
from models.grading import AcademicPeriod, GradeCriteria

class TestSIGE(unittest.TestCase):
    """Comprehensive test suite for SIGE application."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self._create_test_data()
    
    def tearDown(self):
        """Clean up after tests."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def _create_test_data(self):
        """Create basic test data."""
        # Create root user
        root = User(
            username='root',
            email='root@test.com',
            first_name='Root',
            last_name='User',
            document_type='CC',
            document_number='0000000001',
            role='root',
            is_active=True
        )
        root.set_password('root123')
        db.session.add(root)
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@test.com',
            first_name='Admin',
            last_name='User',
            document_type='CC',
            document_number='0000000002',
            role='admin',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Create institution
        institution = Institution(
            name='Test Institution',
            nit='900123456-7',
            address='Test Address',
            phone='6012345678',
            email='test@test.com',
            municipality='Test City',
            department='Test Dept',
            academic_year='2026'
        )
        db.session.add(institution)
        db.session.commit()
        
        # Create campus
        campus = Campus(
            institution_id=institution.id,
            name='Test Campus',
            code='001',
            address='Campus Address',
            jornada='completa',
            active=True
        )
        db.session.add(campus)
        db.session.commit()
    
    # ============================================
    # TEST 1: Application Creation
    # ============================================
    def test_app_creation(self):
        """Test that Flask app can be created."""
        app = create_app('testing')
        self.assertIsNotNone(app)
        self.assertEqual(app.config['TESTING'], True)
    
    # ============================================
    # TEST 2: User Model
    # ============================================
    def test_user_model(self):
        """Test User model operations."""
        user = User.query.filter_by(username='root').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'root')
        self.assertTrue(user.check_password('root123'))
        self.assertFalse(user.check_password('wrong'))
        self.assertTrue(user.is_root())
        self.assertFalse(user.is_admin())
        self.assertEqual(user.get_full_name(), 'Root User')
    
    # ============================================
    # TEST 3: Institution Model
    # ============================================
    def test_institution_model(self):
        """Test Institution model operations."""
        institution = Institution.query.first()
        self.assertIsNotNone(institution)
        self.assertEqual(institution.name, 'Test Institution')
        self.assertEqual(institution.nit, '900123456-7')
    
    # ============================================
    # TEST 4: Campus Model
    # ============================================
    def test_campus_model(self):
        """Test Campus model operations."""
        campus = Campus.query.first()
        self.assertIsNotNone(campus)
        self.assertEqual(campus.name, 'Test Campus')
        self.assertTrue(campus.active)
    
    # ============================================
    # TEST 5: Login Page
    # ============================================
    def test_login_page(self):
        """Test that login page loads."""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Iniciar Sesi', response.data)
    
    # ============================================
    # TEST 6: Successful Login
    # ============================================
    def test_successful_login(self):
        """Test successful login with correct credentials."""
        response = self.client.post('/login', data={
            'username': 'root',
            'password': 'root123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
    
    # ============================================
    # TEST 7: Failed Login
    # ============================================
    def test_failed_login(self):
        """Test failed login with wrong credentials."""
        response = self.client.post('/login', data={
            'username': 'root',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
    
    # ============================================
    # TEST 8: Logout
    # ============================================
    def test_logout(self):
        """Test logout functionality."""
        # Login first
        self.client.post('/login', data={
            'username': 'root',
            'password': 'root123'
        })
        
        # Logout
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
    
    # ============================================
    # TEST 9: Protected Route Redirects
    # ============================================
    def test_protected_route_redirects(self):
        """Test that protected routes redirect to login."""
        response = self.client.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('login', response.request.url.lower())
    
    # ============================================
    # TEST 10: Dashboard Access After Login
    # ============================================
    def test_dashboard_access_after_login(self):
        """Test dashboard access after successful login."""
        # Login
        self.client.post('/login', data={
            'username': 'root',
            'password': 'root123'
        })
        
        # Access dashboard
        response = self.client.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
    
    # ============================================
    # TEST 11: Student Routes (Authenticated)
    # ============================================
    def test_student_list_requires_login(self):
        """Test that student list requires login."""
        response = self.client.get('/students/', follow_redirects=True)
        self.assertIn('login', response.request.url.lower())
    
    # ============================================
    # TEST 12: Institution Routes (Authenticated)
    # ============================================
    def test_institution_routes(self):
        """Test institution routes require login."""
        response = self.client.get('/institution/config', follow_redirects=True)
        self.assertIn('login', response.request.url.lower())
    
    # ============================================
    # TEST 13: Error Pages
    # ============================================
    def test_404_error_page(self):
        """Test 404 error page."""
        response = self.client.get('/nonexistent-page-12345')
        self.assertEqual(response.status_code, 404)
    
    # ============================================
    # TEST 14: Password Hashing
    # ============================================
    def test_password_hashing(self):
        """Test that passwords are properly hashed."""
        user = User()
        user.set_password('testpassword')
        self.assertNotEqual(user.password_hash, 'testpassword')
        self.assertTrue(user.check_password('testpassword'))
        self.assertFalse(user.check_password('wrongpassword'))
    
    # ============================================
    # TEST 15: User Roles
    # ============================================
    def test_user_roles(self):
        """Test user role methods."""
        root = User(username='testroot', email='testroot@test.com', 
                   first_name='Test', last_name='Root', role='root')
        admin = User(username='testadmin', email='testadmin@test.com', 
                    first_name='Test', last_name='Admin', role='admin')
        teacher = User(username='testteacher', email='testteacher@test.com', 
                      first_name='Test', last_name='Teacher', role='teacher')
        
        self.assertTrue(root.is_root())
        self.assertFalse(root.is_admin())
        self.assertTrue(admin.is_admin())
        self.assertFalse(admin.is_root())
        self.assertTrue(teacher.is_teacher())
        self.assertFalse(teacher.is_root())
    
    # ============================================
    # TEST 16: Database Relationships
    # ============================================
    def test_database_relationships(self):
        """Test that database relationships work."""
        institution = Institution.query.first()
        self.assertIsNotNone(institution)
        
        # Test relationship
        campus = Campus.query.filter_by(institution_id=institution.id).first()
        self.assertIsNotNone(campus)
        self.assertEqual(campus.institution_id, institution.id)
    
    # ============================================
    # TEST 17: All Models Import
    # ============================================
    def test_all_models_import(self):
        """Test that all models can be imported."""
        from models.user import User
        from models.institution import Institution, Campus
        from models.academic import Grade, Subject, SubjectGrade, AcademicStudent, ParentStudent
        from models.grading import AcademicPeriod, GradeCriteria, GradeRecord, FinalGrade, AnnualGrade
        from models.attendance import Attendance
        from models.observation import Observation
        from models.report import ReportCard, ReportCardObservation
        from models.achievement import Achievement, StudentAchievement
        
        self.assertIsNotNone(User)
        self.assertIsNotNone(Institution)
        self.assertIsNotNone(Campus)
    
    # ============================================
    # TEST 18: All Routes Import
    # ============================================
    def test_all_routes_import(self):
        """Test that all route blueprints can be imported."""
        from routes.auth import auth_bp
        from routes.dashboard import dashboard_bp
        from routes.institution import institution_bp
        from routes.students import students_bp
        from routes.grades import grades_bp
        from routes.report_cards import report_cards_bp
        from routes.attendance import attendance_bp
        from routes.observations import observations_bp
        from routes.metrics import metrics_bp
        from routes.achievements import achievements_bp
        from routes.parent import parent_bp
        from routes.qr import qr_bp
        
        self.assertIsNotNone(auth_bp)
        self.assertIsNotNone(dashboard_bp)
        self.assertIsNotNone(institution_bp)
    
    # ============================================
    # TEST 19: Extensions Initialized
    # ============================================
    def test_extensions_initialized(self):
        """Test that all extensions are properly initialized."""
        from extensions import db, login_manager, migrate, limiter
        
        self.assertIsNotNone(db)
        self.assertIsNotNone(login_manager)
        self.assertIsNotNone(migrate)
        self.assertIsNotNone(limiter)
    
    # ============================================
    # TEST 20: Complete Login Flow
    # ============================================
    def test_complete_login_flow(self):
        """Test complete login flow from start to dashboard."""
        # Get login page
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        
        # Login with root
        response = self.client.post('/login', data={
            'username': 'root',
            'password': 'root123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Access profile
        response = self.client.get('/profile')
        self.assertEqual(response.status_code, 200)
        
        # Logout
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Try to access protected page
        response = self.client.get('/profile', follow_redirects=True)
        self.assertIn('login', response.request.url.lower())


def run_tests():
    """Run all tests and report results."""
    print("=" * 70)
    print("SIGE - Comprehensive Test Suite")
    print("=" * 70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSIGE)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    if len(result.failures) == 0 and len(result.errors) == 0:
        print("\nALL TESTS PASSED!")
        print(f"{result.testsRun}/{result.testsRun} tests successful")
        return True
    else:
        print(f"\n{len(result.failures) + len(result.errors)}/{result.testsRun} tests failed")
        return False


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
