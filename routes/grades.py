"""
Grades management routes.
Complete grade input, upload, student view, and summary functionality.
"""

import os
import pandas as pd
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_required, current_user
from extensions import db
from models.user import User
from models.institution import Institution, Campus
from models.academic import Grade, Subject, SubjectGrade, AcademicStudent
from models.grading import AcademicPeriod, GradeCriteria, GradeRecord, FinalGrade, AnnualGrade
from utils.decorators import login_required, role_required
from utils.institution_resolver import get_current_institution, get_institution_grades, get_institution_subjects
from services.grade_calculator import GradeCalculatorService

grades_bp = Blueprint('grades', __name__)

# Colombian grading constants
MIN_GRADE = 1.0
MAX_GRADE = 5.0
PASSING_GRADE = 3.0


# ============================================
# 1. Grade Input Selection Page
# ============================================

@grades_bp.route('/input')
@login_required
@role_required('root', 'admin', 'teacher', 'coordinator')
def grade_input():
    """
    Selection page: choose grade + subject + period for grade entry.
    Shows all grades and subjects available for the current user.
    Teachers only see their own assigned subject-grades.
    """
    institution = get_current_institution()
    if not institution:
        # Root without active institution - use first institution or show all
        institution = Institution.query.first()
        if not institution:
            flash('No se ha configurado la institucion. Contacte al administrador.', 'warning')
            return redirect(url_for('dashboard.index'))

    academic_year = institution.academic_year

    # Get active academic periods for this institution
    periods = AcademicPeriod.query.filter_by(
        institution_id=institution.id,
        academic_year=academic_year
    ).order_by(AcademicPeriod.order).all()

    # If no periods exist, redirect to setup
    if not periods:
        flash('No hay periodos academicos configurados. Configure los periodos primero.', 'warning')
        return redirect(url_for('institution.periods'))

    # Get selected period (default to active or first)
    active_period = next((p for p in periods if p.is_active), periods[0])
    selected_period_id = request.args.get('period_id', active_period.id, type=int)

    # Determine which grades and subject-grades the user can access
    if current_user.has_any_role('root', 'admin'):
        # Root/Admin: see all grades in the institution
        grades_list = Grade.query.join(Campus).filter(
            Campus.institution_id == institution.id,
            Grade.academic_year == academic_year
        ).distinct().order_by(Grade.name).all()

        subject_grades = SubjectGrade.query.join(Grade).join(Campus).join(Subject).filter(
            Campus.institution_id == institution.id,
            Grade.academic_year == academic_year
        ).order_by(Grade.name, Subject.name).all()
    elif current_user.has_role('coordinator'):
        # Coordinator: see all grades in the institution
        grades_list = Grade.query.join(Campus).filter(
            Campus.institution_id == institution.id,
            Grade.academic_year == academic_year
        ).distinct().order_by(Grade.name).all()

        subject_grades = SubjectGrade.query.join(Grade).join(Campus).join(Subject).filter(
            Campus.institution_id == institution.id,
            Grade.academic_year == academic_year
        ).order_by(Grade.name, Subject.name).all()
    else:
        # Teacher: only see their own subject-grades
        subject_grades = SubjectGrade.query.filter_by(
            teacher_id=current_user.id
        ).join(Grade).join(Campus).join(Subject).filter(
            Campus.institution_id == institution.id,
            Grade.academic_year == academic_year
        ).order_by(Grade.name, Subject.name).all()

        # Extract unique grades from teacher's subject-grades
        grade_ids = set(sg.grade_id for sg in subject_grades)
        grades_list = Grade.query.filter(Grade.id.in_(grade_ids)).order_by(Grade.name).all()

    # Get evaluation criteria
    criteria = GradeCriteria.query.filter_by(
        institution_id=institution.id
    ).order_by(GradeCriteria.order).all()

    return render_template(
        'grades/select.html',
        grades=grades_list,
        periods=periods,
        criteria=criteria,
        selected_period_id=selected_period_id,
        subject_grades=subject_grades
    )


# ============================================
# 2. Grade Input Spreadsheet
# ============================================

@grades_bp.route('/input/<int:sg_id>/<int:period_id>', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin', 'teacher', 'coordinator')
def grade_input_form(sg_id, period_id):
    """
    Grade input spreadsheet for a specific subject-grade and period.
    Shows all students in the grade with criteria columns.
    Auto-calculates final grade based on weights.
    Handles POST to save all grades at once.
    """
    # Verify subject-grade exists
    subject_grade = db.session.get(SubjectGrade, sg_id)
    if not subject_grade:
        flash('Asignatura-grado no encontrada.', 'error')
        return redirect(url_for('grades.grade_input'))

    # Check permissions: teachers can only access their own subject-grades
    if current_user.has_role('teacher') and subject_grade.teacher_id != current_user.id:
        if not current_user.has_any_role('root', 'admin', 'coordinator'):
            flash('No tienes permiso para editar esta asignatura.', 'error')
            return redirect(url_for('grades.grade_input'))

    # Verify period exists
    period = db.session.get(AcademicPeriod, period_id)
    if not period:
        flash('Periodo academico no encontrado.', 'error')
        return redirect(url_for('grades.grade_input'))

    grade = subject_grade.grade
    subject = subject_grade.subject

    # Get active students in this grade
    students = AcademicStudent.query.filter_by(
        grade_id=grade.id,
        status='activo'
    ).join(User).order_by(User.last_name, User.first_name).all()

    if not students:
        flash('No hay estudiantes activos en este grado.', 'warning')

    # Get institution from grade
    institution = grade.campus.institution

    # Get evaluation criteria with weights (filtered by institution)
    criteria = GradeCriteria.query.filter_by(
        institution_id=institution.id
    ).order_by(GradeCriteria.order).all()

    if not criteria:
        flash('No hay criterios de evaluacion configurados. Configure los criterios primero.', 'warning')
        return redirect(url_for('institution.criteria'))

    # Build criteria weights dict
    criteria_weights = {c.id: c.weight for c in criteria}

    # Handle POST - save grades
    if request.method == 'POST':
        action = request.form.get('action', 'save')

        if action == 'lock':
            # Lock grades for this subject-grade/period
            GradeRecord.query.filter_by(
                subject_grade_id=sg_id,
                period_id=period_id
            ).update({'locked': True})
            db.session.commit()
            flash('Notas bloqueadas exitosamente.', 'success')
            return redirect(url_for('grades.grade_input_form', sg_id=sg_id, period_id=period_id))

        elif action == 'unlock':
            # Unlock grades for this subject-grade/period
            GradeRecord.query.filter_by(
                subject_grade_id=sg_id,
                period_id=period_id
            ).update({'locked': False})
            db.session.commit()
            flash('Notas desbloqueadas exitosamente.', 'success')
            return redirect(url_for('grades.grade_input_form', sg_id=sg_id, period_id=period_id))

        # Save grades
        saved_count = 0
        error_count = 0

        # Check if period is locked before saving
        locked_count = GradeRecord.query.filter_by(
            subject_grade_id=sg_id,
            period_id=period_id,
            locked=True
        ).count()
        total_existing = GradeRecord.query.filter_by(
            subject_grade_id=sg_id,
            period_id=period_id
        ).count()
        period_is_locked = total_existing > 0 and locked_count == total_existing

        for student in students:
            for criterion in criteria:
                field_name = f"grade_{student.id}_{criterion.id}"
                obs_field_name = f"obs_{student.id}_{criterion.id}"
                score_str = request.form.get(field_name, '').strip()
                observation = request.form.get(obs_field_name, '').strip()

                if not score_str:
                    continue

                try:
                    score = float(score_str)

                    # Validate score range
                    if score < MIN_GRADE or score > MAX_GRADE:
                        error_count += 1
                        continue

                    score = round(score, 1)

                    # Check if grade record already exists
                    existing = GradeRecord.query.filter_by(
                        student_id=student.id,
                        subject_grade_id=sg_id,
                        period_id=period_id,
                        criterion_id=criterion.id
                    ).first()

                    if existing:
                        # Check if locked
                        if existing.locked:
                            error_count += 1
                            continue
                        existing.score = score
                        if observation:
                            existing.observation = observation
                        existing.updated_at = datetime.utcnow()
                    else:
                        # If period is fully locked, don't allow new records
                        if period_is_locked:
                            error_count += 1
                            continue
                        new_record = GradeRecord(
                            student_id=student.id,
                            subject_grade_id=sg_id,
                            period_id=period_id,
                            criterion_id=criterion.id,
                            score=score,
                            observation=observation if observation else None,
                            created_by=current_user.id,
                            locked=False
                        )
                        db.session.add(new_record)

                    saved_count += 1

                except (ValueError, TypeError):
                    error_count += 1
                    continue

        # Calculate and save final grades for each student
        final_count = 0
        for student in students:
            final_score = GradeCalculatorService.calculate_final_grade(student.id, sg_id, period_id, criteria)
            if final_score is not None:
                GradeCalculatorService.save_final_grade(student.id, sg_id, period_id, final_score)
                final_count += 1

        db.session.commit()

        if error_count > 0:
            flash(f'{saved_count} notas guardadas, {error_count} con errores (fuera de rango 1.0-5.0 o bloqueadas).', 'warning')
        else:
            flash(f'{saved_count} notas guardadas exitosamente. {final_count} notas finales calculadas.', 'success')

        return redirect(url_for('grades.grade_input_form', sg_id=sg_id, period_id=period_id))

    # GET - load existing grades for display
    # Fetch all grade records for this subject-grade/period
    existing_records = GradeRecord.query.filter_by(
        subject_grade_id=sg_id,
        period_id=period_id
    ).all()

    # Build a dict: student_id -> criterion_id -> GradeRecord
    grade_data = {}
    for record in existing_records:
        if record.student_id not in grade_data:
            grade_data[record.student_id] = {}
        grade_data[record.student_id][record.criterion_id] = record

    # Check if grades are locked (all records for this sg/period must be locked)
    locked_records = GradeRecord.query.filter_by(
        subject_grade_id=sg_id,
        period_id=period_id,
        locked=True
    ).count()
    total_records = GradeRecord.query.filter_by(
        subject_grade_id=sg_id,
        period_id=period_id
    ).count()
    is_locked = total_records > 0 and locked_records == total_records

    # Convert criteria to JSON-serializable list for JavaScript
    criteria_json = [{'id': c.id, 'name': c.name, 'weight': c.weight, 'order': c.order} for c in criteria]

    return render_template(
        'grades/input.html',
        subject_grade=subject_grade,
        grade=grade,
        subject=subject,
        period=period,
        students=students,
        criteria=criteria,
        criteria_json=criteria_json,
        criteria_weights=criteria_weights,
        grade_data=grade_data,
        is_locked=is_locked,
        MIN_GRADE=MIN_GRADE,
        MAX_GRADE=MAX_GRADE,
        PASSING_GRADE=PASSING_GRADE
    )


# ============================================
# 3. Bulk Upload from Excel
# ============================================

@grades_bp.route('/upload', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin', 'teacher', 'coordinator')
def grade_upload():
    """
    Upload grades from an Excel file.
    Parses and validates the file, then saves to database.
    """
    institution = get_current_institution()
    if not institution:
        institution = Institution.query.first()
        if not institution:
            flash('No se ha configurado la institucion.', 'warning')
            return redirect(url_for('dashboard.index'))

    periods = AcademicPeriod.query.filter_by(
        institution_id=institution.id,
        academic_year=institution.academic_year
    ).order_by(AcademicPeriod.order).all()

    criteria = GradeCriteria.query.filter_by(
        institution_id=institution.id
    ).order_by(GradeCriteria.order).all()

    # Get available grades for the user
    if current_user.has_any_role('root', 'admin', 'coordinator'):
        grades_list = Grade.query.join(Campus).filter(
            Campus.institution_id == institution.id,
            Grade.academic_year == institution.academic_year
        ).order_by(Grade.name).all()
        all_subject_grades = SubjectGrade.query.join(Grade).join(Campus).join(Subject).filter(
            Campus.institution_id == institution.id,
            Grade.academic_year == institution.academic_year
        ).order_by(Grade.name, Subject.name).all()
    else:
        # Teacher: only their grades
        all_subject_grades = SubjectGrade.query.filter_by(teacher_id=current_user.id).join(Grade).join(Campus).filter(
            Campus.institution_id == institution.id,
            Grade.academic_year == institution.academic_year
        ).all()
        grade_ids = set(sg.grade_id for sg in all_subject_grades)
        grades_list = Grade.query.filter(Grade.id.in_(grade_ids)).order_by(Grade.name).all()

    if request.method == 'POST':
        # Get form data
        sg_id = request.form.get('subject_grade_id', type=int)
        period_id = request.form.get('period_id', type=int)

        if not sg_id or not period_id:
            flash('Seleccione una asignatura-grado y un periodo.', 'warning')
            return render_template(
                'grades/upload.html',
                grades=grades_list,
                subject_grades=all_subject_grades,
                periods=periods,
                criteria=criteria,
                selected_sg=sg_id,
                selected_period=period_id
            )

        # Verify subject-grade
        subject_grade = db.session.get(SubjectGrade, sg_id)
        if not subject_grade:
            flash('Asignatura-grado no encontrada.', 'error')
            return redirect(url_for('grades.grade_upload'))

        # Check permissions
        if current_user.has_role('teacher') and subject_grade.teacher_id != current_user.id:
            if not current_user.has_any_role('root', 'admin', 'coordinator'):
                flash('No tienes permiso para esta asignatura.', 'error')
                return redirect(url_for('grades.grade_upload'))

        # Check file
        if 'file' not in request.files:
            flash('No se selecciono ningun archivo.', 'warning')
            return render_template(
                'grades/upload.html',
                grades=grades_list,
                subject_grades=all_subject_grades,
                periods=periods,
                criteria=criteria,
                selected_sg=sg_id,
                selected_period=period_id
            )

        file = request.files['file']
        if file.filename == '':
            flash('No se selecciono ningun archivo.', 'warning')
            return render_template(
                'grades/upload.html',
                grades=grades_list,
                subject_grades=all_subject_grades,
                periods=periods,
                criteria=criteria,
                selected_sg=sg_id,
                selected_period=period_id
            )

        if not file.filename.endswith(('.xlsx', '.xls')):
            flash('Solo se permiten archivos Excel (.xlsx, .xls).', 'error')
            return render_template(
                'grades/upload.html',
                grades=grades_list,
                subject_grades=all_subject_grades,
                periods=periods,
                criteria=criteria,
                selected_sg=sg_id,
                selected_period=period_id
            )

        # Save file
        upload_folder = current_app.config['UPLOAD_FOLDER']
        excel_folder = os.path.join(upload_folder, 'excel_imports')
        os.makedirs(excel_folder, exist_ok=True)
        file_path = os.path.join(excel_folder, file.filename)
        file.save(file_path)

        from services.excel_handler import ExcelHandlerService
        result = ExcelHandlerService.process_grade_upload(file_path, institution, sg_id, period_id, current_user)
        
        if result['success']:
            msg = f"{result['saved_count']} notas guardadas desde Excel. {result['final_count']} notas finales calculadas."
            if result.get('errors'):
                msg += f" {result['error_count']} errores."
                flash(msg, 'warning')
            else:
                flash(msg, 'success')
            return redirect(url_for('grades.grade_input_form', sg_id=sg_id, period_id=period_id))
        else:
            flash(f"Error al procesar el archivo: {result.get('error', 'Desconocido')}", 'error')

    return render_template(
        'grades/upload.html',
        grades=grades_list,
        subject_grades=all_subject_grades,
        periods=periods,
        criteria=criteria,
        selected_sg=None,
        selected_period=None
    )


# ============================================
# 6. Lock/Unlock Panel
# ============================================

@grades_bp.route('/lock', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def lock_panel():
    """
    Admin panel to lock/unlock periods for subject-grades.
    """
    institution = get_current_institution()
    if not institution:
        institution = Institution.query.first()
        if not institution:
            flash('No se ha configurado la institucion.', 'warning')
            return redirect(url_for('dashboard.index'))

    grades_list = Grade.query.join(Campus).filter(
        Campus.institution_id == institution.id,
        Grade.academic_year == institution.academic_year
    ).order_by(Grade.name).all()

    all_subject_grades = SubjectGrade.query.join(Grade).join(Campus).join(Subject).filter(
        Campus.institution_id == institution.id,
        Grade.academic_year == institution.academic_year
    ).order_by(Grade.name, Subject.name).all()

    periods = AcademicPeriod.query.filter_by(
        institution_id=institution.id,
        academic_year=institution.academic_year
    ).order_by(AcademicPeriod.order).all()

    if request.method == 'POST':
        sg_id = request.form.get('subject_grade_id', type=int)
        period_id = request.form.get('period_id', type=int)
        action = request.form.get('action')

        if not sg_id or not period_id:
            flash('Seleccione una asignatura-grado y un periodo.', 'warning')
            return redirect(url_for('grades.lock_panel'))

        subject_grade = db.session.get(SubjectGrade, sg_id)
        if not subject_grade:
            flash('Asignatura-grado no encontrada.', 'error')
            return redirect(url_for('grades.lock_panel'))

        period = db.session.get(AcademicPeriod, period_id)
        if not period:
            flash('Periodo academico no encontrado.', 'error')
            return redirect(url_for('grades.lock_panel'))

        if action == 'lock':
            GradeRecord.query.filter_by(
                subject_grade_id=sg_id,
                period_id=period_id
            ).update({'locked': True})
            db.session.commit()
            flash(f'Periodo {period.name} bloqueado para {subject_grade.subject.name} - {subject_grade.grade.name}.', 'success')
        elif action == 'unlock':
            GradeRecord.query.filter_by(
                subject_grade_id=sg_id,
                period_id=period_id
            ).update({'locked': False})
            db.session.commit()
            flash(f'Periodo {period.name} desbloqueado para {subject_grade.subject.name} - {subject_grade.grade.name}.', 'success')

        return redirect(url_for('grades.lock_panel'))

    # Build lock status for each combination
    lock_status = []
    for sg in all_subject_grades:
        for period in periods:
            total = GradeRecord.query.filter_by(
                subject_grade_id=sg.id,
                period_id=period.id
            ).count()
            locked = GradeRecord.query.filter_by(
                subject_grade_id=sg.id,
                period_id=period.id,
                locked=True
            ).count()
            is_locked = total > 0 and locked == total
            lock_status.append({
                'sg': sg,
                'period': period,
                'total_records': total,
                'is_locked': is_locked
            })

    return render_template(
        'grades/lock_panel.html',
        grades=grades_list,
        subject_grades=all_subject_grades,
        periods=periods,
        lock_status=lock_status
    )


# ============================================
# 7. Final Grades by Period
# ============================================

@grades_bp.route('/final/<int:sg_id>/<int:period_id>', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin', 'teacher', 'coordinator')
def final_grades_view(sg_id, period_id):
    """
    View and calculate final grades for all students in a subject-grade/period.
    Shows table with all criteria scores and the weighted final.
    """
    subject_grade = db.session.get(SubjectGrade, sg_id)
    if not subject_grade:
        flash('Asignatura-grado no encontrada.', 'error')
        return redirect(url_for('grades.grade_input'))

    if current_user.has_role('teacher') and subject_grade.teacher_id != current_user.id:
        if not current_user.has_any_role('root', 'admin', 'coordinator'):
            flash('No tienes permiso para ver estas notas.', 'error')
            return redirect(url_for('grades.grade_input'))

    period = db.session.get(AcademicPeriod, period_id)
    if not period:
        flash('Periodo academico no encontrado.', 'error')
        return redirect(url_for('grades.grade_input'))

    grade = subject_grade.grade
    institution = grade.campus.institution
    subject = subject_grade.subject

    students = AcademicStudent.query.filter_by(
        grade_id=grade.id,
        status='activo'
    ).join(User).order_by(User.last_name, User.first_name).all()

    # Get institution from grade
    institution = grade.campus.institution

    # Get evaluation criteria (filtered by institution)
    criteria = GradeCriteria.query.filter_by(
        institution_id=institution.id
    ).order_by(GradeCriteria.order).all()

    if request.method == 'POST':
        # Recalculate all final grades
        calculated = 0
        for student in students:
            final_score = GradeCalculatorService.calculate_final_grade(student.id, sg_id, period_id, criteria)
            if final_score is not None:
                GradeCalculatorService.save_final_grade(student.id, sg_id, period_id, final_score)
                calculated += 1

        db.session.commit()
        flash(f'{calculated} notas finales calculadas y guardadas.', 'success')
        return redirect(url_for('grades.final_grades_view', sg_id=sg_id, period_id=period_id))

    # Build data table
    student_data = []
    for student in students:
        record_lookup = {}
        records = GradeRecord.query.filter_by(
            student_id=student.id,
            subject_grade_id=sg_id,
            period_id=period_id
        ).all()
        for r in records:
            record_lookup[r.criterion_id] = r

        final = FinalGrade.query.filter_by(
            student_id=student.id,
            subject_grade_id=sg_id,
            period_id=period_id
        ).first()

        student_data.append({
            'student': student,
            'user': student.user,
            'records': record_lookup,
            'final': final
        })

    return render_template(
        'grades/final_view.html',
        subject_grade=subject_grade,
        grade=grade,
        subject=subject,
        period=period,
        students=students,
        criteria=criteria,
        student_data=student_data,
        MIN_GRADE=MIN_GRADE,
        MAX_GRADE=MAX_GRADE,
        PASSING_GRADE=PASSING_GRADE
    )


# ============================================
# 8. Annual Grades
# ============================================

@grades_bp.route('/annual/<int:sg_id>')
@login_required
@role_required('root', 'admin', 'teacher', 'coordinator')
def annual_grades_view(sg_id):
    """
    View annual grades (average of 4 periods) for a subject-grade.
    """
    subject_grade = db.session.get(SubjectGrade, sg_id)
    if not subject_grade:
        flash('Asignatura-grado no encontrada.', 'error')
        return redirect(url_for('grades.grade_input'))

    if current_user.has_role('teacher') and subject_grade.teacher_id != current_user.id:
        if not current_user.has_any_role('root', 'admin', 'coordinator'):
            flash('No tienes permiso para ver estas notas.', 'error')
            return redirect(url_for('grades.grade_input'))

    institution = get_current_institution()
    if not institution:
        institution = Institution.query.first()

    grade = subject_grade.grade
    subject = subject_grade.subject

    periods = AcademicPeriod.query.filter_by(
        institution_id=institution.id,
        academic_year=institution.academic_year
    ).order_by(AcademicPeriod.order).all()

    students = AcademicStudent.query.filter_by(
        grade_id=grade.id,
        status='activo'
    ).join(User).order_by(User.last_name, User.first_name).all()

    # Calculate and save annual grades
    for student in students:
        GradeCalculatorService.calculate_and_save_annual_grades(student.id, sg_id, periods, institution.academic_year)

    db.session.commit()

    # Build data for display
    student_data = []
    for student in students:
        annual = AnnualGrade.query.filter_by(
            student_id=student.id,
            subject_grade_id=sg_id,
            academic_year=institution.academic_year
        ).first()

        period_grades = {}
        for period in periods:
            final = FinalGrade.query.filter_by(
                student_id=student.id,
                subject_grade_id=sg_id,
                period_id=period.id
            ).first()
            period_grades[period.id] = final

        student_data.append({
            'student': student,
            'user': student.user,
            'annual': annual,
            'period_grades': period_grades
        })

    return render_template(
        'grades/annual_view.html',
        subject_grade=subject_grade,
        grade=grade,
        subject=subject,
        periods=periods,
        student_data=student_data,
        MIN_GRADE=MIN_GRADE,
        MAX_GRADE=MAX_GRADE,
        PASSING_GRADE=PASSING_GRADE
    )


# ============================================
# 9. Student Full Grades View (Enhanced)
# ============================================

@grades_bp.route('/student/<int:student_id>')
@login_required
@role_required('root', 'admin', 'coordinator', 'teacher', 'student', 'parent')
def student_grades(student_id):
    """
    View all grades for a specific student.
    Shows all subjects and periods with color-coded grades.
    """
    student = db.session.get(AcademicStudent, student_id)
    if not student:
        flash('Estudiante no encontrado.', 'error')
        return redirect(url_for('students.list'))

    # Permission check: students can only see their own grades
    if current_user.has_role('student'):
        academic = AcademicStudent.query.filter_by(user_id=current_user.id).first()
        if not academic or academic.id != student_id:
            flash('No tienes permiso para ver estas notas.', 'error')
            return redirect(url_for('dashboard.index'))

    # Get all final grades for this student
    final_grades = FinalGrade.query.filter_by(
        student_id=student.id
    ).join(SubjectGrade).join(Subject).join(Grade).join(AcademicPeriod).all()

    # Get all grade records for more detail
    grade_records = GradeRecord.query.filter_by(
        student_id=student.id
    ).join(SubjectGrade).join(Subject).join(Grade).join(AcademicPeriod).join(GradeCriteria).all()

    # Organize data by period and subject
    # Structure: {period: {subject_grade_id: {subject, grade, final_score, status, records: [{criterion, score}]}}}
    organized = {}
    for fg in final_grades:
        period = fg.period
        sg = fg.subject_grade
        subject = sg.subject
        grade_obj = sg.grade

        if period.id not in organized:
            organized[period.id] = {
                'period': period,
                'subjects': {}
            }

        # Collect criteria records for this final grade
        records = [gr for gr in grade_records if gr.subject_grade_id == sg.id and gr.period_id == period.id]

        organized[period.id]['subjects'][sg.id] = {
            'subject_grade': sg,
            'subject': subject,
            'grade': grade_obj,
            'final_score': fg.final_score,
            'status': fg.status,
            'records': records
        }

    # Sort periods by order
    sorted_periods = sorted(organized.values(), key=lambda x: x['period'].order)

    # Calculate overall average
    all_scores = [fg.final_score for fg in final_grades if fg.final_score]
    overall_average = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0

    # Count passed/failed
    passed = sum(1 for fg in final_grades if fg.status == 'ganada')
    failed = sum(1 for fg in final_grades if fg.status == 'perdida')

    return render_template(
        'grades/student_view.html',
        student=student,
        user=student.user,
        sorted_periods=sorted_periods,
        overall_average=overall_average,
        passed=passed,
        failed=failed,
        total=len(final_grades),
        MIN_GRADE=MIN_GRADE,
        MAX_GRADE=MAX_GRADE,
        PASSING_GRADE=PASSING_GRADE
    )


# ============================================
# 5. Grade Summary for Group
# ============================================

@grades_bp.route('/summary/<int:sg_id>/<int:period_id>')
@login_required
@role_required('root', 'admin', 'teacher', 'coordinator')
def grade_summary(sg_id, period_id):
    """
    Grade summary for a group.
    Statistics: average, pass/fail rates, distribution.
    """
    subject_grade = db.session.get(SubjectGrade, sg_id)
    if not subject_grade:
        flash('Asignatura-grado no encontrada.', 'error')
        return redirect(url_for('grades.grade_input'))

    # Permission check
    if current_user.has_role('teacher') and subject_grade.teacher_id != current_user.id:
        if not current_user.has_any_role('root', 'admin', 'coordinator'):
            flash('No tienes permiso para ver este resumen.', 'error')
            return redirect(url_for('grades.grade_input'))

    period = db.session.get(AcademicPeriod, period_id)
    if not period:
        flash('Periodo academico no encontrado.', 'error')
        return redirect(url_for('grades.grade_input'))

    grade = subject_grade.grade
    subject = subject_grade.subject
    institution = grade.campus.institution

    # Get all final grades for this subject-grade/period
    final_grades = FinalGrade.query.filter_by(
        subject_grade_id=sg_id,
        period_id=period_id
    ).all()

    # Get all students in this grade
    students = AcademicStudent.query.filter_by(
        grade_id=grade.id,
        status='activo'
    ).join(User).order_by(User.last_name).all()

    # Build student grade lookup
    student_grades = {fg.student_id: fg for fg in final_grades}

    # Statistics
    scores = [fg.final_score for fg in final_grades if fg.final_score is not None]

    if scores:
        average = round(sum(scores) / len(scores), 2)
        max_score = round(max(scores), 2)
        min_score = round(min(scores), 2)
        median = sorted(scores)[len(scores) // 2]
        # Standard deviation
        variance = sum((s - average) ** 2 for s in scores) / len(scores)
        std_dev = round(variance ** 0.5, 2)
    else:
        average = 0.0
        max_score = 0.0
        min_score = 0.0
        median = 0.0
        std_dev = 0.0

    # Pass/fail counts
    passed = sum(1 for fg in final_grades if fg.status == 'ganada')
    failed = sum(1 for fg in final_grades if fg.status == 'perdida')
    not_evaluated = sum(1 for fg in final_grades if fg.status == 'no evaluado')
    total_with_grades = passed + failed

    pass_rate = round((passed / total_with_grades * 100), 1) if total_with_grades > 0 else 0
    fail_rate = round((failed / total_with_grades * 100), 1) if total_with_grades > 0 else 0

    # Distribution for chart (ranges: 1.0-1.9, 2.0-2.9, 3.0-3.9, 4.0-4.9, 5.0)
    distribution = {
        '1.0-1.9': 0,
        '2.0-2.9': 0,
        '3.0-3.9': 0,
        '4.0-4.9': 0,
        '5.0': 0
    }
    for s in scores:
        if s < 2.0:
            distribution['1.0-1.9'] += 1
        elif s < 3.0:
            distribution['2.0-2.9'] += 1
        elif s < 4.0:
            distribution['3.0-3.9'] += 1
        elif s < 5.0:
            distribution['4.0-4.9'] += 1
        else:
            distribution['5.0'] += 1

    # Get criteria (for detailed breakdown) - filtered by institution
    criteria = GradeCriteria.query.filter_by(
        institution_id=institution.id
    ).order_by(GradeCriteria.order).all()

    # Per-criteria statistics
    criteria_stats = []
    for criterion in criteria:
        records = GradeRecord.query.filter_by(
            subject_grade_id=sg_id,
            period_id=period_id,
            criterion_id=criterion.id
        ).all()
        record_scores = [r.score for r in records if r.score is not None]
        if record_scores:
            crit_avg = round(sum(record_scores) / len(record_scores), 2)
        else:
            crit_avg = 0.0
        criteria_stats.append({
            'criterion': criterion,
            'average': crit_avg,
            'count': len(record_scores)
        })

    return render_template(
        'grades/summary.html',
        subject_grade=subject_grade,
        grade=grade,
        subject=subject,
        period=period,
        students=students,
        student_grades=student_grades,
        final_grades=final_grades,
        average=average,
        max_score=max_score,
        min_score=min_score,
        median=median,
        std_dev=std_dev,
        passed=passed,
        failed=failed,
        not_evaluated=not_evaluated,
        pass_rate=pass_rate,
        fail_rate=fail_rate,
        distribution=distribution,
        criteria_stats=criteria_stats,
        MIN_GRADE=MIN_GRADE,
        MAX_GRADE=MAX_GRADE,
        PASSING_GRADE=PASSING_GRADE
    )


# ============================================
# Helper Functions
# ============================================
