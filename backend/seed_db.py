import os
import sys
from pathlib import Path

# Ensure backend directory is in path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from server import create_app
from server.extensions import db, bcrypt
from server.models import User, Template, Document, DocumentVersion, AuditLog
from init_db import auto_migrate_sqlite

DEFAULT_TEMPLATES = [
    {
        "slug": "nda",
        "name": "Mutual Non-Disclosure Agreement (NDA)",
        "description": "Standard bilateral confidentiality agreement for business partnerships, contractors, and intellectual property protection.",
        "category": "commercial"
    },
    {
        "slug": "lease",
        "name": "Residential Lease Agreement",
        "description": "Comprehensive residential property lease defining rent, security deposits, tenancy term, and landlord/tenant duties.",
        "category": "real_estate"
    },
    {
        "slug": "employment",
        "name": "Standard Employment Agreement",
        "description": "Standard full-time/part-time employment contract specifying compensation, roles, IP assignment, and confidentiality.",
        "category": "employment"
    },
    {
        "slug": "freelance",
        "name": "Freelance Contractor Agreement",
        "description": "Independent contractor agreement covering deliverables, milestones, payment schedules, and copyright ownership.",
        "category": "commercial"
    },
    {
        "slug": "poa",
        "name": "General Power of Attorney",
        "description": "Legal authorization granting designated agent power to act on financial and legal affairs on your behalf.",
        "category": "personal"
    },
    {
        "slug": "will",
        "name": "Last Will and Testament",
        "description": "Standard declaration of asset distribution, executor designation, and beneficiary appointments.",
        "category": "personal"
    }
]

def seed_database():
    app = create_app()
    with app.app_context():
        db.create_all()
        auto_migrate_sqlite(app)
        
        print("[*] Seeding default legal templates into database...")
        for tpl in DEFAULT_TEMPLATES:
            existing = Template.query.filter_by(slug=tpl["slug"]).first()
            if not existing:
                t = Template(**tpl)
                db.session.add(t)
                print(f"  + Added template: {tpl['name']}")
            else:
                existing.name = tpl["name"]
                existing.description = tpl["description"]
                existing.category = tpl["category"]
                print(f"  * Updated template: {tpl['name']}")

        # Seed Demo User
        demo_email = "demo@legalease.com"
        demo_user = User.query.filter_by(email=demo_email).first()
        if not demo_user:
            demo_user = User(
                email=demo_email,
                name="Demo User",
                password_hash=bcrypt.generate_password_hash("demo1234").decode("utf-8"),
                role="user"
            )
            db.session.add(demo_user)
            db.session.flush()
            print(f"[+] Created demo user: {demo_email} (password: demo1234)")
        else:
            print(f"[*] Demo user already exists: {demo_email}")

        # Seed Sample NDA Document for Demo User
        existing_doc = Document.query.filter_by(user_id=demo_user.id, template_type="nda").first()
        if not existing_doc:
            sample_answers = {
                "party_a": "Acme Robotics LLC",
                "party_b": "Jordan Reyes",
                "jurisdiction": "Delaware",
                "effective_date": "2026-09-27",
                "term": "2",
                "mutual": "mutual",
                "penalty": "none",
                "penalty_amount": "0"
            }
            sample_content = (
                "1. Parties. This Non-Disclosure Agreement is entered into by Acme Robotics LLC and Jordan Reyes.\n\n"
                "2. Confidential Information. Both parties agree to protect proprietary information and trade secrets disclosed during collaboration.\n\n"
                "3. Term. This Agreement shall remain in effect for 2 years.\n\n"
                "4. Governing Law. This Agreement is governed by the laws of Delaware."
            )
            doc = Document(
                user_id=demo_user.id,
                template_type="nda",
                title="Mutual NDA - Sample Draft",
                jurisdiction="Delaware",
                answers=sample_answers,
                content=sample_content,
                risk_flags=[],
                status="draft"
            )
            db.session.add(doc)
            db.session.flush()
            
            version = DocumentVersion(
                document_id=doc.id,
                version_number=1,
                content=sample_content,
                answers_snapshot=sample_answers
            )
            db.session.add(version)
            print(f"[+] Created sample NDA document (ID: {doc.id})")

        db.session.commit()
        print("[OK] Database seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
