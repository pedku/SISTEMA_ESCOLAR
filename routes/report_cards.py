"""
Report card management routes.
Handles generation, viewing, bulk creation, and management of student report cards (boletines).
"""

import os
from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app, send_file
from flask_login import login_required, current_user
from extensions import db
from models.report import ReportCard, ReportCardObservation
from models.grading import FinalGrade, AnnualGrade, AcademicPeriod
from models.academic import Grade, SubjectGrade, AcademicStudent, Subject
from models.attendance import Attendance
from models.institution import Institution, Campus
from models.user import User
from utils.decorators import login_required, role_required
from utils.institution_resolver import get_current_institution
from utils.pdf_generator import generate_report_card_pdf, save_report_card_pdf

report_cards_bp = Blueprint('report_cards', __name__)


# ============================================
# Helpers
# ============================================

def _get_performance_level(score):
    """Get performance level text for a grade."""
    if score is None:
        return 'N/A'
    if score >= 4.6:
        return 'Superior'
    elif score >= 4.0:
        return 'Alto'
    elif score >= 3.0:
        return 'Basico'
    else:
        return 'Bajo'


def _get_status_text(status):
    """Get display text for grade status."""
    if status == 'ganada':
        return 'Aprobado'
    elif status == 'perdida':
        return 'Reprobado'
    return 'No evaluado'


def _get_student_attendance(student_id, period, subject_grades):
    """Get attendance summary for a student in a period."""
    # Get all attendance records for this student in the period
    query = Attendance.query.filter(
        Attendance.student_id == student_id,
        Attendance.date >= period.start_date,
        Attendance.date <= period.end_date
    )

    # Filter by subject grades if provided
    if subject_grades:
        sg_ids = [sg.id for sg in subject_grades]
        query = query.filter(Attendance.subject_grade_id.in_(sg_ids))

    records = query.all()

    presentes = sum(1 for r in records if r.status == 'presente')
    ausentes = sum(1 for r in records if r.status == 'ausente')
    justificados = sum(1 for r in records if r.status in ('justificado', 'excusado'))

    return {
        'presentes': presentes,
        'ausentes': ausentes,
        'justificados': justificados,
        'total': len(records)
    }


def _get_grade_subjects(grade_id):
    """Get all subject-grades for a grade."""
    return SubjectGrade.query.filter_by(grade_id=grade_id).all()


def _build_grades_data(student_id, period_id, subject_grades):
    """Build grades data for all subjects for a student in a period."""
    grades_data = []

    for sg in subject_grades:
        final_grade = FinalGrade.query.filter_by(
            student_id=student_id,
            subject_grade_id=sg.id,
            period_id=period_id
        ).first()

        grades_data.append({
            'subject_grade': sg,
            'subject_name': sg.subject.name,
            'teacher_name': sg.teacher_user.get_full_name() if sg.teacher_user else 'N/A',
            'final_score': final_grade.final_score if final_grade else None,
            'status': final_grade.status if final_grade else 'no evaluado',
            'observation': final_grade.observation if final_grade else None,
            'performance_level': _get_performance_level(final_grade.final_score) if final_grade and final_grade.final_score else 'N/A',
            'status_text': _get_status_text(final_grade.status) if final_grade else 'No evaluado'
        })

    return grades_data


# ============================================
# Main listing / manage page
# ============================================

@report_cards_bp.route('/')
@login_required
@role_required('root', 'admin', 'coordinator')
def report_cards():
    """Main report card management page."""
    return redirect(url_for('report_cards.manage'))


@report_cards_bp.route('/manage')
@login_required
@role_required('root', 'admin', 'coordinator')
def manage():
    """Panel de gestion de boletines: generar, ver entregados, marcar entrega."""
    institution = get_current_institution()
    if not institution:
        institution = Institution.query.first()
        if not institution:
            flash('No se ha configurado la institucion.', 'warning')
            return redirect(url_for('dashboard.index'))

    academic_year = institution.academic_year

    # Get academic periods
    periods = AcademicPeriod.query.filter_by(
        institution_id=institution.id,
        academic_year=academic_year
    ).order_by(AcademicPeriod.order).all()

    # Get grades for institution
    grades_list = Grade.query.join(Campus).filter(
        Campus.institution_id == institution.id,
        Grade.academic_year == academic_year
    ).order_by(Grade.name).all()

    # Stats
    total_generated = ReportCard.query.count()
    total_delivered = ReportCard.query.filter_by(delivery_status='entregado').count()
    total_pending = total_generated - total_delivered

    return render_template(
        'report_cards/manage.html',
        periods=periods,
        grades_list=grades_list,
        total_generated=total_generated,
        total_delivered=total_delivered,
        total_pending=total_pending
    )


# ============================================
# Generate individual report card
# ============================================

@report_cards_bp.route('/generate/<int:student_id>/<int:period_id>', methods=['POST'])
@login_required
@role_required('root', 'admin', 'coordinator', 'teacher')
def generate(student_id, period_id):
    """Generate a PDF report card for a single student."""
    student = AcademicStudent.query.get_or_404(student_id)
    period = AcademicPeriod.query.get_or_404(period_id)

    # Validate period belongs to institution
    institution = get_current_institution()
    if institution and period.institution_id != institution.id:
        flash('No tiene permiso para acceder a este periodo.', 'danger')
        return redirect(url_for('report_cards.manage'))

    # Get grade and subject-grades
    if not student.grade_id:
        flash('El estudiante no tiene un grado asignado.', 'danger')
        return redirect(url_for('report_cards.manage'))

    subject_grades = _get_grade_subjects(student.grade_id)
    if not subject_grades:
        flash('No hay asignaturas configuradas para este grado.', 'danger')
        return redirect(url_for('report_cards.manage'))

    # Build grades data
    grades_data = _build_grades_data(student.id, period.id, subject_grades)

    # Check if any grades exist
    has_grades = any(g['final_score'] is not None for g in grades_data)
    if not has_grades:
        flash('No hay calificaciones registradas para este estudiante en este periodo.', 'warning')
        return redirect(url_for('report_cards.student_report', student_id=student.id, period_id=period.id))

    # Get attendance
    attendance = _get_student_attendance(student.id, period, subject_grades)

    # Get institution
    if not institution:
        institution = Institution.query.first()

    # Get campus
    campus = Campus.query.get(student.campus_id) if student.campus_id else None

    # Check if report card already exists
    report_card = ReportCard.query.filter_by(
        student_id=student.id,
        period_id=period.id
    ).first()

    if report_card:
        # Regenerate: delete old observations and update
        ReportCardObservation.query.filter_by(report_card_id=report_card.id).delete()
    else:
        report_card = ReportCard(
            student_id=student.id,
            period_id=period.id,
            generated_by=current_user.id
        )
        db.session.add(report_card)
        db.session.flush()  # Get the ID

    # Save subject observations from report card
    for g in grades_data:
        if g.get('observation'):
            obs = ReportCardObservation(
                report_card_id=report_card.id,
                subject_grade_id=g['subject_grade'].id,
                observation=g['observation']
            )
            db.session.add(obs)

    db.session.commit()

    # Generate PDF
    try:
        pdf_bytes, filename = generate_report_card_pdf(
            report_card=report_card,
            student=student,
            institution=institution,
            period=period,
            grades_data=grades_data,
            attendance=attendance,
            campus=campus
        )

        file_path = save_report_card_pdf(pdf_bytes, filename)

        # Update report card with path
        report_card.pdf_path = file_path
        report_card.generated_at = datetime.utcnow()
        db.session.commit()

        flash('Boletin generado exitosamente.', 'success')
        return send_file(file_path, mimetype='application/pdf', as_attachment=True, download_name=filename)

    except Exception as e:
        db.session.rollback()
        flash(f'Error al generar el boletin: {str(e)}', 'danger')
        return redirect(url_for('report_cards.manage'))


# ============================================
# Bulk generation by grade
# ============================================

@report_cards_bp.route('/generate_bulk/<int:grade_id>/<int:period_id>', methods=['POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def generate_bulk(grade_id, period_id):
    """Generate report cards for all students in a grade."""
    grade = Grade.query.get_or_404(grade_id)
    period = AcademicPeriod.query.get_or_404(period_id)

    # Validate institution
    institution = get_current_institution()
    if institution:
        # Verify grade belongs to institution
        campus = Campus.query.get(grade.campus_id)
        if not campus or campus.institution_id != institution.id:
            flash('No tiene permiso para acceder a este grado.', 'danger')
            return jsonify({'success': False, 'error': 'Acceso no permitido'})

        if period.institution_id != institution.id:
            flash('No tiene permiso para acceder a este periodo.', 'danger')
            return jsonify({'success': False, 'error': 'Acceso no permitido'})

    # Get students in this grade
    students = AcademicStudent.query.filter_by(
        grade_id=grade_id,
        status='activo'
    ).all()

    if not students:
        return jsonify({'success': False, 'error': 'No hay estudiantes activos en este grado'})

    # Get subject grades
    subject_grades = _get_grade_subjects(grade_id)
    if not subject_grades:
        return jsonify({'success': False, 'error': 'No hay asignaturas configuradas para este grado'})

    if not institution:
        institution = Institution.query.first()

    results = {
        'total': len(students),
        'generated': 0,
        'skipped': 0,
        'errors': 0,
        'details': []
    }

    for student in students:
        try:
            # Build grades data
            grades_data = _build_grades_data(student.id, period.id, subject_grades)

            # Check if student has any grades
            has_grades = any(g['final_score'] is not None for g in grades_data)
            if not has_grades:
                results['skipped'] += 1
                results['details'].append({
                    'student': student.user.username,
                    'status': 'skipped',
                    'reason': 'Sin calificaciones'
                })
                continue

            # Get attendance
            attendance = _get_student_attendance(student.id, period, subject_grades)
            campus = Campus.query.get(student.campus_id) if student.campus_id else None

            # Check existing
            report_card = ReportCard.query.filter_by(
                student_id=student.id,
                period_id=period.id
            ).first()

            if report_card:
                # Regenerate
                ReportCardObservation.query.filter_by(report_card_id=report_card.id).delete()
            else:
                report_card = ReportCard(
                    student_id=student.id,
                    period_id=period.id,
                    generated_by=current_user.id
                )
                db.session.add(report_card)
                db.session.flush()

            # Save observations
            for g in grades_data:
                if g.get('observation'):
                    obs = ReportCardObservation(
                        report_card_id=report_card.id,
                        subject_grade_id=g['subject_grade'].id,
                        observation=g['observation']
                    )
                    db.session.add(obs)

            db.session.commit()

            # Generate PDF
            pdf_bytes, filename = generate_report_card_pdf(
                report_card=report_card,
                student=student,
                institution=institution,
                period=period,
                grades_data=grades_data,
                attendance=attendance,
                campus=campus
            )

            file_path = save_report_card_pdf(pdf_bytes, filename)

            report_card.pdf_path = file_path
            report_card.generated_at = datetime.utcnow()
            db.session.commit()

            results['generated'] += 1
            results['details'].append({
                'student': student.user.username,
                'status': 'generated',
                'file': filename
            })

        except Exception as e:
            db.session.rollback()
            results['errors'] += 1
            results['details'].append({
                'student': student.user.username if student.user else 'Unknown',
                'status': 'error',
                'error': str(e)
            })

    # If AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'success': True, 'results': results})

    flash(f'Generacion masiva completada: {results["generated"]} generados, {results["skipped"]} omitidos, {results["errors"]} errores.',
          'info')
    return redirect(url_for('report_cards.manage'))


# ============================================
# View / download existing report card
# ============================================

@report_cards_bp.route('/<int:id>')
@login_required
def view_report_card(id):
    """View/download a specific report card PDF."""
    report_card = ReportCard.query.get_or_404(id)
    student = AcademicStudent.query.get(report_card.student_id)

    # Permission check
    if not current_user.is_root() and not current_user.has_any_role('admin', 'coordinator'):
        # Students can only view their own
        if current_user.has_role('student') and student.user_id != current_user.id:
            flash('No tiene permiso para ver este boletin.', 'danger')
            return redirect(url_for('dashboard.index'))

    if not report_card.pdf_path or not os.path.exists(report_card.pdf_path):
        flash('El archivo PDF no esta disponible.', 'warning')
        return redirect(url_for('report_cards.manage'))

    return send_file(
        report_card.pdf_path,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=os.path.basename(report_card.pdf_path)
    )


@report_cards_bp.route('/<int:id>/download')
@login_required
def download_report_card(id):
    """Download a specific report card PDF."""
    report_card = ReportCard.query.get_or_404(id)
    student = AcademicStudent.query.get(report_card.student_id)

    # Permission check
    if not current_user.is_root() and not current_user.has_any_role('admin', 'coordinator'):
        if current_user.has_role('student') and student.user_id != current_user.id:
            flash('No tiene permiso para descargar este boletin.', 'danger')
            return redirect(url_for('dashboard.index'))

    if not report_card.pdf_path or not os.path.exists(report_card.pdf_path):
        flash('El archivo PDF no esta disponible.', 'warning')
        return redirect(url_for('report_cards.manage'))

    return send_file(
        report_card.pdf_path,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=os.path.basename(report_card.pdf_path)
    )


# ============================================
# Student history
# ============================================

@report_cards_bp.route('/history/<int:student_id>')
@login_required
def report_card_history(student_id):
    """View report card history for a student."""
    student = AcademicStudent.query.get_or_404(student_id)

    # Permission check
    if not current_user.is_root() and not current_user.has_any_role('admin', 'coordinator'):
        if current_user.has_role('student') and student.user_id != current_user.id:
            flash('No tiene permiso para ver este historial.', 'danger')
            return redirect(url_for('dashboard.index'))

    # Get all report cards for this student
    report_cards_list = ReportCard.query.filter_by(
        student_id=student_id
    ).order_by(ReportCard.period_id).all()

    # Get all periods for context
    institution = get_current_institution()
    if not institution:
        institution = Institution.query.first()

    all_periods = AcademicPeriod.query.filter_by(
        institution_id=institution.id if institution else 1
    ).order_by(AcademicPeriod.academic_year, AcademicPeriod.order).all()

    return render_template(
        'report_cards/history.html',
        student=student,
        report_cards=report_cards_list,
        all_periods=all_periods
    )


# ============================================
# Student-specific view (select period)
# ============================================

@report_cards_bp.route('/student/<int:student_id>')
@login_required
def student_report(student_id):
    """View report card options for a specific student."""
    student = AcademicStudent.query.get_or_404(student_id)

    # Permission check
    if not current_user.is_root() and not current_user.has_any_role('admin', 'coordinator', 'teacher'):
        if current_user.has_role('student') and student.user_id != current_user.id:
            flash('No tiene permiso para ver este boletin.', 'danger')
            return redirect(url_for('dashboard.index'))

    institution = get_current_institution()
    if not institution:
        institution = Institution.query.first()

    periods = AcademicPeriod.query.filter_by(
        institution_id=institution.id if institution else 1
    ).order_by(AcademicPeriod.academic_year, AcademicPeriod.order).all()

    # Get existing report cards
    existing_cards = {rc.period_id: rc for rc in ReportCard.query.filter_by(student_id=student_id).all()}

    return render_template(
        'report_cards/generate.html',
        student=student,
        periods=periods,
        existing_cards=existing_cards
    )


# ============================================
# Delivery management
# ============================================

@report_cards_bp.route('/<int:id>/deliver', methods=['POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def mark_delivered(id):
    """Mark a report card as delivered."""
    report_card = ReportCard.query.get_or_404(id)
    action = request.form.get('action', 'deliver')

    if action == 'deliver':
        report_card.delivery_status = 'entregado'
        report_card.delivery_date = date.today()
        flash('Boletin marcado como entregado.', 'success')
    elif action == 'pending':
        report_card.delivery_status = 'pendiente'
        report_card.delivery_date = None
        flash('Boletin marcado como pendiente.', 'info')

    db.session.commit()
    return redirect(request.referrer or url_for('report_cards.manage'))


# ============================================
# General observation management
# ============================================

@report_cards_bp.route('/<int:id>/observation', methods=['POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def update_observation(id):
    """Update general observation for a report card."""
    report_card = ReportCard.query.get_or_404(id)
    observation = request.form.get('general_observation', '').strip()

    report_card.general_observation = observation if observation else None
    db.session.commit()

    flash('Observacion general actualizada.', 'success')
    return redirect(request.referrer or url_for('report_cards.manage'))


# ============================================
# Subject observation management (AJAX)
# ============================================

@report_cards_bp.route('/observations', methods=['POST'])
@login_required
@role_required('root', 'admin', 'coordinator', 'teacher')
def save_subject_observation():
    """Save subject-specific observation for a report card (AJAX)."""
    data = request.get_json()
    report_card_id = data.get('report_card_id')
    subject_grade_id = data.get('subject_grade_id')
    observation = data.get('observation', '').strip()

    if not report_card_id or not subject_grade_id:
        return jsonify({'success': False, 'error': 'Datos incompletos'}), 400

    report_card = ReportCard.query.get(report_card_id)
    if not report_card:
        return jsonify({'success': False, 'error': 'Boletin no encontrado'}), 404

    # Check if observation exists
    existing = ReportCardObservation.query.filter_by(
        report_card_id=report_card_id,
        subject_grade_id=subject_grade_id
    ).first()

    if observation:
        if existing:
            existing.observation = observation
        else:
            obs = ReportCardObservation(
                report_card_id=report_card_id,
                subject_grade_id=subject_grade_id,
                observation=observation
            )
            db.session.add(obs)
    else:
        if existing:
            db.session.delete(existing)

    db.session.commit()
    return jsonify({'success': True})


# ============================================
# Delete report card
# ============================================

@report_cards_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def delete_report_card(id):
    """Delete a report card and its PDF file."""
    report_card = ReportCard.query.get_or_404(id)

    # Delete PDF file if exists
    if report_card.pdf_path and os.path.exists(report_card.pdf_path):
        os.remove(report_card.pdf_path)

    # Delete observations (cascade handles this)
    ReportCardObservation.query.filter_by(report_card_id=report_card.id).delete()

    db.session.delete(report_card)
    db.session.commit()

    flash('Boletin eliminado.', 'success')
    return redirect(request.referrer or url_for('report_cards.manage'))


# ============================================
# API: Get students for a grade
# ============================================

@report_cards_bp.route('/api/students/<int:grade_id>')
@login_required
@role_required('root', 'admin', 'coordinator')
def api_grade_students(grade_id):
    """Get students in a grade (JSON API)."""
    grade = Grade.query.get_or_404(grade_id)
    students = AcademicStudent.query.filter_by(
        grade_id=grade_id,
        status='activo'
    ).join(User).order_by(User.first_name, User.last_name).all()

    return jsonify({
        'grade_name': grade.name,
        'students': [{
            'id': s.id,
            'name': s.user.get_full_name(),
            'document': s.document_number
        } for s in students]
    })


@report_cards_bp.route('/api/report_cards')
@login_required
@role_required('root', 'admin', 'coordinator')
def api_report_cards_list():
    """Get all report cards (JSON API)."""
    report_cards_list = ReportCard.query.order_by(ReportCard.generated_at.desc()).all()

    result = []
    for rc in report_cards_list:
        student = AcademicStudent.query.get(rc.student_id)
        grade = student.grade if student and student.grade_id else None
        period = AcademicPeriod.query.get(rc.period_id)

        result.append({
            'id': rc.id,
            'student_id': rc.student_id,
            'student_name': student.user.get_full_name() if student and student.user else 'N/A',
            'grade_name': grade.name if grade else 'N/A',
            'period_name': period.short_name + ' ' + period.academic_year if period else 'N/A',
            'generated_at': rc.generated_at.isoformat() if rc.generated_at else None,
            'delivery_status': rc.delivery_status,
            'pdf_path': rc.pdf_path
        })

    return jsonify({'report_cards': result})
