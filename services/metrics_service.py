"""
Metrics and analytics service.
Handles logic for calculating academic and attendance metrics.
"""

from extensions import db
from sqlalchemy import func, case
from models.academic import SubjectGrade, Grade, AcademicStudent
from models.grading import FinalGrade, AcademicPeriod
from models.attendance import Attendance
from models.user import User
from models.academic import Subject

class MetricsService:

    @staticmethod
    def get_teacher_subject_grades(teacher_id=None, institution=None):
        from models.institution import Campus
        query = db.session.query(SubjectGrade)

        if institution:
            valid_grade_ids = db.session.query(Grade.id).join(
                Campus, Grade.campus_id == Campus.id
            ).filter(Campus.institution_id == institution.id).subquery()
            query = query.filter(SubjectGrade.grade_id.in_(valid_grade_ids))

        if teacher_id:
            query = query.filter(SubjectGrade.teacher_id == teacher_id)

        return query.all()

    @staticmethod
    def get_teacher_groups_data(teacher_id, institution=None):
        query = db.session.query(
            SubjectGrade, Grade, User
        ).join(
            Grade, SubjectGrade.grade_id == Grade.id
        ).join(
            User, SubjectGrade.teacher_id == User.id
        ).filter(
            SubjectGrade.teacher_id == teacher_id
        )

        if institution:
            from models.institution import Campus
            query = query.join(Campus, Grade.campus_id == Campus.id).filter(
                Campus.institution_id == institution.id
            )

        results = query.all()
        groups_data = []

        for sg, grade, teacher in results:
            students = db.session.query(AcademicStudent).filter(
                AcademicStudent.grade_id == grade.id,
                AcademicStudent.status == 'activo'
            ).all()

            student_ids = [s.id for s in students]
            student_count = len(student_ids)

            avg_score = None
            pass_count = 0
            fail_count = 0
            at_risk_count = 0

            if student_ids:
                final_grades = db.session.query(FinalGrade).filter(
                    FinalGrade.subject_grade_id == sg.id,
                    FinalGrade.student_id.in_(student_ids)
                ).all()

                if final_grades:
                    scores = [fg.final_score for fg in final_grades if fg.final_score is not None]
                    if scores:
                        avg_score = round(sum(scores) / len(scores), 2)
                        pass_count = sum(1 for s in scores if s >= 3.0)
                        fail_count = sum(1 for s in scores if s < 3.0)
                        at_risk_count = sum(1 for s in scores if s < 3.0)

            pass_rate = round((pass_count / (pass_count + fail_count)) * 100, 1) if (pass_count + fail_count) > 0 else 0

            groups_data.append({
                'subject_grade_id': sg.id,
                'grade_name': grade.name,
                'grade_id': grade.id,
                'subject_name': sg.subject.name if sg.subject else 'N/A',
                'teacher_name': teacher.get_full_name(),
                'student_count': student_count,
                'avg_score': avg_score,
                'pass_count': pass_count,
                'fail_count': fail_count,
                'pass_rate': pass_rate,
                'at_risk_count': at_risk_count,
            })

        return groups_data

    @staticmethod
    def get_risk_students(teacher_id, institution=None, threshold=3.0):
        sg_query = db.session.query(SubjectGrade).filter(SubjectGrade.teacher_id == teacher_id)

        if institution:
            from models.institution import Campus
            sg_query = sg_query.join(Grade).join(Campus).filter(Campus.institution_id == institution.id)

        subject_grades = sg_query.all()
        sg_ids = [sg.id for sg in subject_grades]

        if not sg_ids:
            return []

        final_grades = db.session.query(
            FinalGrade, AcademicStudent, User, Grade, SubjectGrade
        ).join(
            AcademicStudent, FinalGrade.student_id == AcademicStudent.id
        ).join(
            User, AcademicStudent.user_id == User.id
        ).join(
            Grade, AcademicStudent.grade_id == Grade.id
        ).join(
            SubjectGrade, FinalGrade.subject_grade_id == SubjectGrade.id
        ).filter(
            FinalGrade.subject_grade_id.in_(sg_ids),
            FinalGrade.final_score.isnot(None)
        ).all()

        student_averages = {}
        for fg, student, user, grade, sg in final_grades:
            if student.id not in student_averages:
                student_averages[student.id] = {
                    'student_id': student.id,
                    'student_name': user.get_full_name(),
                    'grade_name': grade.name,
                    'grades': [],
                    'subjects': set()
                }
            student_averages[student.id]['grades'].append(fg.final_score)
            student_averages[student.id]['subjects'].add(sg.subject.name if sg.subject else 'N/A')

        risk_students = []
        for sid, data in student_averages.items():
            avg = round(sum(data['grades']) / len(data['grades']), 2) if data['grades'] else 0
            if avg < threshold:
                risk_students.append({
                    'student_id': sid,
                    'student_name': data['student_name'],
                    'grade_name': data['grade_name'],
                    'avg_score': avg,
                    'subjects': ', '.join(sorted(data['subjects'])),
                    'grade_count': len(data['grades'])
                })

        risk_students.sort(key=lambda x: x['avg_score'])
        return risk_students

    @staticmethod
    def get_grade_distribution(teacher_id, institution=None):
        sg_query = db.session.query(SubjectGrade.id).filter(SubjectGrade.teacher_id == teacher_id)

        if institution:
            from models.institution import Campus
            sg_query = sg_query.join(Grade).join(Campus).filter(Campus.institution_id == institution.id)

        sg_ids = [r[0] for r in sg_query.all()]

        if not sg_ids:
            return []

        final_grades = db.session.query(FinalGrade.final_score).filter(
            FinalGrade.subject_grade_id.in_(sg_ids),
            FinalGrade.final_score.isnot(None)
        ).all()

        return [fg[0] for fg in final_grades]

    @staticmethod
    def get_period_trend(teacher_id, institution=None):
        sg_query = db.session.query(SubjectGrade.id).filter(SubjectGrade.teacher_id == teacher_id)

        if institution:
            from models.institution import Campus
            sg_query = sg_query.join(Grade).join(Campus).filter(Campus.institution_id == institution.id)

        sg_ids = [r[0] for r in sg_query.all()]

        if not sg_ids:
            return []

        results = db.session.query(
            AcademicPeriod.short_name,
            func.avg(FinalGrade.final_score).label('avg_score')
        ).join(
            FinalGrade, AcademicPeriod.id == FinalGrade.period_id
        ).filter(
            FinalGrade.subject_grade_id.in_(sg_ids),
            FinalGrade.final_score.isnot(None)
        ).group_by(
            AcademicPeriod.id, AcademicPeriod.short_name, AcademicPeriod.order
        ).order_by(
            AcademicPeriod.order
        ).all()

        return [(r[0], round(r[1], 2)) for r in results]

    @staticmethod
    def get_institution_average(teacher_id=None, institution=None):
        query = db.session.query(func.avg(FinalGrade.final_score)).filter(FinalGrade.final_score.isnot(None))

        if institution:
            from models.institution import Campus
            query = query.join(SubjectGrade).join(Grade).join(Campus).filter(Campus.institution_id == institution.id)

        result = query.scalar()
        return round(result, 2) if result else 0

    @staticmethod
    def get_teacher_average(teacher_id, institution=None):
        sg_query = db.session.query(SubjectGrade.id).filter(SubjectGrade.teacher_id == teacher_id)

        if institution:
            from models.institution import Campus
            sg_query = sg_query.join(Grade).join(Campus).filter(Campus.institution_id == institution.id)

        sg_ids = [r[0] for r in sg_query.all()]

        if not sg_ids:
            return 0

        result = db.session.query(func.avg(FinalGrade.final_score)).filter(
            FinalGrade.subject_grade_id.in_(sg_ids),
            FinalGrade.final_score.isnot(None)
        ).scalar()

        return round(result, 2) if result else 0

    @staticmethod
    def get_all_teacher_averages(institution=None):
        query = db.session.query(
            User.id, User.first_name, User.last_name, func.avg(FinalGrade.final_score).label('avg_score')
        ).join(
            SubjectGrade, User.id == SubjectGrade.teacher_id
        ).join(
            FinalGrade, SubjectGrade.id == FinalGrade.subject_grade_id
        ).filter(
            FinalGrade.final_score.isnot(None), User.role == 'teacher'
        )

        if institution:
            from models.institution import Campus
            query = query.join(Grade, SubjectGrade.grade_id == Grade.id).join(
                Campus, Grade.campus_id == Campus.id
            ).filter(Campus.institution_id == institution.id)

        query = query.group_by(User.id, User.first_name, User.last_name)
        results = query.all()
        return [(r[0], f"{r[1]} {r[2]}", round(float(r[3]), 2) if r[3] else 0) for r in results]

    @staticmethod
    def get_attendance_data(teacher_id, institution=None):
        sg_query = db.session.query(SubjectGrade.id).filter(SubjectGrade.teacher_id == teacher_id)

        if institution:
            from models.institution import Campus
            sg_query = sg_query.join(Grade).join(Campus).filter(Campus.institution_id == institution.id)

        sg_ids = [r[0] for r in sg_query.all()]

        if not sg_ids:
            return []

        attendance_records = db.session.query(
            Attendance.student_id, Attendance.subject_grade_id,
            func.count(Attendance.id).label('total'),
            func.sum(case((Attendance.status == 'presente', 1), else_=0)).label('present')
        ).filter(Attendance.subject_grade_id.in_(sg_ids)).group_by(
            Attendance.student_id, Attendance.subject_grade_id
        ).all()

        student_attendance = {}
        for ar in attendance_records:
            sid = ar.student_id
            pct = round((ar.present / ar.total) * 100, 1) if ar.total > 0 else 0
            if sid not in student_attendance:
                student_attendance[sid] = []
            student_attendance[sid].append(pct)

        student_averages = {}
        final_grades = db.session.query(
            FinalGrade.student_id, func.avg(FinalGrade.final_score).label('avg')
        ).filter(
            FinalGrade.subject_grade_id.in_(sg_ids), FinalGrade.final_score.isnot(None)
        ).group_by(FinalGrade.student_id).all()

        for fg in final_grades:
            student_averages[fg.student_id] = round(fg.avg, 2)

        results = []
        for sid, att_pcts in student_attendance.items():
            avg_att = round(sum(att_pcts) / len(att_pcts), 1)
            avg_score = student_averages.get(sid, 0)

            student = db.session.query(AcademicStudent, User, Grade).join(
                User, AcademicStudent.user_id == User.id
            ).join(Grade, AcademicStudent.grade_id == Grade.id).filter(AcademicStudent.id == sid).first()

            if student:
                results.append({
                    'student_id': sid,
                    'student_name': student[1].get_full_name(),
                    'grade_name': student[2].name,
                    'attendance_pct': avg_att,
                    'avg_score': avg_score
                })

        return results

    @staticmethod
    def get_total_absences(teacher_id, institution=None):
        sg_query = db.session.query(SubjectGrade.id).filter(SubjectGrade.teacher_id == teacher_id)

        if institution:
            from models.institution import Campus
            sg_query = sg_query.join(Grade).join(Campus).filter(Campus.institution_id == institution.id)

        sg_ids = [r[0] for r in sg_query.all()]

        if not sg_ids:
            return 0, 0

        total = db.session.query(func.count(Attendance.id)).filter(Attendance.subject_grade_id.in_(sg_ids)).scalar() or 0
        absences = db.session.query(func.count(Attendance.id)).filter(
            Attendance.subject_grade_id.in_(sg_ids), Attendance.status == 'ausente'
        ).scalar() or 0

        absence_pct = round((absences / total) * 100, 1) if total > 0 else 0
        return absences, absence_pct

    @staticmethod
    def get_action_plans(teacher_id, institution=None):
        """Generate pedagogical action plans based on subject metrics across different grades."""
        from models.academic import Subject, SubjectGrade, Grade
        from models.grading import FinalGrade
        
        # Get all subject-grades for this teacher
        sg_query = db.session.query(SubjectGrade).filter(SubjectGrade.teacher_id == teacher_id)
        if institution:
            from models.institution import Campus
            sg_query = sg_query.join(Grade).join(Campus).filter(Campus.institution_id == institution.id)
        
        subject_grades = sg_query.all()
        
        # Group by subject
        subject_groups = {}
        for sg in subject_grades:
            if sg.subject_id not in subject_groups:
                subject_groups[sg.subject_id] = {
                    'name': sg.subject.name,
                    'code': sg.subject.code,
                    'grades': []
                }
            
            # Get avg for this specific grade
            avg = db.session.query(func.avg(FinalGrade.final_score)).filter(
                FinalGrade.subject_grade_id == sg.id,
                FinalGrade.final_score.isnot(None)
            ).scalar()
            
            pass_rate = 0
            total_grades = db.session.query(func.count(FinalGrade.id)).filter(
                FinalGrade.subject_grade_id == sg.id,
                FinalGrade.final_score.isnot(None)
            ).scalar() or 0
            
            if total_grades > 0:
                passed = db.session.query(func.count(FinalGrade.id)).filter(
                    FinalGrade.subject_grade_id == sg.id,
                    FinalGrade.final_score >= 3.0
                ).scalar() or 0
                pass_rate = round((passed / total_grades) * 100, 1)
            
            subject_groups[sg.subject_id]['grades'].append({
                'grade_name': sg.grade.name,
                'avg': round(avg, 2) if avg else 0,
                'pass_rate': pass_rate,
                'sg_id': sg.id
            })
            
        # Generate plans
        plans = []
        for sid, data in subject_groups.items():
            if not data['grades']: continue
            
            subject_avg = sum(g['avg'] for g in data['grades']) / len(data['grades'])
            
            for g in data['grades']:
                suggestion = None
                severity = 'info'
                
                # Case 1: Low pass rate
                if g['pass_rate'] < 60:
                    suggestion = f"Reforzar temas básicos de {data['name']}. Se observa una tasa de aprobación crítica ({g['pass_rate']}%)."
                    severity = 'danger'
                
                # Case 2: Significant deviation from other grades
                elif len(data['grades']) > 1 and g['avg'] < (subject_avg - 0.5):
                    suggestion = f"El rendimiento en {g['grade_name']} es notablemente inferior al promedio de otros grupos en {data['name']}. Revisar metodología específica."
                    severity = 'warning'
                
                # Case 3: Low average but acceptable pass rate
                elif g['avg'] < 3.2:
                    suggestion = f"Realizar actividades de nivelación preventiva para subir el promedio del grupo ({g['avg']})."
                    severity = 'info'
                
                if suggestion:
                    plans.append({
                        'subject_name': data['name'],
                        'grade_name': g['grade_name'],
                        'suggestion': suggestion,
                        'severity': severity,
                        'metric': f"Avg: {g['avg']} / Pass: {g['pass_rate']}%"
                    })
        
        return plans
