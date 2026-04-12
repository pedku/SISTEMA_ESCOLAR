"""
Migration script to add is_main_campus column to campuses table.
Uses Flask-SQLAlchemy to handle database migrations.
"""

from app import create_app
from extensions import db
from sqlalchemy import text

def add_is_main_campus_column():
    """Add is_main_campus column to campuses table using SQLAlchemy."""
    app = create_app()
    
    with app.app_context():
        try:
            # Try to add the column - will fail if it already exists
            with db.engine.connect() as conn:
                # Check if using PostgreSQL or SQLite
                dialect = db.engine.dialect.name
                
                if dialect == 'postgresql':
                    # Check if column exists
                    result = conn.execute(text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'campuses' 
                        AND column_name = 'is_main_campus'
                    """))
                    
                    if result.fetchone():
                        print("✅ Column is_main_campus already exists!")
                        return
                    
                    # Add column
                    conn.execute(text("""
                        ALTER TABLE campuses 
                        ADD COLUMN is_main_campus BOOLEAN DEFAULT FALSE
                    """))
                    print("✓ Added is_main_campus column")
                    
                    # Set first campus of each institution as main campus
                    result = conn.execute(text("""
                        SELECT DISTINCT institution_id FROM campuses
                    """))
                    institution_ids = result.fetchall()
                    
                    for inst_id in institution_ids:
                        result = conn.execute(text("""
                            SELECT id FROM campuses 
                            WHERE institution_id = :inst_id 
                            ORDER BY id ASC 
                            LIMIT 1
                        """), {"inst_id": inst_id[0]})
                        first_campus = result.fetchone()
                        
                        if first_campus:
                            conn.execute(text("""
                                UPDATE campuses 
                                SET is_main_campus = TRUE 
                                WHERE id = :campus_id
                            """), {"campus_id": first_campus[0]})
                            print(f"✓ Set campus {first_campus[0]} as main campus for institution {inst_id[0]}")
                
                else:
                    # SQLite - check with pragma
                    result = conn.execute(text("PRAGMA table_info(campuses)"))
                    columns = [row[1] for row in result.fetchall()]
                    
                    if 'is_main_campus' in columns:
                        print("✅ Column is_main_campus already exists!")
                        return
                    
                    # Add column
                    conn.execute(text("""
                        ALTER TABLE campuses 
                        ADD COLUMN is_main_campus BOOLEAN DEFAULT 0
                    """))
                    print("✓ Added is_main_campus column")
                    
                    # Set first campus of each institution as main campus
                    result = conn.execute(text("""
                        SELECT DISTINCT institution_id FROM campuses
                    """))
                    institution_ids = result.fetchall()
                    
                    for inst_id in institution_ids:
                        result = conn.execute(text("""
                            SELECT id FROM campuses 
                            WHERE institution_id = :inst_id 
                            ORDER BY id ASC 
                            LIMIT 1
                        """), {"inst_id": inst_id[0]})
                        first_campus = result.fetchone()
                        
                        if first_campus:
                            conn.execute(text("""
                                UPDATE campuses 
                                SET is_main_campus = 1 
                                WHERE id = :campus_id
                            """), {"campus_id": first_campus[0]})
                            print(f"✓ Set campus {first_campus[0]} as main campus for institution {inst_id[0]}")
                
                conn.commit()
                print("\n✅ Migration completed successfully!")
                print("   - Added is_main_campus column to campuses table")
                print("   - Set first campus of each institution as main campus")
                
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == '__main__':
    print("=" * 60)
    print("Migration: Add is_main_campus to campuses")
    print("=" * 60)
    add_is_main_campus_column()
    print("=" * 60)
