from app import create_app
from extensions import db
from models.academic import AcademicStudent, Grade, ParentStudent
from models.user import User

app = create_app()
with app.app_context():
    student = db.session.get(AcademicStudent, 4)
    if not student:
        print("Student 4 not found")
        exit()
        
    print(f"Student: {student.user.get_full_name()}")
    
    parents = student.parent_students.all()
    print(f"Assigned parents count: {len(parents)}")
    
    for ps in parents:
        print(f"PS ID: {ps.id}, Parent ID: {ps.parent_id}")
        try:
            print(f"PS parent_user: {ps.parent_user}")
            print(f"PS parent_user name: {ps.parent_user.get_full_name()}")
        except AttributeError as e:
            print(f"Error accessing parent_user: {e}")
            # Let's check available attributes
            print(f"Available attributes: {dir(ps)}")
