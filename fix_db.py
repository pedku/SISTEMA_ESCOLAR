"""Quick DB migration to add missing columns."""
import sqlite3

conn = sqlite3.connect('sistema_escolar.db')
c = conn.cursor()

# Check and add users columns
users_cols = [r[1] for r in c.execute('PRAGMA table_info(users)').fetchall()]
for col_name in ['first_name', 'last_name', 'department', 'municipality', 'country', 'must_change_password', 'institution_id']:
    if col_name not in users_cols:
        if col_name == 'must_change_password':
            c.execute(f'ALTER TABLE users ADD COLUMN {col_name} BOOLEAN DEFAULT 1')
        elif col_name == 'institution_id':
            c.execute(f'ALTER TABLE users ADD COLUMN {col_name} INTEGER')
        else:
            c.execute(f'ALTER TABLE users ADD COLUMN {col_name} TEXT')
        print(f'Added users.{col_name}')

# Check and add subjects columns
subj_cols = [r[1] for r in c.execute('PRAGMA table_info(subjects)').fetchall()]
for col_name in ['institution_id', 'name']:
    if col_name not in subj_cols:
        if col_name == 'name':
            c.execute('ALTER TABLE subjects ADD COLUMN name TEXT')
            c.execute("UPDATE subjects SET name = 'Asignatura ' || COALESCE(code, CAST(id AS TEXT)) WHERE name IS NULL")
            print('Added subjects.name and set defaults')
        else:
            c.execute(f'ALTER TABLE subjects ADD COLUMN {col_name} INTEGER')
            print(f'Added subjects.{col_name}')

# Check and add achievements columns
ach_cols = [r[1] for r in c.execute('PRAGMA table_info(achievements)').fetchall()]
if 'institution_id' not in ach_cols:
    c.execute('ALTER TABLE achievements ADD COLUMN institution_id INTEGER')
    print('Added achievements.institution_id')

conn.commit()

# Verify
users_cols = [r[1] for r in c.execute('PRAGMA table_info(users)').fetchall()]
subj_cols = [r[1] for r in c.execute('PRAGMA table_info(subjects)').fetchall()]
print(f'\nFinal Users columns: {users_cols}')
print(f'Final Subjects columns: {subj_cols}')
conn.close()
print('\nMigration complete!')
