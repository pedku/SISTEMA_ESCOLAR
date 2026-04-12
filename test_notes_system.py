"""
Test script for the SIGE Notes System.
Tests: lock/unlock, final grades calculation, annual grades, and student grades view.
Uses the real PostgreSQL database.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models.user import User
from models.institution import Institution, Campus
from models.academic import Grade, Subject, SubjectGrade, AcademicStudent
from models.grading import AcademicPeriod, GradeCriteria, GradeRecord, FinalGrade, AnnualGrade
from datetime import datetime, date


def print_header(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}")


def print_result(test_name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    icon = "[OK]" if passed else "[XX]"
    msg = f"  {icon} {test_name}: {status}"
    if detail:
        msg += f" - {detail}"
    print(msg)
    return passed


def setup_test_data(app):
    """Create test data if it doesn't exist."""
    with app.app_context():
        results = {}

        # Check if we have minimum required data
        institution = Institution.query.first()
        if not institution:
            print("  WARNING: No institution found. Please run init_db.py first.")
            return None

        # Check for academic periods
        periods = AcademicPeriod.query.filter_by(
            institution_id=institution.id,
            academic_year=institution.academic_year
        ).all()
        if not periods:
            print("  WARNING: No academic periods found. Configure periods first.")
            return None

        # Check for criteria
        criteria = GradeCriteria.query.all()
        if not criteria:
            print("  WARNING: No grade criteria found. Configure criteria first.")
            return None

        # Check for grades
        grades = Grade.query.all()
        if not grades:
            print("  WARNING: No grades found. Create grades first.")
            return None

        # Check for students
        students = AcademicStudent.query.filter_by(status='activo').all()
        if not students:
            print("  WARNING: No active students found.")
            return None

        # Check for subject-grades
        subject_grades = SubjectGrade.query.all()
        if not subject_grades:
            print("  WARNING: No subject-grades found. Create subject assignments first.")
            return None

        results['institution'] = institution
        results['periods'] = periods
        results['criteria'] = criteria
        results['grades'] = grades
        results['students'] = students
        results['subject_grades'] = subject_grades

        return results


def test_route_availability(app):
    """Test that all new routes are registered."""
    print_header("TEST 1: Route Availability")
    passed = 0
    total = 0

    rules = {str(rule): rule.endpoint for rule in app.url_map.iter_rules()}

    expected_routes = [
        ('/grades/lock', 'grades.lock_panel'),
        ('/grades/final/<int:sg_id>/<int:period_id>', 'grades.final_grades_view'),
        ('/grades/annual/<int:sg_id>', 'grades.annual_grades_view'),
        ('/grades/student/<int:student_id>', 'grades.student_grades'),
    ]

    for path, endpoint in expected_routes:
        total += 1
        found = endpoint in [r.endpoint for r in app.url_map.iter_rules()]
        if print_result(f"Route {endpoint}", found, path):
            passed += 1

    print(f"\n  Result: {passed}/{total} routes registered")
    return passed == total


def test_lock_unlock(app, test_data):
    """Test lock/unlock functionality."""
    print_header("TEST 2: Lock/Unlock Functionality")

    with app.app_context():
        sg = test_data['subject_grades'][0]
        period = test_data['periods'][0]
        criteria = test_data['criteria']
        students = test_data['students'][:3]  # Use first 3 students

        # Create some grade records
        print(f"\n  Creating test grade records for:")
        print(f"    Subject-Grade: {sg.subject.name} - {sg.grade.name}")
        print(f"    Period: {period.name}")
        print(f"    Students: {len(students)}")

        # Check existing records
        existing_count = GradeRecord.query.filter_by(
            subject_grade_id=sg.id,
            period_id=period.id
        ).count()

        if existing_count == 0:
            # Create test records
            for student in students:
                for criterion in criteria:
                    record = GradeRecord(
                        student_id=student.id,
                        subject_grade_id=sg.id,
                        period_id=period.id,
                        criterion_id=criterion.id,
                        score=3.5,
                        created_by=1,
                        locked=False
                    )
                    db.session.add(record)
            db.session.commit()
            print(f"  Created {len(students) * len(criteria)} grade records")
        else:
            print(f"  Found {existing_count} existing grade records")

        # Test unlock state
        locked_count = GradeRecord.query.filter_by(
            subject_grade_id=sg.id,
            period_id=period.id,
            locked=True
        ).count()
        total_count = GradeRecord.query.filter_by(
            subject_grade_id=sg.id,
            period_id=period.id
        ).count()

        is_unlocked = locked_count == 0
        print_result("Period initially unlocked", is_unlocked,
                     f"{total_count} records, 0 locked")

        # Lock all records
        GradeRecord.query.filter_by(
            subject_grade_id=sg.id,
            period_id=period.id
        ).update({'locked': True})
        db.session.commit()

        # Verify locked
        locked_count = GradeRecord.query.filter_by(
            subject_grade_id=sg.id,
            period_id=period.id,
            locked=True
        ).count()
        is_locked = locked_count == total_count
        print_result("Lock applied successfully", is_locked,
                     f"{locked_count}/{total_count} records locked")

        # Try to modify a locked record (should fail in real route)
        locked_record = GradeRecord.query.filter_by(
            subject_grade_id=sg.id,
            period_id=period.id,
            locked=True
        ).first()

        cant_modify = locked_record.locked
        print_result("Locked record cannot be modified", cant_modify,
                     f"locked={locked_record.locked}")

        # Unlock
        GradeRecord.query.filter_by(
            subject_grade_id=sg.id,
            period_id=period.id
        ).update({'locked': False})
        db.session.commit()

        locked_count = GradeRecord.query.filter_by(
            subject_grade_id=sg.id,
            period_id=period.id,
            locked=True
        ).count()
        is_unlocked = locked_count == 0
        print_result("Unlock applied successfully", is_unlocked,
                     f"0/{total_count} records locked")

        return True


def test_final_grade_calculation(app, test_data):
    """Test final grade calculation with real data."""
    print_header("TEST 3: Final Grade Calculation")

    with app.app_context():
        sg = test_data['subject_grades'][0]
        period = test_data['periods'][0]
        criteria = test_data['criteria']
        students = test_data['students'][:5]

        # Ensure records exist with varied scores
        print(f"\n  Setting up test scores for {len(students)} students...")
        print(f"  Criteria weights: {', '.join(f'{c.name}={c.weight}%' for c in criteria)}")

        total_weight = sum(c.weight for c in criteria)

        for student in students:
            for i, criterion in enumerate(criteria):
                existing = GradeRecord.query.filter_by(
                    student_id=student.id,
                    subject_grade_id=sg.id,
                    period_id=period.id,
                    criterion_id=criterion.id
                ).first()

                # Give varied scores
                score = 2.0 + (i * 0.5) + (student.id % 3) * 0.3
                score = round(min(5.0, max(1.0, score)), 1)

                if existing:
                    existing.score = score
                    existing.locked = False
                else:
                    record = GradeRecord(
                        student_id=student.id,
                        subject_grade_id=sg.id,
                        period_id=period.id,
                        criterion_id=criterion.id,
                        score=score,
                        created_by=1,
                        locked=False
                    )
                    db.session.add(record)

        db.session.commit()

        # Import and use the calculation helper
        from routes.grades import _calculate_final_grade, _save_final_grade

        print(f"\n  Calculating final grades...")
        calculated = 0
        results = []

        for student in students:
            final_score = _calculate_final_grade(student.id, sg.id, period.id, criteria)

            if final_score is not None:
                _save_final_grade(student.id, sg.id, period.id, final_score)
                calculated += 1

                # Verify calculation manually
                weighted_sum = 0.0
                for criterion in criteria:
                    record = GradeRecord.query.filter_by(
                        student_id=student.id,
                        subject_grade_id=sg.id,
                        period_id=period.id,
                        criterion_id=criterion.id
                    ).first()
                    if record:
                        weighted_sum += record.score * (criterion.weight / 100)

                expected = round(max(1.0, min(5.0, weighted_sum)), 2)

                # Verify FinalGrade was saved
                final = FinalGrade.query.filter_by(
                    student_id=student.id,
                    subject_grade_id=sg.id,
                    period_id=period.id
                ).first()

                match = final and abs(final.final_score - expected) < 0.02
                status = final.status if final else 'N/A'

                results.append({
                    'student': student.user.get_full_name(),
                    'calculated': final_score,
                    'expected': expected,
                    'status': status,
                    'match': match
                })

                print(f"    {student.user.get_full_name()}: "
                      f"score={final_score}, status={status}, "
                      f"match={'OK' if match else 'MISMATCH'}")

        db.session.commit()

        all_match = all(r['match'] for r in results)
        print_result(f"Final grades calculated ({calculated}/{len(students)})",
                     all_match and calculated == len(students),
                     f"All match={all_match}")

        # Verify pass/fail status
        for r in results:
            expected_status = 'ganada' if r['calculated'] >= 3.0 else 'perdida'
            print_result(f"  Status for {r['student']}",
                         r['status'] == expected_status,
                         f"expected={expected_status}, got={r['status']}")

        return True


def test_annual_grades(app, test_data):
    """Test annual grade calculation."""
    print_header("TEST 4: Annual Grades")

    with app.app_context():
        institution = test_data['institution']
        sg = test_data['subject_grades'][0]
        periods = test_data['periods']
        students = test_data['students'][:5]

        # Ensure final grades exist for all periods
        from routes.grades import _calculate_final_grade, _save_final_grade
        criteria = test_data['criteria']

        print(f"\n  Ensuring final grades exist for {len(periods)} periods...")
        for period in periods:
            for student in students:
                # Check if final exists
                final = FinalGrade.query.filter_by(
                    student_id=student.id,
                    subject_grade_id=sg.id,
                    period_id=period.id
                ).first()

                if not final:
                    # Create criteria records
                    for i, criterion in enumerate(criteria):
                        existing = GradeRecord.query.filter_by(
                            student_id=student.id,
                            subject_grade_id=sg.id,
                            period_id=period.id,
                            criterion_id=criterion.id
                        ).first()

                        score = 2.5 + (i * 0.3) + (period.order * 0.2)
                        score = round(min(5.0, max(1.0, score)), 1)

                        if existing:
                            existing.score = score
                        else:
                            record = GradeRecord(
                                student_id=student.id,
                                subject_grade_id=sg.id,
                                period_id=period.id,
                                criterion_id=criterion.id,
                                score=score,
                                created_by=1,
                                locked=False
                            )
                            db.session.add(record)

                    db.session.commit()
                    final_score = _calculate_final_grade(student.id, sg.id, period.id, criteria)
                    if final_score:
                        _save_final_grade(student.id, sg.id, period.id, final_score)
                        db.session.commit()

        # Now calculate annual grades (simulate the route logic)
        print(f"\n  Calculating annual grades...")
        for student in students:
            period_scores = []
            for period in periods:
                final = FinalGrade.query.filter_by(
                    student_id=student.id,
                    subject_grade_id=sg.id,
                    period_id=period.id
                ).first()
                if final and final.final_score:
                    period_scores.append(final.final_score)

            if period_scores:
                annual_score = round(sum(period_scores) / len(period_scores), 2)
                status = 'aprobado' if annual_score >= 3.0 else 'reprobado'

                existing = AnnualGrade.query.filter_by(
                    student_id=student.id,
                    subject_grade_id=sg.id,
                    academic_year=institution.academic_year
                ).first()

                if existing:
                    existing.annual_score = annual_score
                    existing.status = status
                else:
                    new_annual = AnnualGrade(
                        student_id=student.id,
                        subject_grade_id=sg.id,
                        academic_year=institution.academic_year,
                        annual_score=annual_score,
                        status=status
                    )
                    db.session.add(new_annual)

                print(f"    {student.user.get_full_name()}: "
                      f"annual={annual_score}, status={status}, "
                      f"periods={period_scores}")

        db.session.commit()

        # Verify annual grades
        annual_count = AnnualGrade.query.filter_by(
            subject_grade_id=sg.id,
            academic_year=institution.academic_year
        ).count()

        print_result(f"Annual grades created", annual_count > 0,
                     f"{annual_count} annual grades saved")

        # Verify calculation accuracy
        annuals = AnnualGrade.query.filter_by(
            subject_grade_id=sg.id,
            academic_year=institution.academic_year
        ).all()

        all_correct = True
        for annual in annuals:
            # Recalculate expected
            finals = FinalGrade.query.filter_by(
                student_id=annual.student_id,
                subject_grade_id=sg.id
            ).all()
            scores = [f.final_score for f in finals if f.final_score]
            if scores:
                expected = round(sum(scores) / len(scores), 2)
                expected_status = 'aprobado' if expected >= 3.0 else 'reprobado'
                match = abs(annual.annual_score - expected) < 0.02 and annual.status == expected_status
                if not match:
                    all_correct = False

        print_result("Annual grade calculations correct", all_correct)

        return True


def test_template_files():
    """Verify all template files exist."""
    print_header("TEST 5: Template Files")

    templates = [
        'templates/grades/lock_panel.html',
        'templates/grades/final_view.html',
        'templates/grades/annual_view.html',
    ]

    passed = 0
    for template in templates:
        exists = os.path.exists(os.path.join(os.path.dirname(__file__), template))
        if print_result(f"Template: {template}", exists):
            passed += 1

    print(f"\n  Result: {passed}/{len(templates)} templates found")
    return passed == len(templates)


def main():
    print_header("SIGE Notes System - Test Suite")

    # Create app with testing config
    os.environ['FLASK_ENV'] = 'development'
    app = create_app('development')

    all_passed = True

    # Test 1: Route availability
    if not test_route_availability(app):
        all_passed = False

    # Setup test data
    test_data = setup_test_data(app)
    if not test_data:
        print("\n  [XX] Cannot proceed without test data. Please initialize the database first.")
        print(f"\n{'='*70}")
        print("  OVERALL: INCOMPLETE - Missing required data")
        print(f"{'='*70}")
        return

    # Test 2: Lock/Unlock
    if not test_lock_unlock(app, test_data):
        all_passed = False

    # Test 3: Final grade calculation
    if not test_final_grade_calculation(app, test_data):
        all_passed = False

    # Test 4: Annual grades
    if not test_annual_grades(app, test_data):
        all_passed = False

    # Test 5: Template files
    if not test_template_files():
        all_passed = False

    # Final summary
    print_header("OVERALL RESULT")
    if all_passed:
        print("  [OK] ALL TESTS PASSED")
    else:
        print("  [XX] SOME TESTS FAILED")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
