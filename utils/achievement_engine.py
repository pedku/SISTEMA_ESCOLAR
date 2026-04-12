"""
Achievement Engine - Auto-award system for gamification.

Provides automatic achievement awarding based on student performance,
attendance, and behavior data.
"""

from datetime import datetime
from flask import current_app
from extensions import db
from models.achievement import Achievement, StudentAchievement
from models.grading import FinalGrade, AcademicPeriod
from models.attendance import Attendance
from models.observation import Observation
from models.academic import AcademicStudent, SubjectGrade
from utils.institution_resolver import get_current_institution


# Achievement definitions - these should match seed data
ACHIEVEMENT_RULES = {
    'superador': {
        'name': 'Superador',
        'description': 'Subi\u00f3 1+ punto entre periodos consecutivos',
        'icon': '\U0001f4c8',
        'category': 'mejora'
    },
    'excelencia': {
        'name': 'Excelencia',
        'description': 'Nota >= 4.5 en un periodo',
        'icon': '\u2b50',
        'category': 'acad\u00e9mico'
    },
    'asistencia_perfecta': {
        'name': 'Asistencia Perfecta',
        'description': '0 inasistencias en un periodo',
        'icon': '\u2705',
        'category': 'asistencia'
    },
    'todo_terreno': {
        'name': 'Todo Terreno',
        'description': 'Todas las materias ganadas en el periodo',
        'icon': '\U0001f3c5',
        'category': 'acad\u00e9mico'
    },
    'resiliente': {
        'name': 'Resiliente',
        'description': 'Recuper\u00f3 una materia perdida entre periodos',
        'icon': '\U0001f4aa',
        'category': 'mejora'
    },
    'constancia': {
        'name': 'Constancia',
        'description': '3 periodos seguidos con promedio >= 4.0',
        'icon': '\U0001f525',
        'category': 'acad\u00e9mico'
    },
    'companero': {
        'name': 'Compa\u00f1ero',
        'description': 'Recibi\u00f3 una observaci\u00f3n positiva',
        'icon': '\U0001f91d',
        'category': 'comportamiento'
    }
}


def _get_achievement_by_key(key):
    """Find an achievement by its rule key (stored in criteria field)."""
    return Achievement.query.filter(
        Achievement.criteria.like(f'%{key}%'),
        Achievement.is_active == True
    ).first()


def _get_student_periods(student_id):
    """Get all academic periods for a student's institution, ordered."""
    student = AcademicStudent.query.get(student_id)
    if not student:
        return []

    periods = AcademicPeriod.query.filter_by(
        institution_id=student.institution_id
    ).order_by(AcademicPeriod.academic_year, AcademicPeriod.order).all()

    return periods


def _check_superador(student_id, period):
    """Check if student improved 1+ point compared to previous period."""
    periods = _get_student_periods(student_id)
    period_index = next((i for i, p in enumerate(periods) if p.id == period.id), None)
    if period_index is None or period_index == 0:
        return False

    prev_period = periods[period_index - 1]

    # Get final grades for current and previous period
    current_grades = FinalGrade.query.filter_by(
        student_id=student_id, period_id=period.id
    ).all()

    prev_grades = FinalGrade.query.filter_by(
        student_id=student_id, period_id=prev_period.id
    ).all()

    if not current_grades or not prev_grades:
        return False

    # Build maps by subject_grade_id
    current_map = {g.subject_grade_id: g.final_score for g in current_grades}
    prev_map = {g.subject_grade_id: g.final_score for g in prev_grades}

    # Check if any common subject improved by 1+ point
    for sg_id in current_map:
        if sg_id in prev_map:
            if current_map[sg_id] - prev_map[sg_id] >= 1.0:
                return True

    return False


def _check_excelencia(student_id, period):
    """Check if student has any grade >= 4.5 in the period."""
    grades = FinalGrade.query.filter_by(
        student_id=student_id, period_id=period.id
    ).filter(FinalGrade.final_score >= 4.5).all()

    return len(grades) > 0


def _check_asistencia_perfecta(student_id, period):
    """Check if student has 0 absences in the period."""
    period = AcademicPeriod.query.get(period.id)
    if not period or not period.start_date or not period.end_date:
        return False

    absences = Attendance.query.filter(
        Attendance.student_id == student_id,
        Attendance.date >= period.start_date,
        Attendance.date <= period.end_date,
        Attendance.status == 'ausente'
    ).count()

    # Only award if there are attendance records and no absences
    total_records = Attendance.query.filter(
        Attendance.student_id == student_id,
        Attendance.date >= period.start_date,
        Attendance.date <= period.end_date
    ).count()

    return total_records > 0 and absences == 0


def _check_todo_terreno(student_id, period):
    """Check if student passed all subjects in the period."""
    grades = FinalGrade.query.filter_by(
        student_id=student_id, period_id=period.id
    ).all()

    if not grades:
        return False

    return all(g.status == 'ganada' for g in grades)


def _check_resiliente(student_id, period):
    """Check if student recovered a previously failed subject."""
    periods = _get_student_periods(student_id)
    period_index = next((i for i, p in enumerate(periods) if p.id == period.id), None)
    if period_index is None or period_index == 0:
        return False

    prev_period = periods[period_index - 1]

    # Get failed subjects in previous period
    prev_failed = FinalGrade.query.filter_by(
        student_id=student_id, period_id=prev_period.id, status='perdida'
    ).all()

    if not prev_failed:
        return False

    prev_failed_ids = {g.subject_grade_id for g in prev_failed}

    # Check if any of those subjects are now passed in current period
    current_grades = FinalGrade.query.filter_by(
        student_id=student_id, period_id=period.id
    ).all()

    for g in current_grades:
        if g.subject_grade_id in prev_failed_ids and g.status == 'ganada':
            return True

    return False


def _check_constancia(student_id, period):
    """Check if student has 3 consecutive periods with average >= 4.0."""
    periods = _get_student_periods(student_id)
    period_index = next((i for i, p in enumerate(periods) if p.id == period.id), None)
    if period_index is None or period_index < 2:
        return False

    # Check this period and 2 previous ones
    for i in range(period_index, period_index - 3, -1):
        p = periods[i]
        grades = FinalGrade.query.filter_by(
            student_id=student_id, period_id=p.id
        ).all()

        if not grades:
            return False

        avg = sum(g.final_score for g in grades) / len(grades)
        if avg < 4.0:
            return False

    return True


def _check_companero(student_id, period=None):
    """Check if student received a positive observation."""
    positive_obs = Observation.query.filter_by(
        student_id=student_id,
        type='positiva'
    ).first()

    return positive_obs is not None


def check_and_award_achievements(student_id, period_id=None):
    """
    Check all achievement rules for a student and auto-award eligible ones.

    Args:
        student_id: The student's ID
        period_id: Optional period to check (if None, checks all periods)

    Returns:
        List of newly awarded achievements
    """
    student = AcademicStudent.query.get(student_id)
    if not student:
        return []

    newly_awarded = []

    # Determine which periods to check
    if period_id:
        periods_to_check = [AcademicPeriod.query.get(period_id)]
    else:
        periods_to_check = _get_student_periods(student_id)

    # Check period-based achievements
    for period in periods_to_check:
        if not period:
            continue

        rules = {
            'superador': lambda: _check_superador(student_id, period),
            'excelencia': lambda: _check_excelencia(student_id, period),
            'asistencia_perfecta': lambda: _check_asistencia_perfecta(student_id, period),
            'todo_terreno': lambda: _check_todo_terreno(student_id, period),
            'resiliente': lambda: _check_resiliente(student_id, period),
            'constancia': lambda: _check_constancia(student_id, period),
        }

        for key, check_fn in rules.items():
            try:
                if check_fn():
                    achievement = _get_achievement_by_key(key)
                    if achievement:
                        result = award_achievement(
                            achievement.id, student_id, period.id, auto=True
                        )
                        if result:
                            newly_awarded.append({
                                'achievement': achievement,
                                'period': period
                            })
            except Exception as e:
                current_app.logger.error(
                    f"Error checking achievement {key}: {e}"
                )

    # Check non-period-based achievements (companero)
    try:
        if _check_companero(student_id):
            achievement = _get_achievement_by_key('companero')
            if achievement:
                result = award_achievement(
                    achievement.id, student_id, period_id, auto=True
                )
                if result:
                    newly_awarded.append({
                        'achievement': achievement,
                        'period': None
                    })
    except Exception as e:
        current_app.logger.error(f"Error checking companero achievement: {e}")

    return newly_awarded


def award_achievement(achievement_id, student_id, period_id=None, auto=False):
    """
    Award an achievement to a student.

    Args:
        achievement_id: The achievement ID
        student_id: The student ID
        period_id: Optional period ID
        auto: Whether this is auto-awarded (True) or manual (False)

    Returns:
        The StudentAchievement object or None if already exists
    """
    # Check if already awarded (prevent duplicates)
    existing = StudentAchievement.query.filter_by(
        student_id=student_id,
        achievement_id=achievement_id,
        period_id=period_id
    ).first()

    if existing:
        return None

    awarded_by = None if auto else None  # Could be current_user.id for manual

    new_achievement = StudentAchievement(
        student_id=student_id,
        achievement_id=achievement_id,
        period_id=period_id,
        awarded_by=awarded_by
    )

    db.session.add(new_achievement)
    db.session.commit()

    return new_achievement


def get_student_achievements(student_id):
    """
    Get all achievements for a student, ordered by earned_at descending.

    Returns:
        List of StudentAchievement objects with achievement relationship loaded
    """
    return StudentAchievement.query.filter_by(
        student_id=student_id
    ).join(Achievement).order_by(
        StudentAchievement.earned_at.desc()
    ).all()


def get_student_achievement_count(student_id):
    """Get total achievement count for a student."""
    return StudentAchievement.query.filter_by(student_id=student_id).count()


def get_leaderboard(institution_id=None, limit=50):
    """
    Get student leaderboard ordered by achievement count.

    Args:
        institution_id: Filter by institution (required for non-root)
        limit: Max number of students to return

    Returns:
        List of dicts with student info and achievement count
    """
    from models.user import User

    query = db.session.query(
        AcademicStudent,
        User,
        db.func.count(StudentAchievement.id).label('achievement_count')
    ).outerjoin(
        StudentAchievement, AcademicStudent.id == StudentAchievement.student_id
    ).join(
        User, AcademicStudent.user_id == User.id
    )

    if institution_id:
        query = query.filter(AcademicStudent.institution_id == institution_id)

    query = query.filter(AcademicStudent.status == 'activo')

    results = query.group_by(
        AcademicStudent.id, User.id
    ).order_by(
        db.desc('achievement_count')
    ).limit(limit).all()

    leaderboard = []
    for student, user, count in results:
        leaderboard.append({
            'student_id': student.id,
            'student_name': user.get_full_name() if hasattr(user, 'get_full_name') else user.username,
            'grade_name': student.grade.name if student.grade else 'N/A',
            'achievement_count': count or 0,
            'photo': student.photo
        })

    return leaderboard


def ensure_seed_achievements(institution_id):
    """
    Ensure all standard achievements exist for an institution.
    Called during institution setup or seed data initialization.
    """
    for key, data in ACHIEVEMENT_RULES.items():
        existing = Achievement.query.filter_by(
            institution_id=institution_id,
            name=data['name']
        ).first()

        if not existing:
            achievement = Achievement(
                institution_id=institution_id,
                name=data['name'],
                description=data['description'],
                icon=data['icon'],
                criteria=key,
                category=data['category'],
                is_active=True
            )
            db.session.add(achievement)

    db.session.commit()
