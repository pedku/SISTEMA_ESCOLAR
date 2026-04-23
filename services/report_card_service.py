"""
Report card service.
Handles logic related to report cards, attendance calculation, and data aggregation.
"""

from extensions import db
from models.attendance import Attendance
from models.academic import SubjectGrade
from models.grading import FinalGrade

class ReportCardService:

    @staticmethod
    def get_performance_level(score):
        """Get performance level text for a grade."""
        if score is None:
            return 'N/A'
        if score >= 4.6:
            return 'Superior'
        elif score >= 4.0:
            return 'Alto'
        elif score >= 3.0:
            return 'Basico'
        else:
            return 'Bajo'

    @staticmethod
    def get_status_text(status):
        """Get display text for grade status."""
        if status == 'ganada':
            return 'Aprobado'
        elif status == 'perdida':
            return 'Reprobado'
        return 'No evaluado'

    @staticmethod
    def get_student_attendance(student_id, period, subject_grades):
        """Get attendance summary for a student in a period."""
        query = Attendance.query.filter(
            Attendance.student_id == student_id,
            Attendance.date >= period.start_date,
            Attendance.date <= period.end_date
        )

        if subject_grades:
            sg_ids = [sg.id for sg in subject_grades]
            query = query.filter(Attendance.subject_grade_id.in_(sg_ids))

        records = query.all()

        presentes = sum(1 for r in records if r.status == 'presente')
        ausentes = sum(1 for r in records if r.status == 'ausente')
        justificados = sum(1 for r in records if r.status in ('justificado', 'excusado'))

        return {
            'presentes': presentes,
            'ausentes': ausentes,
            'justificados': justificados,
            'total': len(records)
        }

    @staticmethod
    def get_grade_subjects(grade_id):
        """Get all subject-grades for a grade."""
        return SubjectGrade.query.filter_by(grade_id=grade_id).all()

    @classmethod
    def build_grades_data(cls, student_id, period_id, subject_grades):
        """Build grades data for all subjects for a student in a period."""
        grades_data = []

        for sg in subject_grades:
            final_grade = FinalGrade.query.filter_by(
                student_id=student_id,
                subject_grade_id=sg.id,
                period_id=period_id
            ).first()

            grades_data.append({
                'subject_grade': sg,
                'subject_name': sg.subject.name,
                'teacher_name': sg.teacher_user.get_full_name() if sg.teacher_user else 'N/A',
                'final_score': final_grade.final_score if final_grade else None,
                'status': final_grade.status if final_grade else 'no evaluado',
                'observation': final_grade.observation if final_grade else None,
                'performance_level': cls.get_performance_level(final_grade.final_score) if final_grade and final_grade.final_score else 'N/A',
                'status_text': cls.get_status_text(final_grade.status) if final_grade else 'No evaluado'
            })

        return grades_data
