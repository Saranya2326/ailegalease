from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from server.extensions import db
from server.models import Document, DocumentVersion
from server.services.llm_service import draft_document, explain_clause
from server.services.risk_service import flag_risks

documents_bp = Blueprint("documents", __name__, url_prefix="/api/documents")

ALLOWED_TEMPLATES = {"nda", "lease", "employment", "will", "freelance", "poa"}


def _get_current_user_id() -> int:
    identity = get_jwt_identity()
    try:
        return int(identity)
    except (TypeError, ValueError):
        return identity


@documents_bp.get("")
@jwt_required()
def list_documents():
    user_id = _get_current_user_id()
    docs = (
        Document.query.filter_by(user_id=user_id)
        .order_by(Document.updated_at.desc())
        .all()
    )
    return jsonify([d.to_dict(include_content=False) for d in docs]), 200


@documents_bp.post("")
@jwt_required()
def create_document():
    """
    Create a new document draft from wizard answers.
    Body: { template_type, title?, answers: {...} }
    """
    user_id = _get_current_user_id()
    data = request.get_json(silent=True) or {}

    template_type = (data.get("template_type") or "nda").lower()
    answers = data.get("answers") or {}

    if template_type not in ALLOWED_TEMPLATES:
        return jsonify({
            "error": f"template_type must be one of {sorted(ALLOWED_TEMPLATES)}"
        }), 400
    if not isinstance(answers, dict):
        return jsonify({"error": "answers must be an object."}), 400

    try:
        drafted_content = draft_document(template_type, answers)
    except Exception as e:
        drafted_content = f"Draft generated with parameters: {answers}"

    risks = flag_risks(template_type, answers)

    doc = Document(
        user_id=user_id,
        template_type=template_type,
        title=data.get("title") or f"Mutual {template_type.upper()} Draft",
        jurisdiction=answers.get("jurisdiction"),
        answers=answers,
        content=drafted_content,
        risk_flags=risks,
        status="draft",
    )
    db.session.add(doc)
    db.session.flush()  # get doc.id before creating the version

    version = DocumentVersion(
        document_id=doc.id,
        version_number=1,
        content=drafted_content,
        answers_snapshot=answers,
    )
    db.session.add(version)
    db.session.commit()

    return jsonify(doc.to_dict()), 201


@documents_bp.get("/<int:doc_id>")
@jwt_required()
def get_document(doc_id):
    user_id = _get_current_user_id()
    doc = Document.query.filter_by(id=doc_id, user_id=user_id).first()
    if not doc:
        return jsonify({"error": "Document not found."}), 404
    return jsonify(doc.to_dict()), 200


@documents_bp.put("/<int:doc_id>")
@jwt_required()
def update_document(doc_id):
    """
    Re-draft a document with updated answers, saving the previous
    version to history.
    Body: { answers: {...}, title?: string }
    """
    user_id = _get_current_user_id()
    doc = Document.query.filter_by(id=doc_id, user_id=user_id).first()
    if not doc:
        return jsonify({"error": "Document not found."}), 404

    data = request.get_json(silent=True) or {}
    new_answers = data.get("answers")
    if not isinstance(new_answers, dict):
        return jsonify({"error": "answers must be an object."}), 400

    if data.get("title"):
        doc.title = data.get("title")

    try:
        drafted_content = draft_document(doc.template_type, new_answers)
    except Exception as e:
        drafted_content = doc.content or ""

    doc.answers = new_answers
    doc.jurisdiction = new_answers.get("jurisdiction", doc.jurisdiction)
    doc.content = drafted_content
    doc.risk_flags = flag_risks(doc.template_type, new_answers)

    next_version_number = (
        db.session.query(db.func.max(DocumentVersion.version_number))
        .filter_by(document_id=doc.id)
        .scalar() or 0
    ) + 1

    version = DocumentVersion(
        document_id=doc.id,
        version_number=next_version_number,
        content=drafted_content,
        answers_snapshot=new_answers,
    )
    db.session.add(version)
    db.session.commit()

    return jsonify(doc.to_dict()), 200


@documents_bp.get("/<int:doc_id>/versions")
@jwt_required()
def list_versions(doc_id):
    user_id = _get_current_user_id()
    doc = Document.query.filter_by(id=doc_id, user_id=user_id).first()
    if not doc:
        return jsonify({"error": "Document not found."}), 404
    return jsonify([v.to_dict() for v in doc.versions]), 200


@documents_bp.post("/<int:doc_id>/explain-clause")
@jwt_required()
def explain(doc_id):
    """Body: { clause_text }"""
    user_id = _get_current_user_id()
    doc = Document.query.filter_by(id=doc_id, user_id=user_id).first()
    if not doc:
        return jsonify({"error": "Document not found."}), 404

    data = request.get_json(silent=True) or {}
    clause_text = (data.get("clause_text") or "").strip()
    if not clause_text:
        return jsonify({"error": "clause_text is required."}), 400

    explanation = explain_clause(clause_text)
    return jsonify({"explanation": explanation}), 200


@documents_bp.delete("/<int:doc_id>")
@jwt_required()
def delete_document(doc_id):
    user_id = _get_current_user_id()
    doc = Document.query.filter_by(id=doc_id, user_id=user_id).first()
    if not doc:
        return jsonify({"error": "Document not found."}), 404
    db.session.delete(doc)
    db.session.commit()
    return jsonify({"message": "Document deleted successfully."}), 200
