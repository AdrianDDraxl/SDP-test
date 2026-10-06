"""Repository persistence, cloning, upload, and deletion services."""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
import threading
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


class RepositoryError(Exception):
    """Base error for repository operations."""


class RepositoryNotFound(RepositoryError):
    """Raised when a repository id is unknown."""


class RepositoryValidationError(RepositoryError):
    """Raised when repository input is invalid."""


class RepositoryCloneError(RepositoryError):
    """Raised when git cannot clone a repository."""


class RepositoryManager:
    """Store repositories on disk and persist their metadata as JSON."""

    def __init__(self, storage_path: str, clone_timeout: int = 600):
        self.storage_path = Path(storage_path).expanduser().resolve()
        self.metadata_path = self.storage_path / "metadata.json"
        self.clone_timeout = clone_timeout
        self._lock = threading.RLock()
        self.storage_path.mkdir(parents=True, exist_ok=True)
        if not self.metadata_path.exists():
            self._write_metadata({})

    def list_repositories(self) -> list[dict]:
        """Return public metadata for all repositories, newest first."""
        with self._lock:
            metadata = self._read_metadata()
        repositories = [self._public_metadata(repo) for repo in metadata.values()]
        return sorted(repositories, key=lambda repo: repo["created_at"], reverse=True)

    def get_repository(self, repo_id: str) -> dict:
        """Return stored metadata for a repository."""
        self._validate_id(repo_id)
        with self._lock:
            repository = self._read_metadata().get(repo_id)
        if repository is None:
            raise RepositoryNotFound("Repository not found")
        if not Path(repository["path"]).is_dir():
            raise RepositoryNotFound("Repository files are missing")
        return dict(repository)

    def clone_repository(self, url: str) -> dict:
        """Synchronously clone a remote git repository and register it."""
        normalized_url = self._validate_clone_url(url)
        repo_id = str(uuid.uuid4())
        destination = self.storage_path / repo_id
        name = self._name_from_url(normalized_url)

        try:
            completed = subprocess.run(
                ["git", "clone", "--", normalized_url, str(destination)],
                check=False,
                capture_output=True,
                text=True,
                timeout=self.clone_timeout,
            )
        except subprocess.TimeoutExpired as error:
            shutil.rmtree(destination, ignore_errors=True)
            raise RepositoryCloneError("Repository clone timed out") from error
        except OSError as error:
            shutil.rmtree(destination, ignore_errors=True)
            raise RepositoryCloneError("Unable to run git clone") from error

        if completed.returncode != 0 or not (destination / ".git").is_dir():
            shutil.rmtree(destination, ignore_errors=True)
            detail = (completed.stderr or completed.stdout).strip()
            if detail:
                detail = detail.splitlines()[-1][:300]
            raise RepositoryCloneError(detail or "Unable to clone repository")

        repository = self._new_metadata(repo_id, name, normalized_url, destination)
        self._add_metadata(repository)
        return {**self._public_metadata(repository), "status": "ready"}

    def upload_repository(self, uploaded_file: FileStorage) -> dict:
        """Safely extract an uploaded zip containing a working git repository."""
        if uploaded_file is None or not uploaded_file.filename:
            raise RepositoryValidationError("A zip file is required")
        filename = secure_filename(uploaded_file.filename)
        if not filename or not filename.lower().endswith(".zip"):
            raise RepositoryValidationError("Uploaded file must be a zip archive")

        repo_id = str(uuid.uuid4())
        destination = self.storage_path / repo_id
        destination.mkdir()

        try:
            with zipfile.ZipFile(uploaded_file.stream) as archive:
                self._validate_archive(archive)
                archive.extractall(destination)
        except RepositoryValidationError:
            shutil.rmtree(destination, ignore_errors=True)
            raise
        except (zipfile.BadZipFile, OSError, RuntimeError) as error:
            shutil.rmtree(destination, ignore_errors=True)
            raise RepositoryValidationError("Uploaded file is not a valid zip archive") from error

        git_directories = sorted(
            (path for path in destination.rglob(".git") if path.is_dir()),
            key=lambda path: len(path.parts),
        )
        if not git_directories:
            shutil.rmtree(destination, ignore_errors=True)
            raise RepositoryValidationError("Zip archive does not contain a .git directory")

        repository_path = git_directories[0].parent.resolve()
        if not self._is_within(repository_path, destination.resolve()):
            shutil.rmtree(destination, ignore_errors=True)
            raise RepositoryValidationError("Zip archive contains an unsafe path")

        name = repository_path.name if repository_path != destination else Path(filename).stem
        repository = self._new_metadata(repo_id, name, None, repository_path)
        self._add_metadata(repository)
        return {**self._public_metadata(repository), "status": "ready"}

    def delete_repository(self, repo_id: str) -> None:
        """Remove a registered repository and its files."""
        self._validate_id(repo_id)
        with self._lock:
            metadata = self._read_metadata()
            repository = metadata.get(repo_id)
            if repository is None:
                raise RepositoryNotFound("Repository not found")

            managed_path = self.storage_path / repo_id
            if managed_path.exists():
                if not self._is_within(managed_path.resolve(), self.storage_path):
                    raise RepositoryError("Refusing to delete an unmanaged path")
                shutil.rmtree(managed_path)
            del metadata[repo_id]
            self._write_metadata(metadata)

    def _add_metadata(self, repository: dict) -> None:
        with self._lock:
            metadata = self._read_metadata()
            metadata[repository["id"]] = repository
            try:
                self._write_metadata(metadata)
            except Exception:
                shutil.rmtree(self.storage_path / repository["id"], ignore_errors=True)
                raise

    def _read_metadata(self) -> dict:
        try:
            with self.metadata_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except FileNotFoundError:
            return {}
        except (json.JSONDecodeError, OSError) as error:
            raise RepositoryError("Repository metadata could not be read") from error
        if not isinstance(data, dict):
            raise RepositoryError("Repository metadata has an invalid format")
        return data

    def _write_metadata(self, metadata: dict) -> None:
        self.storage_path.mkdir(parents=True, exist_ok=True)
        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix="metadata-", suffix=".json", dir=self.storage_path
        )
        try:
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
                json.dump(metadata, handle, indent=2, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, self.metadata_path)
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)

    @staticmethod
    def _public_metadata(repository: dict) -> dict:
        return {
            "id": repository["id"],
            "name": repository["name"],
            "url": repository.get("url"),
            "created_at": repository["created_at"],
        }

    @staticmethod
    def _new_metadata(repo_id: str, name: str, url: str | None, path: Path) -> dict:
        return {
            "id": repo_id,
            "name": name,
            "url": url,
            "path": str(path),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _validate_id(repo_id: str) -> None:
        try:
            parsed = uuid.UUID(repo_id)
        except (ValueError, AttributeError, TypeError) as error:
            raise RepositoryNotFound("Repository not found") from error
        if str(parsed) != repo_id.lower():
            raise RepositoryNotFound("Repository not found")

    @staticmethod
    def _validate_clone_url(url: str) -> str:
        if not isinstance(url, str) or not url.strip():
            raise RepositoryValidationError("A repository URL is required")
        normalized = url.strip()
        if any(character in normalized for character in ("\n", "\r", "\0")):
            raise RepositoryValidationError("Repository URL is invalid")
        parsed = urlparse(normalized)
        valid_remote = parsed.scheme in {"http", "https", "ssh", "git"} and bool(parsed.netloc)
        valid_scp = bool(re.fullmatch(r"[^@\s]+@[^:\s]+:.+", normalized))
        if not valid_remote and not valid_scp:
            raise RepositoryValidationError("Repository URL must be a remote git URL")
        return normalized

    @staticmethod
    def _name_from_url(url: str) -> str:
        path = urlparse(url).path if "://" in url else url.split(":", 1)[-1]
        raw_name = unquote(path.rstrip("/").rsplit("/", 1)[-1])
        if raw_name.lower().endswith(".git"):
            raw_name = raw_name[:-4]
        return secure_filename(raw_name) or "repository"

    @classmethod
    def _validate_archive(cls, archive: zipfile.ZipFile) -> None:
        if not archive.infolist():
            raise RepositoryValidationError("Zip archive is empty")
        for entry in archive.infolist():
            normalized = entry.filename.replace("\\", "/")
            path = Path(normalized)
            if path.is_absolute() or ".." in path.parts:
                raise RepositoryValidationError("Zip archive contains an unsafe path")
            mode = entry.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise RepositoryValidationError("Zip archive cannot contain symbolic links")

    @staticmethod
    def _is_within(path: Path, parent: Path) -> bool:
        try:
            path.relative_to(parent)
            return True
        except ValueError:
            return False
