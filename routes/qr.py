"""
QR access routes.
Implements the PROYECTO-LAB protocol and internal SIGE views.
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import current_user
from utils.decorators import login_required, role_required
from services.qr_service import QRService
from models.qr_access import QRAccessLog, QRToken
from models.scheduling import Classroom

qr_bp = Blueprint('qr', __name__)

@qr_bp.route('/')
@login_required
def index():
    """Redirect to specific view based on role."""
    if current_user.role in ['root', 'admin', 'coordinator']:
        return redirect(url_for('qr.validate_view'))
    return redirect(url_for('qr.my_qr'))

@qr_bp.route('/my-qr')
@login_required
def my_qr():
    """View user's QR code."""
    token_entry = QRService.get_or_create_token(current_user.id)
    # Get recent logs for this user
    recent_logs = QRAccessLog.query.filter_by(user_id=current_user.id).order_by(QRAccessLog.timestamp.desc()).limit(10).all()
    
    return render_template('qr/my_qr.html', 
                         token=token_entry.token, 
                         recent_logs=recent_logs)

@qr_bp.route('/regenerate', methods=['POST'])
@login_required
def regenerate():
    """Invalidate current QR and create a new one."""
    QRService.regenerate_token(current_user.id)
    flash('Su código QR ha sido regenerado exitosamente.', 'success')
    return redirect(url_for('qr.my_qr'))

@qr_bp.route('/validate', methods=['POST'])
def validate_qr():
    """
    Validation endpoint for external scanners (PROYECTO-LAB protocol).
    Expects JSON: {"labID": "...", "qr": "..."}
    """
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Faltan datos en la solicitud'}), 400
    
    lab_id = data.get('labID')
    qr_token = data.get('qr')
    
    if not lab_id or not qr_token:
        return jsonify({'status': 'error', 'message': 'Faltan campos obligatorios (labID, qr)'}), 400
    
    # Use the service to validate
    success, message, user = QRService.validate_access(qr_token, lab_id, ip_address=request.remote_addr)
    
    status = 'success' if success else 'unauthorized'
    
    return jsonify({
        'status': status,
        'labID': lab_id,
        'message': message,
        'user_name': user.name if user else 'Desconocido'
    })

@qr_bp.route('/validate', methods=['GET'])
@login_required
@role_required('root', 'admin', 'coordinator')
def validate_view():
    """Internal view to see recent access logs."""
    logs = QRAccessLog.query.order_by(QRAccessLog.timestamp.desc()).limit(50).all()
    return render_template('qr/validate.html', logs=logs)

@qr_bp.route('/simulator')
@login_required
@role_required('root')
def simulator():
    """
    ROOT ONLY: Tool to simulate a QR scan without hardware.
    """
    classrooms = Classroom.query.all()
    # Get some active tokens for simulation if needed, or just let user type
    return render_template('qr/simulator.html', classrooms=classrooms)

@qr_bp.route('/simulate-scan', methods=['POST'])
@login_required
@role_required('root')
def simulate_scan():
    """Process a simulated scan from the simulator page."""
    lab_id = request.form.get('lab_id')
    qr_token = request.form.get('qr_token')
    
    # We call the same service
    success, message, user = QRService.validate_access(qr_token, lab_id, ip_address=f"SIM-{request.remote_addr}")
    
    if success:
        flash(f"ÉXITO: {message}", "success")
    else:
        flash(f"DENEGADO: {message}", "danger")
        
    return redirect(url_for('qr.simulator'))
