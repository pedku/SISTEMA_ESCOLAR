"""
Test script to verify the application loads correctly.
"""

import sys

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from app import create_app, db
        print("✓ app module")
    except Exception as e:
        print(f"✗ app module: {e}")
        return False
    
    try:
        from models.user import User
        from models.institution import Institution, Campus
        from models.academic import Grade, Subject, SubjectGrade, AcademicStudent, ParentStudent
        from models.grading import AcademicPeriod, GradeCriteria, GradeRecord, FinalGrade, AnnualGrade
        from models.attendance import Attendance
        from models.observation import Observation
        from models.report import ReportCard, ReportCardObservation
        from models.achievement import Achievement, StudentAchievement
        print("✓ all models")
    except Exception as e:
        print(f"✗ models: {e}")
        return False
    
    try:
        from utils.decorators import login_required, role_required
        from utils.validators import validate_email, validate_grade_score
        from utils.template_helpers import get_template_helpers
        from utils.error_handlers import register_error_handlers
        print("✓ utils")
    except Exception as e:
        print(f"✗ utils: {e}")
        return False
    
    try:
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
        print("✓ all routes")
    except Exception as e:
        print(f"✗ routes: {e}")
        return False
    
    return True


def test_app_creation():
    """Test that the Flask app can be created."""
    print("\nTesting app creation...")
    
    try:
        from app import create_app
        app = create_app()
        print("✓ Flask app created successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to create app: {e}")
        return False


if __name__ == '__main__':
    print("=" * 50)
    print("SIGE - System Verification Test")
    print("=" * 50)
    
    success = True
    
    if not test_imports():
        success = False
    
    if not test_app_creation():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✓ All tests passed! System is ready to run.")
        print("\nTo start the application:")
        print("  python init_db.py    (initialize database)")
        print("  python app.py        (start server)")
    else:
        print("✗ Some tests failed. Please fix the errors above.")
    print("=" * 50)
    
    sys.exit(0 if success else 1)
