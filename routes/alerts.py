"""
Alert management routes.
Early warning system for academic risk, attendance, and improvements.
"""

import csv
import io
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, Response
from flask_login import login_required, current_user
from extensions import db
from models.alert import Alert
from models.academic import AcademicStudent
from utils.decorators import role_required
from utils.institution_resolver import get_current_institution
from utils.alert_engine import (
    run_all_alerts,
    run_alert,
    get_active_alerts,
    get_all_alerts,
    resolve_alert,
    get_alert_stats,
    RULE_LABELS
)
from sqlalchemy import select
from datetime import datetime

alerts_bp = Blueprint('alerts', __name__, url_prefix='/alerts')


# ============================================
# Main Alert Panel
# ============================================

@alerts_bp.route('')
@login_required
@role_required('root', 'admin', 'coordinator')
def alerts_list():
    """Main alerts panel with filters."""
    institution = get_current_institution()
    institution_id = institution.id if institution else None

    # Filters
    alert_type = request.args.get('type', '')
    severity = request.args.get('severity', '')
    resolved_filter = request.args.get('resolved', '')

    resolved = None
    if resolved_filter == 'true':
        resolved = True
    elif resolved_filter == 'false':
        resolved = False

    # Get alerts
    alerts = get_all_alerts(
        institution_id=institution_id,
        alert_type=alert_type or None,
        severity=severity or None,
        resolved=resolved
    )

    # Get stats
    stats = get_alert_stats(institution_id)

    return render_template(
        'alerts/list.html',
        alerts=alerts,
        stats=stats,
        alert_type=alert_type,
        severity=severity,
        resolved_filter=resolved_filter,
        rule_labels=RULE_LABELS
    )


# ============================================
# Alert Detail
# ============================================

@alerts_bp.route('/<int:alert_id>')
@login_required
@role_required('root', 'admin', 'coordinator')
def alert_detail(alert_id):
    """Detail view for a specific alert."""
    alert = Alert.query.get_or_404(alert_id)

    # Institution check
    institution = get_current_institution()
    if institution:
        student = AcademicStudent.query.filter_by(
            id=alert.student_id,
            institution_id=institution.id
        ).first()
        if not student:
            flash('No tienes permiso para ver esta alerta.', 'danger')
            return redirect(url_for('alerts.alerts_list'))

    return render_template('alerts/detail.html', alert=alert)


# ============================================
# Run Alert Engine
# ============================================

@alerts_bp.route('/run', methods=['GET'])
@login_required
@role_required('root', 'admin', 'coordinator')
def run_panel():
    """Panel to manually run alert engine."""
    return render_template('alerts/run_panel.html', rule_labels=RULE_LABELS)


@alerts_bp.route('/run', methods=['POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def run_engine():
    """Execute the alert engine."""
    institution = get_current_institution()
    institution_id = institution.id if institution else None

    action = request.form.get('action', 'all')

    if action == 'all':
        results = run_all_alerts(institution_id)
        total_created = sum(
            r.get('alerts_created', 0)
            for r in results.values()
            if r['status'] == 'success'
        )
        flash(f'Motor de alertas ejecutado. {total_created} alertas nuevas generadas.', 'success')
        return render_template('alerts/run_panel.html', results=results, rule_labels=RULE_LABELS)
    else:
        try:
            count = run_alert(action, institution_id)
            flash(f'Regla "{RULE_LABELS.get(action, action)}" ejecutada. {count} alertas nuevas generadas.', 'success')
        except Exception as e:
            flash(f'Error al ejecutar la regla: {str(e)}', 'danger')
            return render_template('alerts/run_panel.html', rule_labels=RULE_LABELS)

        return render_template(
            'alerts/run_panel.html',
            results={action: {
                'status': 'success',
                'alerts_created': count,
                'label': RULE_LABELS.get(action, action)
            }},
            rule_labels=RULE_LABELS
        )


# ============================================
# Resolve Alert
# ============================================

@alerts_bp.route('/<int:alert_id>/resolve', methods=['POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def resolve_alert_route(alert_id):
    """Mark an alert as resolved."""
    alert = Alert.query.get_or_404(alert_id)

    # Institution check
    institution = get_current_institution()
    if institution:
        student = AcademicStudent.query.filter_by(
            id=alert.student_id,
            institution_id=institution.id
        ).first()
        if not student:
            flash('No tienes permiso para resolver esta alerta.', 'danger')
            return redirect(url_for('alerts.alerts_list'))

    notes = request.form.get('notes', '').strip()
    result = resolve_alert(alert_id, current_user.id, notes)

    if result:
        flash('Alerta marcada como resuelta.', 'success')
    else:
        flash('Error al resolver la alerta.', 'danger')

    # Redirect back to detail or list
    next_url = request.form.get('next', '')
    if next_url:
        return redirect(next_url)

    return redirect(url_for('alerts.alert_detail', alert_id=alert_id))


# ============================================
# Export Alerts to CSV
# ============================================

@alerts_bp.route('/export')
@login_required
@role_required('root', 'admin', 'coordinator')
def export_alerts():
    """Export alerts to CSV."""
    institution = get_current_institution()
    institution_id = institution.id if institution else None

    alert_type = request.args.get('type', '')
    severity = request.args.get('severity', '')
    resolved_filter = request.args.get('resolved', '')

    resolved = None
    if resolved_filter == 'true':
        resolved = True
    elif resolved_filter == 'false':
        resolved = False

    alerts = get_all_alerts(
        institution_id=institution_id,
        alert_type=alert_type or None,
        severity=severity or None,
        resolved=resolved
    )

    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'ID', 'Estudiante', 'Tipo', 'Severidad', 'Titulo',
        'Descripcion', 'Fecha Deteccion', 'Estado', 'Fecha Resolucion',
        'Resuelto Por', 'Notas'
    ])

    for alert in alerts:
        student_name = alert.student.user.get_full_name() if alert.student and alert.student.user else 'Desconocido'
        resolver_name = ''
        if alert.resolved_by:
            resolver = db.session.get(db.Model.registry._class_registry['User'], alert.resolved_by)
            if resolver:
                resolver_name = resolver.get_full_name()

        writer.writerow([
            alert.id,
            student_name,
            RULE_LABELS.get(alert.alert_type, alert.alert_type),
            alert.severity,
            alert.title,
            alert.description,
            alert.triggered_at.strftime('%Y-%m-%d %H:%M') if alert.triggered_at else '',
            'Resuelta' if alert.resolved else 'Activa',
            alert.resolved_at.strftime('%Y-%m-%d %H:%M') if alert.resolved_at else '',
            resolver_name,
            alert.notes or ''
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=alertas_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
        }
    )


# ============================================
# API: Get alert count for navbar badge
# ============================================

@alerts_bp.route('/api/count')
@login_required
@role_required('root', 'admin', 'coordinator')
def alert_count():
    """Get count of active alerts for navbar badge."""
    institution = get_current_institution()
    institution_id = institution.id if institution else None

    count = Alert.query.filter_by(resolved=False).count()
    if institution_id:
        student_ids_subq = select(AcademicStudent.id).filter(
            AcademicStudent.institution_id == institution_id
        ).scalar_subquery()
        count = Alert.query.filter(
            Alert.student_id.in_(student_ids_subq),
            Alert.resolved == False
        ).count()

    return jsonify({'count': count})
