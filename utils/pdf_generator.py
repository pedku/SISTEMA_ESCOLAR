"""
PDF generator utility using WeasyPrint.
"""

import os
from datetime import datetime
from flask import render_template, current_app

# Try to import WeasyPrint, but handle missing dependencies gracefully
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except (OSError, ImportError):
    WEASYPRINT_AVAILABLE = False
    HTML = None


def _check_weasyprint():
    """Check if WeasyPrint is available."""
    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError(
            'WeasyPrint no esta disponible. Instale las dependencias requeridas: '
            'pip install weasyprint. En Windows, consulte la documentacion de instalacion.'
        )


def generate_report_card_pdf(report_card, student, institution, period, grades_data,
                              observations=None, attendance=None, campus=None):
    """
    Generate a PDF report card.

    Args:
        report_card: ReportCard instance
        student: AcademicStudent instance
        institution: Institution instance
        period: AcademicPeriod instance
        grades_data: List of dicts with subject grades
        observations: Dict with subject observations (legacy, kept for compatibility)
        attendance: Dict with attendance summary (presentes, ausentes, justificados, total)
        campus: Campus instance

    Returns:
        tuple: (pdf_bytes, filename)
    """
    _check_weasyprint()

    # Render template to HTML
    html_content = render_template(
        'report_cards/pdf_template.html',
        report_card=report_card,
        student=student,
        institution=institution,
        period=period,
        grades_data=grades_data,
        observations=observations,
        attendance=attendance,
        campus=campus,
        generated_date=datetime.now()
    )

    # Generate PDF
    pdf_bytes = HTML(string=html_content).write_pdf()

    # Create filename
    filename = f"boletin_{student.user.username}_{period.short_name}.pdf"

    return pdf_bytes, filename


def save_report_card_pdf(pdf_bytes, filename):
    """
    Save PDF bytes to file.
    
    Returns:
        str: File path
    """
    upload_folder = current_app.config['UPLOAD_FOLDER']
    report_cards_folder = os.path.join(upload_folder, 'report_cards')
    os.makedirs(report_cards_folder, exist_ok=True)
    
    file_path = os.path.join(report_cards_folder, filename)
    
    with open(file_path, 'wb') as f:
        f.write(pdf_bytes)
    
    return file_path


def generate_certificate_pdf(student, institution, certificate_type='enrollment'):
    """
    Generate various certificates.
    
    NOTE: This function is currently disabled because the template
    'certificates/template.html' does not exist. To enable it, create
    the template file at templates/certificates/template.html.

    Args:
        student: AcademicStudent instance
        institution: Institution instance
        certificate_type: 'enrollment', 'grades', 'attendance'

    Returns:
        bytes: PDF bytes
    """
    # TODO: Create templates/certificates/template.html to enable this feature
    raise NotImplementedError(
        "Certificate template generation is not yet implemented. "
        "Create templates/certificates/template.html to enable this feature."
    )
