"""Standalone tests for the Flask API contract."""

import io
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

from app import create_app


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.app = create_app(
            {
                "TESTING": True,
                "REPO_STORAGE_PATH": self.temporary_directory.name,
                "GIT_CLONE_TIMEOUT": 5,
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self.temporary_directory.cleanup()

    @staticmethod
    def repository_zip():
        stream = io.BytesIO()
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory) / "sample"
            subprocess.run(["git", "init", str(repository)], check=True, capture_output=True)
            (repository / "README.md").write_text("sample\n", encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(repository), "add", "README.md"],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repository),
                    "-c",
                    "user.name=API Test",
                    "-c",
                    "user.email=api@example.com",
                    "commit",
                    "-m",
                    "Initial commit",
                ],
                check=True,
                capture_output=True,
            )
            with zipfile.ZipFile(stream, "w") as archive:
                for path in repository.rglob("*"):
                    if path.is_file():
                        archive.write(path, Path("sample") / path.relative_to(repository))
        stream.seek(0)
        return stream

    def upload_repository(self):
        response = self.client.post(
            "/api/repos/upload",
            data={"file": (self.repository_zip(), "sample.zip")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 201)
        return response.get_json()["id"]

    def test_health_and_empty_repository_list(self):
        self.assertEqual(self.client.get("/api/health").get_json(), {"ok": True})
        self.assertEqual(self.client.get("/api/repos").get_json(), [])

    def test_clone_rejects_invalid_url(self):
        response = self.client.post("/api/repos/clone", json={"url": "/tmp/repo"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_upload_list_query_and_delete(self):
        repo_id = self.upload_repository()

        repositories = self.client.get("/api/repos").get_json()
        self.assertEqual(len(repositories), 1)
        self.assertEqual(repositories[0]["id"], repo_id)
        self.assertIn("created_at", repositories[0])
        self.assertNotIn("path", repositories[0])

        commits = self.client.get(f"/api/repos/{repo_id}/commits")
        authors = self.client.get(f"/api/repos/{repo_id}/authors")
        tree = self.client.get(f"/api/repos/{repo_id}/tree")
        self.assertEqual(commits.status_code, 200)
        self.assertEqual(authors.status_code, 200)
        self.assertEqual(tree.status_code, 200)
        self.assertIsInstance(commits.get_json(), list)
        self.assertIsInstance(authors.get_json(), list)
        self.assertIsInstance(tree.get_json(), list)

        metrics = self.client.get(f"/api/repos/{repo_id}/metrics")
        self.assertEqual(metrics.status_code, 200)
        self.assertIn("summary", metrics.get_json())
        self.assertIsInstance(metrics.get_json()["commits_used"], int)

        commit = commits.get_json()[0]
        filtered_metrics = self.client.get(
            f"/api/repos/{repo_id}/metrics",
            query_string={
                "path": "README.md",
                "author": commit["author_email"],
                "from": commit["date"],
                "to": commit["date"],
                "commits": commit["hash"],
            },
        )
        self.assertEqual(filtered_metrics.status_code, 200)
        filtered_data = filtered_metrics.get_json()
        self.assertEqual(filtered_data["commits_used"], 1)
        self.assertEqual(filtered_data["summary"]["added_lines"], 1)
        self.assertEqual(len(filtered_data["timeline"]), 1)
        self.assertEqual(filtered_data["timeline"][0]["added_lines"], 1)

        self.assertEqual(
            self.client.delete(f"/api/repos/{repo_id}").get_json(), {"ok": True}
        )
        self.assertEqual(self.client.get("/api/repos").get_json(), [])

    def test_author_groups_round_trip(self):
        repo_id = self.upload_repository()
        groups = [[{"name": "Alice", "email": "alice@example.com"}]]
        response = self.client.post(
            f"/api/repos/{repo_id}/author-groups", json={"groups": groups}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.client.get(f"/api/repos/{repo_id}/author-groups").get_json(),
            {"groups": groups},
        )

    def test_invalid_filters_and_missing_repository(self):
        repo_id = self.upload_repository()
        response = self.client.get(f"/api/repos/{repo_id}/metrics?from=later")
        self.assertEqual(response.status_code, 400)

        missing_id = "00000000-0000-0000-0000-000000000000"
        response = self.client.get(f"/api/repos/{missing_id}/authors")
        self.assertEqual(response.status_code, 404)

    def test_upload_rejects_zip_slip_and_non_repository(self):
        unsafe = io.BytesIO()
        with zipfile.ZipFile(unsafe, "w") as archive:
            archive.writestr("../escape", "unsafe")
        unsafe.seek(0)
        response = self.client.post(
            "/api/repos/upload",
            data={"file": (unsafe, "unsafe.zip")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)
        storage_entries = list(Path(self.temporary_directory.name).iterdir())
        self.assertEqual(storage_entries, [Path(self.temporary_directory.name) / "metadata.json"])

        ordinary = io.BytesIO()
        with zipfile.ZipFile(ordinary, "w") as archive:
            archive.writestr("README.md", "not a repository")
        ordinary.seek(0)
        response = self.client.post(
            "/api/repos/upload",
            data={"file": (ordinary, "ordinary.zip")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)

    def test_metadata_is_valid_json(self):
        self.upload_repository()
        metadata_path = Path(self.temporary_directory.name) / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        self.assertEqual(len(metadata), 1)


if __name__ == "__main__":
    unittest.main()
