from datetime import datetime, timezone
from server.extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(128), default="User")
    role = db.Column(db.String(32), default="user")
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    documents = db.relationship("Document", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Template(db.Model):
    __tablename__ = "templates"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(64), default="commercial")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "slug": self.slug,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "is_active": self.is_active,
        }


class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    template_type = db.Column(db.String(64), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    jurisdiction = db.Column(db.String(128))
    answers = db.Column(db.JSON, default=dict)
    content = db.Column(db.Text)
    risk_flags = db.Column(db.JSON, default=list)
    status = db.Column(db.String(32), default="draft")
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    versions = db.relationship(
        "DocumentVersion",
        backref="document",
        cascade="all, delete-orphan",
        order_by="DocumentVersion.version_number.asc()",
    )

    def to_dict(self, include_content=True):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "template_type": self.template_type,
            "title": self.title,
            "jurisdiction": self.jurisdiction,
            "answers": self.answers or {},
            "content": self.content if include_content else None,
            "risk_flags": self.risk_flags or [],
            "status": self.status or "draft",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "version_count": len(self.versions) if self.versions else 1,
        }


class DocumentVersion(db.Model):
    __tablename__ = "document_versions"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id"), nullable=False, index=True)
    version_number = db.Column(db.Integer, nullable=False, default=1)
    content = db.Column(db.Text)
    answers_snapshot = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "version_number": self.version_number,
            "content": self.content,
            "answers_snapshot": self.answers_snapshot or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(128), nullable=False)
    details = db.Column(db.JSON, default=dict)
    ip_address = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "details": self.details or {},
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
