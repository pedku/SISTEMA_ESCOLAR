"""
Institution context resolver.
Provides utilities for multi-institution data isolation and context management.
"""

from flask import session, request
from flask_login import current_user
from extensions import db
from models.institution import Institution, Campus


def get_current_institution():
    """
    Get the current institution context for the logged-in user.
    
    For root users:
    - If 'active_institution_id' is set in session, use that
    - Otherwise, return None (root can see all institutions)
    
    For non-root users:
    - Return their assigned institution
    
    Returns:
        Institution object or None
    """
    if not current_user.is_authenticated:
        return None
    
    # Root users can switch between institutions
    if current_user.is_root():
        active_id = session.get('active_institution_id')
        if active_id:
            return Institution.query.get(active_id)
        return None  # Root without active institution sees all
    
    # Non-root users are tied to their assigned institution
    return current_user.institution


def get_active_institution_id():
    """
    Get the active institution ID.
    Returns None for root users without an active institution.
    """
    institution = get_current_institution()
    return institution.id if institution else None


def require_institution():
    """
    Decorator-like function to ensure an institution context exists.
    Returns (institution, error_response) tuple.
    Use in routes that require an institution to be set.
    """
    from flask import jsonify
    
    institution = get_current_institution()
    
    if not institution:
        # For root users, they need to select an institution first
        if current_user.is_root():
            return None, {
                'error': 'No institution selected',
                'message': 'Root users must select an institution before accessing this resource.',
                'needs_institution_selection': True
            }, 400
        
        # For non-root users, they should have an institution assigned
        return None, {
            'error': 'No institution assigned',
            'message': 'Your account is not assigned to any institution. Contact administrator.',
        }, 403
    
    return institution, None


def filter_by_institution(query, model):
    """
    Filter a SQLAlchemy query by the current user's institution.
    
    Args:
        query: SQLAlchemy query object
        model: The model class to filter
    
    Returns:
        Filtered query object
    """
    institution = get_current_institution()
    
    # Root users without active institution can see all data
    if not institution:
        return query
    
    # Models with direct institution_id
    if hasattr(model, 'institution_id'):
        return query.filter(model.institution_id == institution.id)
    
    # Models with campus_id -> Campus -> institution_id
    if hasattr(model, 'campus_id'):
        from models.institution import Campus
        return query.join(Campus).filter(Campus.institution_id == institution.id)
    
    # Models with student_id -> AcademicStudent -> institution_id
    if hasattr(model, 'student_id'):
        from models.academic import AcademicStudent
        return query.join(AcademicStudent).filter(AcademicStudent.institution_id == institution.id)
    
    # Fallback: return unfiltered query
    return query


def get_user_institutions():
    """
    Get all institutions a user can access.
    For root: all institutions
    For others: only their assigned institution
    """
    if current_user.is_root():
        return Institution.query.order_by(Institution.name).all()
    
    if current_user.institution_id:
        return [current_user.institution]
    
    return []


def can_access_institution(user, institution_id):
    """
    Check if a user can access a specific institution.
    """
    if user.is_root():
        return True
    return user.institution_id == institution_id


def set_active_institution(institution_id):
    """
    Set the active institution for root users in session.
    This allows root to switch between institutions.
    """
    if not current_user.is_root():
        return False
    
    # Verify institution exists
    institution = Institution.query.get(institution_id)
    if not institution:
        return False
    
    session['active_institution_id'] = institution_id
    return True


def clear_active_institution():
    """
    Clear the active institution for root users.
    After this, root can see all institutions.
    """
    if 'active_institution_id' in session:
        del session['active_institution_id']


def get_institution_grades(institution=None):
    """
    Get all grades for an institution, handling campus relationship.
    """
    from models.academic import Grade
    
    if not institution:
        institution = get_current_institution()
    
    if not institution:
        return Grade.query
    
    return Grade.query.join(Campus).filter(Campus.institution_id == institution.id)


def get_institution_subjects(institution=None):
    """
    Get all subjects for an institution.
    """
    from models.academic import Subject
    
    if not institution:
        institution = get_current_institution()
    
    if not institution:
        return Subject.query
    
    return Subject.query.filter(Subject.institution_id == institution.id)


def get_institution_students(institution=None):
    """
    Get all academic students for an institution.
    """
    from models.academic import AcademicStudent
    
    if not institution:
        institution = get_current_institution()
    
    if not institution:
        return AcademicStudent.query
    
    return AcademicStudent.query.filter(AcademicStudent.institution_id == institution.id)


def get_institution_teachers(institution=None):
    """
    Get all teachers for an institution via subject-grade assignments.
    """
    from models.user import User
    from models.academic import SubjectGrade, Grade
    
    if not institution:
        institution = get_current_institution()
    
    if not institution:
        return User.query.filter(User.role == 'teacher')
    
    # Get teachers who teach in this institution's grades
    return User.query \
        .join(SubjectGrade, User.id == SubjectGrade.teacher_id) \
        .join(Grade, SubjectGrade.grade_id == Grade.id) \
        .join(Campus, Grade.campus_id == Campus.id) \
        .filter(Campus.institution_id == institution.id, User.role == 'teacher') \
        .distinct()
