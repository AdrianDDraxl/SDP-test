"""Application configuration for the RAT API."""

import os


class Config:
    """Default application settings, overridable through environment variables."""

    REPO_STORAGE_PATH = os.environ.get("RAT_REPO_STORAGE", "/tmp/rat_repos")
    GIT_CLONE_TIMEOUT = int(os.environ.get("RAT_GIT_CLONE_TIMEOUT", "600"))
    MAX_CONTENT_LENGTH = int(os.environ.get("RAT_MAX_UPLOAD_BYTES", str(512 * 1024 * 1024)))
    JSON_SORT_KEYS = False
