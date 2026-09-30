from server.routes.auth import auth_bp
from server.routes.documents import documents_bp
from server.routes.export import export_bp
from server.routes.templates import templates_bp

__all__ = ["auth_bp", "documents_bp", "export_bp", "templates_bp"]
