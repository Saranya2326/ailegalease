import os
import sys
from pathlib import Path

# Ensure backend directory is in path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from server import create_app
from server.extensions import db
from server.models import User, Document, DocumentVersion, Template, AuditLog

def auto_migrate_sqlite(app):
    """Safely add any missing columns to existing SQLite tables."""
    with app.app_context():
        engine = db.engine
        if engine.dialect.name == "sqlite":
            with engine.connect() as conn:
                # 1. users table columns
                try:
                    result = conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()
                    existing_cols = [row[1] for row in result]
                    if "role" not in existing_cols:
                        conn.exec_driver_sql("ALTER TABLE users ADD COLUMN role VARCHAR(32) DEFAULT 'user'")
                        print("[+] Added column 'role' to users table")
                    if "updated_at" not in existing_cols:
                        conn.exec_driver_sql("ALTER TABLE users ADD COLUMN updated_at DATETIME")
                        print("[+] Added column 'updated_at' to users table")
                except Exception:
                    pass

                # 2. documents table columns
                try:
                    result = conn.exec_driver_sql("PRAGMA table_info(documents)").fetchall()
                    existing_cols = [row[1] for row in result]
                    if "status" not in existing_cols:
                        conn.exec_driver_sql("ALTER TABLE documents ADD COLUMN status VARCHAR(32) DEFAULT 'draft'")
                        print("[+] Added column 'status' to documents table")
                    if "risk_flags" not in existing_cols:
                        conn.exec_driver_sql("ALTER TABLE documents ADD COLUMN risk_flags JSON DEFAULT '[]'")
                        print("[+] Added column 'risk_flags' to documents table")
                except Exception:
                    pass

def init_database():
    app = create_app()
    with app.app_context():
        db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
        print(f"[*] Initializing database at: {db_uri}")
        
        # Create all tables
        db.create_all()
        auto_migrate_sqlite(app)
        
        print("[+] All database tables verified and created:")
        print("    - users")
        print("    - documents")
        print("    - document_versions")
        print("    - templates")
        print("    - audit_logs")
        
        print("\n[OK] Database initialization complete.")

if __name__ == "__main__":
    init_database()
