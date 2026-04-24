"""
Grade calculation service.
Handles calculation and persistence of final and annual grades.
"""

from datetime import datetime
from extensions import db
from models.grading import GradeRecord, FinalGrade, AnnualGrade
from config import config
import os

class GradeCalculatorService:
    # Use config values or defaults
    MIN_GRADE = 1.0
    MAX_GRADE = 5.0
    PASSING_GRADE = 3.0

    @classmethod
    def calculate_final_grade(cls, student_id, sg_id, period_id, criteria):
        """
        Calculate final grade for a student in a subject-grade/period.
        Formula: sum(score * weight/100) for each criterion.
        Returns the calculated score or None if insufficient data.
        """
        total_weight = sum(float(c.weight) for c in criteria)
        print(f"DEBUG: total_weight={total_weight} type={type(total_weight)}")
        if total_weight == 0:
            return None

        weighted_sum = 0.0
        weight_applied = 0.0

        for criterion in criteria:
            record = GradeRecord.query.filter_by(
                student_id=student_id,
                subject_grade_id=sg_id,
                period_id=period_id,
                criterion_id=criterion.id
            ).first()

            if record and record.score is not None:
                s = float(record.score)
                w = float(criterion.weight)
                print(f"DEBUG: student={student_id} criterion={criterion.id} score={s}({type(s)}) weight={w}({type(w)})")
                weighted_sum += s * (w / 100.0)
                weight_applied += w

        if weight_applied == 0:
            return None

        # Normalize to 100% if not all criteria have grades
        if float(weight_applied) < float(total_weight):
            final_score = round((float(weighted_sum) / float(weight_applied)) * 100.0, 2)
        else:
            final_score = round(float(weighted_sum), 2)

        # Clamp to valid range
        final_score = max(cls.MIN_GRADE, min(cls.MAX_GRADE, final_score))

        return round(final_score, 2)

    @classmethod
    def save_final_grade(cls, student_id, sg_id, period_id, final_score):
        """Save or update the final grade for a student."""
        existing = FinalGrade.query.filter_by(
            student_id=student_id,
            subject_grade_id=sg_id,
            period_id=period_id
        ).first()

        status = 'ganada' if final_score >= cls.PASSING_GRADE else 'perdida'

        if existing:
            existing.final_score = final_score
            existing.status = status
            existing.calculated_at = datetime.utcnow()
        else:
            new_final = FinalGrade(
                student_id=student_id,
                subject_grade_id=sg_id,
                period_id=period_id,
                final_score=final_score,
                status=status
            )
            db.session.add(new_final)

    @classmethod
    def calculate_and_save_annual_grades(cls, student_id, sg_id, periods, academic_year):
        """Calculate and save annual grades (average of 4 periods) for a student."""
        period_scores = []
        for period in periods:
            final = FinalGrade.query.filter_by(
                student_id=student_id,
                subject_grade_id=sg_id,
                period_id=period.id
            ).first()
            if final and final.final_score is not None:
                period_scores.append(float(final.final_score))

        if period_scores:
            annual_score = round(sum(period_scores) / len(period_scores), 2)
            status = 'aprobado' if annual_score >= cls.PASSING_GRADE else 'reprobado'

            existing = AnnualGrade.query.filter_by(
                student_id=student_id,
                subject_grade_id=sg_id,
                academic_year=academic_year
            ).first()

            if existing:
                existing.annual_score = annual_score
                existing.status = status
            else:
                new_annual = AnnualGrade(
                    student_id=student_id,
                    subject_grade_id=sg_id,
                    academic_year=academic_year,
                    annual_score=annual_score,
                    status=status
                )
                db.session.add(new_annual)
            
            return annual_score
        return None
