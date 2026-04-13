"""
Sistema Integral de Gestión Escolar (SIGE)
Aplicación principal Flask
"""

import os
from flask import Flask
from extensions import db, migrate, login_manager, limiter
from flask_cors import CORS
from config import config


def create_app(config_name=None):
    """Application factory pattern."""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Ensure upload folder exists
    upload_folder = app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    for subfolder in ['logos', 'photos', 'excel_imports', 'report_cards']:
        os.makedirs(os.path.join(upload_folder, subfolder), exist_ok=True)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Configure Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'warning'
    
    # Initialize CSRF but don't enforce it globally for now
    # csrf.init_app(app)
    
    limiter.init_app(app)
    CORS(app)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.institution import institution_bp
    from routes.students import students_bp
    from routes.grades import grades_bp
    from routes.report_cards import report_cards_bp
    from routes.attendance import attendance_bp
    from routes.observations import observations_bp
    from routes.users import users_bp
    from routes.metrics import metrics_bp
    from routes.achievements import achievements_bp
    from routes.parent import parent_bp
    from routes.qr import qr_bp
    from routes.alerts import alerts_bp
    from routes.scheduling import scheduling_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(institution_bp, url_prefix='/institution')
    app.register_blueprint(students_bp, url_prefix='/students')
    app.register_blueprint(grades_bp, url_prefix='/grades')
    app.register_blueprint(report_cards_bp, url_prefix='/report-cards')
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(observations_bp)
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(metrics_bp, url_prefix='/metrics')
    app.register_blueprint(achievements_bp, url_prefix='/achievements')
    app.register_blueprint(parent_bp, url_prefix='/parent')
    app.register_blueprint(qr_bp, url_prefix='/qr')
    app.register_blueprint(alerts_bp)
    app.register_blueprint(scheduling_bp, url_prefix='/scheduling')
    
    # Error handlers
    from utils.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    # Template context processors
    @app.context_processor
    def utility_processor():
        """Add utility functions to template context."""
        from utils.template_helpers import get_template_helpers
        helpers = get_template_helpers()
        # Make csrf_token available in templates even without global CSRF enforcement
        try:
            from flask_wtf.csrf import generate_csrf
            helpers['csrf_token'] = generate_csrf
        except ImportError:
            pass
        return helpers
    
    return app


# MUST be defined AFTER create_app to avoid circular imports
@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    from models.user import User
    return db.session.get(User, int(user_id))


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
