"""
Achievement and gamification routes.
Full CRUD and engine execution for the gamification system.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.achievement import Achievement, StudentAchievement
from models.academic import AcademicStudent
from models.grading import AcademicPeriod
from models.user import User
from utils.decorators import login_required, role_required
from utils.institution_resolver import get_current_institution
from utils.achievement_engine import (
    check_and_award_achievements,
    award_achievement,
    get_student_achievements,
    get_leaderboard,
    ensure_seed_achievements,
    ACHIEVEMENT_RULES
)

achievements_bp = Blueprint('achievements', __name__)


# ============================================
# Achievement Catalog
# ============================================

@achievements_bp.route('/achievements')
@login_required
@role_required('root', 'admin', 'coordinator', 'teacher')
def achievements_list():
    """List all available achievements for the current institution."""
    institution = get_current_institution()
    institution_id = institution.id if institution else None

    # Ensure seed achievements exist
    if institution_id:
        ensure_seed_achievements(institution_id)

    # Query achievements
    query = Achievement.query.filter_by(is_active=True)
    if institution_id:
        query = query.filter(Achievement.institution_id == institution_id)

    category = request.args.get('category', '')
    if category:
        query = query.filter(Achievement.category == category)

    achievements = query.order_by(Achievement.category, Achievement.name).all()

    # Get counts of how many students have each achievement
    achievement_counts = {}
    for ach in achievements:
        count = StudentAchievement.query.filter_by(achievement_id=ach.id).count()
        achievement_counts[ach.id] = count

    categories = ['acad\u00e9mico', 'asistencia', 'comportamiento', 'mejora']

    return render_template(
        'achievements/list.html',
        achievements=achievements,
        categories=categories,
        selected_category=category,
        achievement_counts=achievement_counts
    )


# ============================================
# Student Achievements View
# ============================================

@achievements_bp.route('/achievements/student/<int:student_id>')
@login_required
def student_achievements_view(student_id):
    """View achievements for a specific student."""
    student = AcademicStudent.query.get_or_404(student_id)

    # Permission check
    institution = get_current_institution()
    if institution and student.institution_id != institution.id:
        flash('No tienes permiso para ver los logros de este estudiante.', 'danger')
        return redirect(url_for('achievements.achievements_list'))

    # Teacher can only see their own students
    if current_user.is_teacher():
        from models.academic import SubjectGrade
        is_teacher_of_student = db.session.query(SubjectGrade.id).join(
            AcademicStudent, AcademicStudent.grade_id == SubjectGrade.grade_id
        ).filter(
            SubjectGrade.teacher_id == current_user.id,
            AcademicStudent.id == student_id
        ).first()

        if not is_teacher_of_student:
            flash('No tienes permiso para ver los logros de este estudiante.', 'danger')
            return redirect(url_for('achievements.achievements_list'))

    student_achievements = get_student_achievements(student_id)

    # Get student user info
    user = User.query.get(student.user_id) if student.user_id else None

    return render_template(
        'achievements/student_achievements.html',
        student=student,
        user=user,
        achievements=student_achievements
    )


# ============================================
# Manual Award
# ============================================

@achievements_bp.route('/achievements/award', methods=['POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def award_achievement_manual():
    """Manually award an achievement to a student."""
    achievement_id = request.form.get('achievement_id', type=int)
    student_id = request.form.get('student_id', type=int)
    period_id = request.form.get('period_id', type=int)

    if not achievement_id or not student_id:
        flash('Debe seleccionar un logro y un estudiante.', 'danger')
        return redirect(url_for('achievements.achievements_list'))

    student = AcademicStudent.query.get_or_404(student_id)
    achievement = Achievement.query.get_or_404(achievement_id)

    # Permission check
    institution = get_current_institution()
    if institution and student.institution_id != institution.id:
        flash('No tienes permiso para otorgar logros a este estudiante.', 'danger')
        return redirect(url_for('achievements.achievements_list'))

    result = award_achievement(achievement_id, student_id, period_id)

    if result:
        student_name = ''
        if student.user_id:
            user = User.query.get(student.user_id)
            student_name = user.get_full_name() if hasattr(user, 'get_full_name') else user.username
        flash(f'Logro "{achievement.name}" otorgado a {student_name}.', 'success')
    else:
        flash('El estudiante ya tiene este logro para el periodo seleccionado.', 'warning')

    return redirect(url_for('achievements.student_achievements_view', student_id=student_id))


# ============================================
# Leaderboard
# ============================================

@achievements_bp.route('/leaderboard')
@login_required
def leaderboard_view():
    """View student leaderboard."""
    institution = get_current_institution()
    institution_id = institution.id if institution else None

    limit = request.args.get('limit', 50, type=int)
    grade_id = request.args.get('grade', '', type=str)

    leaderboard_data = get_leaderboard(institution_id, limit=limit)

    # Get grades for filter
    grades = []
    if institution_id:
        from models.academic import Grade
        from models.institution import Campus
        grades = Grade.query.join(Campus).filter(
            Campus.institution_id == institution_id
        ).order_by(Grade.name).all()

    # Apply grade filter on client side if needed
    selected_grade = grade_id if grade_id else ''

    return render_template(
        'achievements/leaderboard.html',
        leaderboard=leaderboard_data,
        grades=grades,
        selected_grade=selected_grade
    )


# ============================================
# Engine Execution
# ============================================

@achievements_bp.route('/achievements/run_engine', methods=['POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def run_engine():
    """Run the achievement engine for all students or a specific one."""
    institution = get_current_institution()

    student_id = request.form.get('student_id', type=int)
    period_id = request.form.get('period_id', type=int)

    newly_awarded = []

    if student_id:
        # Run for specific student
        student = AcademicStudent.query.get_or_404(student_id)
        if institution and student.institution_id != institution.id:
            flash('No tienes permiso para ejecutar el motor para este estudiante.', 'danger')
            return redirect(url_for('achievements.achievements_list'))

        newly_awarded = check_and_award_achievements(student_id, period_id)
    else:
        # Run for all active students in the institution
        query = AcademicStudent.query.filter_by(status='activo')
        if institution:
            query = query.filter(AcademicStudent.institution_id == institution.id)

        students = query.all()
        for student in students:
            newly_awarded.extend(check_and_award_achievements(student.id, period_id))

    if newly_awarded:
        flash(
            f'Se otorgaron {len(newly_awarded)} logros autom\u00e1ticamente.',
            'success'
        )
    else:
        flash('No se encontraron nuevos logros para otorgar.', 'info')

    # If running from student page, go back there
    if student_id:
        return redirect(url_for('achievements.student_achievements_view', student_id=student_id))

    return redirect(url_for('achievements.achievements_list'))


# ============================================
# AJAX API endpoints
# ============================================

@achievements_bp.route('/achievements/api/student/<int:student_id>')
@login_required
def api_student_achievements(student_id):
    """API endpoint for student achievements (JSON)."""
    student = AcademicStudent.query.get_or_404(student_id)
    achievements = get_student_achievements(student_id)

    return jsonify({
        'student_id': student_id,
        'total': len(achievements),
        'achievements': [
            {
                'id': sa.id,
                'name': sa.achievement.name,
                'description': sa.achievement.description,
                'icon': sa.achievement.icon,
                'category': sa.achievement.category,
                'earned_at': sa.earned_at.strftime('%Y-%m-%d %H:%M') if sa.earned_at else None,
                'period_id': sa.period_id
            }
            for sa in achievements
        ]
    })


@achievements_bp.route('/achievements/api/list')
@login_required
def api_achievements_list():
    """API endpoint for achievements list (JSON)."""
    institution = get_current_institution()
    institution_id = institution.id if institution else None

    query = Achievement.query.filter_by(is_active=True)
    if institution_id:
        query = query.filter(Achievement.institution_id == institution_id)

    achievements = query.order_by(Achievement.name).all()

    return jsonify({
        'total': len(achievements),
        'achievements': [ach.to_dict() for ach in achievements]
    })
