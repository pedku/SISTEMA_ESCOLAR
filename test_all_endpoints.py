"""Comprehensive endpoint test."""
from app import create_app

app = create_app()
c = app.test_client()
c.post('/login', data={'username':'root','password':'root123'})

results = []
def test(path, name):
    r = c.get(path)
    status = 'PASS' if r.status_code in [200, 302] else 'FAIL'
    results.append(f'{status:6} {r.status_code}  {name:40} {path}')

# Auth
test('/login', 'Login page')
test('/profile', 'Profile')
test('/change-password-first-time', 'Force password change')

# Dashboard
test('/', 'Home redirect')
test('/dashboard/root', 'Root dashboard')
test('/dashboard/admin', 'Admin dashboard')
test('/alerts', 'Alerts page')

# Institution
test('/institution/list', 'Institutions list')
test('/institution/new', 'New institution form')
test('/institution/institutions/select', 'Select institution')
test('/institution/config', 'Institution config')
test('/institution/campuses', 'Campuses list')
test('/institution/grades', 'Grades list')
test('/institution/subjects', 'Subjects list')
test('/institution/periods', 'Periods list')
test('/institution/criteria', 'Criteria list')

# Users
test('/users/users', 'Users list')
test('/users/users/new', 'New user form')
test('/users/users/import-excel', 'Import users Excel')

# Students
test('/students/', 'Students list')
test('/students/new', 'New student form')
test('/students/upload', 'Upload students Excel')

# Grades
test('/grades/input', 'Grade input select')
test('/grades/upload', 'Grade upload')

# Attendance
test('/attendance/', 'Attendance')
test('/attendance/summary', 'Attendance summary')

# Observations
test('/observations', 'Observations list')
test('/observations/new', 'New observation form')

# Stub modules
test('/report-cards/', 'Report cards')
test('/metrics/institution', 'Institution metrics')
test('/metrics/teacher', 'Teacher metrics')
test('/metrics/heatmap', 'Metrics heatmap')
test('/metrics/risk-students', 'Risk students')
test('/achievements/achievements', 'Achievements list')
test('/achievements/leaderboard', 'Leaderboard')
test('/parent/dashboard', 'Parent dashboard')
test('/qr/', 'QR validate')
test('/qr/my-qr', 'My QR code')

# Write results
passed = sum(1 for r in results if r.startswith('PASS'))
failed = sum(1 for r in results if r.startswith('FAIL'))
total = len(results)

with open('test_results.txt', 'w') as f:
    f.write(f'\n=== COMPREHENSIVE ENDPOINT TEST ===\n')
    f.write(f'Results: {passed}/{total} passed, {failed} failed\n\n')
    for r in results:
        f.write(r + '\n')
    f.write(f'\n{"="*50}\n')
    
print(f'Results: {passed}/{total} passed, {failed} failed')
for r in results:
    print(r)
