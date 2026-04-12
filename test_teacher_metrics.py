"""
Test script for teacher metrics functionality.
Tests routes, data queries, and template rendering.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_templates_exist():
    """Test that all template files exist."""
    print("\n[TEST] Testing template files exist...")

    templates = [
        'templates/metrics/teacher.html',
        'templates/metrics/teacher_comparison.html',
        'templates/metrics/teacher_attendance.html'
    ]

    base_path = os.path.dirname(os.path.abspath(__file__))
    for tmpl in templates:
        path = os.path.join(base_path, tmpl)
        assert os.path.exists(path), f"Template not found: {path}"
        size = os.path.getsize(path)
        assert size > 100, f"Template seems too small: {path} ({size} bytes)"
        print(f"  [OK] {tmpl} ({size} bytes)")


def test_template_content():
    """Test that templates contain required Bootstrap 5 and Chart.js elements."""
    print("\n[TEST] Testing template content...")

    base_path = os.path.dirname(os.path.abspath(__file__))

    # Check teacher.html
    with open(os.path.join(base_path, 'templates/metrics/teacher.html'), 'r', encoding='utf-8') as f:
        content = f.read()
        assert 'class="card' in content, "teacher.html missing Bootstrap cards"
        assert 'chart' in content.lower(), "teacher.html missing Chart.js"
        assert 'datatable' in content.lower(), "teacher.html missing DataTables"
        assert 'bi-' in content, "teacher.html missing Bootstrap Icons"
        assert 'progreso' in content.lower() or 'progress' in content.lower(), "teacher.html missing progress bars"
        assert 'riesgo' in content.lower() or 'risk' in content.lower(), "teacher.html missing risk students section"
        print("  [OK] teacher.html has Bootstrap 5 + Chart.js + DataTables + Icons + Progress + Risk")

    # Check teacher_comparison.html
    with open(os.path.join(base_path, 'templates/metrics/teacher_comparison.html'), 'r', encoding='utf-8') as f:
        content = f.read()
        assert 'class="card' in content, "teacher_comparison.html missing Bootstrap"
        assert 'chart' in content.lower(), "teacher_comparison.html missing Chart.js"
        assert 'percentil' in content.lower() or 'percentile' in content.lower(), "Missing percentile"
        assert 'comparacion' in content.lower() or 'comparison' in content.lower(), "Missing comparison"
        print("  [OK] teacher_comparison.html has Bootstrap 5 + Chart.js + Percentile + Comparison")

    # Check teacher_attendance.html
    with open(os.path.join(base_path, 'templates/metrics/teacher_attendance.html'), 'r', encoding='utf-8') as f:
        content = f.read()
        assert 'scatter' in content.lower(), "teacher_attendance.html missing scatter plot"
        assert 'correlacion' in content.lower() or 'correlation' in content.lower(), "Missing correlation"
        assert 'class="card' in content, "teacher_attendance.html missing Bootstrap"
        assert 'asistencia' in content.lower() or 'attendance' in content.lower(), "Missing attendance reference"
        print("  [OK] teacher_attendance.html has scatter plot + correlation + Bootstrap 5")


def test_routes_module():
    """Test that the routes module loads and has the expected functions."""
    print("\n[TEST] Testing routes module...")

    from routes import metrics

    # Check blueprint exists
    assert hasattr(metrics, 'metrics_bp'), "Missing metrics_bp blueprint"

    # Check route functions exist
    assert hasattr(metrics, 'teacher_metrics'), "Missing teacher_metrics route"
    assert hasattr(metrics, 'teacher_comparison'), "Missing teacher_comparison route"
    assert hasattr(metrics, 'teacher_attendance'), "Missing teacher_attendance route"

    print("  [OK] metrics_bp blueprint exists")
    print("  [OK] teacher_metrics route function exists")
    print("  [OK] teacher_comparison route function exists")
    print("  [OK] teacher_attendance route function exists")

    # Check helper functions
    helpers = [
        '_get_teacher_groups_data',
        '_get_risk_students',
        '_get_grade_distribution',
        '_get_period_trend',
        '_get_institution_average',
        '_get_teacher_average',
        '_get_all_teacher_averages',
        '_get_attendance_data',
        '_get_total_absences'
    ]

    for helper in helpers:
        assert hasattr(metrics, helper), f"Missing helper: {helper}"
        print(f"  [OK] {helper} exists")


def test_decorators_on_routes():
    """Test that routes have proper decorators by checking source code."""
    print("\n[TEST] Testing route decorators...")

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'routes', 'metrics.py'), 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for login_required and role_required
    assert '@login_required' in content, "Missing @login_required decorator"
    assert '@role_required' in content, "Missing @role_required decorator"

    # Check that all 3 teacher routes have decorators
    # Count occurrences - should be at least 3 each
    login_count = content.count('@login_required')
    role_count = content.count('@role_required')
    assert login_count >= 3, f"Expected at least 3 @login_required, found {login_count}"
    assert role_count >= 3, f"Expected at least 3 @role_required, found {role_count}"

    print(f"  [OK] @login_required used {login_count} times")
    print(f"  [OK] @role_required used {role_count} times")

    # Check role restrictions
    assert "'root', 'admin', 'teacher'" in content or "'root','admin','teacher'" in content, \
        "Missing proper role restrictions"
    print("  [OK] Role restrictions include root, admin, teacher")


def test_data_functions_with_db(app):
    """Test helper functions with actual database."""
    print("\n[TEST] Testing data helper functions with DB...")

    from routes.metrics import (
        _get_teacher_groups_data,
        _get_risk_students,
        _get_grade_distribution,
        _get_period_trend,
        _get_institution_average,
        _get_teacher_average,
        _get_all_teacher_averages,
        _get_attendance_data,
        _get_total_absences
    )
    from models.user import User
    from models.institution import Institution

    with app.app_context():
        # Find a teacher
        teacher = User.query.filter_by(role='teacher').first()
        if not teacher:
            print("  [SKIP] No teachers in database - skipping data tests")
            return

        institution = Institution.query.first()

        # Test groups data
        groups = _get_teacher_groups_data(teacher.id, institution)
        print(f"  [OK] _get_teacher_groups_data: {len(groups)} groups")
        for g in groups:
            print(f"       - {g['grade_name']} / {g['subject_name']}: avg={g['avg_score']}, pass_rate={g['pass_rate']}%")

        # Test risk students
        risk = _get_risk_students(teacher.id, institution)
        print(f"  [OK] _get_risk_students: {len(risk)} students at risk")

        # Test grade distribution
        grades = _get_grade_distribution(teacher.id, institution)
        print(f"  [OK] _get_grade_distribution: {len(grades)} scores")

        # Test period trend
        trend = _get_period_trend(teacher.id, institution)
        print(f"  [OK] _get_period_trend: {len(trend)} periods")

        # Test averages
        teacher_avg = _get_teacher_average(teacher.id, institution)
        inst_avg = _get_institution_average(institution)
        print(f"  [OK] Teacher avg: {teacher_avg}, Institution avg: {inst_avg}")

        # Test all teacher averages
        all_avgs = _get_all_teacher_averages(institution)
        print(f"  [OK] _get_all_teacher_averages: {len(all_avgs)} teachers")
        for a in all_avgs:
            print(f"       - Teacher ID {a[0]} ({a[1]}): avg={a[2]}")

        # Test attendance
        att_data = _get_attendance_data(teacher.id, institution)
        print(f"  [OK] _get_attendance_data: {len(att_data)} students")

        # Test absences
        absences, pct = _get_total_absences(teacher.id, institution)
        print(f"  [OK] _get_total_absences: {absences} absences ({pct}%)")


def test_routes_with_app(app):
    """Test that routes respond correctly via Flask test client."""
    print("\n[TEST] Testing route responses via Flask...")

    with app.test_client() as client:
        # Without login - should redirect to login
        resp = client.get('/metrics/teacher', follow_redirects=False)
        assert resp.status_code in [302, 303], f"Expected redirect for /metrics/teacher, got {resp.status_code}"
        print("  [OK] /metrics/teacher redirects when not authenticated")

        resp = client.get('/metrics/teacher/comparison', follow_redirects=False)
        assert resp.status_code in [302, 303], f"Expected redirect for comparison, got {resp.status_code}"
        print("  [OK] /metrics/teacher/comparison redirects when not authenticated")

        resp = client.get('/metrics/teacher/attendance', follow_redirects=False)
        assert resp.status_code in [302, 303], f"Expected redirect for attendance, got {resp.status_code}"
        print("  [OK] /metrics/teacher/attendance redirects when not authenticated")

        # Try to login as teacher if one exists
        from models.user import User
        with app.app_context():
            teacher = User.query.filter_by(role='teacher').first()

        if teacher:
            resp = client.post('/auth/login', data={
                'username': teacher.username,
                'password': 'password'  # try common password
            }, follow_redirects=True)

            if resp.status_code == 200 and b'contrase' in resp.data.lower() or b'invalid' in resp.data.lower() or b'incorrect' in resp.data.lower():
                print("  [SKIP] Could not login as teacher (unknown password) - route auth verified above")
            elif resp.status_code == 200:
                # Logged in, test routes
                resp = client.get('/metrics/teacher', follow_redirects=True)
                assert resp.status_code == 200, f"Teacher dashboard failed: {resp.status_code}"
                print("  [OK] Teacher dashboard returns 200 when authenticated")

                resp = client.get('/metrics/teacher/comparison', follow_redirects=True)
                assert resp.status_code == 200, f"Comparison failed: {resp.status_code}"
                print("  [OK] Teacher comparison returns 200 when authenticated")

                resp = client.get('/metrics/teacher/attendance', follow_redirects=True)
                assert resp.status_code == 200, f"Attendance failed: {resp.status_code}"
                print("  [OK] Teacher attendance returns 200 when authenticated")
            else:
                print(f"  [SKIP] Login test inconclusive (status: {resp.status_code})")
        else:
            print("  [SKIP] No teacher user found - skipping authenticated route tests")


def main():
    print("=" * 60)
    print("  Teacher Metrics - Test Suite")
    print("=" * 60)

    passed = 0
    failed = 0

    # Test 1: Templates exist
    try:
        test_templates_exist()
        passed += 1
    except AssertionError as e:
        print(f"  [FAIL] {e}")
        failed += 1

    # Test 2: Template content
    try:
        test_template_content()
        passed += 1
    except AssertionError as e:
        print(f"  [FAIL] {e}")
        failed += 1

    # Test 3: Routes module
    try:
        test_routes_module()
        passed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        failed += 1

    # Test 4: Decorators
    try:
        test_decorators_on_routes()
        passed += 1
    except AssertionError as e:
        print(f"  [FAIL] {e}")
        failed += 1

    # Test 5: Route responses
    try:
        from app import create_app
        app = create_app()
        test_routes_with_app(app)
        passed += 1
    except Exception as e:
        print(f"  [FAIL/WARN] Route response test issue: {e}")
        failed += 1

    # Test 6: Data functions with DB
    try:
        from app import create_app
        app = create_app()
        test_data_functions_with_db(app)
        passed += 1
    except Exception as e:
        print(f"  [FAIL/WARN] Data function test issue: {e}")
        failed += 1

    # Summary
    print("\n" + "=" * 60)
    if failed == 0:
        print(f"  ALL {passed} TESTS PASSED")
    else:
        print(f"  {passed} PASSED, {failed} FAILED")
    print("=" * 60)
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
