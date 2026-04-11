"""
Error handlers for Flask application.
Single dynamic error page for all HTTP errors.
"""

from flask import render_template, jsonify


def register_error_handlers(app):
    """Register error handlers with the Flask app."""
    
    @app.errorhandler(400)
    def bad_request(e):
        return _handle_error(400, e)
    
    @app.errorhandler(401)
    def unauthorized(e):
        return _handle_error(401, e)
    
    @app.errorhandler(403)
    def forbidden(e):
        return _handle_error(403, e)
    
    @app.errorhandler(404)
    def not_found(e):
        return _handle_error(404, e)
    
    @app.errorhandler(413)
    def request_entity_too_large(e):
        return _handle_error(413, e)
    
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return _handle_error(429, e)
    
    @app.errorhandler(500)
    def internal_error(e):
        return _handle_error(500, e)


def _handle_error(status_code, exception):
    """Handle error and return appropriate response."""
    
    # Error messages dictionary
    error_info = {
        400: {
            'title': 'Solicitud Incorrecta',
            'message': 'La solicitud no pudo ser procesada por el servidor.'
        },
        401: {
            'title': 'No Autorizado',
            'message': 'Debes iniciar sesión para acceder a esta página.'
        },
        403: {
            'title': 'Acceso Prohibido',
            'message': 'No tienes permisos para acceder a este recurso.'
        },
        404: {
            'title': 'Página No Encontrada',
            'message': 'El recurso que buscas no existe o ha sido movido.'
        },
        413: {
            'title': 'Archivo Demasiado Grande',
            'message': 'El archivo excede el tamaño máximo permitido (10MB).'
        },
        429: {
            'title': 'Demasiadas Solicitudes',
            'message': 'Has realizado demasiadas solicitudes. Espera un momento.'
        },
        500: {
            'title': 'Error Interno del Servidor',
            'message': 'Ha ocurrido un error inesperado. Intente nuevamente más tarde.'
        }
    }
    
    info = error_info.get(status_code, {
        'title': 'Error',
        'message': 'Ha ocurrido un error inesperado.'
    })
    
    # Check if request wants JSON or HTML
    from flask import request
    if request.is_json or request.accept_mimetypes.best == 'application/json':
        from flask import jsonify
        return jsonify({
            'error': info['title'],
            'message': info['message'],
            'status_code': status_code
        }), status_code
    
    # Return HTML template
    return render_template(
        'error.html',
        error_code=status_code,
        error_title=info['title'],
        error_message=info['message']
    ), status_code
