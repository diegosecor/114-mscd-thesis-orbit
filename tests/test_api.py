"""Small end-to-end tests for the local JSON API."""

from __future__ import annotations

import json
import tempfile
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app  # noqa: E402


class ThesisApiTests(unittest.TestCase):
    def setUp(self) -> None:
        test_parent = Path(__file__).resolve().parents[1] / "tmp"
        test_parent.mkdir(exist_ok=True)
        self.temp_dir = tempfile.TemporaryDirectory(dir=test_parent)
        self.previous_data_dir = app.DATA_DIR
        self.previous_db_path = app.DB_PATH
        app.DATA_DIR = Path(self.temp_dir.name)
        app.DB_PATH = app.DATA_DIR / "test.db"
        app.init_db()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), app.OrbitRequestHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()
        app.DATA_DIR = self.previous_data_dir
        app.DB_PATH = self.previous_db_path
        for attempt in range(8):
            try:
                self.temp_dir.cleanup()
                break
            except PermissionError:
                if attempt == 7:
                    raise
                time.sleep(0.1)

    def request(self, method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            f"{self.url}{path}",
            data=body,
            headers={"Content-Type": "application/json"} if body else {},
            method=method,
        )
        try:
            with urlopen(request) as response:  # noqa: S310 - local test server
                return response.status, json.loads(response.read())
        except HTTPError as error:
            return error.code, json.loads(error.read())

    def test_crud_and_filters(self) -> None:
        status, created = self.request(
            "POST",
            "/api/theses",
            {
                "title": "Orbit Test Thesis",
                "author": "Test Author",
                "category": "XR + Immersion",
                "year": 2025,
                "page_count": 92,
                "word_count": 18900,
                "keywords": "XR, interaction",
            },
        )
        self.assertEqual(status, 201)
        thesis_id = created["id"]

        status, listed = self.request("GET", "/api/theses?category=XR%20%2B%20Immersion&page_min=80&word_max=20000")
        self.assertEqual(status, 200)
        self.assertEqual([item["id"] for item in listed["theses"]], [thesis_id])

        status, updated = self.request("PUT", f"/api/theses/{thesis_id}", {"category": "AI + Generative Design"})
        self.assertEqual(status, 200)
        self.assertEqual(updated["category"], "AI + Generative Design")

        status, deleted = self.request("DELETE", f"/api/theses/{thesis_id}")
        self.assertEqual(status, 200)
        self.assertEqual(deleted["deleted"], thesis_id)

        status, listed = self.request("GET", "/api/theses")
        self.assertEqual(status, 200)
        self.assertEqual(listed["theses"], [])

    def test_rejects_bad_numeric_filter(self) -> None:
        status, response = self.request("GET", "/api/theses?page_min=many")
        self.assertEqual(status, 400)
        self.assertIn("whole numbers", response["error"])


if __name__ == "__main__":
    unittest.main()
