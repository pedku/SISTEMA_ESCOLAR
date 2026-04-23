from app import create_app
from extensions import db
from models.academic import AcademicStudent, Grade, SubjectGrade
from models.scheduling import Schedule
from models.user import User
from flask import render_template

app = create_app()
with app.app_context():
    student = db.session.get(AcademicStudent, 4)
    if not student:
        print("Student 4 not found")
        exit()
        
    schedules = Schedule.query.join(SubjectGrade).filter(
        SubjectGrade.grade_id == student.grade_id
    ).all()
    
    schedule_grid = {}
    for sch in schedules:
        day_idx = sch.day_of_week
        time_key = sch.start_time.strftime('%H:%M')
        if day_idx not in schedule_grid:
            schedule_grid[day_idx] = {}
        schedule_grid[day_idx][time_key] = sch

    days = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes']
    
    with app.test_request_context():
        # Setup session/user if needed by template helpers
        from flask_login import login_user
        user = db.session.get(User, student.user_id)
        # login_user(user) # Might need more setup
        
        try:
            html = render_template('students/profile.html', 
                                  student=student, 
                                  schedules=schedules,
                                  schedule_grid=schedule_grid,
                                  days=days)
            print("Render Success!")
        except Exception as e:
            print(f"Render Error: {e}")
            import traceback
            traceback.print_exc()
