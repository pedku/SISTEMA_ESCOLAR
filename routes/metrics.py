"""
Metrics and analytics routes.
"""

from flask import Blueprint, render_template, request
from flask_login import current_user
from utils.decorators import login_required, role_required
from utils.institution_resolver import get_current_institution
from extensions import db
from models.academic import SubjectGrade, Grade, AcademicStudent, Subject
from models.grading import FinalGrade, GradeRecord, AcademicPeriod
from models.attendance import Attendance
from models.user import User
from models.institution import Campus
from datetime import datetime
from sqlalchemy import func, case

metrics_bp = Blueprint('metrics', __name__)


from services.metrics_service import MetricsService


@metrics_bp.route('/teacher')
@login_required
@role_required('root', 'admin', 'teacher', 'coordinator')
def teacher_metrics():
    """View teacher-specific metrics."""
    institution = get_current_institution()

    # Determine which teacher to show
    # If current user is a teacher, show their own data
    # If admin/root, show all or a specific teacher
    if current_user.is_teacher():
        teacher_id = current_user.id
    else:
        # Default to current user if teacher, or show all for admin/root
        teacher_id_param = request.args.get('teacher_id', type=int)
        teacher_id = teacher_id_param or current_user.id

    # Get groups data
    groups_data = MetricsService.get_teacher_groups_data(teacher_id, institution)

    # Get grade distribution
    all_grades = MetricsService.get_grade_distribution(teacher_id, institution)

    # Get period trend
    period_trend = MetricsService.get_period_trend(teacher_id, institution)
    period_labels = [p[0] for p in period_trend]
    period_scores = [p[1] for p in period_trend]

    # Get at-risk students
    risk_students = MetricsService.get_risk_students(teacher_id, institution)

    # Get absence data
    absences, absence_pct = MetricsService.get_total_absences(teacher_id, institution)

    # Calculate summary stats
    total_students = sum(g['student_count'] for g in groups_data)
    all_scores = [g['avg_score'] for g in groups_data if g['avg_score'] is not None]
    overall_avg = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0

    total_pass = sum(g['pass_count'] for g in groups_data)
    total_fail = sum(g['fail_count'] for g in groups_data)
    overall_pass_rate = round((total_pass / (total_pass + total_fail)) * 100, 1) if (total_pass + total_fail) > 0 else 0

    # Get list of teachers for admin/root filter
    teachers_list = []
    if current_user.has_any_role('root', 'admin', 'coordinator'):
        teacher_query = db.session.query(User).filter(User.role == 'teacher')
        if institution:
            teacher_query = teacher_query.filter(User.institution_id == institution.id)
        teachers_list = teacher_query.order_by(User.first_name).all()

    selected_teacher = db.session.get(User, teacher_id) if teacher_id else None

    # Get action plans
    action_plans = MetricsService.get_action_plans(teacher_id, institution)

    return render_template('metrics/teacher.html',
                           groups_data=groups_data,
                           grade_distribution=all_grades,
                           period_labels=period_labels,
                           period_scores=period_scores,
                           risk_students=risk_students,
                           action_plans=action_plans,
                           absences=absences,
                           absence_pct=absence_pct,
                           total_students=total_students,
                           overall_avg=overall_avg,
                           overall_pass_rate=overall_pass_rate,
                           teachers_list=teachers_list,
                           selected_teacher=selected_teacher,
                           current_teacher_id=teacher_id)


@metrics_bp.route('/teacher/comparison')
@login_required
@role_required('root', 'admin', 'coordinator')
def teacher_comparison():
    """Anonymous comparative view between teachers (Profesor A, B, C...)."""
    institution = get_current_institution()

    # Get all teachers with their subject-grades
    teacher_query = db.session.query(
        User.id.label('teacher_id'),
        User.first_name,
        User.last_name
    ).join(
        SubjectGrade, User.id == SubjectGrade.teacher_id
    ).filter(
        User.role == 'teacher'
    ).distinct()

    if institution:
        teacher_query = teacher_query.join(Grade, SubjectGrade.grade_id == Grade.id).join(
            Campus, Grade.campus_id == Campus.id
        ).filter(Campus.institution_id == institution.id)

    teachers = teacher_query.order_by(User.first_name).all()

    if not teachers:
        return render_template('metrics/teacher_comparison.html', teacher_data=[], global_avg=0, best_pass_rate=0)

    # Build anonymous data
    teacher_data = []
    all_avgs = []

    for teacher in teachers:
        # Get subject-grades for this teacher
        sg_query = db.session.query(SubjectGrade.id).filter(
            SubjectGrade.teacher_id == teacher.teacher_id
        )
        if institution:
            sg_query = sg_query.join(Grade).join(Campus).filter(
                Campus.institution_id == institution.id
            )
        sg_ids = [sg[0] for sg in sg_query.all()]

        if not sg_ids:
            continue

        # Get students
        grade_ids = db.session.query(Grade.id).join(
            SubjectGrade, Grade.id == SubjectGrade.grade_id
        ).filter(
            SubjectGrade.teacher_id == teacher.teacher_id
        ).distinct().all()
        grade_ids = [g[0] for g in grade_ids]

        student_count = db.session.query(func.count()).select_from(AcademicStudent).filter(
            AcademicStudent.grade_id.in_(grade_ids),
            AcademicStudent.status == 'activo'
        ).scalar() if grade_ids else 0

        group_count = len(sg_ids)

        # Get final grades
        scores = db.session.query(FinalGrade.final_score).filter(
            FinalGrade.subject_grade_id.in_(sg_ids),
            FinalGrade.final_score.isnot(None)
        ).all()
        scores = [s[0] for s in scores]

        avg_score = round(sum(scores) / len(scores), 2) if scores else 0
        passed = sum(1 for s in scores if s >= 3.0)
        failed = sum(1 for s in scores if s < 3.0)
        pass_rate = round((passed / (passed + failed)) * 100, 1) if (passed + failed) > 0 else 0

        all_avgs.append(avg_score)

        teacher_data.append({
            'teacher_id': teacher.teacher_id,
            'group_count': group_count,
            'student_count': student_count or 0,
            'avg_score': avg_score,
            'pass_rate': pass_rate,
            'passed': passed,
            'failed': failed
        })

    # Sort by avg_score descending and assign letters
    teacher_data.sort(key=lambda x: x['avg_score'], reverse=True)

    # Calculate percentiles
    for i, td in enumerate(teacher_data):
        td['letter'] = chr(65 + i)  # A, B, C...
        below_count = sum(1 for a in all_avgs if a < td['avg_score'])
        td['percentile'] = round((below_count / len(all_avgs)) * 100, 1) if all_avgs else 0
        td['is_best'] = (i == 0)

    global_avg = round(sum(all_avgs) / len(all_avgs), 2) if all_avgs else 0
    best_pass_rate = max((td['pass_rate'] for td in teacher_data), default=0)

    return render_template('metrics/teacher_comparison.html',
                           teacher_data=teacher_data,
                           global_avg=global_avg,
                           best_pass_rate=best_pass_rate)


@metrics_bp.route('/teacher/attendance')
@login_required
@role_required('root', 'admin', 'teacher', 'coordinator')
def teacher_attendance():
    """Attendance vs performance correlation view."""
    institution = get_current_institution()

    if current_user.is_teacher():
        teacher_id = current_user.id
    else:
        teacher_id = request.args.get('teacher_id', type=int) or current_user.id

    # Get scatter plot data
    scatter_data = MetricsService.get_attendance_data(teacher_id, institution)

    # Calculate correlation
    if scatter_data:
        attendance_pcts = [d['attendance_pct'] for d in scatter_data]
        avg_scores = [d['avg_score'] for d in scatter_data if d['avg_score'] > 0]

        # Filter to pairs where both values exist
        pairs = [(d['attendance_pct'], d['avg_score']) for d in scatter_data
                 if d['avg_score'] > 0]

        if len(pairs) > 1:
            xs = [p[0] for p in pairs]
            ys = [p[1] for p in pairs]
            n = len(pairs)
            sum_x = sum(xs)
            sum_y = sum(ys)
            sum_xy = sum(x * y for x, y in pairs)
            sum_x2 = sum(x * x for x in xs)
            sum_y2 = sum(y * y for y in ys)

            numerator = n * sum_xy - sum_x * sum_y
            denom = ((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)) ** 0.5
            correlation = round(numerator / denom, 3) if denom != 0 else 0
        else:
            correlation = 0
    else:
        correlation = 0

    # Summary stats
    total_students = len(scatter_data)
    if scatter_data:
        avg_attendance = round(sum(d['attendance_pct'] for d in scatter_data) / total_students, 1)
        avg_score = round(sum(d['avg_score'] for d in scatter_data if d['avg_score'] > 0) /
                          max(1, sum(1 for d in scatter_data if d['avg_score'] > 0)), 2)
    else:
        avg_attendance = 0
        avg_score = 0

    # Low attendance students (< 80%)
    low_attendance = [d for d in scatter_data if d['attendance_pct'] < 80]

    # Students with both low attendance and low grades
    critical_students = [d for d in scatter_data
                         if d['attendance_pct'] < 80 and d['avg_score'] < 3.0]

    selected_teacher = db.session.get(User, teacher_id) if teacher_id else None

    teachers_list = []
    if current_user.has_any_role('root', 'admin', 'coordinator'):
        teacher_query = db.session.query(User).filter(User.role == 'teacher')
        if institution:
            teacher_query = teacher_query.filter(User.institution_id == institution.id)
        teachers_list = teacher_query.order_by(User.first_name).all()

    return render_template('metrics/teacher_attendance.html',
                           scatter_data=scatter_data,
                           correlation=correlation,
                           total_students=total_students,
                           avg_attendance=avg_attendance,
                           avg_score=avg_score,
                           low_attendance=low_attendance,
                           critical_students=critical_students,
                           selected_teacher=selected_teacher,
                           current_teacher_id=teacher_id,
                           teachers_list=teachers_list)


@metrics_bp.route('/institution')
@login_required
@role_required('root', 'admin', 'coordinator')
def institution_metrics():
    """View institution-wide metrics."""
    institution = get_current_institution()

    # --- KPIs ---
    # Get all students in institution
    students_query = db.session.query(AcademicStudent).filter(
        AcademicStudent.status == 'activo'
    )
    if institution:
        students_query = students_query.filter(AcademicStudent.institution_id == institution.id)
    total_students = students_query.count()

    # Get all final grades and compute average
    grades_query = db.session.query(FinalGrade).filter(
        FinalGrade.final_score.isnot(None)
    )
    if institution:
        grades_query = grades_query.join(SubjectGrade).join(Grade).join(
            Campus, Grade.campus_id == Campus.id
        ).filter(Campus.institution_id == institution.id)

    all_final_grades = grades_query.all()
    all_scores = [fg.final_score for fg in all_final_grades if fg.final_score is not None]
    inst_avg = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0

    # Approval rate
    passed = sum(1 for s in all_scores if s >= 3.0)
    failed = sum(1 for s in all_scores if s < 3.0)
    pass_rate = round((passed / (passed + failed)) * 100, 1) if (passed + failed) > 0 else 0

    # Students at risk (avg < 3.0)
    student_avg_query = db.session.query(
        FinalGrade.student_id,
        func.avg(FinalGrade.final_score).label('avg_score')
    ).filter(
        FinalGrade.final_score.isnot(None)
    ).group_by(FinalGrade.student_id)

    if institution:
        student_avg_query = student_avg_query.join(SubjectGrade).join(Grade).join(
            Campus, Grade.campus_id == Campus.id
        ).filter(Campus.institution_id == institution.id)

    student_averages = student_avg_query.subquery()
    at_risk = db.session.query(func.count()).select_from(student_averages).filter(
        student_averages.c.avg_score < 3.0
    ).scalar() or 0

    # Absenteeism rate
    attendance_query = db.session.query(Attendance)
    if institution:
        attendance_query = attendance_query.join(SubjectGrade).join(Grade).join(
            Campus, Grade.campus_id == Campus.id
        ).filter(Campus.institution_id == institution.id)

    total_attendance = attendance_query.count()
    absences = attendance_query.filter(Attendance.status == 'ausente').count()
    absence_rate = round((absences / total_attendance) * 100, 1) if total_attendance > 0 else 0

    # --- Performance by Campus (Sede) ---
    campus_data = []
    campuses = db.session.query(Campus).filter(Campus.active == True)
    if institution:
        campuses = campuses.filter(Campus.institution_id == institution.id)
    campuses = campuses.all()

    for campus in campuses:
        grades = db.session.query(Grade).filter(Grade.campus_id == campus.id).all()
        grade_ids = [g.id for g in grades]

        if not grade_ids:
            continue

        sg_ids = db.session.query(SubjectGrade.id).filter(
            SubjectGrade.grade_id.in_(grade_ids)
        ).all()
        sg_ids = [sg[0] for sg in sg_ids]

        if not sg_ids:
            continue

        sg_students = db.session.query(AcademicStudent.id).filter(
            AcademicStudent.grade_id.in_(grade_ids),
            AcademicStudent.status == 'activo'
        ).distinct().count()

        campus_grades = db.session.query(FinalGrade.final_score).filter(
            FinalGrade.subject_grade_id.in_(sg_ids),
            FinalGrade.final_score.isnot(None)
        ).all()
        campus_scores = [g[0] for g in campus_grades]
        campus_avg = round(sum(campus_scores) / len(campus_scores), 2) if campus_scores else 0
        campus_passed = sum(1 for s in campus_scores if s >= 3.0)
        campus_failed = sum(1 for s in campus_scores if s < 3.0)
        campus_pass_rate = round((campus_passed / (campus_passed + campus_failed)) * 100, 1) if (campus_passed + campus_failed) > 0 else 0
        campus_at_risk = sum(1 for s in campus_scores if s < 3.0)

        campus_data.append({
            'campus_name': campus.name,
            'student_count': sg_students,
            'avg_score': campus_avg,
            'pass_rate': campus_pass_rate,
            'at_risk_count': campus_at_risk
        })

    # --- Performance by Grade ---
    grade_data = []
    grades_query = db.session.query(Grade)
    if institution:
        grades_query = grades_query.join(Campus).filter(Campus.institution_id == institution.id)
    grades_query = grades_query.order_by(Grade.name)

    for grade in grades_query.all():
        sg_ids = db.session.query(SubjectGrade.id).filter(
            SubjectGrade.grade_id == grade.id
        ).all()
        sg_ids = [sg[0] for sg in sg_ids]

        if not sg_ids:
            continue

        grade_students = db.session.query(AcademicStudent.id).filter(
            AcademicStudent.grade_id == grade.id,
            AcademicStudent.status == 'activo'
        ).distinct().count()

        grade_grades = db.session.query(FinalGrade.final_score).filter(
            FinalGrade.subject_grade_id.in_(sg_ids),
            FinalGrade.final_score.isnot(None)
        ).all()
        grade_scores = [g[0] for g in grade_grades]
        grade_avg = round(sum(grade_scores) / len(grade_scores), 2) if grade_scores else 0
        grade_passed = sum(1 for s in grade_scores if s >= 3.0)
        grade_failed = sum(1 for s in grade_scores if s < 3.0)
        grade_pass_rate = round((grade_passed / (grade_passed + grade_failed)) * 100, 1) if (grade_passed + grade_failed) > 0 else 0

        grade_data.append({
            'grade_name': grade.name,
            'campus_name': grade.campus.name if grade.campus else 'N/A',
            'student_count': grade_students,
            'avg_score': grade_avg,
            'pass_rate': grade_pass_rate
        })

    # --- Top 10 Best Students ---
    top_students = db.session.query(
        AcademicStudent.id.label('student_id'),
        User.first_name,
        User.last_name,
        Grade.name.label('grade_name'),
        func.avg(FinalGrade.final_score).label('avg_score')
    ).join(
        User, AcademicStudent.user_id == User.id
    ).join(
        Grade, AcademicStudent.grade_id == Grade.id
    ).join(
        FinalGrade, AcademicStudent.id == FinalGrade.student_id
    ).filter(
        AcademicStudent.status == 'activo',
        FinalGrade.final_score.isnot(None)
    )

    if institution:
        top_students = top_students.join(Campus, Grade.campus_id == Campus.id).filter(
            Campus.institution_id == institution.id
        )

    top_students = top_students.group_by(
        AcademicStudent.id, User.first_name, User.last_name, Grade.name
    ).order_by(
        func.avg(FinalGrade.final_score).desc()
    ).limit(10).all()

    top_students_list = []
    for ts in top_students:
        # Count failed subjects
        failed_subjects = db.session.query(func.count()).select_from(FinalGrade).join(
            SubjectGrade, FinalGrade.subject_grade_id == SubjectGrade.id
        ).filter(
            FinalGrade.student_id == ts.student_id,
            FinalGrade.final_score < 3.0
        ).scalar() or 0

        top_students_list.append({
            'student_id': ts.student_id,
            'student_name': f"{ts.first_name} {ts.last_name}",
            'grade_name': ts.grade_name,
            'avg_score': round(ts.avg_score, 2),
            'failed_subjects': failed_subjects
        })

    # --- Top 10 Students at Risk ---
    risk_students_query = db.session.query(
        AcademicStudent.id.label('student_id'),
        User.first_name,
        User.last_name,
        Grade.name.label('grade_name'),
        func.avg(FinalGrade.final_score).label('avg_score')
    ).join(
        User, AcademicStudent.user_id == User.id
    ).join(
        Grade, AcademicStudent.grade_id == Grade.id
    ).join(
        FinalGrade, AcademicStudent.id == FinalGrade.student_id
    ).filter(
        AcademicStudent.status == 'activo',
        FinalGrade.final_score.isnot(None)
    )

    if institution:
        risk_students_query = risk_students_query.join(Campus, Grade.campus_id == Campus.id).filter(
            Campus.institution_id == institution.id
        )

    risk_students_query = risk_students_query.group_by(
        AcademicStudent.id, User.first_name, User.last_name, Grade.name
    ).having(
        func.avg(FinalGrade.final_score) < 3.0
    ).order_by(
        func.avg(FinalGrade.final_score).asc()
    ).limit(10).all()

    risk_students_list = []
    for rs in risk_students_query:
        failed_subjects = db.session.query(func.count()).select_from(FinalGrade).filter(
            FinalGrade.student_id == rs.student_id,
            FinalGrade.final_score < 3.0
        ).scalar() or 0

        risk_students_list.append({
            'student_id': rs.student_id,
            'student_name': f"{rs.first_name} {rs.last_name}",
            'grade_name': rs.grade_name,
            'avg_score': round(rs.avg_score, 2),
            'failed_subjects': failed_subjects
        })

    return render_template('metrics/institution.html',
                           inst_avg=inst_avg,
                           pass_rate=pass_rate,
                           at_risk_count=at_risk,
                           absence_rate=absence_rate,
                           total_students=total_students,
                           campus_data=campus_data,
                           grade_data=grade_data,
                           top_students=top_students_list,
                           risk_students=risk_students_list)


@metrics_bp.route('/heatmap')
@login_required
@role_required('root', 'admin', 'coordinator')
def metrics_heatmap():
    """View performance heatmap."""
    institution = get_current_institution()

    # Get all grades
    grades_query = db.session.query(Grade)
    if institution:
        grades_query = grades_query.join(Campus).filter(Campus.institution_id == institution.id)
    grades_query = grades_query.order_by(Grade.name)
    all_grades = grades_query.all()

    # Get all subjects
    subjects_query = db.session.query(Subject)
    if institution:
        subjects_query = subjects_query.filter(Subject.institution_id == institution.id)
    subjects_query = subjects_query.order_by(Subject.name)
    all_subjects = subjects_query.all()

    # Build matrix: grade x subject -> failure rate
    heatmap_data = []
    for grade in all_grades:
        row = {'grade_name': grade.name, 'campus_name': grade.campus.name if grade.campus else 'N/A', 'cells': {}}

        sg_ids = db.session.query(SubjectGrade.id, SubjectGrade.subject_id).filter(
            SubjectGrade.grade_id == grade.id
        ).all()
        sg_map = {sg[1]: sg[0] for sg in sg_ids}  # subject_id -> sg_id

        for subject in all_subjects:
            if subject.id not in sg_map:
                row['cells'][subject.id] = None
                continue

            sg_id = sg_map[subject.id]
            total_grades = db.session.query(func.count()).select_from(FinalGrade).filter(
                FinalGrade.subject_grade_id == sg_id,
                FinalGrade.final_score.isnot(None)
            ).scalar() or 0

            failed_grades = db.session.query(func.count()).select_from(FinalGrade).filter(
                FinalGrade.subject_grade_id == sg_id,
                FinalGrade.final_score < 3.0
            ).scalar() or 0

            failure_rate = round((failed_grades / total_grades) * 100, 1) if total_grades > 0 else 0
            avg_score = db.session.query(func.avg(FinalGrade.final_score)).filter(
                FinalGrade.subject_grade_id == sg_id,
                FinalGrade.final_score.isnot(None)
            ).scalar()
            avg_score = round(avg_score, 2) if avg_score else 0

            row['cells'][subject.id] = {
                'failure_rate': failure_rate,
                'avg_score': avg_score,
                'total': total_grades,
                'failed': failed_grades
            }

        heatmap_data.append(row)

    return render_template('metrics/heatmap.html',
                           grades=all_grades,
                           subjects=all_subjects,
                           heatmap_data=heatmap_data)


@metrics_bp.route('/trends')
@login_required
@role_required('root', 'admin', 'coordinator')
def metrics_trends():
    """View institutional trends over time."""
    institution = get_current_institution()

    # Get academic periods (last 2 years)
    periods_query = db.session.query(AcademicPeriod)
    if institution:
        periods_query = periods_query.filter(AcademicPeriod.institution_id == institution.id)
    periods_query = periods_query.order_by(AcademicPeriod.academic_year.desc(), AcademicPeriod.order.desc())
    periods = periods_query.all()

    # Filter to last 2 years
    if periods:
        years = sorted(set(p.academic_year for p in periods), reverse=True)[:2]
        periods = [p for p in periods if p.academic_year in years]
        periods.sort(key=lambda p: (p.academic_year, p.order))

    period_labels = [f"{p.short_name} ({p.academic_year})" for p in periods]
    period_ids = [p.id for p in periods]

    # Average per period
    avg_per_period = []
    pass_rate_per_period = []

    for period in periods:
        fg_query = db.session.query(FinalGrade.final_score).filter(
            FinalGrade.period_id == period.id,
            FinalGrade.final_score.isnot(None)
        )

        if institution:
            fg_query = fg_query.join(SubjectGrade).join(Grade).join(
                Campus, Grade.campus_id == Campus.id
            ).filter(Campus.institution_id == institution.id)

        scores = [fg[0] for fg in fg_query.all()]
        if scores:
            avg = round(sum(scores) / len(scores), 2)
            passed = sum(1 for s in scores if s >= 3.0)
            pr = round((passed / len(scores)) * 100, 1)
        else:
            avg = 0
            pr = 0

        avg_per_period.append(avg)
        pass_rate_per_period.append(pr)

    # Analysis: improvement or deterioration
    trend_analysis = ''
    if len(avg_per_period) >= 2:
        first_half = avg_per_period[:len(avg_per_period) // 2]
        second_half = avg_per_period[len(avg_per_period) // 2:]
        avg_first = sum(first_half) / len(first_half) if first_half else 0
        avg_second = sum(second_half) / len(second_half) if second_half else 0
        diff = round(avg_second - avg_first, 2)

        if diff > 0:
            trend_analysis = f"mejora"
        elif diff < 0:
            trend_analysis = f"deterioro"
        else:
            trend_analysis = f"estabilidad"

    # Monthly attendance trend
    attendance_query = db.session.query(
        func.date_trunc('month', Attendance.date).label('month'),
        func.count().label('total'),
        func.sum(case((Attendance.status == 'presente', 1), else_=0)).label('present')
    )

    if institution:
        attendance_query = attendance_query.join(SubjectGrade).join(Grade).join(
            Campus, Grade.campus_id == Campus.id
        ).filter(Campus.institution_id == institution.id)

    attendance_query = attendance_query.group_by(
        func.date_trunc('month', Attendance.date)
    ).order_by(
        func.date_trunc('month', Attendance.date)
    )

    # Use raw SQL for SQLite compatibility
    attendance_raw = db.session.query(
        func.strftime('%Y-%m', Attendance.date).label('month'),
        func.count().label('total'),
        func.sum(case((Attendance.status == 'presente', 1), else_=0)).label('present')
    )

    if institution:
        attendance_raw = attendance_raw.join(SubjectGrade).join(Grade).join(
            Campus, Grade.campus_id == Campus.id
        ).filter(Campus.institution_id == institution.id)

    attendance_raw = attendance_raw.group_by(
        func.strftime('%Y-%m', Attendance.date)
    ).order_by(
        func.strftime('%Y-%m', Attendance.date)
    ).all()

    attendance_labels = [a[0] for a in attendance_raw]
    attendance_rates = [round((a[2] / a[1]) * 100, 1) if a[1] > 0 else 0 for a in attendance_raw]

    return render_template('metrics/trends.html',
                           period_labels=period_labels,
                           avg_per_period=avg_per_period,
                           pass_rate_per_period=pass_rate_per_period,
                           trend_analysis=trend_analysis,
                           attendance_labels=attendance_labels,
                           attendance_rates=attendance_rates)


@metrics_bp.route('/export')
@login_required
@role_required('root', 'admin', 'coordinator')
def metrics_export():
    """Export all metrics to Excel file."""
    from io import BytesIO
    from flask import send_file
    try:
        import openpyxl
    except ImportError:
        from flask import flash, redirect
        flash('openpyxl no está instalado. Instálalo con: pip install openpyxl', 'error')
        return redirect(url_for('metrics.institution_metrics'))

    institution = get_current_institution()

    wb = openpyxl.Workbook()

    # --- Sheet 1: KPIs ---
    ws1 = wb.active
    ws1.title = "KPIs Generales"

    # Get stats
    all_final_grades = db.session.query(FinalGrade).filter(FinalGrade.final_score.isnot(None))
    if institution:
        all_final_grades = all_final_grades.join(SubjectGrade).join(Grade).join(
            Campus, Grade.campus_id == Campus.id
        ).filter(Campus.institution_id == institution.id)
    all_final_grades = all_final_grades.all()

    all_scores = [fg.final_score for fg in all_final_grades]
    inst_avg = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0
    passed = sum(1 for s in all_scores if s >= 3.0)
    failed = sum(1 for s in all_scores if s < 3.0)
    pass_rate = round((passed / (passed + failed)) * 100, 1) if (passed + failed) > 0 else 0

    student_avg_query = db.session.query(
        FinalGrade.student_id,
        func.avg(FinalGrade.final_score).label('avg_score')
    ).filter(FinalGrade.final_score.isnot(None))
    if institution:
        student_avg_query = student_avg_query.join(SubjectGrade).join(Grade).join(
            Campus, Grade.campus_id == Campus.id
        ).filter(Campus.institution_id == institution.id)
    student_avg_query = student_avg_query.group_by(FinalGrade.student_id).all()

    at_risk = sum(1 for sa in student_avg_query if sa.avg_score < 3.0)

    attendance_query = db.session.query(Attendance)
    if institution:
        attendance_query = attendance_query.join(SubjectGrade).join(Grade).join(
            Campus, Grade.campus_id == Campus.id
        ).filter(Campus.institution_id == institution.id)
    total_att = attendance_query.count()
    absences = attendance_query.filter(Attendance.status == 'ausente').count()
    absence_rate = round((absences / total_att) * 100, 1) if total_att > 0 else 0

    ws1.append(["Métrica", "Valor"])
    ws1.append(["Promedio Institucional", inst_avg])
    ws1.append(["% Aprobación", f"{pass_rate}%"])
    ws1.append(["Estudiantes en Riesgo", at_risk])
    ws1.append(["Tasa de Inasistencia", f"{absence_rate}%"])
    ws1.append(["Total Estudiantes Activos", db.session.query(func.count(AcademicStudent.id)).filter(
        AcademicStudent.status == 'activo',
        AcademicStudent.institution_id == (institution.id if institution else AcademicStudent.institution_id)
    ).scalar() if institution else db.session.query(func.count(AcademicStudent.id)).filter(
        AcademicStudent.status == 'activo'
    ).scalar()])

    # --- Sheet 2: Campus Performance ---
    ws2 = wb.active
    ws2.title = "Rendimiento por Sede"
    ws2.append(["Sede", "Estudiantes", "Promedio", "% Aprobación", "En Riesgo"])

    campuses = db.session.query(Campus).filter(Campus.active == True)
    if institution:
        campuses = campuses.filter(Campus.institution_id == institution.id)

    for campus in campuses.all():
        grades = db.session.query(Grade).filter(Grade.campus_id == campus.id).all()
        grade_ids = [g.id for g in grades]
        if not grade_ids:
            continue

        sg_ids = db.session.query(SubjectGrade.id).filter(SubjectGrade.grade_id.in_(grade_ids)).all()
        sg_ids = [sg[0] for sg in sg_ids]
        if not sg_ids:
            continue

        campus_scores = [fg.final_score for fg in db.session.query(FinalGrade).filter(
            FinalGrade.subject_grade_id.in_(sg_ids),
            FinalGrade.final_score.isnot(None)
        ).all()]

        c_passed = sum(1 for s in campus_scores if s >= 3.0)
        c_failed = sum(1 for s in campus_scores if s < 3.0)
        c_avg = round(sum(campus_scores) / len(campus_scores), 2) if campus_scores else 0
        c_pr = round((c_passed / (c_passed + c_failed)) * 100, 1) if (c_passed + c_failed) > 0 else 0
        c_risk = c_failed

        ws2.append([campus.name, len(grade_ids), c_avg, c_pr, c_risk])

    # --- Sheet 3: Grade Performance ---
    ws3 = wb.active
    ws3.title = "Rendimiento por Grado"
    ws3.append(["Grado", "Sede", "Estudiantes", "Promedio", "% Aprobación"])

    grades_query = db.session.query(Grade)
    if institution:
        grades_query = grades_query.join(Campus).filter(Campus.institution_id == institution.id)

    for grade in grades_query.order_by(Grade.name).all():
        sg_ids = [sg[0] for sg in db.session.query(SubjectGrade.id).filter(SubjectGrade.grade_id == grade.id).all()]
        if not sg_ids:
            continue

        grade_scores = [fg.final_score for fg in db.session.query(FinalGrade).filter(
            FinalGrade.subject_grade_id.in_(sg_ids),
            FinalGrade.final_score.isnot(None)
        ).all()]

        g_passed = sum(1 for s in grade_scores if s >= 3.0)
        g_failed = sum(1 for s in grade_scores if s < 3.0)
        g_avg = round(sum(grade_scores) / len(grade_scores), 2) if grade_scores else 0
        g_pr = round((g_passed / (g_passed + g_failed)) * 100, 1) if (g_passed + g_failed) > 0 else 0
        g_students = db.session.query(func.count()).select_from(AcademicStudent).filter(
            AcademicStudent.grade_id == grade.id,
            AcademicStudent.status == 'activo'
        ).scalar()

        ws3.append([grade.name, grade.campus.name if grade.campus else 'N/A', g_students, g_avg, g_pr])

    # --- Sheet 4: Top 10 Students ---
    ws4 = wb.active
    ws4.title = "Top 10 Estudiantes"
    ws4.append(["#", "Estudiante", "Grado", "Promedio", "Materias Perdidas"])

    top_query = db.session.query(
        AcademicStudent.id,
        User.first_name,
        User.last_name,
        Grade.name,
        func.avg(FinalGrade.final_score)
    ).join(User, AcademicStudent.user_id == User.id
    ).join(Grade, AcademicStudent.grade_id == Grade.id
    ).join(FinalGrade, AcademicStudent.id == FinalGrade.student_id
    ).filter(AcademicStudent.status == 'activo', FinalGrade.final_score.isnot(None))

    if institution:
        top_query = top_query.join(Campus, Grade.campus_id == Campus.id).filter(Campus.institution_id == institution.id)

    top_query = top_query.group_by(AcademicStudent.id, User.first_name, User.last_name, Grade.name
    ).order_by(func.avg(FinalGrade.final_score).desc()).limit(10).all()

    for i, tq in enumerate(top_query, 1):
        failed = db.session.query(func.count()).select_from(FinalGrade).filter(
            FinalGrade.student_id == tq[0], FinalGrade.final_score < 3.0
        ).scalar() or 0
        ws4.append([i, f"{tq[1]} {tq[2]}", tq[3], round(tq[4], 2), failed])

    # --- Sheet 5: Risk Students ---
    ws5 = wb.active
    ws5.title = "Estudiantes en Riesgo"
    ws5.append(["Estudiante", "Grado", "Promedio", "Materias Perdidas"])

    risk_query = db.session.query(
        AcademicStudent.id,
        User.first_name,
        User.last_name,
        Grade.name,
        func.avg(FinalGrade.final_score)
    ).join(User, AcademicStudent.user_id == User.id
    ).join(Grade, AcademicStudent.grade_id == Grade.id
    ).join(FinalGrade, AcademicStudent.id == FinalGrade.student_id
    ).filter(AcademicStudent.status == 'activo', FinalGrade.final_score.isnot(None))

    if institution:
        risk_query = risk_query.join(Campus, Grade.campus_id == Campus.id).filter(Campus.institution_id == institution.id)

    risk_query = risk_query.group_by(AcademicStudent.id, User.first_name, User.last_name, Grade.name
    ).having(func.avg(FinalGrade.final_score) < 3.0
    ).order_by(func.avg(FinalGrade.final_score).asc()).all()

    for rq in risk_query:
        failed = db.session.query(func.count()).select_from(FinalGrade).filter(
            FinalGrade.student_id == rq[0], FinalGrade.final_score < 3.0
        ).scalar() or 0
        ws5.append([f"{rq[1]} {rq[2]}", rq[3], round(rq[4], 2), failed])

    # Export
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'metricas_institucionales_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )


@metrics_bp.route('/risk-students')
@login_required
@role_required('root', 'admin', 'coordinator', 'teacher')
def risk_students():
    """View students at risk with full data."""
    institution = get_current_institution()
    if not institution:
        flash('Seleccione institución primero.', 'warning')
        return redirect(url_for('dashboard.index'))

    # Usar la función existente _get_risk_students
    threshold = request.args.get('threshold', 3.0, type=float)
    teacher_id = current_user.id if current_user.has_role('teacher') else None

    risk_list = _get_risk_students(teacher_id, institution, threshold)

    # Estadísticas
    total_at_risk = len(risk_list)
    high_risk = sum(1 for r in risk_list if r['avg_score'] < 2.0)
    medium_risk = sum(1 for r in risk_list if 2.0 <= r['avg_score'] < 3.0)

    return render_template('metrics/risk_students.html',
                           risk_students=risk_list,
                           total_at_risk=total_at_risk,
                           high_risk=high_risk,
                           medium_risk=medium_risk,
                           threshold=threshold)
