"""
Parent portal routes.
Full implementation for parents to view their children's grades, attendance,
observations, and report cards. Read-only access.
"""

from datetime import datetime, date, timedelta
from calendar import monthrange
from sqlalchemy import func
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from extensions import db
from models.academic import AcademicStudent, ParentStudent, SubjectGrade, Grade
from models.grading import AcademicPeriod, FinalGrade, GradeRecord
from models.attendance import Attendance
from models.observation import Observation
from models.report import ReportCard
from models.user import User
from utils.decorators import login_required, role_required
from utils.institution_resolver import get_current_institution

parent_bp = Blueprint('parent', __name__)


def _get_parent_students():
    """Get all students assigned to the current parent."""
    return (
        ParentStudent.query
        .filter_by(parent_id=current_user.id)
        .join(AcademicStudent)
        .options(
            db.joinedload(ParentStudent.student).joinedload(AcademicStudent.user),
            db.joinedload(ParentStudent.student).joinedload(AcademicStudent.grade)
        )
        .all()
    )


def _verify_student_access(student_id):
    """Verify that the current parent has access to the given student."""
    link = ParentStudent.query.filter_by(
        parent_id=current_user.id,
        student_id=student_id
    ).first()
    if not link:
        abort(403)
    return link.student


def _get_student_average(student_id, period_id=None):
    """Get the overall average for a student, optionally filtered by period."""
    query = FinalGrade.query.filter_by(student_id=student_id)
    if period_id:
        query = query.filter_by(period_id=period_id)
    grades = query.all()
    if not grades:
        return 0.0
    valid = [g.final_score for g in grades if g.final_score > 0]
    if not valid:
        return 0.0
    return round(sum(valid) / len(valid), 2)


def _get_attendance_stats(student_id, start_date=None, end_date=None):
    """Get attendance statistics for a student in a date range."""
    query = Attendance.query.filter_by(student_id=student_id)
    if start_date:
        query = query.filter(Attendance.date >= start_date)
    if end_date:
        query = query.filter(Attendance.date <= end_date)
    records = query.all()
    total = len(records)
    presentes = sum(1 for r in records if r.status == 'presente')
    ausentes = sum(1 for r in records if r.status == 'ausente')
    justificados = sum(1 for r in records if r.status in ('justificado', 'excusado'))
    return {
        'total': total,
        'presentes': presentes,
        'ausentes': ausentes,
        'justificados': justificados,
        'attendance_pct': round((presentes / total * 100), 1) if total > 0 else 0
    }


# ============================================
# 1. Dashboard
# ============================================

@parent_bp.route('/dashboard')
@login_required
@role_required('parent')
def parent_dashboard():
    """Parent portal dashboard showing assigned students and summaries."""
    parent_students = _get_parent_students()

    student_summaries = []
    for ps in parent_students:
        student = ps.student
        student_user = student.user

        # Current average
        avg = _get_student_average(student.id)

        # Attendance last 30 days
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)
        att_stats = _get_attendance_stats(student.id, start_date=thirty_days_ago, end_date=today)

        # Active alerts (negative observations not yet notified, or any recent negative)
        alerts = Observation.query.filter(
            Observation.student_id == student.id,
            Observation.type.in_(['negativa', 'convivencia'])
        ).order_by(Observation.date.desc()).limit(3).all()

        # Grade info
        grade_obj = student.grade
        campus_name = student.campus.name if student.campus else 'N/A'

        student_summaries.append({
            'student': student,
            'student_user': student_user,
            'grade': grade_obj,
            'campus_name': campus_name,
            'average': avg,
            'attendance_pct': att_stats['attendance_pct'],
            'alerts': alerts
        })

    return render_template(
        'parent/dashboard.html',
        students=parent_students,
        student_summaries=student_summaries
    )


# ============================================
# 2. Grades
# ============================================

@parent_bp.route('/grades/<int:student_id>')
@login_required
@role_required('parent')
def parent_view_grades(student_id):
    """View complete grades for parent's student."""
    student = _verify_student_access(student_id)
    student_user = student.user

    institution = get_current_institution()
    if not institution:
        flash('No se ha configurado la institucion.', 'warning')
        return redirect(url_for('parent.parent_dashboard'))

    academic_year = institution.academic_year

    # All periods for this institution/year
    periods = AcademicPeriod.query.filter_by(
        institution_id=institution.id,
        academic_year=academic_year
    ).order_by(AcademicPeriod.order).all()

    # Subject-grades for this student's grade
    subject_grades = []
    if student.grade_id:
        subject_grades = SubjectGrade.query.filter_by(
            grade_id=student.grade_id
        ).join(SubjectGrade.subject).order_by(Subject.name).all()

    # Build grade matrix: for each subject-grade, get final grades per period
    grade_matrix = []
    for sg in subject_grades:
        row = {'subject_grade': sg, 'subject_name': sg.subject.name, 'periods': {}}
        for period in periods:
            fg = FinalGrade.query.filter_by(
                student_id=student.id,
                subject_grade_id=sg.id,
                period_id=period.id
            ).first()
            row['periods'][period.id] = fg
        # Previous period comparison: get last period's final grade
        row['previous_avg'] = None
        if len(periods) > 1:
            prev_period = periods[-2] if len(periods) >= 2 else None
            if prev_period:
                prev_fg = FinalGrade.query.filter_by(
                    student_id=student.id,
                    subject_grade_id=sg.id,
                    period_id=prev_period.id
                ).first()
                if prev_fg:
                    row['previous_avg'] = prev_fg.final_score

        grade_matrix.append(row)

    # Overall average
    overall_avg = _get_student_average(student.id)

    return render_template(
        'parent/grades.html',
        student=student,
        student_user=student_user,
        periods=periods,
        grade_matrix=grade_matrix,
        overall_avg=overall_avg,
        MIN_GRADE=1.0,
        MAX_GRADE=5.0,
        PASSING_GRADE=3.0
    )


# ============================================
# 3. Attendance
# ============================================

@parent_bp.route('/attendance/<int:student_id>')
@login_required
@role_required('parent')
def parent_view_attendance(student_id):
    """View attendance for parent's student with calendar and stats."""
    student = _verify_student_access(student_id)

    # Parse month/year from query params (default: current month)
    today = date.today()
    selected_month = request.args.get('month', today.month, type=int)
    selected_year = request.args.get('year', today.year, type=int)

    # Clamp values
    selected_month = max(1, min(12, selected_month))
    selected_year = max(2020, min(2030, selected_year))

    # Month boundaries
    month_start = date(selected_year, selected_month, 1)
    _, last_day = monthrange(selected_year, selected_month)
    month_end = date(selected_year, selected_month, last_day)

    # Attendance records for the month
    month_records = Attendance.query.filter(
        Attendance.student_id == student.id,
        Attendance.date >= month_start,
        Attendance.date <= month_end
    ).order_by(Attendance.date).all()

    # Build calendar grid: date -> status map
    attendance_map = {}
    for rec in month_records:
        attendance_map[rec.date.day] = rec.status

    # Month stats
    month_stats = _get_attendance_stats(student.id, start_date=month_start, end_date=month_end)

    # Year stats
    year_start = date(selected_year, 1, 1)
    year_stats = _get_attendance_stats(student.id, start_date=year_start, end_date=today)

    # Monthly breakdown for bar chart (current year)
    monthly_data = []
    month_names = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                   'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    for m in range(1, 13):
        m_start = date(selected_year, m, 1)
        _, m_last = monthrange(selected_year, m)
        m_end = date(selected_year, m, m_last)
        if m_end > today:
            m_end = today
        if m_start > today:
            monthly_data.append({'month': month_names[m - 1], 'presentes': 0, 'ausentes': 0, 'justificados': 0})
            continue
        stats = _get_attendance_stats(student.id, start_date=m_start, end_date=m_end)
        monthly_data.append({
            'month': month_names[m - 1],
            'presentes': stats['presentes'],
            'ausentes': stats['ausentes'],
            'justificados': stats['justificados']
        })

    # Detailed history (last 50 records)
    history = Attendance.query.filter_by(
        student_id=student.id
    ).order_by(Attendance.date.desc()).limit(50).all()

    # Calendar helpers
    first_weekday = month_start.weekday()  # 0=Monday
    days_in_month = last_day
    calendar_days = []
    # Pad empty days before the 1st
    for _ in range(first_weekday):
        calendar_days.append(None)
    for d in range(1, days_in_month + 1):
        calendar_days.append(d)

    month_names_dict = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }

    # Navigation for prev/next month
    if selected_month == 1:
        prev_month, prev_year = 12, selected_year - 1
    else:
        prev_month, prev_year = selected_month - 1, selected_year
    if selected_month == 12:
        next_month, next_year = 1, selected_year + 1
    else:
        next_month, next_year = selected_month + 1, selected_year

    return render_template(
        'parent/attendance.html',
        student=student,
        attendance_map=attendance_map,
        month_stats=month_stats,
        year_stats=year_stats,
        monthly_data=monthly_data,
        history=history,
        calendar_days=calendar_days,
        selected_month=selected_month,
        selected_year=selected_year,
        month_name=month_names_dict.get(selected_month, ''),
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year
    )


# ============================================
# 4. Observations
# ============================================

@parent_bp.route('/observations/<int:student_id>')
@login_required
@role_required('parent')
def parent_view_observations(student_id):
    """View observations for parent's student with filters."""
    student = _verify_student_access(student_id)

    # Filter by type
    obs_type = request.args.get('type', 'all')
    query = Observation.query.filter_by(student_id=student.id)
    if obs_type != 'all':
        query = query.filter_by(type=obs_type)
    observations = query.order_by(Observation.date.desc()).all()

    # Counts by type
    total_obs = Observation.query.filter_by(student_id=student.id).count()
    positivas = Observation.query.filter_by(student_id=student.id, type='positiva').count()
    negativas = Observation.query.filter_by(student_id=student.id, type='negativa').count()
    seguimiento = Observation.query.filter_by(student_id=student.id, type='seguimiento').count()
    convivencia = Observation.query.filter_by(student_id=student.id, type='convivencia').count()

    # Type labels
    type_labels = {
        'positiva': 'Positiva',
        'negativa': 'Negativa',
        'seguimiento': 'Seguimiento',
        'convivencia': 'Convivencia'
    }

    # Type badge classes
    type_badge_class = {
        'positiva': 'bg-success',
        'negativa': 'bg-danger',
        'seguimiento': 'bg-info',
        'convivencia': 'bg-warning text-dark'
    }

    return render_template(
        'parent/observations.html',
        student=student,
        observations=observations,
        obs_type=obs_type,
        total_obs=total_obs,
        positivas=positivas,
        negativas=negativas,
        seguimiento=seguimiento,
        convivencia=convivencia,
        type_labels=type_labels,
        type_badge_class=type_badge_class
    )


# ============================================
# 5. Report Cards
# ============================================

@parent_bp.route('/report-cards/<int:student_id>')
@login_required
@role_required('parent')
def parent_view_report_cards(student_id):
    """View report cards for parent's student."""
    student = _verify_student_access(student_id)

    report_cards = ReportCard.query.filter_by(
        student_id=student.id
    ).join(ReportCard.period).order_by(
        AcademicPeriod.order.desc()
    ).all()

    # Include subject observations for each report card
    rc_data = []
    for rc in report_cards:
        subject_obs = rc.subject_observations.all()
        rc_data.append({
            'report_card': rc,
            'subject_observations': subject_obs
        })

    return render_template(
        'parent/report_cards.html',
        student=student,
        report_cards_data=rc_data
    )
