"""
Report card management routes.
"""

from flask import Blueprint, render_template

report_cards_bp = Blueprint('report_cards', __name__, url_prefix='/')


@report_cards_bp.route('/report-cards')
def report_cards():
    """Generate and view report cards."""
    return render_template('report_cards/generate.html')


@report_cards_bp.route('/report-cards/<int:id>')
def view_report_card(id):
    """View specific report card."""
    return render_template('report_cards/view.html', report_card_id=id)


@report_cards_bp.route('/report-cards/history/<int:student_id>')
def report_card_history(student_id):
    """View report card history for a student."""
    return render_template('report_cards/history.html', student_id=student_id)
