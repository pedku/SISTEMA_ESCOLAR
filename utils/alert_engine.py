"""
Alert Engine - Motor de reglas para Alertas Tempranas.

Automatically detects academic risk, attendance issues, and positive improvements
based on student grades and attendance data.

Rules:
| Alerta | Condicion | Severidad |
|--------|-----------|-----------|
| Riesgo Academico | Promedio < 3.0 en cualquier materia | alta |
| Tendencia Negativa | Bajo >0.5 puntos entre periodos | media |
| Inasistencia Critica | >20% inasistencias en mes | media |
| Grupo en Riesgo | >30% del grupo pierde con mismo profesor | alta |
| Riesgo de Desercion | Ausencias + notas bajas combinadas | alta |
| Mejora Destacable | Subio >1.0 punto entre periodos | baja (positiva) |
"""

from datetime import datetime, timedelta
from sqlalchemy import func, case, select
from extensions import db
from models.alert import Alert
from models.grading import FinalGrade, AcademicPeriod
from models.attendance import Attendance
from models.academic import AcademicStudent, SubjectGrade, Grade
from models.institution import Institution, Campus
from models.user import User


def _create_alert(student_id, alert_type, severity, title, description):
    """Create an alert if no active alert of the same type exists for this student."""
    existing = Alert.query.filter_by(
        student_id=student_id,
        alert_type=alert_type,
        resolved=False
    ).first()

    if existing:
        return existing

    alert = Alert(
        student_id=student_id,
        alert_type=alert_type,
        severity=severity,
        title=title,
        description=description
    )
    db.session.add(alert)
    return alert


def _get_institution_student_ids(institution_id):
    """Get all student IDs for an institution."""
    return db.session.query(AcademicStudent.id).filter(
        AcademicStudent.institution_id == institution_id,
        AcademicStudent.status == 'activo'
    ).all()


def _get_active_periods(institution_id):
    """Get all academic periods for an institution, ordered by order."""
    return AcademicPeriod.query.filter_by(
        institution_id=institution_id
    ).order_by(AcademicPeriod.order).all()


def run_riesgo_academico(institution_id=None):
    """
    Rule: Riesgo Academico
    Condition: Promedio < 3.0 en cualquier materia
    Severity: alta
    """
    created = 0

    # Find final grades below 3.0
    query = db.session.query(
        FinalGrade.student_id,
        FinalGrade.subject_grade_id,
        FinalGrade.final_score,
        FinalGrade.period_id
    ).filter(
        FinalGrade.final_score < 3.0,
        FinalGrade.status == 'perdida'
    )

    # Filter by institution if specified
    if institution_id:
        student_ids_subq = select(AcademicStudent.id).filter(
            AcademicStudent.institution_id == institution_id,
            AcademicStudent.status == 'activo'
        )
        query = query.filter(FinalGrade.student_id.in_(student_ids_subq))

    low_grades = query.all()

    for record in low_grades:
        student = AcademicStudent.query.get(record.student_id)
        if not student or student.status != 'activo':
            continue

        subject_grade = SubjectGrade.query.get(record.subject_grade_id)
        period = AcademicPeriod.query.get(record.period_id)

        subject_name = subject_grade.subject.name if subject_grade and subject_grade.subject else 'Materia'
        period_name = period.name if period else 'Periodo'
        student_name = student.user.get_full_name() if student.user else 'Estudiante'

        _create_alert(
            student_id=record.student_id,
            alert_type='riesgo_academico',
            severity='alta',
            title=f'Riesgo Academico: {student_name}',
            description=(
                f'El estudiante {student_name} tiene nota final de {record.final_score} '
                f'en {subject_name} durante {period_name}. '
                f'La nota esta por debajo del minimo (3.0).'
            )
        )
        created += 1

    return created


def run_tendencia_negativa(institution_id=None):
    """
    Rule: Tendencia Negativa
    Condition: Bajo >0.5 puntos entre periodos consecutivos
    Severity: media
    """
    created = 0

    if institution_id:
        student_ids_subq = select(AcademicStudent.id).filter(
            AcademicStudent.institution_id == institution_id,
            AcademicStudent.status == 'activo'
        )
    else:
        student_ids_subq = select(AcademicStudent.id).filter(
            AcademicStudent.status == 'activo'
        )

    if not db.session.execute(student_ids_subq).scalars().all():
        return 0

    periods = _get_active_periods(institution_id) if institution_id else _get_all_periods()

    for i in range(1, len(periods)):
        prev_period = periods[i - 1]
        curr_period = periods[i]

        # Get students with grades in both periods
        prev_grades = db.session.query(
            FinalGrade.student_id,
            FinalGrade.subject_grade_id,
            FinalGrade.final_score
        ).filter(
            FinalGrade.student_id.in_(student_ids_subq),
            FinalGrade.period_id == prev_period.id
        ).all()

        curr_grades = db.session.query(
            FinalGrade.student_id,
            FinalGrade.subject_grade_id,
            FinalGrade.final_score
        ).filter(
            FinalGrade.student_id.in_(student_ids_subq),
            FinalGrade.period_id == curr_period.id
        ).all()

        # Build lookup dicts
        prev_lookup = {}
        for g in prev_grades:
            key = (g.student_id, g.subject_grade_id)
            prev_lookup[key] = g.final_score

        curr_lookup = {}
        for g in curr_grades:
            key = (g.student_id, g.subject_grade_id)
            curr_lookup[key] = g.final_score

        # Find negative trends
        for key, prev_score in prev_lookup.items():
            if key in curr_lookup:
                curr_score = curr_lookup[key]
                diff = curr_score - prev_score
                if diff < -0.5:
                    student_id, subject_grade_id = key
                    student = AcademicStudent.query.get(student_id)
                    if not student or student.status != 'activo':
                        continue

                    subject_grade = SubjectGrade.query.get(subject_grade_id)
                    subject_name = subject_grade.subject.name if subject_grade and subject_grade.subject else 'Materia'
                    student_name = student.user.get_full_name() if student.user else 'Estudiante'

                    _create_alert(
                        student_id=student_id,
                        alert_type='tendencia_negativa',
                        severity='media',
                        title=f'Tendencia Negativa: {student_name}',
                        description=(
                            f'El estudiante {student_name} bajo su rendimiento en {subject_name}: '
                            f'de {prev_score} ({prev_period.name}) a {curr_score} ({curr_period.name}). '
                            f'Diferencia: {diff:.2f} puntos.'
                        )
                    )
                    created += 1

    return created


def run_inasistencia_critica(institution_id=None):
    """
    Rule: Inasistencia Critica
    Condition: >20% inasistencias en el ultimo mes
    Severity: media
    """
    created = 0

    one_month_ago = datetime.utcnow() - timedelta(days=30)

    query = db.session.query(
        Attendance.student_id,
        func.count(Attendance.id).label('total'),
        func.sum(case((Attendance.status == 'ausente', 1), else_=0)).label('absences')
    ).filter(
        Attendance.date >= one_month_ago.date()
    ).group_by(Attendance.student_id)

    if institution_id:
        student_ids_subq = select(AcademicStudent.id).filter(
            AcademicStudent.institution_id == institution_id,
            AcademicStudent.status == 'activo'
        )
        query = query.filter(Attendance.student_id.in_(student_ids_subq))

    attendance_summary = query.all()

    for record in attendance_summary:
        if record.total == 0:
            continue

        absence_rate = record.absences / record.total
        if absence_rate > 0.20:
            student = AcademicStudent.query.get(record.student_id)
            if not student or student.status != 'activo':
                continue

            student_name = student.user.get_full_name() if student.user else 'Estudiante'

            _create_alert(
                student_id=record.student_id,
                alert_type='inasistencia_critica',
                severity='media',
                title=f'Inasistencia Critica: {student_name}',
                description=(
                    f'El estudiante {student_name} tiene un {absence_rate:.1%} de inasistencias '
                    f'en el ultimo mes ({int(record.absences)} de {int(record.total)} clases). '
                    f'Supera el umbral critico del 20%.'
                )
            )
            created += 1

    return created


def run_grupo_riesgo(institution_id=None):
    """
    Rule: Grupo en Riesgo
    Condition: >30% del grupo pierde con mismo profesor
    Severity: alta
    """
    created = 0

    # Get subject-grade combinations with failing rates
    query = db.session.query(
        SubjectGrade.id.label('subject_grade_id'),
        SubjectGrade.grade_id,
        SubjectGrade.teacher_id,
        func.count(FinalGrade.id).label('total_students'),
        func.sum(case((FinalGrade.status == 'perdida', 1), else_=0)).label('failing_students')
    ).join(
        FinalGrade,
        SubjectGrade.id == FinalGrade.subject_grade_id
    ).group_by(
        SubjectGrade.id,
        SubjectGrade.grade_id,
        SubjectGrade.teacher_id
    )

    if institution_id:
        query = query.join(Grade, SubjectGrade.grade_id == Grade.id) \
                     .join(Campus, Grade.campus_id == Campus.id) \
                     .filter(Campus.institution_id == institution_id)

    sg_summary = query.all()

    for record in sg_summary:
        if record.total_students == 0:
            continue

        fail_rate = record.failing_students / record.total_students
        if fail_rate > 0.30:
            subject_grade = SubjectGrade.query.get(record.subject_grade_id)
            grade = Grade.query.get(record.grade_id)
            teacher = User.query.get(record.teacher_id)

            subject_name = subject_grade.subject.name if subject_grade and subject_grade.subject else 'Materia'
            grade_name = grade.name if grade else 'Grado'
            teacher_name = teacher.get_full_name() if teacher else 'Profesor'

            # Create alerts for all students in this subject-grade who are failing
            failing_students = FinalGrade.query.filter_by(
                subject_grade_id=record.subject_grade_id,
                status='perdida'
            ).all()

            for fg in failing_students:
                student = AcademicStudent.query.get(fg.student_id)
                if not student or student.status != 'activo':
                    continue

                student_name = student.user.get_full_name() if student.user else 'Estudiante'

                _create_alert(
                    student_id=fg.student_id,
                    alert_type='grupo_riesgo',
                    severity='alta',
                    title=f'Grupo en Riesgo: {grade_name} - {subject_name}',
                    description=(
                        f'El estudiante {student_name} pertenece al grupo {grade_name} en '
                        f'{subject_name} con el profesor {teacher_name}. '
                        f'El {fail_rate:.1%} del grupo ({int(record.failing_students)} de '
                        f'{int(record.total_students)} estudiantes) tiene nota perdida. '
                        f'Esto indica un posible problema grupal.'
                    )
                )
                created += 1

    return created


def run_riesgo_desercion(institution_id=None):
    """
    Rule: Riesgo de Desercion
    Condition: Ausencias + notas bajas combinadas
    - Promedio general < 3.0 Y
    - Inasistencia > 15% en el ultimo mes
    Severity: alta
    """
    created = 0

    one_month_ago = datetime.utcnow() - timedelta(days=30)

    # Get students with low overall average
    low_avg_query = db.session.query(
        FinalGrade.student_id,
        func.avg(FinalGrade.final_score).label('avg_score')
    ).group_by(FinalGrade.student_id).having(
        func.avg(FinalGrade.final_score) < 3.0
    )

    if institution_id:
        student_ids_subq = select(AcademicStudent.id).filter(
            AcademicStudent.institution_id == institution_id,
            AcademicStudent.status == 'activo'
        )
        low_avg_query = low_avg_query.filter(FinalGrade.student_id.in_(student_ids_subq))

    low_avg_students = {row.student_id: row.avg_score for row in low_avg_query.all()}

    # Check their attendance
    for student_id, avg_score in low_avg_students.items():
        attendance_stats = db.session.query(
            func.count(Attendance.id).label('total'),
            func.sum(case((Attendance.status == 'ausente', 1), else_=0)).label('absences')
        ).filter(
            Attendance.student_id == student_id,
            Attendance.date >= one_month_ago.date()
        ).first()

        if attendance_stats and attendance_stats.total > 0:
            absence_rate = attendance_stats.absences / attendance_stats.total
            if absence_rate > 0.15:
                student = AcademicStudent.query.get(student_id)
                if not student or student.status != 'activo':
                    continue

                student_name = student.user.get_full_name() if student.user else 'Estudiante'
                grade = Grade.query.get(student.grade_id)
                grade_name = grade.name if grade else 'N/A'

                _create_alert(
                    student_id=student_id,
                    alert_type='riesgo_desercion',
                    severity='alta',
                    title=f'Riesgo de Desercion: {student_name}',
                    description=(
                        f'ALERTA CRITICA: El estudiante {student_name} (Grado {grade_name}) '
                        f'presenta factores de riesgo de desercion escolar. '
                        f'Promedio general: {avg_score:.2f} | '
                        f'Inasistencia ultimo mes: {absence_rate:.1%} '
                        f'({int(attendance_stats.absences)} de {int(attendance_stats.total)} clases). '
                        f'Se requiere intervencion inmediata.'
                    )
                )
                created += 1

    return created


def run_mejora_destacable(institution_id=None):
    """
    Rule: Mejora Destacable
    Condition: Subio >1.0 punto entre periodos consecutivos
    Severity: baja (positiva)
    """
    created = 0

    if institution_id:
        student_ids_subq = select(AcademicStudent.id).filter(
            AcademicStudent.institution_id == institution_id,
            AcademicStudent.status == 'activo'
        )
    else:
        student_ids_subq = select(AcademicStudent.id).filter(
            AcademicStudent.status == 'activo'
        )

    if not db.session.execute(student_ids_subq).scalars().all():
        return 0

    periods = _get_active_periods(institution_id) if institution_id else _get_all_periods()

    for i in range(1, len(periods)):
        prev_period = periods[i - 1]
        curr_period = periods[i]

        prev_grades = db.session.query(
            FinalGrade.student_id,
            FinalGrade.subject_grade_id,
            FinalGrade.final_score
        ).filter(
            FinalGrade.student_id.in_(student_ids_subq),
            FinalGrade.period_id == prev_period.id
        ).all()

        curr_grades = db.session.query(
            FinalGrade.student_id,
            FinalGrade.subject_grade_id,
            FinalGrade.final_score
        ).filter(
            FinalGrade.student_id.in_(student_ids_subq),
            FinalGrade.period_id == curr_period.id
        ).all()

        prev_lookup = {}
        for g in prev_grades:
            key = (g.student_id, g.subject_grade_id)
            prev_lookup[key] = g.final_score

        curr_lookup = {}
        for g in curr_grades:
            key = (g.student_id, g.subject_grade_id)
            curr_lookup[key] = g.final_score

        for key, prev_score in prev_lookup.items():
            if key in curr_lookup:
                curr_score = curr_lookup[key]
                diff = curr_score - prev_score
                if diff > 1.0:
                    student_id, subject_grade_id = key
                    student = AcademicStudent.query.get(student_id)
                    if not student or student.status != 'activo':
                        continue

                    subject_grade = SubjectGrade.query.get(subject_grade_id)
                    subject_name = subject_grade.subject.name if subject_grade and subject_grade.subject else 'Materia'
                    student_name = student.user.get_full_name() if student.user else 'Estudiante'

                    _create_alert(
                        student_id=student_id,
                        alert_type='mejora_destacable',
                        severity='baja',
                        title=f'Mejora Destacable: {student_name}',
                        description=(
                            f'Felicitaciones! El estudiante {student_name} mostro una mejora '
                            f'significativa en {subject_name}: '
                            f'de {prev_score} ({prev_period.name}) a {curr_score} ({curr_period.name}). '
                            f'Mejora: +{diff:.2f} puntos.'
                        )
                    )
                    created += 1

    return created


def _get_all_periods():
    """Get all periods across all institutions, ordered."""
    return AcademicPeriod.query.order_by(
        AcademicPeriod.institution_id,
        AcademicPeriod.order
    ).all()


# ============================================
# Main Engine Functions
# ============================================

RULE_FUNCTIONS = {
    'riesgo_academico': run_riesgo_academico,
    'tendencia_negativa': run_tendencia_negativa,
    'inasistencia_critica': run_inasistencia_critica,
    'grupo_riesgo': run_grupo_riesgo,
    'riesgo_desercion': run_riesgo_desercion,
    'mejora_destacable': run_mejora_destacable,
}

RULE_LABELS = {
    'riesgo_academico': 'Riesgo Academico',
    'tendencia_negativa': 'Tendencia Negativa',
    'inasistencia_critica': 'Inasistencia Critica',
    'grupo_riesgo': 'Grupo en Riesgo',
    'riesgo_desercion': 'Riesgo de Desercion',
    'mejora_destacable': 'Mejora Destacable',
}


def run_alert(alert_type, institution_id=None):
    """
    Execute a specific alert rule.

    Args:
        alert_type: Type of alert to run
        institution_id: Optional institution filter

    Returns:
        Number of alerts created/updated
    """
    if alert_type not in RULE_FUNCTIONS:
        raise ValueError(f'Unknown alert type: {alert_type}')

    db.session.begin_nested()
    try:
        count = RULE_FUNCTIONS[alert_type](institution_id)
        db.session.commit()
        return count
    except Exception:
        db.session.rollback()
        raise


def run_all_alerts(institution_id=None):
    """
    Execute all alert rules.

    Args:
        institution_id: Optional institution filter

    Returns:
        dict with results per rule type
    """
    results = {}
    for alert_type, func in RULE_FUNCTIONS.items():
        try:
            count = run_alert(alert_type, institution_id)
            results[alert_type] = {
                'status': 'success',
                'alerts_created': count,
                'label': RULE_LABELS[alert_type]
            }
        except Exception as e:
            results[alert_type] = {
                'status': 'error',
                'error': str(e),
                'label': RULE_LABELS[alert_type]
            }
    return results


def get_active_alerts(institution_id=None, alert_type=None, severity=None):
    """
    Get active (unresolved) alerts.

    Args:
        institution_id: Optional institution filter
        alert_type: Optional alert type filter
        severity: Optional severity filter

    Returns:
        Query of Alert objects
    """
    query = Alert.query.filter_by(resolved=False)

    if institution_id:
        student_ids_subq = select(AcademicStudent.id).filter(
            AcademicStudent.institution_id == institution_id
        ).scalar_subquery()
        query = query.filter(Alert.student_id.in_(student_ids_subq))

    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)

    if severity:
        query = query.filter(Alert.severity == severity)

    return query.order_by(
        db.case(
            (Alert.severity == 'alta', 1),
            (Alert.severity == 'media', 2),
            (Alert.severity == 'baja', 3),
            else_=4
        ),
        Alert.triggered_at.desc()
    ).all()


def get_all_alerts(institution_id=None, alert_type=None, severity=None, resolved=None):
    """
    Get alerts with optional filters.

    Args:
        institution_id: Optional institution filter
        alert_type: Optional alert type filter
        severity: Optional severity filter
        resolved: Optional resolved status filter (True/False/None for all)

    Returns:
        List of Alert objects
    """
    query = Alert.query

    if institution_id:
        student_ids_subq = select(AcademicStudent.id).filter(
            AcademicStudent.institution_id == institution_id
        ).scalar_subquery()
        query = query.filter(Alert.student_id.in_(student_ids_subq))

    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)

    if severity:
        query = query.filter(Alert.severity == severity)

    if resolved is not None:
        query = query.filter(Alert.resolved == resolved)

    return query.order_by(
        Alert.resolved,
        db.case(
            (Alert.severity == 'alta', 1),
            (Alert.severity == 'media', 2),
            (Alert.severity == 'baja', 3),
            else_=4
        ),
        Alert.triggered_at.desc()
    ).all()


def resolve_alert(alert_id, user_id, notes=None):
    """
    Mark an alert as resolved.

    Args:
        alert_id: ID of the alert to resolve
        user_id: ID of the user resolving the alert
        notes: Optional resolution notes

    Returns:
        Alert object or None if not found
    """
    alert = Alert.query.get(alert_id)
    if not alert:
        return None

    alert.resolved = True
    alert.resolved_at = datetime.utcnow()
    alert.resolved_by = user_id
    alert.notes = notes

    db.session.commit()
    return alert


def get_alert_stats(institution_id=None):
    """
    Get alert statistics.

    Returns:
        dict with statistics
    """
    query = Alert.query

    if institution_id:
        student_ids_subq = select(AcademicStudent.id).filter(
            AcademicStudent.institution_id == institution_id
        ).scalar_subquery()
        query = query.filter(Alert.student_id.in_(student_ids_subq))

    total = query.count()
    active = query.filter_by(resolved=False).count()
    resolved = query.filter_by(resolved=True).count()

    # By type
    by_type = {}
    for alert_type, label in RULE_LABELS.items():
        count = query.filter_by(alert_type=alert_type, resolved=False).count()
        by_type[alert_type] = {'label': label, 'count': count}

    # By severity
    by_severity = {
        'alta': query.filter_by(severity='alta', resolved=False).count(),
        'media': query.filter_by(severity='media', resolved=False).count(),
        'baja': query.filter_by(severity='baja', resolved=False).count(),
    }

    return {
        'total': total,
        'active': active,
        'resolved': resolved,
        'by_type': by_type,
        'by_severity': by_severity
    }
