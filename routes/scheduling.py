"""
Scheduling Blueprint - Sistema de Matricula, Asignacion y Horarios
Handles student enrollment, teacher assignments, and schedule generation.
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required
from extensions import db
from utils.decorators import role_required
from utils.institution_resolver import get_current_institution
from models.scheduling import Classroom, StudentEnrollment, TeacherSubjectAssignment, Schedule, ScheduleBlock
from models.academic import AcademicStudent, SubjectGrade, Grade, Subject
from models.user import User
from models.institution import Campus
from datetime import datetime, date
from sqlalchemy import and_

scheduling_bp = Blueprint('scheduling', __name__)


# ============================================================================
# STUDENT ENROLLMENT - MATRICULA DE ESTUDIANTES
# ============================================================================

@scheduling_bp.route('/enrollments')
@login_required
@role_required('root', 'admin', 'coordinator')
def enrollment_list():
    """List all student enrollments (matriculas)."""
    institution = get_current_institution()
    if not institution:
        flash('Seleccione una institucion primero.', 'warning')
        return redirect(url_for('dashboard.index'))

    # Filters
    grade_id = request.args.get('grade_id', type=int)
    subject_id = request.args.get('subject_id', type=int)
    academic_year = request.args.get('academic_year', institution.academic_year)
    status = request.args.get('status', 'activa')

    query = db.session.query(StudentEnrollment).join(AcademicStudent).filter(
        AcademicStudent.institution_id == institution.id
    )

    if grade_id:
        query = query.filter(AcademicStudent.grade_id == grade_id)
    if academic_year:
        query = query.filter(StudentEnrollment.academic_year == academic_year)
    if status:
        query = query.filter(StudentEnrollment.status == status)

    enrollments = query.order_by(StudentEnrollment.enrollment_date.desc()).all()

    # Get grades and subjects for filters
    grades = Grade.query.filter(
        Grade.campus_id.in_(db.session.query(Campus.id).filter_by(institution_id=institution.id))
    ).filter_by(academic_year=academic_year).all()
    subjects = Subject.query.filter_by(institution_id=institution.id).all()

    # Stats
    total_enrollments = len(enrollments)
    active_enrollments = sum(1 for e in enrollments if e.status == 'activa')

    return render_template('scheduling/enrollments/list.html',
                         enrollments=enrollments,
                         grades=grades,
                         subjects=subjects,
                         total_enrollments=total_enrollments,
                         active_enrollments=active_enrollments,
                         selected_grade_id=grade_id,
                         selected_subject_id=subject_id,
                         academic_year=academic_year,
                         selected_status=status)


@scheduling_bp.route('/enrollments/new', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def enrollment_create():
    """Create new student enrollments (matricular estudiantes a un grado)."""
    institution = get_current_institution()
    if not institution:
        flash('Seleccione una institucion primero.', 'warning')
        return redirect(url_for('dashboard.index'))

    academic_year = institution.academic_year

    if request.method == 'POST':
        grade_id = request.form.get('grade_id', type=int)
        student_ids = request.form.getlist('student_ids', type=int)

        errors = []
        success_count = 0
        skip_count = 0

        if not grade_id:
            errors.append('Seleccione un grado')
        if not student_ids:
            errors.append('Seleccione al menos un estudiante')

        if errors:
            for error in errors:
                flash(error, 'danger')
        else:
            # Get ALL subject-grades for this grade
            subject_grades = SubjectGrade.query.filter_by(grade_id=grade_id).all()

            if not subject_grades:
                flash('Este grado no tiene materias asignadas. Asigne materias primero.', 'warning')
                return redirect(url_for('scheduling.subject_grade_create'))

            # Enroll each student in ALL subjects of the grade
            for student_id in student_ids:
                for sg in subject_grades:
                    # Check if enrollment already exists
                    existing = StudentEnrollment.query.filter_by(
                        student_id=student_id,
                        subject_grade_id=sg.id,
                        academic_year=academic_year
                    ).first()

                    if existing:
                        skip_count += 1
                        continue

                    # Create enrollment
                    enrollment = StudentEnrollment(
                        student_id=student_id,
                        subject_grade_id=sg.id,
                        academic_year=academic_year,
                        enrollment_date=date.today(),
                        status='activa'
                    )
                    db.session.add(enrollment)
                    success_count += 1

            if success_count > 0:
                db.session.commit()
                msg = f'{success_count} matriculas creadas exitosamente.'
                if skip_count > 0:
                    msg += f' ({skip_count} ya existian)'
                flash(msg, 'success')
                return redirect(url_for('scheduling.enrollment_list'))
            else:
                flash('No se pudieron crear matriculas (todas ya existian).', 'info')

    # GET - show form
    grades = Grade.query.filter_by(
        campus_id=db.session.query(Campus.id).filter_by(institution_id=institution.id).subquery()
    ).filter_by(academic_year=academic_year).all()

    # Students will be loaded via AJAX based on grade selection
    return render_template('scheduling/enrollments/form.html',
                         grades=grades,
                         academic_year=academic_year,
                         mode='create')


@scheduling_bp.route('/enrollments/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def enrollment_edit(id):
    """Edit student enrollment."""
    institution = get_current_institution()
    enrollment = db.session.get(StudentEnrollment, id)

    if not enrollment:
        flash('Matricula no encontrada', 'danger')
        return redirect(url_for('scheduling.enrollment_list'))

    # Verify institution access
    student = db.session.get(AcademicStudent, enrollment.student_id)
    if student.institution_id != institution.id:
        flash('No tiene permiso para editar esta matricula', 'danger')
        return redirect(url_for('scheduling.enrollment_list'))

    if request.method == 'POST':
        status = request.form.get('status', 'activa')
        final_score = request.form.get('final_score', type=float)
        status_note = request.form.get('status_note')

        enrollment.status = status
        if final_score is not None:
            enrollment.final_score = final_score
        enrollment.status_note = status_note

        db.session.commit()
        flash('Matricula actualizada exitosamente', 'success')
        return redirect(url_for('scheduling.enrollment_list'))

    return render_template('scheduling/enrollments/form.html',
                         enrollment=enrollment,
                         mode='edit')


@scheduling_bp.route('/enrollments/<int:id>/delete', methods=['POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def enrollment_delete(id):
    """Delete student enrollment."""
    institution = get_current_institution()
    enrollment = db.session.get(StudentEnrollment, id)

    if not enrollment:
        flash('Matricula no encontrada', 'danger')
        return redirect(url_for('scheduling.enrollment_list'))

    # Verify institution access
    student = db.session.get(AcademicStudent, enrollment.student_id)
    if student.institution_id != institution.id:
        flash('No tiene permiso', 'danger')
        return redirect(url_for('scheduling.enrollment_list'))

    db.session.delete(enrollment)
    db.session.commit()
    flash('Matricula eliminada', 'success')
    return redirect(url_for('scheduling.enrollment_list'))


# ============================================================================
# TEACHER ASSIGNMENT - ASIGNACION DE PROFESORES
# ============================================================================

@scheduling_bp.route('/assignments')
@login_required
@role_required('root', 'admin', 'coordinator')
def assignment_list():
    """List all teacher assignments."""
    institution = get_current_institution()
    if not institution:
        flash('Seleccione una institucion primero.', 'warning')
        return redirect(url_for('dashboard.index'))

    academic_year = request.args.get('academic_year', institution.academic_year)
    grade_id = request.args.get('grade_id', type=int)

    query = db.session.query(TeacherSubjectAssignment).join(SubjectGrade).join(Grade).filter(
        Grade.campus_id.in_(db.session.query(Campus.id).filter_by(institution_id=institution.id))
    ).filter(
        TeacherSubjectAssignment.academic_year == academic_year
    )

    if grade_id:
        query = query.filter(SubjectGrade.grade_id == grade_id)

    assignments = query.order_by(TeacherSubjectAssignment.assignment_date.desc()).all()

    grades = Grade.query.filter(
        Grade.campus_id.in_(db.session.query(Campus.id).filter_by(institution_id=institution.id))
    ).filter_by(academic_year=academic_year).all()

    # Stats
    total_assignments = len(assignments)
    active_assignments = sum(1 for a in assignments if a.status == 'activo')

    return render_template('scheduling/assignments/list.html',
                         assignments=assignments,
                         grades=grades,
                         total_assignments=total_assignments,
                         active_assignments=active_assignments,
                         academic_year=academic_year,
                         selected_grade_id=grade_id)


@scheduling_bp.route('/assignments/new', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def assignment_create():
    """Create new teacher assignment."""
    institution = get_current_institution()
    if not institution:
        flash('Seleccione una institucion primero.', 'warning')
        return redirect(url_for('dashboard.index'))

    academic_year = institution.academic_year

    if request.method == 'POST':
        grade_id = request.form.get('grade_id', type=int)
        subject_id = request.form.get('subject_id', type=int)
        teacher_id = request.form.get('teacher_id', type=int)

        errors = []

        if not grade_id:
            errors.append('Seleccione un grado')
        if not subject_id:
            errors.append('Seleccione una materia')
        if not teacher_id:
            errors.append('Seleccione un profesor')

        if errors:
            for error in errors:
                flash(error, 'danger')
        else:
            # Find or create SubjectGrade
            subject_grade = SubjectGrade.query.filter_by(
                subject_id=subject_id,
                grade_id=grade_id,
                teacher_id=teacher_id
            ).first()

            if not subject_grade:
                # Create new SubjectGrade
                subject_grade = SubjectGrade(
                    subject_id=subject_id,
                    grade_id=grade_id,
                    teacher_id=teacher_id
                )
                db.session.add(subject_grade)
                db.session.flush()

            # Check if assignment already exists
            existing = TeacherSubjectAssignment.query.filter_by(
                subject_grade_id=subject_grade.id,
                academic_year=academic_year
            ).first()

            if existing:
                flash('El profesor ya esta asignado a esta materia en este grado', 'warning')
            else:
                assignment = TeacherSubjectAssignment(
                    subject_grade_id=subject_grade.id,
                    teacher_id=teacher_id,
                    academic_year=academic_year,
                    assignment_date=date.today(),
                    status='activo'
                )
                db.session.add(assignment)
                db.session.commit()
                flash('Profesor asignado exitosamente', 'success')
                return redirect(url_for('scheduling.assignment_list'))

    # GET - show form
    grades = Grade.query.filter(
        Grade.campus_id.in_(db.session.query(Campus.id).filter_by(institution_id=institution.id))
    ).filter_by(academic_year=academic_year).all()

    subjects = Subject.query.filter_by(institution_id=institution.id).all()
    
    teachers = User.query.filter_by(
        institution_id=institution.id,
        role='teacher'
    ).filter_by(is_active=True).all()

    return render_template('scheduling/assignments/form.html',
                         grades=grades,
                         subjects=subjects,
                         teachers=teachers,
                         academic_year=academic_year,
                         mode='create')


@scheduling_bp.route('/assignments/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def assignment_edit(id):
    """Edit teacher assignment."""
    institution = get_current_institution()
    assignment = db.session.get(TeacherSubjectAssignment, id)

    if not assignment:
        flash('Asignacion no encontrada', 'danger')
        return redirect(url_for('scheduling.assignment_list'))

    # Verify institution access
    subject_grade = db.session.get(SubjectGrade, assignment.subject_grade_id)
    grade = db.session.get(Grade, subject_grade.grade_id)
    campus = db.session.get(Campus, grade.campus_id)
    if campus.institution_id != institution.id:
        flash('No tiene permiso', 'danger')
        return redirect(url_for('scheduling.assignment_list'))

    if request.method == 'POST':
        status = request.form.get('status', 'activo')
        notes = request.form.get('notes')

        assignment.status = status
        assignment.notes = notes

        db.session.commit()
        flash('Asignacion actualizada exitosamente', 'success')
        return redirect(url_for('scheduling.assignment_list'))

    grades = Grade.query.filter(
        Grade.campus_id.in_(db.session.query(Campus.id).filter_by(institution_id=institution.id))
    ).all()

    subjects = Subject.query.filter_by(institution_id=institution.id).all()
    teachers = User.query.filter_by(institution_id=institution.id, role='teacher').all()

    return render_template('scheduling/assignments/form.html',
                         assignment=assignment,
                         grades=grades,
                         subjects=subjects,
                         teachers=teachers,
                         mode='edit')


@scheduling_bp.route('/assignments/<int:id>/delete', methods=['POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def assignment_delete(id):
    """Delete teacher assignment."""
    institution = get_current_institution()
    assignment = db.session.get(TeacherSubjectAssignment, id)

    if not assignment:
        flash('Asignacion no encontrada', 'danger')
        return redirect(url_for('scheduling.assignment_list'))

    # Verify institution access
    subject_grade = db.session.get(SubjectGrade, assignment.subject_grade_id)
    grade = db.session.get(Grade, subject_grade.grade_id)
    campus = db.session.get(Campus, grade.campus_id)
    if campus.institution_id != institution.id:
        flash('No tiene permiso', 'danger')
        return redirect(url_for('scheduling.assignment_list'))

    db.session.delete(assignment)
    db.session.commit()
    flash('Asignacion eliminada', 'success')
    return redirect(url_for('scheduling.assignment_list'))


# ============================================================================
# SUBJECT-GRADE ASSIGNMENT - ASIGNAR MATERIAS A GRADOS
# ============================================================================

@scheduling_bp.route('/subject-grades')
@login_required
@role_required('root', 'admin', 'coordinator')
def subject_grade_list():
    """List all subject-grade assignments."""
    institution = get_current_institution()
    if not institution:
        flash('Seleccione una institucion primero.', 'warning')
        return redirect(url_for('dashboard.index'))

    academic_year = request.args.get('academic_year', institution.academic_year)
    grade_id = request.args.get('grade_id', type=int)

    query = db.session.query(SubjectGrade).join(Grade).filter(
        Grade.campus_id.in_(db.session.query(Campus.id).filter_by(institution_id=institution.id))
    )

    if grade_id:
        query = query.filter(SubjectGrade.grade_id == grade_id)

    subject_grades = query.order_by(SubjectGrade.grade_id, SubjectGrade.subject_id).all()

    grades = Grade.query.filter(
        Grade.campus_id.in_(db.session.query(Campus.id).filter_by(institution_id=institution.id))
    ).filter_by(academic_year=academic_year).all()

    subjects = Subject.query.filter_by(institution_id=institution.id).all()

    return render_template('scheduling/subject_grades/list.html',
                         subject_grades=subject_grades,
                         grades=grades,
                         subjects=subjects,
                         academic_year=academic_year,
                         selected_grade_id=grade_id)


@scheduling_bp.route('/subject-grades/new', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def subject_grade_create():
    """Assign subject to grade."""
    institution = get_current_institution()
    if not institution:
        flash('Seleccione una institucion primero.', 'warning')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        grade_ids = request.form.getlist('grade_ids', type=int)
        subject_ids = request.form.getlist('subject_ids', type=int)
        teacher_id = request.form.get('teacher_id', type=int)

        errors = []
        success_count = 0

        if not grade_ids:
            errors.append('Seleccione al menos un grado')
        if not subject_ids:
            errors.append('Seleccione al menos una materia')

        if errors:
            for error in errors:
                flash(error, 'danger')
        else:
            for grade_id in grade_ids:
                for subject_id in subject_ids:
                    # Check if already exists
                    existing = SubjectGrade.query.filter_by(
                        subject_id=subject_id,
                        grade_id=grade_id,
                        teacher_id=teacher_id
                    ).first()

                    if existing:
                        continue

                    subject_grade = SubjectGrade(
                        subject_id=subject_id,
                        grade_id=grade_id,
                        teacher_id=teacher_id
                    )
                    db.session.add(subject_grade)
                    success_count += 1

            if success_count > 0:
                db.session.commit()
                flash(f'{success_count} asignaciones creadas', 'success')
                return redirect(url_for('scheduling.subject_grade_list'))
            else:
                flash('Las asignaciones ya existen', 'info')

    grades = Grade.query.filter(
        Grade.campus_id.in_(db.session.query(Campus.id).filter_by(institution_id=institution.id))
    ).all()

    subjects = Subject.query.filter_by(institution_id=institution.id).all()
    teachers = User.query.filter_by(institution_id=institution.id, role='teacher').all()

    return render_template('scheduling/subject_grades/form.html',
                         grades=grades,
                         subjects=subjects,
                         teachers=teachers,
                         mode='create')


@scheduling_bp.route('/subject-grades/<int:id>/delete', methods=['POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def subject_grade_delete(id):
    """Delete subject-grade assignment."""
    institution = get_current_institution()
    subject_grade = db.session.get(SubjectGrade, id)

    if not subject_grade:
        flash('Asignacion no encontrada', 'danger')
        return redirect(url_for('scheduling.subject_grade_list'))

    # Verify institution access
    grade = db.session.get(Grade, subject_grade.grade_id)
    campus = db.session.get(Campus, grade.campus_id)
    if campus.institution_id != institution.id:
        flash('No tiene permiso', 'danger')
        return redirect(url_for('scheduling.subject_grade_list'))

    db.session.delete(subject_grade)
    db.session.commit()
    flash('Asignacion eliminada', 'success')
    return redirect(url_for('scheduling.subject_grade_list'))


# ============================================================================
# CLASSROOMS - GESTION DE SALONES
# ============================================================================

@scheduling_bp.route('/classrooms')
@login_required
@role_required('root', 'admin', 'coordinator')
def classroom_list():
    """List all classrooms."""
    institution = get_current_institution()
    if not institution:
        flash('Seleccione una institucion primero.', 'warning')
        return redirect(url_for('dashboard.index'))

    campus_id = request.args.get('campus_id', type=int)

    query = db.session.query(Classroom).join(Campus).filter(
        Campus.institution_id == institution.id
    )

    if campus_id:
        query = query.filter(Classroom.campus_id == campus_id)

    classrooms = query.order_by(Classroom.campus_id, Classroom.name).all()

    campuses = Campus.query.filter_by(institution_id=institution.id, active=True).all()

    # Stats
    total_classrooms = len(classrooms)
    aula_count = sum(1 for c in classrooms if c.classroom_type == 'aula')
    lab_count = sum(1 for c in classrooms if c.classroom_type == 'laboratorio')

    return render_template('scheduling/classrooms/list.html',
                         classrooms=classrooms,
                         campuses=campuses,
                         total_classrooms=total_classrooms,
                         aula_count=aula_count,
                         lab_count=lab_count,
                         selected_campus_id=campus_id)


@scheduling_bp.route('/classrooms/new', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def classroom_create():
    """Create new classroom."""
    institution = get_current_institution()
    if not institution:
        flash('Seleccione una institucion primero.', 'warning')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        campus_id = request.form.get('campus_id', type=int)
        name = request.form.get('name')
        code = request.form.get('code')
        capacity = request.form.get('capacity', 40, type=int)
        floor = request.form.get('floor', 1, type=int)
        building = request.form.get('building')
        classroom_type = request.form.get('classroom_type', 'aula')
        resources = request.form.get('resources')

        errors = []
        if not campus_id:
            errors.append('Seleccione una sede')
        if not name:
            errors.append('Ingrese el nombre')
        if not code:
            errors.append('Ingrese el codigo')

        if errors:
            for error in errors:
                flash(error, 'danger')
        else:
            classroom = Classroom(
                campus_id=campus_id,
                name=name,
                code=code,
                capacity=capacity,
                floor=floor,
                building=building,
                classroom_type=classroom_type,
                resources=resources
            )
            db.session.add(classroom)
            db.session.commit()
            flash('Salon creado exitosamente', 'success')
            return redirect(url_for('scheduling.classroom_list'))

    campuses = Campus.query.filter_by(institution_id=institution.id, active=True).all()

    return render_template('scheduling/classrooms/form.html',
                         campuses=campuses,
                         mode='create')


@scheduling_bp.route('/classrooms/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def classroom_edit(id):
    """Edit classroom."""
    institution = get_current_institution()
    classroom = db.session.get(Classroom, id)

    if not classroom:
        flash('Salon no encontrado', 'danger')
        return redirect(url_for('scheduling.classroom_list'))

    # Verify institution access
    campus = db.session.get(Campus, classroom.campus_id)
    if campus.institution_id != institution.id:
        flash('No tiene permiso', 'danger')
        return redirect(url_for('scheduling.classroom_list'))

    if request.method == 'POST':
        classroom.name = request.form.get('name')
        classroom.code = request.form.get('code')
        classroom.capacity = request.form.get('capacity', 40, type=int)
        classroom.floor = request.form.get('floor', 1, type=int)
        classroom.building = request.form.get('building')
        classroom.classroom_type = request.form.get('classroom_type', 'aula')
        classroom.resources = request.form.get('resources')

        db.session.commit()
        flash('Salon actualizado exitosamente', 'success')
        return redirect(url_for('scheduling.classroom_list'))

    campuses = Campus.query.filter_by(institution_id=institution.id, active=True).all()

    return render_template('scheduling/classrooms/form.html',
                         classroom=classroom,
                         campuses=campuses,
                         mode='edit')


@scheduling_bp.route('/classrooms/<int:id>/delete', methods=['POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def classroom_delete(id):
    """Delete classroom."""
    institution = get_current_institution()
    classroom = db.session.get(Classroom, id)

    if not classroom:
        flash('Salon no encontrado', 'danger')
        return redirect(url_for('scheduling.classroom_list'))

    campus = db.session.get(Campus, classroom.campus_id)
    if campus.institution_id != institution.id:
        flash('No tiene permiso', 'danger')
        return redirect(url_for('scheduling.classroom_list'))

    db.session.delete(classroom)
    db.session.commit()
    flash('Salon eliminado', 'success')
    return redirect(url_for('scheduling.classroom_list'))


# ============================================================================
# SCHEDULE GENERATION - GENERADOR DE HORARIOS
# ============================================================================

@scheduling_bp.route('/schedules/generate')
@login_required
@role_required('root', 'admin', 'coordinator')
def schedule_generate_view():
    """View to generate schedules automatically."""
    institution = get_current_institution()
    if not institution:
        flash('Seleccione una institucion primero.', 'warning')
        return redirect(url_for('dashboard.index'))

    academic_year = institution.academic_year
    
    campuses = Campus.query.filter_by(institution_id=institution.id, active=True).all()
    grades = Grade.query.filter(
        Grade.campus_id.in_(db.session.query(Campus.id).filter_by(institution_id=institution.id))
    ).filter_by(academic_year=academic_year).all()

    return render_template('scheduling/schedules/generate.html',
                         campuses=campuses,
                         grades=grades,
                         academic_year=academic_year)


@scheduling_bp.route('/schedules/generate/run', methods=['POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def schedule_generate_run():
    """Run automatic schedule generation algorithm."""
    institution = get_current_institution()
    if not institution:
        return jsonify({'success': False, 'error': 'Institucion no seleccionada'})

    academic_year = institution.academic_year
    grade_id = request.form.get('grade_id', type=int)
    campus_id = request.form.get('campus_id', type=int)

    # Get grade or all grades in campus
    grades = []
    if grade_id:
        grade = db.session.get(Grade, grade_id)
        if grade:
            grades = [grade]
    elif campus_id:
        grades = Grade.query.filter_by(campus_id=campus_id, academic_year=academic_year).all()
    else:
        grades = Grade.query.filter(
            Grade.campus_id.in_(db.session.query(Campus.id).filter_by(institution_id=institution.id))
        ).filter_by(academic_year=academic_year).all()

    # Get schedule blocks
    blocks = []
    if campus_id:
        blocks = ScheduleBlock.query.filter_by(
            campus_id=campus_id,
            academic_year=academic_year
        ).order_by(ScheduleBlock.order_num).all()
    else:
        # Get blocks from first campus
        if grades:
            campus = db.session.get(Campus, grades[0].campus_id)
            if campus:
                blocks = ScheduleBlock.query.filter_by(
                    campus_id=campus.id,
                    academic_year=academic_year
                ).order_by(ScheduleBlock.order_num).all()

    if not blocks:
        # Create default blocks if none exist
        default_blocks = [
            ('Bloque 1', '07:00', '08:00', False, 1),
            ('Bloque 2', '08:00', '09:00', False, 2),
            ('Recreo', '09:00', '09:30', True, 3),
            ('Bloque 3', '09:30', '10:30', False, 4),
            ('Bloque 4', '10:30', '11:30', False, 5),
            ('Almuerzo', '11:30', '12:30', True, 6),
            ('Bloque 5', '12:30', '01:30', False, 7),
            ('Bloque 6', '01:30', '02:30', False, 8),
        ]
        
        campus = db.session.get(Campus, grades[0].campus_id) if grades else None
        if campus:
            for name, start, end, is_break, order_num in default_blocks:
                block = ScheduleBlock(
                    campus_id=campus.id,
                    name=name,
                    start_time=datetime.strptime(start, '%H:%M').time(),
                    end_time=datetime.strptime(end, '%H:%M').time(),
                    is_break=is_break,
                    order_num=order_num,
                    academic_year=academic_year
                )
                db.session.add(block)
            db.session.commit()
            blocks = ScheduleBlock.query.filter_by(
                campus_id=campus.id,
                academic_year=academic_year
            ).order_by(ScheduleBlock.order_num).all()

    # Get classrooms
    classrooms = []
    if campus_id:
        classrooms = Classroom.query.filter_by(campus_id=campus_id).all()
    elif grades:
        campus = db.session.get(Campus, grades[0].campus_id)
        if campus:
            classrooms = Classroom.query.filter_by(campus_id=campus.id).all()

    if not classrooms:
        return jsonify({'success': False, 'error': 'No hay salones disponibles'})

    # Schedule generation algorithm
    scheduled_count = 0
    conflicts = 0
    
    for grade in grades:
        # Get subject-grades for this grade
        subject_grades = SubjectGrade.query.filter_by(grade_id=grade.id).all()
        
        if not subject_grades:
            continue

        # Get available time slots (day x block)
        days = [0, 1, 2, 3, 4]  # Mon-Fri
        available_slots = [(day, block) for day in days for block in blocks if not block.is_break]
        
        # Shuffle for variety
        import random
        random.shuffle(available_slots)

        # Assign each subject to slots
        for subject_grade in subject_grades:
            # Check if already scheduled
            existing = Schedule.query.filter_by(
                subject_grade_id=subject_grade.id,
                academic_year=academic_year,
                is_active=True
            ).all()
            
            if existing:
                continue

            # Try to assign to available slots
            for day, block in available_slots:
                # Check teacher availability
                teacher_conflict = Schedule.query.join(SubjectGrade).filter(
                    SubjectGrade.teacher_id == subject_grade.teacher_id,
                    Schedule.day_of_week == day,
                    Schedule.start_time == block.start_time,
                    Schedule.academic_year == academic_year,
                    Schedule.is_active == True
                ).first()

                if teacher_conflict:
                    continue

                # Check classroom availability
                classroom = classrooms[0]  # Default classroom
                room_conflict = Schedule.query.filter_by(
                    classroom_id=classroom.id,
                    day_of_week=day,
                    start_time=block.start_time,
                    academic_year=academic_year,
                    is_active=True
                ).first()

                if room_conflict:
                    # Try another classroom
                    for c in classrooms:
                        room_conflict = Schedule.query.filter_by(
                            classroom_id=c.id,
                            day_of_week=day,
                            start_time=block.start_time,
                            academic_year=academic_year,
                            is_active=True
                        ).first()
                        if not room_conflict:
                            classroom = c
                            break
                    
                    if room_conflict:
                        continue

                # Create schedule
                schedule = Schedule(
                    subject_grade_id=subject_grade.id,
                    classroom_id=classroom.id,
                    day_of_week=day,
                    start_time=block.start_time,
                    end_time=block.end_time,
                    academic_year=academic_year,
                    is_active=True
                )
                db.session.add(schedule)
                scheduled_count += 1
                break
            else:
                conflicts += 1

    if scheduled_count > 0:
        db.session.commit()
        return jsonify({
            'success': True,
            'scheduled': scheduled_count,
            'conflicts': conflicts
        })
    else:
        return jsonify({
            'success': False,
            'error': 'No se pudieron generar horarios. Verifique que existan materias asignadas y salones disponibles.',
            'conflicts': conflicts
        })


# ============================================================================
# SCHEDULE VIEWING - VISUALIZACION DE HORARIOS
# ============================================================================

@scheduling_bp.route('/schedules')
@login_required
@role_required('root', 'admin', 'coordinator', 'teacher', 'student')
def schedule_list():
    """View schedules (filtered by role)."""
    institution = get_current_institution()
    if not institution:
        flash('Seleccione una institucion primero.', 'warning')
        return redirect(url_for('dashboard.index'))

    academic_year = institution.academic_year
    current_user = request.current_user if hasattr(request, 'current_user') else None

    # Filter based on role
    schedules = []
    
    if current_user and current_user.role == 'teacher':
        # Teacher sees their own schedules
        schedules = Schedule.query.join(SubjectGrade).filter(
            SubjectGrade.teacher_id == current_user.id,
            Schedule.academic_year == academic_year,
            Schedule.is_active == True
        ).order_by(Schedule.day_of_week, Schedule.start_time).all()
    
    elif current_user and current_user.role == 'student':
        # Student sees their grade schedules
        student_profile = AcademicStudent.query.filter_by(user_id=current_user.id).first()
        if student_profile:
            schedules = Schedule.query.join(SubjectGrade).filter(
                SubjectGrade.grade_id == student_profile.grade_id,
                Schedule.academic_year == academic_year,
                Schedule.is_active == True
            ).order_by(Schedule.day_of_week, Schedule.start_time).all()
    
    else:
        # Admin/coordinator sees all
        grade_id = request.args.get('grade_id', type=int)
        
        query = Schedule.query.join(SubjectGrade).join(Grade).filter(
            Grade.campus_id.in_(db.session.query(Campus.id).filter_by(institution_id=institution.id)),
            Schedule.academic_year == academic_year,
            Schedule.is_active == True
        )
        
        if grade_id:
            query = query.filter(SubjectGrade.grade_id == grade_id)
        
        schedules = query.order_by(Schedule.day_of_week, Schedule.start_time).all()

    # Organize by day and time
    schedule_grid = {}
    days = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes']
    
    for schedule in schedules:
        day_idx = schedule.day_of_week
        time_key = schedule.start_time.strftime('%H:%M')
        
        if day_idx not in schedule_grid:
            schedule_grid[day_idx] = {}
        
        schedule_grid[day_idx][time_key] = schedule

    grades = Grade.query.filter(
        Grade.campus_id.in_(db.session.query(Campus.id).filter_by(institution_id=institution.id))
    ).filter_by(academic_year=academic_year).all()

    return render_template('scheduling/schedules/list.html',
                         schedules=schedules,
                         schedule_grid=schedule_grid,
                         days=days,
                         grades=grades,
                         academic_year=academic_year)


@scheduling_bp.route('/schedules/<int:id>/delete', methods=['POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def schedule_delete(id):
    """Delete schedule entry."""
    institution = get_current_institution()
    schedule = db.session.get(Schedule, id)

    if not schedule:
        flash('Horario no encontrado', 'danger')
        return redirect(url_for('scheduling.schedule_list'))

    # Verify institution access
    subject_grade = db.session.get(SubjectGrade, schedule.subject_grade_id)
    grade = db.session.get(Grade, subject_grade.grade_id)
    campus = db.session.get(Campus, grade.campus_id)
    if campus.institution_id != institution.id:
        flash('No tiene permiso', 'danger')
        return redirect(url_for('scheduling.schedule_list'))

    db.session.delete(schedule)
    db.session.commit()
    flash('Horario eliminado', 'success')
    return redirect(url_for('scheduling.schedule_list'))


# ============================================================================
# SCHEDULE BLOCKS - BLOQUES DE TIEMPO
# ============================================================================

@scheduling_bp.route('/blocks')
@login_required
@role_required('root', 'admin', 'coordinator')
def block_list():
    """List schedule blocks."""
    institution = get_current_institution()
    if not institution:
        flash('Seleccione una institucion primero.', 'warning')
        return redirect(url_for('dashboard.index'))

    academic_year = institution.academic_year
    campus_id = request.args.get('campus_id', type=int)

    query = ScheduleBlock.query.join(Campus).filter(
        Campus.institution_id == institution.id,
        ScheduleBlock.academic_year == academic_year
    )

    if campus_id:
        query = query.filter(ScheduleBlock.campus_id == campus_id)

    blocks = query.order_by(ScheduleBlock.campus_id, ScheduleBlock.order_num).all()

    campuses = Campus.query.filter_by(institution_id=institution.id, active=True).all()

    return render_template('scheduling/blocks/list.html',
                         blocks=blocks,
                         campuses=campuses,
                         academic_year=academic_year,
                         selected_campus_id=campus_id)


@scheduling_bp.route('/blocks/new', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def block_create():
    """Create schedule block."""
    institution = get_current_institution()
    if not institution:
        flash('Seleccione una institucion primero.', 'warning')
        return redirect(url_for('dashboard.index'))

    academic_year = institution.academic_year

    if request.method == 'POST':
        campus_id = request.form.get('campus_id', type=int)
        name = request.form.get('name')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        is_break = request.form.get('is_break') == 'on'
        order_num = request.form.get('order_num', 0, type=int)

        errors = []
        if not campus_id:
            errors.append('Seleccione una sede')
        if not name:
            errors.append('Ingrese el nombre')
        if not start_time:
            errors.append('Ingrese la hora de inicio')
        if not end_time:
            errors.append('Ingrese la hora de fin')

        if errors:
            for error in errors:
                flash(error, 'danger')
        else:
            block = ScheduleBlock(
                campus_id=campus_id,
                name=name,
                start_time=datetime.strptime(start_time, '%H:%M').time(),
                end_time=datetime.strptime(end_time, '%H:%M').time(),
                is_break=is_break,
                order_num=order_num,
                academic_year=academic_year
            )
            db.session.add(block)
            db.session.commit()
            flash('Bloque de tiempo creado exitosamente', 'success')
            return redirect(url_for('scheduling.block_list'))

    campuses = Campus.query.filter_by(institution_id=institution.id, active=True).all()

    return render_template('scheduling/blocks/form.html',
                         campuses=campuses,
                         academic_year=academic_year,
                         mode='create')


@scheduling_bp.route('/blocks/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def block_edit(id):
    """Edit schedule block."""
    institution = get_current_institution()
    block = db.session.get(ScheduleBlock, id)

    if not block:
        flash('Bloque no encontrado', 'danger')
        return redirect(url_for('scheduling.block_list'))

    campus = db.session.get(Campus, block.campus_id)
    if campus.institution_id != institution.id:
        flash('No tiene permiso', 'danger')
        return redirect(url_for('scheduling.block_list'))

    if request.method == 'POST':
        block.name = request.form.get('name')
        block.start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
        block.end_time = datetime.strptime(request.form.get('end_time'), '%H:%M').time()
        block.is_break = request.form.get('is_break') == 'on'
        block.order_num = request.form.get('order_num', 0, type=int)

        db.session.commit()
        flash('Bloque de tiempo actualizado exitosamente', 'success')
        return redirect(url_for('scheduling.block_list'))

    campuses = Campus.query.filter_by(institution_id=institution.id, active=True).all()

    return render_template('scheduling/blocks/form.html',
                         block=block,
                         campuses=campuses,
                         mode='edit')


@scheduling_bp.route('/blocks/<int:id>/delete', methods=['POST'])
@login_required
@role_required('root', 'admin', 'coordinator')
def block_delete(id):
    """Delete schedule block."""
    institution = get_current_institution()
    block = db.session.get(ScheduleBlock, id)

    if not block:
        flash('Bloque no encontrado', 'danger')
        return redirect(url_for('scheduling.block_list'))

    campus = db.session.get(Campus, block.campus_id)
    if campus.institution_id != institution.id:
        flash('No tiene permiso', 'danger')
        return redirect(url_for('scheduling.block_list'))

    db.session.delete(block)
    db.session.commit()
    flash('Bloque de tiempo eliminado', 'success')
    return redirect(url_for('scheduling.block_list'))


# ============================================================================
# API ENDPOINTS
# ============================================================================

@scheduling_bp.route('/api/students/by-grade/<int:grade_id>')
@login_required
def api_students_by_grade(grade_id):
    """Get students by grade (AJAX)."""
    students = AcademicStudent.query.filter_by(
        grade_id=grade_id,
        status='activo'
    ).order_by(AcademicStudent.user_id).all()

    return jsonify([{
        'id': s.id,
        'name': s.user.first_name + ' ' + s.user.last_name,
        'document': s.document_number
    } for s in students])


@scheduling_bp.route('/api/subject-grades/by-grade/<int:grade_id>')
@login_required
def api_subject_grades_by_grade(grade_id):
    """Get subject-grades by grade (AJAX)."""
    subject_grades = SubjectGrade.query.filter_by(grade_id=grade_id).all()

    return jsonify([{
        'id': sg.id,
        'subject_name': sg.subject.name,
        'grade_name': sg.grade.name,
        'teacher_name': sg.teacher_user.first_name + ' ' + sg.teacher_user.last_name if sg.teacher_user else 'Sin asignar'
    } for sg in subject_grades])
