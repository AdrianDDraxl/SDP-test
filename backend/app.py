"""Flask application entry point for the RAT API."""

import logging

from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from config import Config
from routes import register_blueprints
from services.repo_manager import RepositoryManager


def create_app(config_overrides=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    CORS(app)
    app.extensions["repo_manager"] = RepositoryManager(
        app.config["REPO_STORAGE_PATH"],
        clone_timeout=app.config["GIT_CLONE_TIMEOUT"],
    )
    app.extensions["analyzers"] = {}
    register_blueprints(app)

    @app.get("/api/health")
    def health():
        return jsonify({"ok": True})

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return jsonify({"error": error.description}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        app.logger.exception("Unhandled API error", exc_info=error)
        return jsonify({"error": "An internal server error occurred"}), 500

    return app


app = create_app()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True, port=5000)
