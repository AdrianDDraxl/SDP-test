"""Route blueprint registration."""

from .metrics import metrics_bp
from .repos import repos_bp


def register_blueprints(app):
    """Register all API blueprints on an application."""
    app.register_blueprint(repos_bp)
    app.register_blueprint(metrics_bp)
