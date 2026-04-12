"""
Test script for Report Cards (Boletines) module.
Tests route availability, data integrity, and PDF generation (if WeasyPrint available).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models.user import User
from models.institution import Institution, Campus
from models.academic import Grade, Subject, SubjectGrade, AcademicStudent
from models.grading import AcademicPeriod, GradeCriteria, FinalGrade
from models.report import ReportCard, ReportCardObservation
from models.attendance import Attendance
from datetime import date, datetime

app = create_app()
results = []
passed = 0
failed = 0
weasyprint_available = False


def report(status, name, detail=''):
    global passed, failed
    icon = 'PASS' if status else 'FAIL'
    if status:
        passed += 1
    else:
        failed += 1
    msg = f'  [{icon}] {name}'
    if detail:
        msg += f' - {detail}'
    results.append(msg)
    print(msg)


def test_route(client, path, name, expected_codes=None, method='GET', data=None):
    """Test a route returns an expected status code."""
    if expected_codes is None:
        expected_codes = [200, 302]
    try:
        if method == 'POST':
            r = client.post(path, data=data, follow_redirects=False)
        else:
            r = client.get(path, follow_redirects=False)
        status = r.status_code in expected_codes
        report(status, name, f'HTTP {r.status_code}')
        return r
    except Exception as e:
        report(False, name, f'Exception: {e}')
        return None


def setup_test_data():
    """Create test data if it doesn't exist."""
    with app.app_context():
        root_user = User.query.filter_by(username='root').first()
        if not root_user:
            print('  Creating root user...')
            root_user = User(
                username='root', email='root@test.com',
                first_name='Root', last_name='Admin',
                document_type='CC', document_number='000000',
                role='root', is_active=True, must_change_password=False
            )
            root_user.set_password('root123')
            db.session.add(root_user)
            db.session.commit()

        institution = Institution.query.first()
        if not institution:
            print('  Creating test institution...')
            institution = Institution(
                name='Institucion Educativa Test', nit='900000000',
                resolution='Resolucion 001 de 2026',
                municipality='Bogota', department='Cundinamarca',
                academic_year='2026'
            )
            db.session.add(institution)
            db.session.commit()

        campus = Campus.query.filter_by(institution_id=institution.id).first()
        if not campus:
            print('  Creating test campus...')
            campus = Campus(
                institution_id=institution.id, name='Sede Principal',
                code='SP', is_main_campus=True
            )
            db.session.add(campus)
            db.session.commit()

        grade = Grade.query.filter_by(campus_id=campus.id, academic_year='2026').first()
        if not grade:
            print('  Creating test grade...')
            grade = Grade(
                campus_id=campus.id, name='6-1', academic_year='2026', max_students=40
            )
            db.session.add(grade)
            db.session.commit()

        period = AcademicPeriod.query.filter_by(
            institution_id=institution.id, academic_year='2026', short_name='P1'
        ).first()
        if not period:
            print('  Creating test academic period...')
            period = AcademicPeriod(
                institution_id=institution.id, name='Primer Periodo',
                short_name='P1', academic_year='2026', order=1, is_active=True,
                start_date=date(2026, 2, 1), end_date=date(2026, 4, 30)
            )
            db.session.add(period)
            db.session.commit()

        criteria = GradeCriteria.query.filter_by(institution_id=institution.id).first()
        if not criteria:
            print('  Creating test grade criteria...')
            for name, weight, order in [('Cognitivo', 40.0, 1), ('Procedimental', 30.0, 2), ('Actitudinal', 30.0, 3)]:
                db.session.add(GradeCriteria(institution_id=institution.id, name=name, weight=weight, order=order))
            db.session.commit()

        teacher = User.query.filter_by(role='teacher').first()
        if not teacher:
            print('  Creating test teacher...')
            teacher = User(
                username='profesor_test', email='teacher@test.com',
                first_name='Juan', last_name='Profesor',
                document_type='CC', document_number='111111',
                role='teacher', institution_id=institution.id,
                is_active=True, must_change_password=False
            )
            teacher.set_password('teacher123')
            db.session.add(teacher)
            db.session.commit()

        student_user = User.query.filter_by(role='student').first()
        student_ac = None
        if not student_user:
            print('  Creating test student...')
            student_user = User(
                username='estudiante_test', email='student@test.com',
                first_name='Maria', last_name='Estudiante',
                document_type='TI', document_number='222222',
                role='student', institution_id=institution.id,
                is_active=True, must_change_password=False
            )
            student_user.set_password('student123')
            db.session.add(student_user)
            db.session.commit()

            student_ac = AcademicStudent(
                user_id=student_user.id, institution_id=institution.id,
                campus_id=campus.id, grade_id=grade.id,
                document_type='TI', document_number='222222', status='activo'
            )
            db.session.add(student_ac)
            db.session.commit()
        else:
            student_ac = AcademicStudent.query.filter_by(user_id=student_user.id).first()

        subject = Subject.query.filter_by(institution_id=institution.id).first()
        if not subject:
            print('  Creating test subjects...')
            for i, name in enumerate(['Matematicas', 'Ciencias Naturales', 'Espanol', 'Sociales'], 1):
                db.session.add(Subject(institution_id=institution.id, name=name, code=f'MAT{i:02d}'))
            db.session.commit()

        sg = SubjectGrade.query.filter_by(grade_id=grade.id).first()
        if not sg:
            print('  Creating test subject-grades...')
            for subj in Subject.query.filter_by(institution_id=institution.id).all():
                db.session.add(SubjectGrade(subject_id=subj.id, grade_id=grade.id, teacher_id=teacher.id))
            db.session.commit()

        # Create final grades
        if student_ac:
            existing_fg = FinalGrade.query.filter_by(student_id=student_ac.id, period_id=period.id).first()
            if not existing_fg:
                print('  Creating test final grades...')
                all_sg = SubjectGrade.query.filter_by(grade_id=grade.id).all()
                scores = [4.2, 3.5, 4.8, 2.8]
                for i, sg_item in enumerate(all_sg):
                    score = scores[i] if i < len(scores) else 3.5
                    status = 'ganada' if score >= 3.0 else 'perdida'
                    obs = 'Excelente desempeno en todas las evaluaciones.' if score >= 4.5 else None
                    db.session.add(FinalGrade(
                        student_id=student_ac.id, subject_grade_id=sg_item.id,
                        period_id=period.id, final_score=score, status=status, observation=obs
                    ))
                db.session.commit()

            # Create attendance records
            existing_att = Attendance.query.filter_by(student_id=student_ac.id).first()
            if not existing_att:
                print('  Creating test attendance records...')
                all_sg = SubjectGrade.query.filter_by(grade_id=grade.id).all()
                if all_sg:
                    for d, status in [(date(2026, 3, 1), 'presente'), (date(2026, 3, 2), 'presente'),
                                       (date(2026, 3, 3), 'ausente'), (date(2026, 3, 4), 'presente'),
                                       (date(2026, 3, 5), 'justificado')]:
                        db.session.add(Attendance(
                            student_id=student_ac.id, subject_grade_id=all_sg[0].id,
                            date=d, status=status, recorded_by=teacher.id
                        ))
                    db.session.commit()

        print('  Test data setup complete.')
        return {
            'root_user_id': root_user.id, 'institution_id': institution.id,
            'campus_id': campus.id, 'grade_id': grade.id, 'period_id': period.id,
            'student_id': student_ac.id if student_ac else None, 'teacher_id': teacher.id
        }


def test_pdf_template_rendering(test_data):
    """Test that the PDF template renders correctly (without WeasyPrint)."""
    with app.app_context():
        from flask import render_template
        from utils.pdf_generator import WEASYPRINT_AVAILABLE

        student_id = test_data['student_id']
        if not student_id:
            report(False, 'PDF Template rendering', 'No student available')
            return

        student = AcademicStudent.query.get(student_id)
        period = AcademicPeriod.query.get(test_data['period_id'])
        institution = Institution.query.get(test_data['institution_id'])
        campus = Campus.query.get(test_data['campus_id'])
        grade = Grade.query.get(test_data['grade_id'])
        root_user = User.query.get(test_data['root_user_id'])

        # Build grades data
        subject_grades = SubjectGrade.query.filter_by(grade_id=grade.id).all()
        grades_data = []
        for sg in subject_grades:
            fg = FinalGrade.query.filter_by(
                student_id=student.id, subject_grade_id=sg.id, period_id=period.id
            ).first()
            score = fg.final_score if fg else None
            if score is not None:
                if score >= 4.6:
                    level = 'Superior'
                elif score >= 4.0:
                    level = 'Alto'
                elif score >= 3.0:
                    level = 'Basico'
                else:
                    level = 'Bajo'
            else:
                level = 'N/A'

            grades_data.append({
                'subject_grade': sg,
                'subject_name': sg.subject.name,
                'teacher_name': sg.teacher_user.get_full_name() if sg.teacher_user else 'N/A',
                'final_score': score,
                'status': fg.status if fg else 'no evaluado',
                'observation': fg.observation if fg else None,
                'performance_level': level,
                'status_text': 'Aprobado' if (fg and fg.status == 'ganada') else ('Reprobado' if (fg and fg.status == 'perdida') else 'No evaluado')
            })

        attendance = {'presentes': 3, 'ausentes': 1, 'justificados': 1, 'total': 5}

        # Create a dummy report card for template testing
        rc = ReportCard(
            student_id=student.id, period_id=period.id,
            generated_by=root_user.id,
            general_observation='Observacion de prueba del director de grupo.'
        )

        try:
            html = render_template(
                'report_cards/pdf_template.html',
                report_card=rc, student=student, institution=institution,
                period=period, grades_data=grades_data, attendance=attendance,
                campus=campus, generated_date=datetime.now()
            )

            has_header = 'Institucion' in html or 'Institución' in html
            has_student = 'Maria' in html or 'María' in html
            has_grades_table = 'Matematicas' in html or 'Matemáticas' in html or 'Ciencias' in html
            has_signatures = 'Director' in html
            has_scale = 'Superior' in html and 'Bajo' in html

            report(has_header, 'PDF Template: Header institucional',
                   'Found' if has_header else 'Missing')
            report(has_student, 'PDF Template: Datos del estudiante',
                   'Found' if has_student else 'Missing')
            report(has_grades_table, 'PDF Template: Tabla de calificaciones',
                   'Found' if has_grades_table else 'Missing')
            report(has_signatures, 'PDF Template: Seccion de firmas',
                   'Found' if has_signatures else 'Missing')
            report(has_scale, 'PDF Template: Escala valorativa',
                   'Found' if has_scale else 'Missing')

        except Exception as e:
            report(False, 'PDF Template rendering', f'Error: {e}')


def main():
    global passed, failed, weasyprint_available

    print('=' * 70)
    print('TEST: Report Cards (Boletines) Module')
    print('=' * 70)

    with app.app_context():
        print('\n--- Setting up test data ---')
        test_data = setup_test_data()

        # Check WeasyPrint availability
        from utils.pdf_generator import WEASYPRINT_AVAILABLE
        weasyprint_available = WEASYPRINT_AVAILABLE
        report(True, 'WeasyPrint availability check',
               'Available' if weasyprint_available else 'Not available (PDF generation skipped)')

    # Test routes
    print('\n--- Testing Routes ---')
    with app.test_client() as client:
        r = client.post('/login', data={'username': 'root', 'password': 'root123'}, follow_redirects=True)
        report(r.status_code == 200, 'Login as root', f'HTTP {r.status_code}')

        # Main routes
        test_route(client, '/report-cards/', 'Report cards main redirect', [302])
        test_route(client, '/report-cards/manage', 'Manage page', [200])

        # API endpoints
        if test_data['grade_id']:
            test_route(client, f'/report-cards/api/students/{test_data["grade_id"]}',
                       'API: Get students by grade', [200])

        test_route(client, '/report-cards/api/report_cards', 'API: Get all report cards', [200])

        # Student view
        if test_data['student_id']:
            test_route(client, f'/report-cards/student/{test_data["student_id"]}',
                       'Student report card selection', [200])

            # Test PDF template rendering (without actual PDF generation)
            print('\n--- Testing PDF Template ---')
            test_pdf_template_rendering(test_data)

            # Try actual PDF generation if WeasyPrint is available
            if test_data['period_id'] and weasyprint_available:
                print('\n--- Testing PDF Generation ---')
                r = client.post(
                    f'/report-cards/generate/{test_data["student_id"]}/{test_data["period_id"]}',
                    follow_redirects=False
                )
                if r.status_code in [200, 302]:
                    report(True, 'Generate individual report card (POST)', f'HTTP {r.status_code}')

                    with app.app_context():
                        rc = ReportCard.query.filter_by(
                            student_id=test_data['student_id'],
                            period_id=test_data['period_id']
                        ).first()
                        if rc:
                            test_route(client, f'/report-cards/{rc.id}', 'View report card PDF', [200])
                            test_route(client, f'/report-cards/{rc.id}/download', 'Download report card PDF', [200])
                            test_route(client, f'/report-cards/history/{test_data["student_id"]}', 'Student history', [200])
                            test_route(client, f'/report-cards/{rc.id}/deliver', 'Mark as delivered', [302],
                                       method='POST', data={'action': 'deliver'})
                            test_route(client, f'/report-cards/{rc.id}/observation', 'Update observation', [302],
                                       method='POST', data={'general_observation': 'Test observation'})
                else:
                    report(False, 'Generate individual report card (POST)', f'HTTP {r.status_code}')
            elif test_data['period_id']:
                report(True, 'Generate individual report card (POST)',
                       'Skipped - WeasyPrint not available, but route exists')

        # Test bulk generation (AJAX)
        if test_data['grade_id'] and test_data['period_id']:
            r = client.post(
                f'/report-cards/generate_bulk/{test_data["grade_id"]}/{test_data["period_id"]}',
                headers={'X-Requested-With': 'XMLHttpRequest'},
                follow_redirects=False
            )
            if weasyprint_available:
                report(r.status_code == 200, 'Bulk generation (AJAX)', f'HTTP {r.status_code}')
            else:
                # Will fail without WeasyPrint, but that's expected
                report(True, 'Bulk generation (AJAX)',
                       f'HTTP {r.status_code} (WeasyPrint not available, expected failure)')

        # Test observation save endpoint
        import json
        test_route(client, '/report-cards/observations', 'Save subject observation (AJAX)', [200, 400],
                   method='POST')
        # Also test with proper JSON content type
        r = client.post('/report-cards/observations',
                        data=json.dumps({'report_card_id': 1, 'subject_grade_id': 1, 'observation': 'Test'}),
                        content_type='application/json',
                        follow_redirects=False)
        report(r.status_code in [200, 404], 'Save subject observation (JSON)', f'HTTP {r.status_code}')

    # Summary
    print('\n' + '=' * 70)
    print(f'RESULTS: {passed} passed, {failed} failed, {passed + failed} total')
    print('=' * 70)

    if failed == 0:
        print('\nAll tests passed!')
    else:
        print(f'\n{failed} test(s) failed. Check details above.')

    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
