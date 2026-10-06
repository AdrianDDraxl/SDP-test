"""Git data and metrics API routes."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from threading import RLock

from flask import Blueprint, current_app, jsonify, request

from services.repo_manager import RepositoryNotFound

from engine.analyzer import GitAnalyzer


metrics_bp = Blueprint("metrics", __name__, url_prefix="/api/repos")
_analyzer_lock = RLock()


def _manager():
    return current_app.extensions["repo_manager"]


def _get_analyzer(repo_id):
    repository = _manager().get_repository(repo_id)
    with _analyzer_lock:
        analyzers = current_app.extensions["analyzers"]
        analyzer = analyzers.get(repo_id)
        if analyzer is None:
            analyzer = GitAnalyzer(repository["path"])
            saved_groups = repository.get("author_groups")
            if saved_groups:
                try:
                    analyzer.set_author_groups(saved_groups)
                except (TypeError, ValueError):
                    pass  # ignore invalid persisted groups
            analyzers[repo_id] = analyzer
    return analyzer


def _parse_timestamp(name):
    raw_value = request.args.get(name)
    if raw_value in (None, ""):
        return None
    try:
        return int(raw_value)
    except ValueError as error:
        raise ValueError(f"Query parameter '{name}' must be a unix timestamp") from error


def _parse_commits():
    raw_value = request.args.get("commits")
    if raw_value in (None, ""):
        return None
    commits = [commit.strip() for commit in raw_value.split(",") if commit.strip()]
    if not commits:
        raise ValueError("Query parameter 'commits' must contain at least one hash")
    return commits


def _parse_authors():
    raw_value = request.args.get("author")
    if raw_value in (None, ""):
        return None
    authors = [author.strip() for author in raw_value.split(",") if author.strip()]
    if not authors:
        raise ValueError("Query parameter 'author' must contain at least one value")
    return authors


def _to_jsonable(value):
    if is_dataclass(value):
        return _to_jsonable(asdict(value))
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return _to_jsonable(to_dict())
    if hasattr(value, "__dict__"):
        return _to_jsonable(vars(value))
    return value


def _engine_response(callback):
    try:
        return jsonify(_to_jsonable(callback()))
    except RepositoryNotFound as error:
        return jsonify({"error": str(error)}), 404
    except (TypeError, ValueError) as error:
        return jsonify({"error": str(error)}), 400


@metrics_bp.get("/<repo_id>/commits")
def get_commits(repo_id):
    def query():
        from_ts = _parse_timestamp("from")
        to_ts = _parse_timestamp("to")
        if from_ts is not None and to_ts is not None and from_ts > to_ts:
            raise ValueError("Query parameter 'from' cannot be greater than 'to'")
        return _get_analyzer(repo_id).get_commits(from_ts=from_ts, to_ts=to_ts)

    return _engine_response(query)


@metrics_bp.get("/<repo_id>/authors")
def get_authors(repo_id):
    return _engine_response(lambda: _get_analyzer(repo_id).get_authors())


@metrics_bp.get("/<repo_id>/tree")
def get_tree(repo_id):
    commit_hash = request.args.get("commit") or None
    return _engine_response(lambda: _get_analyzer(repo_id).get_file_tree(commit_hash))


@metrics_bp.get("/<repo_id>/metrics")
def get_metrics(repo_id):
    def query():
        from_ts = _parse_timestamp("from")
        to_ts = _parse_timestamp("to")
        if from_ts is not None and to_ts is not None and from_ts > to_ts:
            raise ValueError("Query parameter 'from' cannot be greater than 'to'")
        return _get_analyzer(repo_id).compute_metrics(
            path=request.args.get("path") or None,
            author=_parse_authors(),
            from_ts=from_ts,
            to_ts=to_ts,
            commit_hashes=_parse_commits(),
        )

    return _engine_response(query)


@metrics_bp.get("/<repo_id>/author-groups")
def get_author_groups(repo_id):
    return _engine_response(
        lambda: {"groups": _get_analyzer(repo_id).get_author_groups()}
    )


@metrics_bp.post("/<repo_id>/author-groups")
def set_author_groups(repo_id):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or "groups" not in payload:
        return jsonify({"error": "Request body must contain 'groups'"}), 400
    try:
        groups = _validate_author_groups(payload["groups"])
        _get_analyzer(repo_id).set_author_groups(groups)
        _manager().update_author_groups(repo_id, groups)
    except RepositoryNotFound as error:
        return jsonify({"error": str(error)}), 404
    except (TypeError, ValueError) as error:
        return jsonify({"error": str(error)}), 400
    return jsonify({"ok": True})


def _validate_author_groups(groups):
    if not isinstance(groups, list):
        raise ValueError("'groups' must be an array")
    validated = []
    for group in groups:
        if not isinstance(group, list) or not group:
            raise ValueError("Each author group must be a non-empty array")
        validated_group = []
        for author in group:
            if not isinstance(author, dict):
                raise ValueError("Each author must be an object")
            name = author.get("name")
            email = author.get("email")
            if not isinstance(name, str) or not name.strip():
                raise ValueError("Each author must have a non-empty name")
            if not isinstance(email, str) or not email.strip():
                raise ValueError("Each author must have a non-empty email")
            validated_group.append({"name": name.strip(), "email": email.strip()})
        validated.append(validated_group)
    return validated
