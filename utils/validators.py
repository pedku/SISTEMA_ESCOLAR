"""
Data validation utilities.
"""

import re
from datetime import datetime
from flask import current_app


def allowed_file(filename):
    """Check if uploaded file has allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config.get('ALLOWED_EXTENSIONS', {'xlsx', 'xls', 'csv'})


def validate_grade_score(score):
    """
    Validate grade score is within valid range (1.0 - 5.0).
    Returns (is_valid, error_message)
    """
    try:
        score = float(score)
        if score < 1.0 or score > 5.0:
            return False, 'La calificación debe estar entre 1.0 y 5.0'
        return True, None
    except (ValueError, TypeError):
        return False, 'La calificación debe ser un número válido'


def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_date(date_string, date_format='%Y-%m-%d'):
    """Validate date string format."""
    try:
        datetime.strptime(date_string, date_format)
        return True, None
    except ValueError:
        return False, f'Fecha inválida. Formato esperado: {date_format}'


def validate_document(document_type, document_number):
    """
    Validate document type and number.
    Returns (is_valid, error_message)
    """
    valid_types = ['CC', 'TI', 'RC', 'Pasaporte', 'CE']
    
    if document_type not in valid_types:
        return False, f'Tipo de documento inválido. Tipos válidos: {", ".join(valid_types)}'
    
    if not document_number or len(document_number.strip()) == 0:
        return False, 'El número de documento es requerido'
    
    if len(document_number) > 30:
        return False, 'El número de documento es demasiado largo (máx. 30 caracteres)'
    
    return True, None


def validate_phone(phone):
    """Validate phone number format."""
    if not phone:
        return True, None  # Phone is optional
    
    pattern = r'^[\+]?[\d\s\-\(\)]{7,20}$'
    if re.match(pattern, phone):
        return True, None
    return False, 'Formato de teléfono inválido'


def sanitize_string(text):
    """Sanitize user input string."""
    if not text:
        return text
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def validate_academic_year(year):
    """Validate academic year format."""
    pattern = r'^\d{4}(-\d{2})?$'  # e.g., "2026" or "2026-1"
    if re.match(pattern, year):
        return True, None
    return False, 'Formato de año académico inválido (ej: 2026 o 2026-1)'


def validate_file_size(file, max_size=None):
    """Validate file size."""
    if max_size is None:
        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 10485760)
    
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if size > max_size:
        max_mb = max_size / (1024 * 1024)
        return False, f'El archivo es demasiado grande (máx. {max_mb:.1f}MB)'
    
    return True, None


def format_grade(grade, decimal_places=1):
    """Format grade for display."""
    if grade is None:
        return 'N/A'
    return f'{grade:.{decimal_places}f}'


def get_grade_status(grade, passing_grade=3.0):
    """Get grade status (passed/failed)."""
    if grade is None:
        return 'no evaluado'
    if grade >= passing_grade:
        return 'ganada'
    return 'perdida'


def get_grade_performance_level(grade):
    """Get performance level based on grade."""
    if grade is None:
        return 'N/A'
    if grade >= 4.6:
        return 'Superior'
    elif grade >= 4.0:
        return 'Alto'
    elif grade >= 3.0:
        return 'Básico'
    else:
        return 'Bajo'


def get_grade_class(grade, passing_grade=3.0):
    """Get CSS class for grade display (color-coded)."""
    if grade is None:
        return 'text-muted'
    if grade >= 4.5:
        return 'grade-excellent'
    elif grade >= 4.0:
        return 'grade-good'
    elif grade >= passing_grade:
        return 'grade-average'
    elif grade >= 2.0:
        return 'grade-below'
    else:
        return 'grade-fail'
