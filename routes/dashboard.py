"""
Dashboard routes for different user roles.
"""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models.academic import AcademicStudent, Grade, Subject
from models.grading import FinalGrade, AcademicPeriod
from models.observation import Observation
from models.attendance import Attendance

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    """Main dashboard - redirects based on user role."""
    # Map roles to their dashboard routes
    role_dashboards = {
        'root': 'dashboard.admin_dashboard',  # Root uses admin dashboard
        'admin': 'dashboard.admin_dashboard',
        'coordinator': 'dashboard.coordinator_dashboard',
        'teacher': 'dashboard.teacher_dashboard',
        'student': 'dashboard.student_dashboard',
        'parent': 'dashboard.parent_dashboard',
        'viewer': 'dashboard.viewer_dashboard'
    }
    
    dashboard_route = role_dashboards.get(current_user.role, 'dashboard.admin_dashboard')
    return redirect(url_for(dashboard_route))


@dashboard_bp.route('/dashboard/admin')
@login_required
def admin_dashboard():
    """Dashboard for admin/root users."""
    from models.institution import Institution, Campus
    
    institution = Institution.query.first()
    total_students = AcademicStudent.query.filter_by(status='activo').count()
    total_teachers = db.session.execute(db.text("SELECT COUNT(*) FROM users WHERE role = 'teacher'")).scalar()
    total_grades = Grade.query.count()
    total_subjects = Subject.query.count()
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
    total_students = AcademicStudent.query.filter_by(status='activo').count()
    
    # Get students at risk (average < 3.0)
    # This would need a more complex query, placeholder for now
    
    return render_template('dashboard/coordinator.html',
                          total_students=total_students)


@dashboard_bp.route('/dashboard/teacher')
@login_required
def teacher_dashboard():
    """Dashboard for teachers."""
    # Get teacher's assigned subjects
    subject_grades = current_user.subject_grades.all()
    
    return render_template('dashboard/teacher.html',
                          subject_grades=subject_grades)


@dashboard_bp.route('/dashboard/student')
@login_required
def student_dashboard():
    """Dashboard for students."""
    # Get student's academic record
    academic_student = AcademicStudent.query.filter_by(user_id=current_user.id).first()
    
    if not academic_student:
        # Student profile not created yet
        return render_template('dashboard/student.html', academic_student=None)
    
    # Get recent grades
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
    
    # Get students assigned to this parent
    parent_students = ParentStudent.query.filter_by(parent_id=current_user.id).all()
    students = [ps.student for ps in parent_students]
    
    return render_template('dashboard/parent.html',
                          students=students)


@dashboard_bp.route('/dashboard/viewer')
@login_required
def viewer_dashboard():
    """Dashboard for viewers (read-only)."""
    return render_template('dashboard/viewer.html')


@dashboard_bp.route('/alerts')
@login_required
def alerts():
    """View alerts and early warnings."""
    if not current_user.has_any_role('root', 'admin', 'coordinator'):
        return redirect(url_for('dashboard.index'))
    
    # TODO: Implement alert system
    alerts = []
    
    return render_template('alerts.html', alerts=alerts)
