import os
import tempfile
import pytest
from app import create_app
from extensions import db
from models.user import User
from models.institution import Institution
from werkzeug.security import generate_password_hash

@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for the test session."""
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SERVER_NAME': 'localhost.localdomain'
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture(scope='function')
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture(scope='function')
def init_database(app):
    """Fixture to initialize database with required test data."""
    db.drop_all()
    db.create_all()

    institution = Institution(
        name='Test Institution',
        nit='123456789',
        academic_year='2026'
    )
    db.session.add(institution)
    db.session.commit()
    
    root_user = User(
        username='root',
        email='root@sige.edu.co',
        password_hash=generate_password_hash('root123'),
        first_name='Root',
        last_name='User',
        document_type='CC',
        document_number='111111111',
        role='root',
        institution_id=institution.id,
        is_active=True
    )
    db.session.add(root_user)
    db.session.commit()
    
    yield {'institution': institution, 'root_user': root_user}

    db.session.remove()
