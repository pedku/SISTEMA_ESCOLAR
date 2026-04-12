"""
Achievement and gamification routes.
"""

from flask import Blueprint, render_template

achievements_bp = Blueprint('achievements', __name__)


@achievements_bp.route('/achievements')
def achievements():
    """View available achievements."""
    return render_template('achievements/list.html')


@achievements_bp.route('/achievements/student/<int:id>')
def student_achievements(id):
    """View achievements for a specific student."""
    return render_template('achievements/student_achievements.html', student_id=id)


@achievements_bp.route('/leaderboard')
def leaderboard():
    """View student leaderboard."""
    return render_template('achievements/leaderboard.html')
