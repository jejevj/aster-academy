import pathlib
import tempfile
import unittest

import core
from models.database import DatabaseSettings
from repositories.sqlite_repository import SQLiteRepository
from services.dashboard import recent_attempt_summaries


class TestDashboardSummaries(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.test_db = pathlib.Path(self.tmpdir.name) / "dashboard.sqlite3"
        self.orig_db = core.DB
        self.orig_repo = core.DATABASE_REPOSITORY
        core.DB = self.test_db
        core.DATABASE_REPOSITORY = SQLiteRepository(self.test_db, 15)
        core.init_db()

    def tearDown(self):
        core.DB = self.orig_db
        core.DATABASE_REPOSITORY = self.orig_repo
        self.tmpdir.cleanup()

    def test_returns_finished_attempts_newest_first_with_percentage(self):
        with core.connect() as conn:
            user_id = conn.execute(
                "INSERT INTO users(name,email,password_hash) VALUES (?,?,?)",
                ("Student", "student@example.test", "hash"),
            ).lastrowid
            set_id = conn.execute("SELECT id FROM question_sets LIMIT 1").fetchone()["id"]
            conn.execute(
                "INSERT INTO attempts(user_id,set_id,score,total,started_at,finished_at) VALUES (?,?,?,?,?,?)",
                (user_id, set_id, 70, 100, "2026-01-01 08:00:00", "2026-01-01 09:00:00"),
            )
            conn.execute(
                "INSERT INTO attempts(user_id,set_id,score,total,started_at,finished_at) VALUES (?,?,?,?,?,?)",
                (user_id, set_id, 45, 90, "2026-01-02 08:00:00", "2026-01-02 09:00:00"),
            )
            summaries = recent_attempt_summaries(conn, user_id)

        self.assertEqual(len(summaries), 2)
        self.assertEqual(summaries[0]["score"], 45)
        self.assertEqual(summaries[0]["total"], 90)
        self.assertEqual(summaries[0]["percentage"], 50)
        self.assertEqual(summaries[1]["percentage"], 70)

    def test_excludes_unfinished_attempts_and_respects_limit(self):
        with core.connect() as conn:
            user_id = conn.execute(
                "INSERT INTO users(name,email,password_hash) VALUES (?,?,?)",
                ("Student", "student2@example.test", "hash"),
            ).lastrowid
            set_id = conn.execute("SELECT id FROM question_sets LIMIT 1").fetchone()["id"]
            for index in range(4):
                conn.execute(
                    "INSERT INTO attempts(user_id,set_id,score,total,started_at,finished_at) VALUES (?,?,?,?,?,?)",
                    (user_id, set_id, index, 10, f"2026-01-0{index + 1} 08:00:00", f"2026-01-0{index + 1} 09:00:00"),
                )
            conn.execute(
                "INSERT INTO attempts(user_id,set_id,score,total,started_at) VALUES (?,?,?,?,?)",
                (user_id, set_id, 0, 10, "2026-01-05 08:00:00"),
            )
            summaries = recent_attempt_summaries(conn, user_id, limit=3)

        self.assertEqual([item["score"] for item in summaries], [3, 2, 1])


if __name__ == "__main__":
    unittest.main()
