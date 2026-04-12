"""
Dashboard routes for different user roles.
Supports multi-institution architecture.
"""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models.academic import AcademicStudent, Grade, Subject
from models.grading import FinalGrade, AcademicPeriod
from models.observation import Observation
from models.attendance import Attendance
from utils.institution_resolver import get_current_institution, get_institution_grades, get_institution_subjects, get_institution_students, get_institution_teachers

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    """Main dashboard - redirects based on user role."""
    # Map roles to their dashboard routes
    role_dashboards = {
        'root': 'dashboard.root_dashboard',  # Root has its own dashboard
        'admin': 'dashboard.admin_dashboard',
        'coordinator': 'dashboard.coordinator_dashboard',
        'teacher': 'dashboard.teacher_dashboard',
        'student': 'dashboard.student_dashboard',
        'parent': 'dashboard.parent_dashboard',
        'viewer': 'dashboard.viewer_dashboard'
    }

    dashboard_route = role_dashboards.get(current_user.role, 'dashboard.admin_dashboard')
    return redirect(url_for(dashboard_route))


@dashboard_bp.route('/dashboard/root')
@login_required
def root_dashboard():
    """Dashboard for root/super-admin - shows all institutions overview."""
    from models.institution import Institution, Campus
    from models.user import User
    
    # All institutions with stats
    institutions = Institution.query.order_by(Institution.name).all()
    
    # Build institution stats
    inst_stats = []
    total_users_all = 0
    total_admins_all = 0
    
    for inst in institutions:
        # Count users for this institution
        students = AcademicStudent.query.filter_by(institution_id=inst.id, status='activo').count()
        teachers = User.query.filter_by(institution_id=inst.id, role='teacher').count()
        admins = User.query.filter_by(institution_id=inst.id, role='admin').count()
        campuses = Campus.query.filter_by(institution_id=inst.id).count()
        
        inst_stats.append({
            'institution': inst,
            'students': students,
            'teachers': teachers,
            'admins': admins,
            'campuses': campuses,
            'total_users': students + teachers + admins
        })
        
        total_users_all += students + teachers + admins
        total_admins_all += admins
    
    # Global stats
    total_institutions = len(institutions)
    total_users = User.query.count()
    total_students = AcademicStudent.query.filter_by(status='activo').count()
    total_teachers = User.query.filter_by(role='teacher').count()
    
    return render_template(
        'dashboard/root.html',
        inst_stats=inst_stats,
        global_stats={
            'institutions': total_institutions,
            'users': total_users,
            'students': total_students,
            'teachers': total_teachers,
            'admins': total_admins_all
        }
    )


@dashboard_bp.route('/dashboard/admin')
@login_required
def admin_dashboard():
    """Dashboard for admin/root users."""
    from models.institution import Institution, Campus

    institution = get_current_institution()
    total_students = get_institution_students(institution).filter_by(status='activo').count()
    total_teachers = get_institution_teachers(institution).count()
    total_grades = get_institution_grades(institution).count()
    total_subjects = get_institution_subjects(institution).count()

    # Campus count filtered by institution
    if institution:
        total_campuses = Campus.query.filter_by(institution_id=institution.id).count()
    else:
        # Root without active institution sees all campuses
        total_campuses = Campus.query.count()

    return render_template('dashboard/admin.html',
                          institution=institution,
                          total_students=total_students,
                          total_teachers=total_teachers,
                          total_grades=total_grades,
                          total_subjects=total_subjects,
                          total_campuses=total_campuses)


@dashboard_bp.route('/dashboard/coordinator')
@login_required
def coordinator_dashboard():
    """Dashboard for coordinators."""
    institution = get_current_institution()
    total_students = get_institution_students(institution).filter_by(status='activo').count()

    # Get students at risk (average < 3.0)
    # This would need a more complex query, placeholder for now

    # Get recent observations filtered by institution
    recent_observations = []
    if institution:
        # Get all student IDs for this institution
        student_ids = db.session.query(AcademicStudent.id).filter(
            AcademicStudent.institution_id == institution.id
        ).subquery()
        recent_observations = Observation.query.filter(
            Observation.student_id.in_(student_ids)
        ).order_by(Observation.date.desc()).limit(10).all()

    return render_template('dashboard/coordinator.html',
                          total_students=total_students,
                          recent_observations=recent_observations)


@dashboard_bp.route('/dashboard/teacher')
@login_required
def teacher_dashboard():
    """Dashboard for teachers."""
    from models.institution import Campus
    from models.academic import SubjectGrade

    institution = get_current_institution()

    # Get teacher's assigned subjects, filtered by institution
    if institution:
        subject_grades = current_user.subject_grades \
            .join(Grade) \
            .join(Campus) \
            .filter(Campus.institution_id == institution.id) \
            .all()
    else:
        # Root without active institution sees all
        subject_grades = current_user.subject_grades.all()

    # Get student count for teacher's classes filtered by institution
    total_students = 0
    for sg in subject_grades:
        total_students += sg.grade.academic_students.filter_by(status='activo').count()

    return render_template('dashboard/teacher.html',
                          subject_grades=subject_grades,
                          total_students=total_students)


@dashboard_bp.route('/dashboard/student')
@login_required
def student_dashboard():
    """Dashboard for students."""
    institution = get_current_institution()

    # Get student's academic record, filtered by institution
    if institution:
        academic_student = AcademicStudent.query.filter_by(
            user_id=current_user.id,
            institution_id=institution.id
        ).first()
    else:
        academic_student = AcademicStudent.query.filter_by(user_id=current_user.id).first()

    if not academic_student:
        # Student profile not created yet
        return render_template('dashboard/student.html', academic_student=None)

    # Get recent grades filtered by institution
    if institution:
        final_grades = FinalGrade.query \
            .filter_by(student_id=academic_student.id) \
            .join(AcademicPeriod) \
            .filter(AcademicPeriod.institution_id == institution.id) \
            .order_by(FinalGrade.calculated_at.desc()) \
            .limit(10).all()
    else:
        final_grades = FinalGrade.query.filter_by(student_id=academic_student.id).order_by(
            FinalGrade.calculated_at.desc()
        ).limit(10).all()

    return render_template('dashboard/student.html',
                          academic_student=academic_student,
                          final_grades=final_grades)


@dashboard_bp.route('/dashboard/parent')
@login_required
def parent_dashboard():
    """Dashboard for parents."""
    from models.academic import ParentStudent

    institution = get_current_institution()

    # Get students assigned to this parent, filtered by institution
    if institution:
        parent_students = ParentStudent.query \
            .join(AcademicStudent, ParentStudent.student_id == AcademicStudent.id) \
            .filter(
                ParentStudent.parent_id == current_user.id,
                AcademicStudent.institution_id == institution.id
            ).all()
    else:
        parent_students = ParentStudent.query.filter_by(parent_id=current_user.id).all()

    students = [ps.student for ps in parent_students]

    return render_template('dashboard/parent.html',
                          students=students)


@dashboard_bp.route('/dashboard/viewer')
@login_required
def viewer_dashboard():
    """Dashboard for viewers (read-only)."""
    institution = get_current_institution()

    # Get basic stats filtered by institution
    total_students = get_institution_students(institution).filter_by(status='activo').count()
    total_subjects = get_institution_subjects(institution).count()
    total_grades = get_institution_grades(institution).count()

    return render_template('dashboard/viewer.html',
                          institution=institution,
                          total_students=total_students,
                          total_subjects=total_subjects,
                          total_grades=total_grades)


@dashboard_bp.route('/alerts')
@login_required
def alerts():
    """View alerts and early warnings."""
    if not current_user.has_any_role('root', 'admin', 'coordinator'):
        return redirect(url_for('dashboard.index'))

    from models.institution import Campus

    institution = get_current_institution()
    alerts = []

    if institution:
        # Get student IDs for this institution
        student_ids = db.session.query(AcademicStudent.id).filter(
            AcademicStudent.institution_id == institution.id
        ).subquery()

        # Get students with low grades (status 'perdida')
        low_grade_students = FinalGrade.query \
            .filter(
                FinalGrade.student_id.in_(student_ids),
                FinalGrade.status == 'perdida'
            ).all()

        # Get recent negative observations
        negative_observations = Observation.query \
            .filter(
                Observation.student_id.in_(student_ids),
                Observation.type.in_(['negativa', 'convivencia'])
            ).order_by(Observation.date.desc()).limit(10).all()

        # Get attendance issues (unjustified absences)
        attendance_issues = Attendance.query \
            .filter(
                Attendance.student_id.in_(student_ids),
                Attendance.status == 'ausente'
            ).order_by(Attendance.date.desc()).limit(10).all()

        alerts = {
            'low_grade_students': low_grade_students,
            'negative_observations': negative_observations,
            'attendance_issues': attendance_issues
        }
    else:
        # Root without active institution - global stats
        low_grade_students = FinalGrade.query.filter_by(status='perdida').all()
        negative_observations = Observation.query.filter(
            Observation.type.in_(['negativa', 'convivencia'])
        ).order_by(Observation.date.desc()).limit(20).all()
        attendance_issues = Attendance.query.filter_by(status='ausente').order_by(
            Attendance.date.desc()
        ).limit(20).all()

        alerts = {
            'low_grade_students': low_grade_students,
            'negative_observations': negative_observations,
            'attendance_issues': attendance_issues
        }

    return render_template('alerts.html', alerts=alerts, institution=institution)
