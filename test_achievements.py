"""
Test script for the Achievement Engine.
Tests auto-award rules, manual awarding, and leaderboard.

Usage: python test_achievements.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models.achievement import Achievement, StudentAchievement
from models.grading import FinalGrade, AcademicPeriod
from models.attendance import Attendance
from models.observation import Observation
from models.academic import AcademicStudent, SubjectGrade, Grade, Subject
from models.user import User
from models.institution import Institution, Campus
from utils.achievement_engine import (
    check_and_award_achievements,
    award_achievement,
    get_student_achievements,
    get_leaderboard,
    ensure_seed_achievements,
    _check_superador,
    _check_excelencia,
    _check_asistencia_perfecta,
    _check_todo_terreno,
    _check_resiliente,
    _check_constancia,
    _check_companero,
    _get_student_periods,
)
from datetime import date, datetime, timedelta


def setup_test_data(app):
    """Create test institution, student, grades, etc."""
    with app.app_context():
        # Check if test institution already exists
        existing = Institution.query.filter_by(name='Test Achievement Institution').first()
        if existing:
            print(f"  Using existing institution (id={existing.id})")
            return existing.id

        # Create institution
        institution = Institution(
            name='Test Achievement Institution',
            nit='TEST_ACH_NIT'
        )
        db.session.add(institution)
        db.session.flush()

        # Create campus
        campus = Campus(
            institution_id=institution.id,
            name='Campus Principal',
            address='Test Address',
            is_main_campus=True
        )
        db.session.add(campus)
        db.session.flush()

        # Create user for student
        user = User(
            username='test_student_ach',
            email='test_ach@example.com',
            role='student',
            first_name='Test',
            last_name='Student',
            is_active=True
        )
        user.set_password('testpass123')
        db.session.add(user)
        db.session.flush()

        # Create grade
        grade = Grade(
            campus_id=campus.id,
            name='Test-1',
            academic_year='2026'
        )
        db.session.add(grade)
        db.session.flush()

        # Create academic student
        student = AcademicStudent(
            user_id=user.id,
            institution_id=institution.id,
            campus_id=campus.id,
            grade_id=grade.id,
            document_number='TEST001',
            status='activo'
        )
        db.session.add(student)
        db.session.flush()

        # Create periods
        period1 = AcademicPeriod(
            institution_id=institution.id,
            name='Periodo 1',
            short_name='P1',
            academic_year='2026',
            order=1,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 4, 30),
            is_active=False
        )
        period2 = AcademicPeriod(
            institution_id=institution.id,
            name='Periodo 2',
            short_name='P2',
            academic_year='2026',
            order=2,
            start_date=date(2026, 5, 1),
            end_date=date(2026, 7, 31),
            is_active=True
        )
        period3 = AcademicPeriod(
            institution_id=institution.id,
            name='Periodo 3',
            short_name='P3',
            academic_year='2026',
            order=3,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 10, 31),
            is_active=False
        )
        db.session.add_all([period1, period2, period3])
        db.session.flush()

        # Create a teacher user
        teacher = User(
            username='test_teacher_ach',
            email='teacher_ach@example.com',
            role='teacher',
            first_name='Test',
            last_name='Teacher',
            is_active=True
        )
        teacher.set_password('testpass123')
        db.session.add(teacher)
        db.session.flush()

        # Create subject
        subject = Subject(
            institution_id=institution.id,
            name='Matematicas',
            code='MAT_ACH_TEST'
        )
        db.session.add(subject)
        db.session.flush()

        # Create subject-grade
        sg = SubjectGrade(
            subject_id=subject.id,
            grade_id=grade.id,
            teacher_id=teacher.id
        )
        db.session.add(sg)
        db.session.flush()

        # Create final grades for period 1 (lower scores)
        fg1_p1 = FinalGrade(
            student_id=student.id,
            subject_grade_id=sg.id,
            period_id=period1.id,
            final_score=3.0,
            status='ganada'
        )
        db.session.add(fg1_p1)

        # Create final grades for period 2 (improved by 1+ point)
        fg1_p2 = FinalGrade(
            student_id=student.id,
            subject_grade_id=sg.id,
            period_id=period2.id,
            final_score=4.2,
            status='ganada'
        )
        db.session.add(fg1_p2)

        # Create attendance records for period 2 (all present)
        for day in range(1, 11):
            att = Attendance(
                student_id=student.id,
                subject_grade_id=sg.id,
                date=date(2026, 5, day),
                status='presente',
                recorded_by=teacher.id
            )
            db.session.add(att)

        # Create a positive observation
        obs = Observation(
            student_id=student.id,
            author_id=teacher.id,
            type='positiva',
            category='Valores',
            description='Excelente companerismo en clase'
        )
        db.session.add(obs)

        db.session.commit()

        # Ensure seed achievements
        ensure_seed_achievements(institution.id)

        print(f"  Created test data: institution={institution.id}, student={student.id}")
        print(f"  Periods: P1={period1.id}, P2={period2.id}, P3={period3.id}")
        print(f"  SubjectGrade={sg.id}, Teacher={teacher.id}")

        return institution.id


def test_engine_rules(app, institution_id):
    """Test individual achievement engine rules."""
    with app.app_context():
        print("\n" + "=" * 60)
        print("TESTING INDIVIDUAL ENGINE RULES")
        print("=" * 60)

        student = AcademicStudent.query.filter_by(
            institution_id=institution_id,
            document_number='TEST001'
        ).first()
        if not student:
            print("  ERROR: Student not found")
            return

        periods = _get_student_periods(student.id)
        print(f"\n  Student: {student.id}, Periods found: {len(periods)}")

        if len(periods) >= 2:
            p1, p2 = periods[0], periods[1]

            # Test Superador (improved 1+ point)
            result = _check_superador(student.id, p2)
            print(f"\n  [Superador] Improved 1+ point in P2: {'PASS' if result else 'FAIL'}")

            # Test Excelencia (>= 4.5)
            # Our test data has 4.2, so this should be False
            result = _check_excelencia(student.id, p2)
            print(f"  [Excelencia] Grade >= 4.5 in P2 (score=4.2): {'FAIL (expected False)' if not result else 'UNEXPECTED PASS'}")

            # Test Asistencia Perfecta
            result = _check_asistencia_perfecta(student.id, p2)
            print(f"  [Asistencia Perfecta] 0 absences in P2: {'PASS' if result else 'FAIL'}")

            # Test Todo Terreno (all subjects passed)
            result = _check_todo_terreno(student.id, p2)
            print(f"  [Todo Terreno] All subjects passed in P2: {'PASS' if result else 'FAIL'}")

            # Test Companero (positive observation)
            result = _check_companero(student.id)
            print(f"  [Companero] Has positive observation: {'PASS' if result else 'FAIL'}")

            # Test Constancia (needs 3 periods with avg >= 4.0)
            # We only have grades for P1 and P2, so P3 has none
            result = _check_constancia(student.id, p2)
            print(f"  [Constancia] 3 periods >= 4.0 at P2: {'FAIL (expected - only 2 periods with data)' if not result else 'UNEXPECTED PASS'}")

            # Test Resiliente (recovered a failed subject)
            # We don't have failed subjects in test data
            result = _check_resiliente(student.id, p2)
            print(f"  [Resiliente] Recovered failed subject at P2: {'FAIL (expected - no failed subjects)' if not result else 'UNEXPECTED PASS'}")


def test_auto_award(app, institution_id):
    """Test the auto-award engine."""
    with app.app_context():
        print("\n" + "=" * 60)
        print("TESTING AUTO-AWARD ENGINE")
        print("=" * 60)

        student = AcademicStudent.query.filter_by(
            institution_id=institution_id,
            document_number='TEST001'
        ).first()
        if not student:
            print("  ERROR: Student not found")
            return

        # Clear existing achievements for clean test
        StudentAchievement.query.filter_by(student_id=student.id).delete()
        db.session.commit()

        # Run auto-award for P2
        newly_awarded = check_and_award_achievements(student.id, period_id=None)

        print(f"\n  Newly awarded achievements: {len(newly_awarded)}")
        for item in newly_awarded:
            print(f"    - {item['achievement'].name} ({item['achievement'].icon})")

        # Get all achievements for student
        all_achievements = get_student_achievements(student.id)
        print(f"\n  Total achievements for student: {len(all_achievements)}")
        for sa in all_achievements:
            print(f"    - {sa.achievement.name} | {sa.earned_at.strftime('%Y-%m-%d %H:%M')}")


def test_manual_award(app, institution_id):
    """Test manual achievement awarding."""
    with app.app_context():
        print("\n" + "=" * 60)
        print("TESTING MANUAL AWARD")
        print("=" * 60)

        student = AcademicStudent.query.filter_by(
            institution_id=institution_id,
            document_number='TEST001'
        ).first()
        if not student:
            print("  ERROR: Student not found")
            return

        # Find an achievement to award
        ach = Achievement.query.filter_by(
            institution_id=institution_id,
            name='Excelencia'
        ).first()

        if ach:
            # Award it
            result = award_achievement(ach.id, student.id)
            if result:
                print(f"\n  PASS: Manually awarded '{ach.name}' to student")
            else:
                print(f"\n  FAIL: Could not award '{ach.name}' (may already exist)")

            # Try duplicate
            result2 = award_achievement(ach.id, student.id)
            if result2 is None:
                print(f"  PASS: Duplicate correctly prevented for '{ach.name}'")
            else:
                print(f"  FAIL: Duplicate was not prevented")


def test_leaderboard(app, institution_id):
    """Test leaderboard generation."""
    with app.app_context():
        print("\n" + "=" * 60)
        print("TESTING LEADERBOARD")
        print("=" * 60)

        leaderboard = get_leaderboard(institution_id, limit=10)

        print(f"\n  Leaderboard entries: {len(leaderboard)}")
        for i, entry in enumerate(leaderboard):
            print(f"    {i+1}. {entry['student_name']} - {entry['achievement_count']} achievements")


def test_achievement_seeds(app, institution_id):
    """Verify all seed achievements exist."""
    with app.app_context():
        print("\n" + "=" * 60)
        print("TESTING SEED ACHIEVEMENTS")
        print("=" * 60)

        achievements = Achievement.query.filter_by(
            institution_id=institution_id,
            is_active=True
        ).all()

        print(f"\n  Total achievements: {len(achievements)}")
        for ach in achievements:
            print(f"    {ach.icon} {ach.name} | {ach.category} | criteria: {ach.criteria}")

        expected = ['Superador', 'Excelencia', 'Asistencia Perfecta', 'Todo Terreno',
                    'Resiliente', 'Constancia', 'Compa\u00f1ero']
        found_names = [a.name for a in achievements]

        for name in expected:
            if name in found_names:
                print(f"  PASS: '{name}' exists")
            else:
                print(f"  FAIL: '{name}' missing")


def main():
    """Main test runner."""
    print("=" * 60)
    print("ACHIEVEMENT ENGINE TEST SUITE")
    print("=" * 60)

    app = create_app('development')

    # Setup test data
    print("\n[1/5] Setting up test data...")
    institution_id = setup_test_data(app)

    # Test seeds
    print("\n[2/5] Verifying seed achievements...")
    test_achievement_seeds(app, institution_id)

    # Test individual rules
    print("\n[3/5] Testing individual engine rules...")
    test_engine_rules(app, institution_id)

    # Test auto-award
    print("\n[4/5] Testing auto-award engine...")
    test_auto_award(app, institution_id)

    # Test manual award
    print("\n[5/5] Testing manual award and leaderboard...")
    test_manual_award(app, institution_id)
    test_leaderboard(app, institution_id)

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)


if __name__ == '__main__':
    main()
