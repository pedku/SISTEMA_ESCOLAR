# 📋 PostgreSQL Setup Guide - SIGE

## Current Status
- ✅ **SQLite**: Working for development/testing
- ⏳ **PostgreSQL**: Needs setup for production

---

## Option 1: Use SQLite (Current - Recommended for Development)

Already working! No changes needed.
```env
USE_SQLITE=True
```

**Pros:**
- No installation required
- Perfect for development
- Single file database
- Easy to backup/reset

**Cons:**
- Not for production
- Limited concurrent connections
- No advanced features

---

## Option 2: Setup PostgreSQL (For Production)

### Step 1: Install PostgreSQL

1. **Download**: https://www.postgresql.org/download/windows/
2. **Install** with default settings
3. **Remember your password** for postgres user
4. **Default port**: 5432

### Step 2: Create Database

Open pgAdmin or use command line:

```sql
-- Connect to PostgreSQL as postgres user
-- Then run:
CREATE DATABASE sistema_escolar;
```

Or via command line:
```bash
# Open cmd as Administrator
cd "C:\Program Files\PostgreSQL\16\bin"
createdb -U postgres -p 5432 sistema_escolar
```

### Step 3: Update .env File

Edit `c:\Users\crack\Desktop\SISTEMA_ESCOLAR\.env`:

```env
# Change this to False to use PostgreSQL
USE_SQLITE=False

# PostgreSQL Configuration
DATABASE_USER=postgres
DATABASE_PASSWORD=your_postgres_password
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=sistema_escolar
```

### Step 4: Initialize Database

```bash
cd c:\Users\crack\Desktop\SISTEMA_ESCOLAR
python init_db.py
```

### Step 5: Start Application

```bash
python app.py
```

---

## Troubleshooting

### Problem: "Connection refused"
- **Solution**: Check if PostgreSQL service is running
  ```bash
  # Open services.msc
  # Find "postgresql-x64-XX" and make sure it's "Running"
  ```

### Problem: "password authentication failed"
- **Solution**: Verify password in `.env` matches your PostgreSQL password

### Problem: "database does not exist"
- **Solution**: Run the CREATE DATABASE command from Step 2

### Problem: UnicodeDecodeError with password
- **Solution**: The password contains special characters. The config.py already URL-encodes it, so this should be fixed.

---

## Quick Switch Between SQLite and PostgreSQL

### To use SQLite (Development):
```env
USE_SQLITE=True
```

### To use PostgreSQL (Production):
```env
USE_SQLITE=False
DATABASE_PASSWORD=your_password
```

No code changes needed! The application automatically switches based on `USE_SQLITE` setting.

---

## Database Migration (SQLite → PostgreSQL)

When you're ready to move from SQLite to PostgreSQL:

1. **Backup SQLite data** (if needed):
   - The file is at: `c:\Users\crack\Desktop\SISTEMA_ESCOLAR\sistema_escolar.db`

2. **Setup PostgreSQL** following steps above

3. **Run initialization**:
   ```bash
   python init_db.py
   ```

4. **Change .env** to `USE_SQLITE=False`

5. **Restart application**

Note: Currently, there's no automatic migration tool. You'd need to manually export/import data if you have important data in SQLite.

---

## PostgreSQL Advantages for Production

- ✅ Multi-user concurrent access
- ✅ Better performance for large datasets
- ✅ ACID compliance
- ✅ Advanced querying capabilities
- ✅ Backup and recovery tools
- ✅ Better security features

---

## Current Configuration

The project is already configured with:
- ✅ URL-encoded passwords (handles special characters)
- ✅ SQLite fallback for easy development
- ✅ Easy switch with `USE_SQLITE` flag
- ✅ Flask-SQLAlchemy ORM (works with both databases)
- ✅ Flask-Migrate for schema management
