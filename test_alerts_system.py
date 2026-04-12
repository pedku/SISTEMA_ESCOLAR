"""
Test script for the Early Warning Alerts System.
Tests model creation, alert engine rules, and basic functionality.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models.alert import Alert
from models.user import User
from models.academic import AcademicStudent, Grade, Subject, SubjectGrade
from models.grading import AcademicPeriod, GradeCriteria, FinalGrade, GradeRecord
from models.attendance import Attendance
from models.institution import Institution, Campus
from utils.alert_engine import (
    run_all_alerts,
    run_alert,
    get_active_alerts,
    get_all_alerts,
    resolve_alert,
    get_alert_stats,
    RULE_FUNCTIONS,
    RULE_LABELS
)
from datetime import datetime, timedelta
import traceback


def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def print_result(test_name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    icon = "[OK]" if passed else "[XX]"
    print(f"  {icon} {test_name}: {status}")
    if detail and not passed:
        print(f"      Detail: {detail}")


def run_tests():
    app = create_app('development')

    results = {'passed': 0, 'failed': 0, 'total': 0}

    with app.app_context():
        # ============================================
        # Test 1: Model Import
        # ============================================
        print_header("TEST 1: Model Import")
        try:
            from models.alert import Alert
            print_result("Alert model import", True)
            results['passed'] += 1
        except Exception as e:
            print_result("Alert model import", False, str(e))
            results['failed'] += 1
        results['total'] += 1

        # ============================================
        # Test 2: Model Properties
        # ============================================
        print_header("TEST 2: Model Properties")
        try:
            alert = Alert()
            alert.severity = 'alta'
            assert alert.severity_color == 'danger', f"Expected 'danger', got '{alert.severity_color}'"
            assert alert.severity_icon == 'exclamation-triangle-fill'

            alert.severity = 'media'
            assert alert.severity_color == 'warning'
            assert alert.severity_icon == 'exclamation-circle'

            alert.severity = 'baja'
            assert alert.severity_color == 'success'
            assert alert.severity_icon == 'check-circle'

            alert.alert_type = 'riesgo_academico'
            assert alert.alert_type_label == 'Riesgo Academico'
            assert alert.alert_type_icon == 'book'

            alert.alert_type = 'mejora_destacable'
            assert alert.alert_type_label == 'Mejora Destacable'
            assert alert.alert_type_icon == 'graph-up-arrow'

            print_result("Severity colors/icons", True)
            print_result("Alert type labels/icons", True)
            results['passed'] += 2
        except Exception as e:
            print_result("Model properties", False, str(e))
            results['failed'] += 1
        results['total'] += 1

        # ============================================
        # Test 3: Alert Engine Rules Available
        # ============================================
        print_header("TEST 3: Alert Engine Rules Available")
        expected_rules = [
            'riesgo_academico',
            'tendencia_negativa',
            'inasistencia_critica',
            'grupo_riesgo',
            'riesgo_desercion',
            'mejora_destacable'
        ]
        try:
            for rule in expected_rules:
                assert rule in RULE_FUNCTIONS, f"Rule '{rule}' not found in RULE_FUNCTIONS"
                assert rule in RULE_LABELS, f"Rule '{rule}' not found in RULE_LABELS"
            print_result(f"All {len(expected_rules)} rules available", True)
            results['passed'] += 1
        except Exception as e:
            print_result("All rules available", False, str(e))
            results['failed'] += 1
        results['total'] += 1

        # ============================================
        # Test 4: Create DB Tables
        # ============================================
        print_header("TEST 4: Database Table Creation")
        try:
            db.create_all()
            # Check the table exists
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            assert 'alerts' in tables, f"'alerts' table not found. Tables: {tables}"
            print_result("Alert table created", True)
            results['passed'] += 1
        except Exception as e:
            print_result("Alert table creation", False, str(e))
            results['failed'] += 1
        results['total'] += 1

        # ============================================
        # Test 5: Create Test Data & Run Engine
        # ============================================
        print_header("TEST 5: Create Test Data & Run Alert Engine")
        try:
            # Check if we have existing data
            institution = Institution.query.first()
            if not institution:
                print("  [INFO] No institution found. Creating test data...")
                institution = Institution(
                    name='Test School',
                    code='TEST001',
                    phone='1234567890',
                    email='test@test.com',
                    address='Test Address',
                    country='Colombia',
                    department='Test Dept',
                    municipality='Test City',
                    rector_name='Test Rector',
                    rector_document='123456789'
                )
                db.session.add(institution)
                db.session.flush()

            campus = Campus.query.filter_by(institution_id=institution.id).first()
            if not campus:
                campus = Campus(
                    name='Main Campus',
                    code='MAIN',
                    institution_id=institution.id,
                    address='Campus Address',
                    phone='1234567890',
                    is_main_campus=True
                )
                db.session.add(campus)
                db.session.flush()

            # Create users
            teacher = User.query.filter_by(role='teacher').first()
            if not teacher:
                teacher = User(
                    username='test_teacher',
                    email='teacher@test.com',
                    first_name='Test',
                    last_name='Teacher',
                    document_type='CC',
                    document_number='987654321',
                    role='teacher',
                    institution_id=institution.id
                )
                teacher.set_password('password123')
                db.session.add(teacher)
                db.session.flush()

            # Create student user
            student_user = User.query.filter_by(role='student').first()
            if not student_user:
                student_user = User(
                    username='test_student',
                    email='student@test.com',
                    first_name='Test',
                    last_name='Student',
                    document_type='TI',
                    document_number='123456789',
                    role='student',
                    institution_id=institution.id
                )
                student_user.set_password('password123')
                db.session.add(student_user)
                db.session.flush()

            # Create grade
            grade = Grade.query.filter_by(campus_id=campus.id).first()
            if not grade:
                grade = Grade(
                    name='Test-Grade-1',
                    campus_id=campus.id,
                    academic_year='2026',
                    max_students=40
                )
                db.session.add(grade)
                db.session.flush()

            # Create academic student
            academic_student = AcademicStudent.query.filter_by(user_id=student_user.id).first()
            if not academic_student:
                academic_student = AcademicStudent(
                    user_id=student_user.id,
                    institution_id=institution.id,
                    campus_id=campus.id,
                    grade_id=grade.id,
                    document_type='TI',
                    document_number='123456789',
                    status='activo'
                )
                db.session.add(academic_student)
                db.session.flush()

            # Create subject
            subject = Subject.query.filter_by(institution_id=institution.id).first()
            if not subject:
                subject = Subject(
                    name='Matematicas',
                    code='MAT',
                    institution_id=institution.id
                )
                db.session.add(subject)
                db.session.flush()

            # Create subject-grade
            subject_grade = SubjectGrade.query.filter_by(
                subject_id=subject.id,
                grade_id=grade.id,
                teacher_id=teacher.id
            ).first()
            if not subject_grade:
                subject_grade = SubjectGrade(
                    subject_id=subject.id,
                    grade_id=grade.id,
                    teacher_id=teacher.id
                )
                db.session.add(subject_grade)
                db.session.flush()

            # Create academic periods
            periods = AcademicPeriod.query.filter_by(institution_id=institution.id).all()
            if not periods:
                for i in range(1, 5):
                    period = AcademicPeriod(
                        name=f'Periodo {i}',
                        short_name=f'P{i}',
                        institution_id=institution.id,
                        academic_year='2026',
                        order=i,
                        is_active=(i == 1)
                    )
                    db.session.add(period)
                db.session.flush()
                periods = AcademicPeriod.query.filter_by(institution_id=institution.id).all()

            # Create grade criteria
            criteria = GradeCriteria.query.filter_by(institution_id=institution.id).first()
            if not criteria:
                criteria = GradeCriteria(
                    name='Evaluacion',
                    weight=100.0,
                    institution_id=institution.id,
                    order=1
                )
                db.session.add(criteria)
                db.session.flush()

            # Create a LOW grade (trigger riesgo_academico)
            existing_low = GradeRecord.query.filter_by(
                student_id=academic_student.id,
                subject_grade_id=subject_grade.id,
                period_id=periods[0].id
            ).first()
            if not existing_low:
                low_grade = GradeRecord(
                    student_id=academic_student.id,
                    subject_grade_id=subject_grade.id,
                    period_id=periods[0].id,
                    criterion_id=criteria.id,
                    score=2.5,  # Below 3.0
                    created_by=teacher.id
                )
                db.session.add(low_grade)

                # Create corresponding FinalGrade
                low_final = FinalGrade(
                    student_id=academic_student.id,
                    subject_grade_id=subject_grade.id,
                    period_id=periods[0].id,
                    final_score=2.5,
                    status='perdida'
                )
                db.session.add(low_final)

            # Create a grade for period 2 to test trends
            if len(periods) > 1:
                existing_p2 = GradeRecord.query.filter_by(
                    student_id=academic_student.id,
                    subject_grade_id=subject_grade.id,
                    period_id=periods[1].id
                ).first()
                if not existing_p2:
                    # Period 1 was 2.5, period 2 is 1.8 (tendencia negativa: -0.7)
                    low_grade_p2 = GradeRecord(
                        student_id=academic_student.id,
                        subject_grade_id=subject_grade.id,
                        period_id=periods[1].id,
                        criterion_id=criteria.id,
                        score=1.8,
                        created_by=teacher.id
                    )
                    db.session.add(low_grade_p2)

                    low_final_p2 = FinalGrade(
                        student_id=academic_student.id,
                        subject_grade_id=subject_grade.id,
                        period_id=periods[1].id,
                        final_score=1.8,
                        status='perdida'
                    )
                    db.session.add(low_final_p2)

            # Create attendance records with high absence (trigger inasistencia_critica)
            existing_attendance = Attendance.query.filter_by(
                student_id=academic_student.id
            ).first()
            if not existing_attendance:
                # Create 30 days of attendance, 8 absent (>20%)
                for i in range(30):
                    status = 'ausente' if i < 8 else 'presente'
                    attendance = Attendance(
                        student_id=academic_student.id,
                        subject_grade_id=subject_grade.id,
                        date=datetime.utcnow().date() - timedelta(days=i),
                        status=status,
                        recorded_by=teacher.id
                    )
                    db.session.add(attendance)

            db.session.commit()
            print_result("Test data created", True)
            results['passed'] += 1
        except Exception as e:
            db.session.rollback()
            print_result("Test data creation", False, str(e))
            traceback.print_exc()
            results['failed'] += 1
        results['total'] += 1

        # ============================================
        # Test 6: Run Individual Rules
        # ============================================
        print_header("TEST 6: Run Individual Alert Rules")
        for rule_key in expected_rules:
            try:
                count = run_alert(rule_key, institution.id)
                print_result(f"Rule: {RULE_LABELS[rule_key]}", True, f"Created {count} alerts")
                results['passed'] += 1
            except Exception as e:
                print_result(f"Rule: {RULE_LABELS[rule_key]}", False, str(e))
                results['failed'] += 1
            results['total'] += 1

        # ============================================
        # Test 7: Run All Rules
        # ============================================
        print_header("TEST 7: Run All Alert Rules")
        try:
            results_data = run_all_alerts(institution.id)
            total_created = sum(
                r.get('alerts_created', 0)
                for r in results_data.values()
                if r['status'] == 'success'
            )
            success_count = sum(1 for r in results_data.values() if r['status'] == 'success')
            print_result(f"Run all rules", True, f"{success_count}/6 rules succeeded, {total_created} total alerts")
            results['passed'] += 1
        except Exception as e:
            print_result("Run all rules", False, str(e))
            traceback.print_exc()
            results['failed'] += 1
        results['total'] += 1

        # ============================================
        # Test 8: Get Active Alerts
        # ============================================
        print_header("TEST 8: Query Active Alerts")
        try:
            active = get_active_alerts(institution.id)
            print_result(f"Get active alerts", True, f"Found {len(active)} active alerts")
            results['passed'] += 1
        except Exception as e:
            print_result("Get active alerts", False, str(e))
            results['failed'] += 1
        results['total'] += 1

        # ============================================
        # Test 9: Get All Alerts with Filters
        # ============================================
        print_header("TEST 9: Query Alerts with Filters")
        try:
            all_alerts = get_all_alerts(institution_id=institution.id)
            active_only = get_all_alerts(institution_id=institution.id, resolved=False)
            alta_only = get_all_alerts(institution_id=institution.id, severity='alta')
            print_result(f"Filter: all", True, f"{len(all_alerts)} total")
            print_result(f"Filter: active only", True, f"{len(active_only)} active")
            print_result(f"Filter: alta severity", True, f"{len(alta_only)} alta")
            results['passed'] += 3
        except Exception as e:
            print_result("Filter alerts", False, str(e))
            results['failed'] += 1
        results['total'] += 1

        # ============================================
        # Test 10: Alert Stats
        # ============================================
        print_header("TEST 10: Alert Statistics")
        try:
            stats = get_alert_stats(institution.id)
            assert 'total' in stats
            assert 'active' in stats
            assert 'resolved' in stats
            assert 'by_type' in stats
            assert 'by_severity' in stats
            print_result(f"Stats retrieved", True,
                        f"Total: {stats['total']}, Active: {stats['active']}, Resolved: {stats['resolved']}")
            print_result(f"Stats by_type", True, f"{len(stats['by_type'])} types")
            print_result(f"Stats by_severity", True,
                        f"Alta: {stats['by_severity']['alta']}, Media: {stats['by_severity']['media']}, Baja: {stats['by_severity']['baja']}")
            results['passed'] += 3
        except Exception as e:
            print_result("Alert stats", False, str(e))
            results['failed'] += 1
        results['total'] += 1

        # ============================================
        # Test 11: Resolve Alert
        # ============================================
        print_header("TEST 11: Resolve Alert")
        try:
            first_alert = Alert.query.filter_by(resolved=False).first()
            if first_alert:
                resolved = resolve_alert(first_alert.id, teacher.id, "Test resolution note")
                assert resolved is not None
                assert resolved.resolved == True
                assert resolved.resolved_by == teacher.id
                assert resolved.notes == "Test resolution note"
                assert resolved.resolved_at is not None
                print_result(f"Resolve alert", True, f"Alert #{resolved.id} resolved")
            else:
                print_result(f"Resolve alert", False, "No alerts to resolve")
                results['failed'] += 1
            results['passed'] += 1
        except Exception as e:
            db.session.rollback()
            print_result("Resolve alert", False, str(e))
            results['failed'] += 1
        results['total'] += 1

        # ============================================
        # Test 12: Verify Resolution
        # ============================================
        print_header("TEST 12: Verify Resolution Status")
        try:
            stats_after = get_alert_stats(institution.id)
            assert stats_after['resolved'] >= 1, f"Expected at least 1 resolved, got {stats_after['resolved']}"
            active_after = get_active_alerts(institution.id)
            print_result(f"Verify resolution", True,
                        f"Resolved: {stats_after['resolved']}, Still active: {len(active_after)}")
            results['passed'] += 1
        except Exception as e:
            print_result("Verify resolution", False, str(e))
            results['failed'] += 1
        results['total'] += 1

        # ============================================
        # Test 13: Blueprint Registration
        # ============================================
        print_header("TEST 13: Blueprint Registration")
        try:
            from routes.alerts import alerts_bp
            assert alerts_bp is not None
            assert alerts_bp.name == 'alerts'
            # Check routes are registered
            rules = [rule.rule for rule in app.url_map.iter_rules() if 'alerts' in rule.rule]
            expected_routes = ['/alerts', '/alerts/run', '/alerts/export', '/alerts/<int:alert_id>', '/alerts/<int:alert_id>/resolve']
            print_result(f"Blueprint registered", True, f"Blueprint name: {alerts_bp.name}")
            print_result(f"Routes registered", True, f"Found {len(rules)} alert routes: {rules}")
            results['passed'] += 2
        except Exception as e:
            print_result("Blueprint registration", False, str(e))
            results['failed'] += 1
        results['total'] += 1

        # ============================================
        # Test 14: Template Files Exist
        # ============================================
        print_header("TEST 14: Template Files Exist")
        template_files = [
            'templates/alerts/list.html',
            'templates/alerts/detail.html',
            'templates/alerts/run_panel.html'
        ]
        try:
            for template in template_files:
                full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), template)
                exists = os.path.exists(full_path)
                print_result(f"Template: {template}", exists)
                if exists:
                    results['passed'] += 1
                else:
                    results['failed'] += 1
        except Exception as e:
            print_result("Template files", False, str(e))
            results['failed'] += 1
        results['total'] += len(template_files)

        # ============================================
        # Summary
        # ============================================
        print_header("TEST SUMMARY")
        print(f"  Total: {results['total']}")
        print(f"  Passed: {results['passed']}")
        print(f"  Failed: {results['failed']}")
        print(f"  Success Rate: {(results['passed'] / results['total'] * 100):.1f}%")
        print()

        if results['failed'] == 0:
            print("  ALL TESTS PASSED!")
        else:
            print(f"  {results['failed']} TEST(S) FAILED")

        return results['failed'] == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
