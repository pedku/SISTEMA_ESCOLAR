"""
Excel handler service.
Handles bulk uploads for students and grades.
"""

import pandas as pd
from werkzeug.security import generate_password_hash
from extensions import db
from models.user import User
from models.academic import AcademicStudent, Campus, Grade, SubjectGrade
from models.grading import GradeRecord, GradeCriteria
from utils.username_generator import generate_username_from_db
from services.grade_calculator import GradeCalculatorService

class ExcelHandlerService:
    MIN_GRADE = 1.0
    MAX_GRADE = 5.0

    @classmethod
    def process_student_upload(cls, file_path, institution):
        """Process bulk student upload from Excel file."""
        try:
            df = pd.read_excel(file_path)
            # Normalize column names
            df.columns = [col.lower().strip().replace(' ', '_') for col in df.columns]

            created_count = 0
            errors = []

            for index, row in df.iterrows():
                try:
                    # Extract data
                    first_name = str(row.get('nombre', '')).strip()
                    last_name = str(row.get('apellido', '')).strip()
                    doc_number = str(row.get('documento', '')).strip()

                    if not first_name or not last_name or not doc_number:
                        errors.append(f"Fila {index + 2}: Nombre, apellido y documento son requeridos")
                        continue

                    # Check if student already exists
                    if AcademicStudent.query.filter_by(document_number=doc_number).first():
                        errors.append(f"Fila {index + 2}: Estudiante con documento {doc_number} ya existe")
                        continue

                    # Generate username
                    username = generate_username_from_db(
                        first_name,
                        last_name,
                        query_func=lambda pattern: [
                            u.username for u in User.query.filter(User.username.like(f'{pattern}%')).all()
                        ]
                    )

                    # Create user
                    user = User(
                        username=username,
                        email=f"{username}@sige.edu.co",
                        password_hash=generate_password_hash('estudiante123'),
                        first_name=first_name,
                        last_name=last_name,
                        document_type=str(row.get('tipo_documento', 'TI')).strip(),
                        document_number=doc_number,
                        role='student',
                        institution_id=institution.id,
                        is_active=True
                    )
                    db.session.add(user)
                    db.session.flush()

                    # Find campus
                    campus_name = str(row.get('sede', '')).strip()
                    campus = Campus.query.filter_by(
                        name=campus_name,
                        institution_id=institution.id
                    ).first() if campus_name else Campus.query.filter_by(
                        institution_id=institution.id
                    ).first()

                    if not campus:
                        errors.append(f"Fila {index + 2}: Sede '{campus_name}' no encontrada")
                        db.session.rollback()
                        continue

                    # Find grade
                    grade_name = str(row.get('grado', '')).strip()
                    grade = Grade.query.filter_by(
                        name=grade_name,
                        campus_id=campus.id,
                    ).first() if grade_name else None

                    # Create academic student
                    student = AcademicStudent(
                        user_id=user.id,
                        institution_id=institution.id,
                        campus_id=campus.id,
                        grade_id=grade.id if grade else None,
                        document_type=str(row.get('tipo_documento', 'TI')).strip(),
                        document_number=doc_number,
                        birth_date=pd.to_datetime(row.get('fecha_nacimiento')).date() if pd.notna(row.get('fecha_nacimiento')) else None,
                        address=str(row.get('direccion', '')).strip(),
                        neighborhood=str(row.get('barrio', '')).strip(),
                        stratum=int(row.get('estrato')) if pd.notna(row.get('estrato')) else None,
                        gender=str(row.get('genero', '')).strip(),
                        blood_type=str(row.get('tipo_sangre', '')).strip(),
                        eps=str(row.get('eps', '')).strip(),
                        guardian_name=str(row.get('acudiente', '')).strip(),
                        guardian_phone=str(row.get('telefono_acudiente', '')).strip(),
                        guardian_email=str(row.get('email_acudiente', '')).strip(),
                        enrolled_year=institution.academic_year,
                        status='activo'
                    )
                    db.session.add(student)
                    created_count += 1

                except Exception as e:
                    errors.append(f"Fila {index + 2}: Error - {str(e)}")
                    db.session.rollback()

            db.session.commit()
            return {'success': True, 'created_count': created_count, 'errors': errors}

        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @classmethod
    def process_grade_upload(cls, file_path, institution, sg_id, period_id, current_user):
        """Process bulk grade upload from Excel file."""
        try:
            df = pd.read_excel(file_path)

            subject_grade = db.session.get(SubjectGrade, sg_id)
            criteria = GradeCriteria.query.filter_by(institution_id=institution.id).order_by(GradeCriteria.order).all()

            # Get students in this grade
            students = AcademicStudent.query.filter_by(
                grade_id=subject_grade.grade_id,
                status='activo'
            ).join(User).all()

            student_lookup = {s.document_number.strip().lower(): s for s in students}

            saved_count = 0
            error_count = 0
            errors = []

            for index, row in df.iterrows():
                try:
                    # Find student by document number
                    doc_number = str(row.get('documento', '')).strip().lower()
                    if not doc_number:
                        # Try by name
                        first_name = str(row.get('nombre', '')).strip().lower()
                        last_name = str(row.get('apellido', '')).strip().lower()
                        if first_name and last_name:
                            user = User.query.filter(
                                db.and_(
                                    db.func.lower(User.first_name) == first_name,
                                    db.func.lower(User.last_name) == last_name
                                )
                            ).first()
                            if user:
                                student = AcademicStudent.query.filter_by(user_id=user.id).first()
                            else:
                                errors.append(f"Fila {index + 2}: Estudiante no encontrado por nombre")
                                error_count += 1
                                continue
                        else:
                            errors.append(f"Fila {index + 2}: Documento o nombre requeridos")
                            error_count += 1
                            continue
                    elif doc_number in student_lookup:
                        student = student_lookup[doc_number]
                    else:
                        errors.append(f"Fila {index + 2}: Estudiante con documento {doc_number} no encontrado")
                        error_count += 1
                        continue

                    # Save grades for each criterion
                    for criterion in criteria:
                        col_name = criterion.name.lower().strip()
                        score_str = None
                        for key in [col_name, col_name.replace(' ', '_'), col_name.replace(' ', ''), criterion.name]:
                            val = row.get(key)
                            if val is not None and str(val).strip():
                                score_str = str(val).strip()
                                break

                        if score_str:
                            try:
                                score = round(float(score_str), 1)
                                if score < cls.MIN_GRADE or score > cls.MAX_GRADE:
                                    errors.append(f"Fila {index + 2}: Nota de {criterion.name} fuera de rango ({score})")
                                    error_count += 1
                                    continue

                                existing = GradeRecord.query.filter_by(
                                    student_id=student.id,
                                    subject_grade_id=sg_id,
                                    period_id=period_id,
                                    criterion_id=criterion.id
                                ).first()

                                if existing and existing.locked:
                                    errors.append(f"Fila {index + 2}: Notas bloqueadas para {student.user.get_full_name()}")
                                    error_count += 1
                                    continue

                                if existing:
                                    existing.score = score
                                else:
                                    new_record = GradeRecord(
                                        student_id=student.id,
                                        subject_grade_id=sg_id,
                                        period_id=period_id,
                                        criterion_id=criterion.id,
                                        score=score,
                                        created_by=current_user.id,
                                        locked=False
                                    )
                                    db.session.add(new_record)

                                saved_count += 1
                            except (ValueError, TypeError):
                                errors.append(f"Fila {index + 2}: Valor invalido para {criterion.name}: '{score_str}'")
                                error_count += 1

                except Exception as e:
                    errors.append(f"Fila {index + 2}: Error - {str(e)}")
                    error_count += 1
                    db.session.rollback()

            # Calculate final grades
            final_count = 0
            for student in students:
                final_score = GradeCalculatorService.calculate_final_grade(student.id, sg_id, period_id, criteria)
                if final_score is not None:
                    GradeCalculatorService.save_final_grade(student.id, sg_id, period_id, final_score)
                    final_count += 1

            db.session.commit()
            return {
                'success': True,
                'saved_count': saved_count,
                'final_count': final_count,
                'error_count': error_count,
                'errors': errors
            }

        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
