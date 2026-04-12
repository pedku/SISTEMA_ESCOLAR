"""
Form helpers utility.
Provides functions to handle form data and errors consistently across the application.
"""


def get_form_data(request_form, defaults=None):
    """
    Extract all form data from request.form into a dict.
    Makes it easy to pass to templates for repopulating fields.
    
    Args:
        request_form: Flask request.form object
        defaults: Optional dict of default values
    
    Returns:
        Dict with all form field values
    """
    if defaults is None:
        defaults = {}
    
    form_data = dict(defaults)
    for key in request_form:
        # Handle multi-select fields
        if isinstance(request_form.getlist(key), list) and len(request_form.getlist(key)) > 1:
            form_data[key] = request_form.getlist(key)
        else:
            form_data[key] = request_form.get(key, '').strip()
    
    return form_data


def render_form_with_errors(template, form_data=None, errors=None, **kwargs):
    """
    Render a template with form data and errors.
    This is a helper to avoid code duplication in routes.
    
    Args:
        template: Template name to render
        form_data: Dict with form field values
        errors: Dict with field errors {field_name: error_message}
        **kwargs: Additional context variables
    
    Returns:
        Rendered template
    """
    from flask import render_template
    
    context = dict(kwargs)
    context['form_data'] = form_data or {}
    context['errors'] = errors or {}
    
    return render_template(template, **context)


def validate_required_fields(request_form, fields):
    """
    Validate that required fields are not empty.
    
    Args:
        request_form: Flask request.form object
        fields: List of field names that are required
    
    Returns:
        Dict of errors (empty if all valid)
    """
    errors = {}
    
    for field in fields:
        value = request_form.get(field, '').strip()
        if not value:
            field_label = field.replace('_', ' ').title()
            errors[field] = f'{field_label} es obligatorio'
    
    return errors


def add_error(errors, field, message):
    """
    Add an error to the errors dict.
    
    Args:
        errors: Errors dict
        field: Field name
        message: Error message
    
    Returns:
        Updated errors dict
    """
    errors[field] = message
    return errors


def has_errors(errors):
    """Check if there are any errors."""
    return bool(errors)
