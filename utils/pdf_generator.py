"""
PDF generator utility using WeasyPrint.
"""

import os
from datetime import datetime
from flask import render_template, current_app
from weasyprint import HTML


def generate_report_card_pdf(report_card, student, institution, period, grades_data, observations):
    """
    Generate a PDF report card.
    
    Args:
        report_card: ReportCard instance
        student: AcademicStudent instance
        institution: Institution instance
        period: AcademicPeriod instance
        grades_data: List of dicts with subject grades
        observations: Dict with subject observations
    
    Returns:
        tuple: (pdf_bytes, filename)
    """
    # Render template to HTML
    html_content = render_template(
        'report_cards/pdf_template.html',
        report_card=report_card,
        student=student,
        institution=institution,
        period=period,
        grades_data=grades_data,
        observations=observations,
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
    
    Args:
        student: AcademicStudent instance
        institution: Institution instance
        certificate_type: 'enrollment', 'grades', 'attendance'
    
    Returns:
        bytes: PDF bytes
    """
    html_content = render_template(
        'certificates/template.html',
        student=student,
        institution=institution,
        certificate_type=certificate_type,
        generated_date=datetime.now()
    )
    
    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes
