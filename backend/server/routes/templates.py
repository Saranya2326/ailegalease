from flask import Blueprint, jsonify
from server.models import Template

templates_bp = Blueprint("templates", __name__, url_prefix="/api/templates")


@templates_bp.get("")
def list_templates():
    """Return all active legal templates from the database."""
    templates = Template.query.filter_by(is_active=True).all()
    return jsonify([t.to_dict() for t in templates]), 200


@templates_bp.get("/<slug>")
def get_template(slug):
    """Return a single legal template by slug."""
    template = Template.query.filter_by(slug=slug, is_active=True).first()
    if not template:
        return jsonify({"error": "Template not found."}), 404
    return jsonify(template.to_dict()), 200
