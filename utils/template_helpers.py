"""
Template helper functions for Jinja2.
"""

from datetime import datetime
from flask import request
from flask_login import current_user
from utils.validators import format_grade, get_grade_status, get_grade_performance_level, get_grade_class


def get_template_helpers():
    """Return dictionary of helper functions for template context."""
    return {
        'now': datetime.now,
        'current_year': lambda: datetime.now().year,
        'current_user': current_user,
        'request_path': request.path,
        'format_grade': format_grade,
        'get_grade_status': get_grade_status,
        'get_grade_performance_level': get_grade_performance_level,
        'get_grade_class': get_grade_class,
        'is_active_route': lambda route: request.path.startswith(route),
        'user_has_role': lambda role: current_user.has_role(role) if current_user.is_authenticated else False,
        'user_has_any_role': lambda *roles: current_user.has_any_role(*roles) if current_user.is_authenticated else False,
    }
