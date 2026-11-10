import pathlib
import tempfile
import unittest

import core
from models.database import DatabaseSettings
from repositories.public_reference_repository import by_id, by_token
from repositories.sqlite_repository import SQLiteRepository


class TestArticleAndLiveManagementContracts(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.test_db = pathlib.Path(self.tmpdir.name) / "content.sqlite3"
        self.orig_db = core.DB
        self.orig_repo = core.DATABASE_REPOSITORY
        core.DB = self.test_db
        core.DATABASE_REPOSITORY = SQLiteRepository(self.test_db, 15)
        core.init_db()

    def tearDown(self):
        core.DB = self.orig_db
        core.DATABASE_REPOSITORY = self.orig_repo
        self.tmpdir.cleanup()

    def test_schema_adds_content_indexes_and_opaque_references(self):
        with core.connect() as conn:
            article_id = conn.execute(
                "INSERT INTO articles(slug,title,body) VALUES (?,?,?)", ("uji-artikel", "Uji", "Isi")
            ).lastrowid
            session_id = conn.execute(
                "INSERT INTO live_sessions(title,starts_at) VALUES (?,?)", ("Uji live", "2030-01-01 09:00")
            ).lastrowid
            self.assertTrue(by_id(conn, "article", article_id))
            self.assertTrue(by_id(conn, "live_session", session_id))
            self.assertEqual(by_token(conn, "article", by_id(conn, "article", article_id)), article_id)
            indexes = {row["name"] for row in conn.execute("PRAGMA index_list(articles)")}
            self.assertIn("idx_articles_public", indexes)

    def test_content_forms_use_rich_text_editor(self):
        templates = pathlib.Path(__file__).resolve().parents[1] / "templates"
        for name in ("admin_article_form.html", "admin_live_session_form.html"):
            content = (templates / name).read_text()
            self.assertIn("quill@2.0.3", content)
            self.assertIn("new Quill", content)

    def test_content_publish_requires_dedicated_permission(self):
        self.assertEqual(core.required_permissions("POST", "/admin/artikel/simpan", {"published": "1"}), ("articles.create", "articles.publish"))
        self.assertEqual(core.required_permissions("POST", "/admin/jadwal/simpan", {"session_id": "8", "published": "1"}), ("live_sessions.update", "live_sessions.publish"))
        self.assertEqual(core.permission_for("GET", "/admin/artikel/baru"), "articles.create")
        self.assertEqual(core.permission_for("GET", "/admin/jadwal/baru"), "live_sessions.create")


if __name__ == "__main__":
    unittest.main()
