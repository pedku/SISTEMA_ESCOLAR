"""
QR access routes (from existing system).
"""

from flask import Blueprint, render_template
from utils.decorators import login_required

qr_bp = Blueprint('qr', __name__)


@qr_bp.route('/')
@login_required
def qr_validate():
    """QR validation page."""
    return render_template('qr/validate.html')


@qr_bp.route('/my-qr')
@login_required
def my_qr():
    """View user's QR code."""
    return render_template('qr/my_qr.html')
