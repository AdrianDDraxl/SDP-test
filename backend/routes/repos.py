"""Repository management API routes."""

from flask import Blueprint, current_app, jsonify, request

from services.repo_manager import (
    RepositoryCloneError,
    RepositoryNotFound,
    RepositoryValidationError,
)

repos_bp = Blueprint("repos", __name__, url_prefix="/api/repos")


def _manager():
    return current_app.extensions["repo_manager"]


@repos_bp.post("/clone")
def clone_repository():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400
    try:
        repository = _manager().clone_repository(payload.get("url"))
    except (RepositoryValidationError, RepositoryCloneError) as error:
        return jsonify({"error": str(error)}), 400
    return jsonify(repository), 201


@repos_bp.post("/upload")
def upload_repository():
    try:
        repository = _manager().upload_repository(request.files.get("file"))
    except RepositoryValidationError as error:
        return jsonify({"error": str(error)}), 400
    return jsonify(repository), 201


@repos_bp.get("")
def list_repositories():
    return jsonify(_manager().list_repositories())


@repos_bp.delete("/<repo_id>")
def delete_repository(repo_id):
    try:
        _manager().delete_repository(repo_id)
    except RepositoryNotFound as error:
        return jsonify({"error": str(error)}), 404
    current_app.extensions["analyzers"].pop(repo_id, None)
    return jsonify({"ok": True})
