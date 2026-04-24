from models.academic import SubjectGrade, Subject, Grade
from models.grading import FinalGrade
from extensions import db
from sqlalchemy import func

class TeacherAnalyticsService:
    @staticmethod
    def get_teacher_stats(teacher_id, academic_year=None):
        """Get performance statistics for a teacher across all their subject-grades."""
        query = SubjectGrade.query.filter_by(teacher_id=teacher_id).join(Grade)
        if academic_year:
            query = query.filter(Grade.academic_year == academic_year)
        
        sgs = query.all()
        
        stats = []
        for sg in sgs:
            # Average grade from FinalGrade table
            avg_grade = db.session.query(func.avg(FinalGrade.final_score)).filter_by(subject_grade_id=sg.id).scalar() or 0
            
            # Count students failing (grade < 3.0)
            failing_count = db.session.query(func.count(FinalGrade.id)).filter(
                FinalGrade.subject_grade_id == sg.id, 
                FinalGrade.final_score < 3.0
            ).scalar() or 0
            
            # Total students with final grades
            total_students = db.session.query(func.count(FinalGrade.id)).filter_by(subject_grade_id=sg.id).scalar() or 0
            
            failing_rate = (failing_count / total_students * 100) if total_students > 0 else 0
            
            stats.append({
                'sg_id': sg.id,
                'subject_name': sg.subject.name,
                'subject_code': sg.subject.code,
                'grade_name': sg.grade.name,
                'shift': sg.grade.shift,
                'average': round(float(avg_grade), 2),
                'failing_rate': round(failing_rate, 1),
                'total_students': total_students
            })
            
        return stats

    @staticmethod
    def generate_action_plans(stats):
        """Generate AI-driven suggestions based on performance disparities."""
        plans = []
        
        # Group by subject code to detect longitudinal disparities
        by_code = {}
        for s in stats:
            code = s['subject_code'] or 'GENERAL'
            if code not in by_code:
                by_code[code] = []
            by_code[code].append(s)
            
        for code, groups in by_code.items():
            if len(groups) > 1:
                # Comparison logic
                averages = [g['average'] for g in groups if g['total_students'] > 0]
                if averages:
                    diff = max(averages) - min(averages)
                    if diff > 0.7:
                        worst = min(groups, key=lambda x: x['average'])
                        best = max(groups, key=lambda x: x['average'])
                        plans.append({
                            'severity': 'warning',
                            'title': f'Disparidad en {code}',
                            'message': f'Existe una diferencia de {round(diff, 2)} puntos entre {best["grade_name"]} y {worst["grade_name"]}.',
                            'action': f'Revisar si el factor jornada ({worst["shift"]}) influye en el rendimiento y aplicar técnicas de refuerzo usadas en {best["grade_name"]}.'
                        })

            # High failure rate alerts
            for g in groups:
                if g['failing_rate'] > 25:
                    plans.append({
                        'severity': 'danger',
                        'title': f'Alerta Crítica: {g["grade_name"]}',
                        'message': f'La tasa de reprobación en {g["subject_name"]} es del {g["failing_rate"]}%.',
                        'action': 'Implementar plan de nivelación inmediato y revisar la carga académica del grupo.'
                    })
                    
        return plans
