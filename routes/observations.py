"""
Observation management routes.
Full CRUD for behavior and academic observations with institution-aware filtering.
Includes guardian notification system.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.observation import Observation
from models.academic import AcademicStudent, ParentStudent
from models.user import User
from models.institution import Campus
from utils.decorators import role_required
from utils.institution_resolver import get_current_institution
from datetime import datetime, timedelta

observations_bp = Blueprint('observations', __name__)


# ============================================
# Observation List (Index)
# ============================================

@observations_bp.route('/observations')
@login_required
@role_required('root', 'admin', 'coordinator', 'teacher')
def observations_list():
    """List observations with filters."""
    institution = get_current_institution()
    
    # Base query - start from Observation and filter by institution through student
    query = Observation.query

    # Institution filter
    if institution:
        # Get student IDs for this institution
        institution_student_ids = db.session.query(AcademicStudent.id).filter(
            AcademicStudent.institution_id == institution.id
        ).subquery()
        query = query.filter(Observation.student_id.in_(institution_student_ids))
    
    # Apply filters
    obs_type = request.args.get('type', '')
    category = request.args.get('category', '')
    student_name = request.args.get('student', '').strip()
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    author_id = request.args.get('author', '')
    
    if obs_type:
        query = query.filter(Observation.type == obs_type)
    if category:
        query = query.filter(Observation.category == category)
    if author_id:
        query = query.filter(Observation.author_id == int(author_id))
    if date_from:
        try:
            query = query.filter(Observation.date >= datetime.strptime(date_from, '%Y-%m-%d'))
        except ValueError:
            pass
    if date_to:
        try:
            query = query.filter(Observation.date <= datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1))
        except ValueError:
            pass
    
    # Teacher filter - only see observations for their students
    if current_user.is_teacher():
        # Get students from subject_grades this teacher teaches
        from models.academic import SubjectGrade
        teacher_student_ids = db.session.query(AcademicStudent.id).join(
            SubjectGrade, AcademicStudent.grade_id == SubjectGrade.grade_id
        ).filter(
            SubjectGrade.teacher_id == current_user.id
        ).distinct().subquery()
        query = query.filter(Observation.student_id.in_(teacher_student_ids))
    
    # Student name search
    if student_name:
        student_ids = db.session.query(AcademicStudent.id).join(
            User, AcademicStudent.user_id == User.id
        ).filter(
            db.or_(
                User.first_name.ilike(f'%{student_name}%'),
                User.last_name.ilike(f'%{student_name}%'),
                db.concat(User.first_name, ' ', User.last_name).ilike(f'%{student_name}%')
            )
        ).distinct().subquery()
        query = query.filter(Observation.student_id.in_(student_ids))
    
    # Order by date descending
    query = query.order_by(Observation.date.desc())
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Get filter options for dropdown
    obs_types = ['positiva', 'negativa', 'seguimiento', 'convivencia']
    categories = db.session.query(Observation.category).distinct().filter(
        Observation.category.isnot(None)
    ).all()
    categories = [c[0] for c in categories if c[0]]
    
    # Get authors for filter
    authors = User.query.filter(
        User.role.in_(['root', 'admin', 'coordinator', 'teacher'])
    ).order_by(User.first_name).all()
    
    # Statistics
    # Use institution_student_ids for institution-scoped stats, or teacher_student_ids if teacher
    stats_scope = institution_student_ids if institution else None
    if current_user.is_teacher():
        stats_scope = teacher_student_ids

    stats = {
        'total': pagination.total,
        'positiva': Observation.query.filter(Observation.type == 'positiva').count() if not stats_scope else
                   Observation.query.filter(Observation.type == 'positiva', Observation.student_id.in_(stats_scope)).count(),
        'negativa': Observation.query.filter(Observation.type == 'negativa').count() if not stats_scope else
                   Observation.query.filter(Observation.type == 'negativa', Observation.student_id.in_(stats_scope)).count(),
        'seguimiento': Observation.query.filter(Observation.type == 'seguimiento').count() if not stats_scope else
                      Observation.query.filter(Observation.type == 'seguimiento', Observation.student_id.in_(stats_scope)).count(),
        'convivencia': Observation.query.filter(Observation.type == 'convivencia').count() if not stats_scope else
                      Observation.query.filter(Observation.type == 'convivencia', Observation.student_id.in_(stats_scope)).count(),
        'notificadas': Observation.query.filter(Observation.notified == True).count() if not stats_scope else
                      Observation.query.filter(Observation.notified == True, Observation.student_id.in_(stats_scope)).count(),
        'pendientes': Observation.query.filter(Observation.notified == False).count() if not stats_scope else
                     Observation.query.filter(Observation.notified == False, Observation.student_id.in_(stats_scope)).count(),
    }
    
    return render_template(
        'observations/list.html',
        observations=pagination.items,
        pagination=pagination,
        stats=stats,
        obs_types=obs_types,
        categories=categories,
        authors=authors,
        filters={
            'type': obs_type,
            'category': category,
            'student': student_name,
            'date_from': date_from,
            'date_to': date_to,
            'author': author_id
        }
    )


# ============================================
# Create Observation
# ============================================

@observations_bp.route('/observations/new', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin', 'coordinator', 'teacher')
def observation_create():
    """Create a new observation."""
    institution = get_current_institution()
    
    if request.method == 'POST':
        student_id = request.form.get('student_id', type=int)
        obs_type = request.form.get('type', '').strip()
        description = request.form.get('description', '').strip()
        
        if not student_id or not obs_type or not description:
            flash('Estudiante, tipo y descripción son obligatorios.', 'error')
            students = _get_available_students(institution)
            return render_template('observations/create.html', students=students, observation=None, today=datetime.utcnow().strftime('%Y-%m-%d'))
        
        # Verify student belongs to institution
        student = AcademicStudent.query.get(student_id)
        if not student:
            flash('Estudiante no encontrado.', 'error')
            return redirect(url_for('observations.observation_create'))
        
        if institution and student.institution_id != institution.id:
            flash('No tiene permiso para crear observaciones para este estudiante.', 'error')
            return redirect(url_for('observations.observation_create'))
        
        observation = Observation(
            student_id=student_id,
            author_id=current_user.id,
            type=obs_type,
            category=request.form.get('category', '').strip() or None,
            description=description,
            commitments=request.form.get('commitments', '').strip() or None,
            date=datetime.strptime(request.form.get('date', ''), '%Y-%m-%d') if request.form.get('date') else datetime.utcnow(),
            notified=False
        )
        
        try:
            db.session.add(observation)
            db.session.commit()
            
            # Auto-notify if required
            if observation.requires_notification() and student.grade and student.grade.director_id:
                flash('Observación creada exitosamente. El director de grupo será notificado.', 'success')
            else:
                flash('Observación creada exitosamente.', 'success')
            
            return redirect(url_for('observations.observation_detail', id=observation.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear la observación: {str(e)}', 'error')
    
    students = _get_available_students(institution)
    return render_template('observations/create.html', students=students, observation=None, today=datetime.utcnow().strftime('%Y-%m-%d'))


# ============================================
# View Observation Detail
# ============================================

@observations_bp.route('/observations/<int:id>')
@login_required
@role_required('root', 'admin', 'coordinator', 'teacher')
def observation_detail(id):
    """View observation details."""
    observation = Observation.query.get_or_404(id)
    
    # Verify access
    if not _can_access_observation(observation):
        flash('No tiene permiso para ver esta observación.', 'error')
        return redirect(url_for('observations.observations_list'))
    
    student = AcademicStudent.query.get(observation.student_id)
    author = User.query.get(observation.author_id)
    
    return render_template(
        'observations/detail.html',
        observation=observation,
        student=student,
        author=author
    )


# ============================================
# Edit Observation
# ============================================

@observations_bp.route('/observations/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin', 'coordinator', 'teacher')
def observation_edit(id):
    """Edit an observation."""
    observation = Observation.query.get_or_404(id)
    
    # Verify access
    if not _can_access_observation(observation):
        flash('No tiene permiso para editar esta observación.', 'error')
        return redirect(url_for('observations.observations_list'))
    
    # Only author or admin/coordinator can edit
    if observation.author_id != current_user.id and not current_user.has_any_role('root', 'admin', 'coordinator'):
        flash('Solo el autor puede editar esta observación.', 'error')
        return redirect(url_for('observations.observation_detail', id=id))
    
    if request.method == 'POST':
        observation.type = request.form.get('type', '').strip()
        observation.category = request.form.get('category', '').strip() or None
        observation.description = request.form.get('description', '').strip()
        observation.commitments = request.form.get('commitments', '').strip() or None
        
        if request.form.get('date'):
            try:
                observation.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d')
            except ValueError:
                flash('Fecha inválida.', 'error')
        
        try:
            db.session.commit()
            flash('Observación actualizada exitosamente.', 'success')
            return redirect(url_for('observations.observation_detail', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'error')
    
    students = _get_available_students(get_current_institution())
    return render_template('observations/create.html', students=students, observation=observation, today=datetime.utcnow().strftime('%Y-%m-%d'))


# ============================================
# Delete Observation
# ============================================

@observations_bp.route('/observations/<int:id>/delete', methods=['POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def observation_delete(id):
    """Delete an observation."""
    observation = Observation.query.get_or_404(id)
    
    if not _can_access_observation(observation):
        flash('No tiene permiso para eliminar esta observación.', 'error')
        return redirect(url_for('observations.observations_list'))
    
    try:
        db.session.delete(observation)
        db.session.commit()
        flash('Observación eliminada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {str(e)}', 'error')
    
    return redirect(url_for('observations.observations_list'))


# ============================================
# Student Observation History
# ============================================

@observations_bp.route('/observations/student/<int:student_id>')
@login_required
@role_required('root', 'admin', 'coordinator', 'teacher')
def student_observations(student_id):
    """View observation history for a student."""
    student = AcademicStudent.query.get_or_404(student_id)
    
    # Verify institution access
    institution = get_current_institution()
    if institution and student.institution_id != institution.id:
        flash('No tiene acceso a este estudiante.', 'error')
        return redirect(url_for('observations.observations_list'))
    
    # Get user for student
    student_user = User.query.get(student.user_id)
    
    # Get observations for this student
    observations = Observation.query.filter_by(student_id=student_id).order_by(
        Observation.date.desc()
    ).all()
    
    # Statistics for this student
    stats = {
        'total': len(observations),
        'positiva': sum(1 for o in observations if o.type == 'positiva'),
        'negativa': sum(1 for o in observations if o.type == 'negativa'),
        'seguimiento': sum(1 for o in observations if o.type == 'seguimiento'),
        'convivencia': sum(1 for o in observations if o.type == 'convivencia'),
        'notificadas': sum(1 for o in observations if o.notified),
        'pendientes': sum(1 for o in observations if not o.notified),
    }
    
    # Get parent contacts for notification
    parent_students = db.session.query(User).join(
        ParentStudent, User.id == ParentStudent.parent_id
    ).filter(
        ParentStudent.student_id == student_id
    ).all()
    
    return render_template(
        'observations/student_history.html',
        student=student,
        student_user=student_user,
        observations=observations,
        stats=stats,
        parents=parent_students
    )


# ============================================
# Mark as Notified
# ============================================

@observations_bp.route('/observations/<int:id>/notify', methods=['POST'])
@login_required
@role_required('root', 'admin', 'coordinator', 'teacher')
def mark_notified(id):
    """Mark observation as notified to parents."""
    observation = Observation.query.get_or_404(id)
    
    if not _can_access_observation(observation):
        return jsonify({'success': False, 'error': 'No autorizado'}), 403
    
    observation.notified = True
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Marcada como notificada'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# Quick Observation from Student Profile
# ============================================

@observations_bp.route('/observations/student/<int:student_id>/quick', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin', 'coordinator', 'teacher')
def quick_observation(student_id):
    """Quick observation creation from student profile."""
    student = AcademicStudent.query.get_or_404(student_id)
    
    # Verify institution access
    institution = get_current_institution()
    if institution and student.institution_id != institution.id:
        flash('No tiene acceso a este estudiante.', 'error')
        return redirect(url_for('students.list'))
    
    if request.method == 'POST':
        obs_type = request.form.get('type', '').strip()
        description = request.form.get('description', '').strip()
        
        if not obs_type or not description:
            flash('Tipo y descripción son obligatorios.', 'error')
            return redirect(url_for('observations.quick_observation', student_id=student_id))
        
        observation = Observation(
            student_id=student_id,
            author_id=current_user.id,
            type=obs_type,
            category=request.form.get('category', '').strip() or None,
            description=description,
            commitments=request.form.get('commitments', '').strip() or None,
            notified=False
        )
        
        try:
            db.session.add(observation)
            db.session.commit()
            flash('Observación creada exitosamente.', 'success')
            
            # Return to student profile
            return redirect(url_for('students.profile', id=student.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear: {str(e)}', 'error')
    
    return render_template(
        'observations/quick_form.html',
        student=student,
        student_user=User.query.get(student.user_id)
    )


# ============================================
# Export to CSV
# ============================================

@observations_bp.route('/observations/export')
@login_required
@role_required('root', 'admin', 'coordinator')
def observations_export():
    """Export observations to CSV."""
    from flask import Response
    import csv
    import io
    
    institution = get_current_institution()
    
    # Build query (same as list)
    query = Observation.query
    if institution:
        student_ids = db.session.query(AcademicStudent.id).filter(
            AcademicStudent.institution_id == institution.id
        ).subquery()
        query = query.filter(Observation.student_id.in_(student_ids))
    
    observations = query.order_by(Observation.date.desc()).all()
    
    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Fecha', 'Estudiante', 'Tipo', 'Categoría', 'Descripción', 
                     'Compromisos', 'Autor', 'Notificado'])
    
    for obs in observations:
        student = AcademicStudent.query.get(obs.student_id)
        student_user = User.query.get(student.user_id) if student else None
        author = User.query.get(obs.author_id)
        
        writer.writerow([
            obs.date.strftime('%Y-%m-%d') if obs.date else '',
            student_user.get_full_name() if student_user else 'N/A',
            obs.type,
            obs.category or '',
            obs.description,
            obs.commitments or '',
            author.get_full_name() if author else 'N/A',
            'Sí' if obs.notified else 'No'
        ])
    
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=observaciones.csv'}
    )


# ============================================
# Helper Functions
# ============================================

def _get_available_students(institution):
    """Get students available for observations."""
    query = AcademicStudent.query.filter_by(status='activo')
    
    if institution:
        query = query.filter_by(institution_id=institution.id)
    
    # For teachers, only their students
    if current_user.is_teacher():
        from models.academic import SubjectGrade
        query = query.join(SubjectGrade).filter(SubjectGrade.teacher_id == current_user.id)
    
    students = query.order_by(AcademicStudent.grade_id).all()
    
    result = []
    for student in students:
        user = User.query.get(student.user_id)
        if user:
            result.append({
                'id': student.id,
                'user_id': student.user_id,
                'name': user.get_full_name(),
                'grade': student.grade.name if student.grade else 'N/A',
                'document': student.document_number
            })
    
    return result


def _can_access_observation(observation):
    """Check if current user can access an observation."""
    institution = get_current_institution()
    
    if not institution:
        return True  # Root without active institution can see all
    
    student = AcademicStudent.query.get(observation.student_id)
    return student and student.institution_id == institution.id
