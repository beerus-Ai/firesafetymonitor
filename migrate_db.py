
from app import app, db
from models import Alert
from sqlalchemy import text

def migrate_database():
    """Add missing columns to existing database"""
    with app.app_context():
        try:
            # Check if image_urls column exists
            result = db.engine.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='alert' AND column_name='image_urls'"))
            if not result.fetchone():
                # Add image_urls column
                db.engine.execute(text("ALTER TABLE alert ADD COLUMN image_urls TEXT"))
                print("Added image_urls column to alert table")
            else:
                print("image_urls column already exists")
            
            # Check if AdminResponse table exists
            result = db.engine.execute(text("SELECT table_name FROM information_schema.tables WHERE table_name='admin_response'"))
            if not result.fetchone():
                # Create AdminResponse table
                db.create_all()
                print("Created missing tables")
            else:
                print("AdminResponse table already exists")
                
        except Exception as e:
            print(f"Migration error: {e}")

if __name__ == "__main__":
    migrate_database()
