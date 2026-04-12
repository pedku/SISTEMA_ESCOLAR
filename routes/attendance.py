"""
Attendance management routes.
Full implementation for taking attendance, viewing history, and summary reports.
"""

from datetime import datetime, date, timedelta
from sqlalchemy import func, extract
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.user import User
from models.institution import Institution, Campus
from models.academic import Grade, Subject, SubjectGrade, AcademicStudent
from models.attendance import Attendance
from utils.decorators import login_required, role_required
from utils.institution_resolver import get_current_institution, get_institution_grades, get_institution_students

attendance_bp = Blueprint('attendance', __name__)

# Attendance status options
ATTENDANCE_STATUS = {
    'presente': {'label': 'Presente', 'class': 'badge-success', 'icon': '✓'},
    'ausente': {'label': 'Ausente', 'class': 'badge-danger', 'icon': '✗'},
    'justificado': {'label': 'Justificado', 'class': 'badge-warning', 'icon': '⚑'},
    'excusado': {'label': 'Excusado', 'class': 'badge-info', 'icon': 'ℹ'}
}


# ============================================
# 1. Take Attendance Page
# ============================================

@attendance_bp.route('/')
@login_required
@role_required('root', 'admin', 'teacher', 'coordinator')
def attendance():
    """
    Selection page: choose grade + subject + date for attendance.
    Similar to grade_input pattern.
    """
    institution = get_current_institution()

    academic_year = institution.academic_year if institution else None

    # Determine which grades the user can access
    if current_user.has_any_role('root', 'admin', 'coordinator'):
        if institution:
            grades_list = Grade.query.join(Campus).filter(
                Campus.institution_id == institution.id,
                Grade.academic_year == academic_year
            ).order_by(Grade.name).all()

            subject_grades = SubjectGrade.query.join(Grade).join(Campus).filter(
                Campus.institution_id == institution.id,
                Grade.academic_year == academic_year
            ).order_by(Grade.name, Subject.name).all()
        else:
            # Root without active institution: see all
            grades_list = Grade.query.filter_by(
                academic_year=academic_year
            ).order_by(Grade.name).all() if academic_year else Grade.query.order_by(Grade.name).all()

            subject_grades = SubjectGrade.query.join(Grade).filter(
                Grade.academic_year == academic_year
            ).order_by(Grade.name, Subject.name).all() if academic_year else SubjectGrade.query.join(Grade).order_by(Grade.name, Subject.name).all()
    else:
        # Teacher: only their assigned subject-grades
        if institution:
            subject_grades = SubjectGrade.query.join(Grade).join(Campus).filter(
                SubjectGrade.teacher_id == current_user.id,
                Campus.institution_id == institution.id,
                Grade.academic_year == academic_year
            ).order_by(Grade.name, Subject.name).all()
        else:
            subject_grades = SubjectGrade.query.join(Grade).filter(
                SubjectGrade.teacher_id == current_user.id,
                Grade.academic_year == academic_year
            ).order_by(Grade.name, Subject.name).all()

        grades_list = list(set(sg.grade for sg in subject_grades))
        grades_list.sort(key=lambda g: g.name)

    # Get selected grade and subject from query params
    selected_grade_id = request.args.get('grade_id', type=int)
    selected_sg_id = request.args.get('sg_id', type=int)
    selected_date = request.args.get('date', date.today().isoformat())

    # If specific subject-grade selected, load students
    students = []
    selected_sg = None
    if selected_sg_id:
        selected_sg = SubjectGrade.query.get(selected_sg_id)
        if selected_sg:
            students_query = AcademicStudent.query.filter_by(
                grade_id=selected_sg.grade_id,
                status='activo'
            ).order_by(
                db.case(
                    (db.func.lower(AcademicStudent.guardian_name).startswith('a'), 1),
                    (db.func.lower(AcademicStudent.guardian_name).startswith('b'), 2),
                    else_=3
                ),
                AcademicStudent.user_id
            )

            # Filter by institution if applicable
            if institution:
                students_query = students_query.filter(AcademicStudent.institution_id == institution.id)

            students = students_query.all()

            # Sort by last name (we'll use user relationship)
            students = sorted(students, key=lambda s: _get_student_sort_key(s))

    return render_template('attendance/take.html',
                           grades=grades_list,
                           subject_grades=subject_grades,
                           students=students,
                           selected_sg=selected_sg,
                           selected_sg_id=selected_sg_id,
                           selected_date=selected_date,
                           status_options=ATTENDANCE_STATUS)


# ============================================
# 2. Save Attendance (POST)
# ============================================

@attendance_bp.route('/save', methods=['POST'])
@login_required
@role_required('root', 'admin', 'teacher', 'coordinator')
def save_attendance():
    """
    Save attendance records for a group.
    Expects JSON: {sg_id, date, records: [{student_id, status, observation}]}
    """
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Datos invalidos'}), 400

    sg_id = data.get('sg_id')
    date_str = data.get('date')
    records = data.get('records', [])

    if not sg_id or not date_str or not records:
        return jsonify({'success': False, 'error': 'Faltan datos requeridos'}), 400

    try:
        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'error': 'Fecha invalida'}), 400

    # Verify subject-grade exists
    sg = SubjectGrade.query.get(sg_id)
    if not sg:
        return jsonify({'success': False, 'error': 'Asignatura-grado no encontrada'}), 400

    # Teacher can only take attendance for their assigned subject-grades
    if current_user.has_role('teacher') and sg.teacher_id != current_user.id:
        return jsonify({'success': False, 'error': 'No tienes permiso para esta asignatura'}), 403

    saved_count = 0
    errors = []

    for record in records:
        student_id = record.get('student_id')
        status = record.get('status', 'presente')
        observation = record.get('observation', '')

        # Validate status
        if status not in ATTENDANCE_STATUS:
            errors.append(f'Estado invalido para estudiante {student_id}')
            continue

        # Verify student exists and belongs to this grade
        student = AcademicStudent.query.filter_by(
            id=student_id,
            grade_id=sg.grade_id,
            status='activo'
        ).first()

        if not student:
            errors.append(f'Estudiante {student_id} no encontrado en este grado')
            continue

        # Check if attendance already exists for this student/date/subject
        existing = Attendance.query.filter_by(
            student_id=student_id,
            subject_grade_id=sg_id,
            date=attendance_date
        ).first()

        if existing:
            # Update existing record
            existing.status = status
            existing.observation = observation if observation else existing.observation
        else:
            # Create new record
            new_attendance = Attendance(
                student_id=student_id,
                subject_grade_id=sg_id,
                date=attendance_date,
                status=status,
                observation=observation,
                recorded_by=current_user.id
            )
            db.session.add(new_attendance)

        saved_count += 1

    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'saved': saved_count,
            'errors': errors,
            'message': f'Asistencia guardada: {saved_count} registros'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Error al guardar: {str(e)}'}), 500


# ============================================
# 3. Get Existing Attendance (AJAX)
# ============================================

@attendance_bp.route('/get', methods=['GET'])
@login_required
@role_required('root', 'admin', 'teacher', 'coordinator')
def get_attendance():
    """
    Get existing attendance records for a given date and subject-grade.
    Used to pre-fill the attendance form.
    """
    sg_id = request.args.get('sg_id', type=int)
    date_str = request.args.get('date')

    if not sg_id or not date_str:
        return jsonify({'success': False, 'error': 'Faltan parametros'}), 400

    try:
        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'error': 'Fecha invalida'}), 400

    records = Attendance.query.filter_by(
        subject_grade_id=sg_id,
        date=attendance_date
    ).all()

    result = {r.student_id: {'status': r.status, 'observation': r.observation or ''} for r in records}

    return jsonify({'success': True, 'records': result})


# ============================================
# 4. Student Attendance History
# ============================================

@attendance_bp.route('/student/<int:student_id>')
@login_required
def student_attendance_history(student_id):
    """
    View attendance history for a specific student.
    """
    student = AcademicStudent.query.get_or_404(student_id)

    # Permission check
    if current_user.has_role('teacher'):
        # Teacher can only see attendance for their subject-grades
        sg_ids = [sg.id for sg in SubjectGrade.query.filter_by(teacher_id=current_user.id).all()]
        attendance_records = Attendance.query.filter(
            Attendance.student_id == student_id,
            Attendance.subject_grade_id.in_(sg_ids)
        ).order_by(Attendance.date.desc()).all()
    else:
        attendance_records = Attendance.query.filter_by(
            student_id=student_id
        ).order_by(Attendance.date.desc()).all()

    # Calculate summary stats
    total_records = len(attendance_records)
    presentes = sum(1 for r in attendance_records if r.status == 'presente')
    ausentes = sum(1 for r in attendance_records if r.status == 'ausente')
    justificados = sum(1 for r in attendance_records if r.status in ['justificado', 'excusado'])

    absence_rate = (ausentes / total_records * 100) if total_records > 0 else 0

    # Group by month for trend analysis
    monthly_stats = {}
    for record in attendance_records:
        month_key = record.date.strftime('%Y-%m')
        if month_key not in monthly_stats:
            monthly_stats[month_key] = {'presente': 0, 'ausente': 0, 'justificado': 0, 'excusado': 0}
        monthly_stats[month_key][record.status] += 1

    return render_template('attendance/summary.html',
                           student=student,
                           attendance_records=attendance_records,
                           total_records=total_records,
                           presentes=presentes,
                           ausentes=ausentes,
                           justificados=justificados,
                           absence_rate=round(absence_rate, 1),
                           monthly_stats=monthly_stats,
                           status_options=ATTENDANCE_STATUS)


# ============================================
# 5. Attendance Summary for Group
# ============================================

@attendance_bp.route('/summary')
@login_required
@role_required('root', 'admin', 'teacher', 'coordinator')
def attendance_summary():
    """
    Attendance summary for a grade + subject.
    Shows percentages and trends for the whole group.
    """
    institution = get_current_institution()

    sg_id = request.args.get('sg_id', type=int)
    if not sg_id:
        flash('Seleccione una asignatura y grado.', 'warning')
        return redirect(url_for('attendance.attendance'))

    sg = SubjectGrade.query.get_or_404(sg_id)

    # Permission check
    if current_user.has_role('teacher') and sg.teacher_id != current_user.id:
        flash('No tienes permiso para ver esta asignatura.', 'danger')
        return redirect(url_for('attendance.attendance'))

    # Verify institution access if applicable
    if institution:
        # Verify this subject-grade belongs to the current institution
        grade_campus = db.session.query(Campus).join(Grade, Grade.campus_id == Campus.id).filter(
            Grade.id == sg.grade_id,
            Campus.institution_id == institution.id
        ).first()
        if not grade_campus:
            flash('No tienes permiso para ver esta asignatura.', 'danger')
            return redirect(url_for('attendance.attendance'))

    # Get all students in this grade
    students_query = AcademicStudent.query.filter_by(
        grade_id=sg.grade_id,
        status='activo'
    ).order_by(AcademicStudent.user_id)

    if institution:
        students_query = students_query.filter(AcademicStudent.institution_id == institution.id)

    students = students_query.all()

    # Get all attendance records for this subject-grade
    all_records = Attendance.query.filter_by(
        subject_grade_id=sg_id
    ).all()

    # Calculate per-student stats
    student_stats = []
    for student in students:
        student_records = [r for r in all_records if r.student_id == student.id]
        total = len(student_records)
        presentes = sum(1 for r in student_records if r.status == 'presente')
        ausentes = sum(1 for r in student_records if r.status == 'ausente')
        justificados = sum(1 for r in student_records if r.status in ['justificado', 'excusado'])
        absence_rate = round((ausentes / total * 100) if total > 0 else 0, 1)

        student_stats.append({
            'student': student,
            'total': total,
            'presentes': presentes,
            'ausentes': ausentes,
            'justificados': justificados,
            'absence_rate': absence_rate,
            'present_rate': round((presentes / total * 100) if total > 0 else 0, 1)
        })

    # Overall group stats
    total_records = len(all_records)
    total_presentes = sum(1 for r in all_records if r.status == 'presente')
    total_ausentes = sum(1 for r in all_records if r.status == 'ausente')
    total_justificados = sum(1 for r in all_records if r.status in ['justificado', 'excusado'])

    # Monthly trend
    monthly_trend = {}
    for record in all_records:
        month_key = record.date.strftime('%Y-%m')
        if month_key not in monthly_trend:
            monthly_trend[month_key] = {'presente': 0, 'ausente': 0, 'justificado': 0, 'excusado': 0}
        monthly_trend[month_key][record.status] += 1

    # Students with critical absence rate (>20%)
    at_risk = [s for s in student_stats if s['absence_rate'] > 20]

    return render_template('attendance/summary_group.html',
                           subject_grade=sg,
                           student_stats=student_stats,
                           total_records=total_records,
                           total_presentes=total_presentes,
                           total_ausentes=total_ausentes,
                           total_justificados=total_justificados,
                           monthly_trend=monthly_trend,
                           at_risk_students=at_risk,
                           status_options=ATTENDANCE_STATUS)


# ============================================
# 6. Attendance by Date Range Report
# ============================================

@attendance_bp.route('/attendance/report')
@login_required
@role_required('root', 'admin', 'teacher', 'coordinator')
def attendance_report():
    """
    Generate attendance report for a date range.
    """
    institution = get_current_institution()

    sg_id = request.args.get('sg_id', type=int)
    start_date = request.args.get('start_date', type=str)
    end_date = request.args.get('end_date', type=str)

    if not sg_id:
        flash('Seleccione una asignatura y grado.', 'warning')
        return redirect(url_for('attendance.attendance'))

    sg = SubjectGrade.query.get_or_404(sg_id)

    # Verify institution access if applicable
    if institution:
        grade_campus = db.session.query(Campus).join(Grade, Grade.campus_id == Campus.id).filter(
            Grade.id == sg.grade_id,
            Campus.institution_id == institution.id
        ).first()
        if not grade_campus:
            flash('No tienes permiso para ver esta asignatura.', 'danger')
            return redirect(url_for('attendance.attendance'))

    # Default date range: current month
    today = date.today()
    if not start_date:
        start_date = today.replace(day=1).isoformat()
    if not end_date:
        end_date = today.isoformat()

    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        flash('Fechas invalidas.', 'danger')
        return redirect(url_for('attendance.attendance_summary', sg_id=sg_id))

    # Get records in range
    records = Attendance.query.filter(
        Attendance.subject_grade_id == sg_id,
        Attendance.date >= start,
        Attendance.date <= end
    ).all()

    # Get students
    students_query = AcademicStudent.query.filter_by(
        grade_id=sg.grade_id,
        status='activo'
    ).order_by(AcademicStudent.user_id)

    if institution:
        students_query = students_query.filter(AcademicStudent.institution_id == institution.id)

    students = students_query.all()

    # Build per-student report
    student_report = []
    for student in students:
        student_records = [r for r in records if r.student_id == student.id]
        total = len(student_records)
        presentes = sum(1 for r in student_records if r.status == 'presente')
        ausentes = sum(1 for r in student_records if r.status == 'ausente')
        justificados = sum(1 for r in student_records if r.status in ['justificado', 'excusado'])
        absence_rate = round((ausentes / total * 100) if total > 0 else 0, 1)

        student_report.append({
            'student': student,
            'total': total,
            'presentes': presentes,
            'ausentes': ausentes,
            'justificados': justificados,
            'absence_rate': absence_rate
        })

    return render_template('attendance/report.html',
                           subject_grade=sg,
                           student_report=student_report,
                           start_date=start_date,
                           end_date=end_date,
                           status_options=ATTENDANCE_STATUS)


# ============================================
# Helpers
# ============================================

def _get_student_sort_key(student):
    """Get sort key for student (by last name if available)."""
    if student.user and student.user.name:
        # Try to extract last name (second word)
        parts = student.user.name.strip().split()
        if len(parts) >= 2:
            return parts[-1].lower()
        return student.user.name.lower()
    return ''
