import unittest
import tempfile
import pathlib
import re
import core
from models.database import DatabaseSettings
from repositories.sqlite_repository import SQLiteRepository
from controllers.http_controller import App

class TestOpaqueRouting(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.test_db = pathlib.Path(self.tmpdir.name) / "test_routes.sqlite3"
        self.orig_db = core.DB
        self.orig_repo = core.DATABASE_REPOSITORY
        core.DB = self.test_db
        core.DATABASE_REPOSITORY = SQLiteRepository(self.test_db, 15)
        core.init_db()

    def tearDown(self):
        core.DB = self.orig_db
        core.DATABASE_REPOSITORY = self.orig_repo
        self.tmpdir.cleanup()

    def test_legacy_numeric_routes_are_rejected(self):
        handler = App.__new__(App)
        # Direct access using numeric IDs must be rejected by resolve_public_path
        self.assertIsNone(handler.resolve_public_path("/admin/bank-soal/1"))
        self.assertIsNone(handler.resolve_public_path("/admin/bank-soal/1/edit"))
        self.assertIsNone(handler.resolve_public_path("/admin/bank-soal/1/blueprint"))
        self.assertIsNone(handler.resolve_public_path("/admin/kursus/1/edit"))
        self.assertIsNone(handler.resolve_public_path("/tryout/1/mulai"))
        self.assertIsNone(handler.resolve_public_path("/tryout/1/soal"))

    def test_opaque_urls_filter_replaces_ids(self):
        handler = App.__new__(App)
        with core.connect() as c:
            p = c.execute("SELECT id FROM programs LIMIT 1").fetchone()
            s = c.execute("SELECT id FROM question_sets LIMIT 1").fetchone()
            pid = p["id"]
            sid = s["id"]

        markup = f'<a href="/admin/kursus/{pid}/edit">Edit</a> <a href="/admin/bank-soal/{sid}/blueprint">BP</a>'
        filtered = handler.opaque_urls(markup)

        # After filtering, raw numeric IDs must not exist in href
        self.assertNotIn(f'/admin/kursus/{pid}/edit', filtered)
        self.assertNotIn(f'/admin/bank-soal/{sid}/blueprint', filtered)
        # Check that opaque tokens are present
        self.assertRegex(filtered, r'/admin/kursus/[A-Za-z0-9_-]{10,}/edit')
        self.assertRegex(filtered, r'/admin/bank-soal/[A-Za-z0-9_-]{10,}/blueprint')

if __name__ == "__main__":
    unittest.main()
