"""
PostgreSQL Database Setup Script
Automatically creates the database and initializes it with seed data.
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

load_dotenv()


def check_postgresql_installed():
    """Check if PostgreSQL is installed and accessible."""
    try:
        import psycopg2
        return True
    except ImportError:
        print("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
        return False


def test_connection():
    """Test PostgreSQL connection."""
    import psycopg2
    
    db_user = os.getenv('DATABASE_USER', 'postgres')
    db_password = os.getenv('DATABASE_PASSWORD', '')
    db_host = os.getenv('DATABASE_HOST', 'localhost')
    db_port = os.getenv('DATABASE_PORT', '5432')
    
    try:
        conn = psycopg2.connect(
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        conn.close()
        print(f"✅ Connection successful to PostgreSQL at {db_host}:{db_port}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False


def create_database():
    """Create the database if it doesn't exist."""
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    
    db_user = os.getenv('DATABASE_USER', 'postgres')
    db_password = os.getenv('DATABASE_PASSWORD', '')
    db_host = os.getenv('DATABASE_HOST', 'localhost')
    db_port = os.getenv('DATABASE_PORT', '5432')
    db_name = os.getenv('DATABASE_NAME', 'sistema_escolar')
    
    print(f"\n📊 Attempting to create database: {db_name}")
    
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()
        
        if exists:
            print(f"⚠️  Database '{db_name}' already exists")
        else:
            cursor.execute(f'CREATE DATABASE {db_name}')
            print(f"✅ Database '{db_name}' created successfully")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {str(e)}")
        return False


def initialize_with_seed_data():
    """Run init_db.py to populate database."""
    print("\n🌱 Initializing database with seed data...")
    
    try:
        # Import and run init_db
        sys.path.insert(0, os.path.dirname(__file__))
        from init_db import init_db
        init_db()
        return True
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        return False


def main():
    """Main setup process."""
    print("=" * 60)
    print("🚀 SIGE - PostgreSQL Database Setup")
    print("=" * 60)
    
    # Step 1: Check psycopg2
    print("\n1️⃣  Checking dependencies...")
    if not check_postgresql_installed():
        print("\n💡 Install with: pip install psycopg2-binary")
        sys.exit(1)
    print("✅ psycopg2 installed")
    
    # Step 2: Test connection
    print("\n2️⃣  Testing PostgreSQL connection...")
    if not test_connection():
        print("\n💡 Make sure PostgreSQL is running and credentials are correct in .env")
        sys.exit(1)
    
    # Step 3: Create database
    print("\n3️⃣  Creating database...")
    if not create_database():
        print("\n💡 Check PostgreSQL permissions")
        sys.exit(1)
    
    # Step 4: Initialize with seed data
    print("\n4️⃣  Initializing with seed data...")
    if not initialize_with_seed_data():
        print("\n❌ Database setup incomplete")
        sys.exit(1)
    
    # Success!
    print("\n" + "=" * 60)
    print("✅ PostgreSQL setup completed successfully!")
    print("=" * 60)
    print("\n📋 Next steps:")
    print("   1. Edit .env and set USE_SQLITE=False")
    print("   2. Run: python app.py")
    print("   3. Access: http://localhost:5000")
    print("\n🔑 Default credentials:")
    print("   - root / root123")
    print("   - admin / admin123")
    print("=" * 60)


if __name__ == '__main__':
    main()
