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

    def test_category_analysis_identifies_weakest_category_and_previous_score(self):
        with core.connect() as conn:
            user_id = conn.execute(
                "INSERT INTO users(name,email,password_hash) VALUES (?,?,?)",
                ("Analyst", "analyst@example.test", "hash"),
            ).lastrowid
            set_id = conn.execute("SELECT id FROM question_sets LIMIT 1").fetchone()["id"]
            category_rows = conn.execute(
                "SELECT id, name FROM question_categories WHERE parent_id IS NULL ORDER BY id LIMIT 2"
            ).fetchall()
            self.assertEqual(len(category_rows), 2)
            older = conn.execute(
                "INSERT INTO attempts(user_id,set_id,score,total,started_at,finished_at,score_breakdown_snapshot) VALUES (?,?,?,?,?,?,?)",
                (user_id, set_id, 70, 100, "2026-01-01 08:00:00", "2026-01-01 09:00:00", '{"1":{"score":70,"max_score":100}}'),
            ).lastrowid
            newest = conn.execute(
                "INSERT INTO attempts(user_id,set_id,score,total,started_at,finished_at,score_breakdown_snapshot) VALUES (?,?,?,?,?,?,?)",
                (user_id, set_id, 60, 100, "2026-01-02 08:00:00", "2026-01-02 09:00:00", '{}'),
            ).lastrowid
            conn.execute(
                "UPDATE attempts SET score_breakdown_snapshot=? WHERE id=?",
                (
                    '{"%s":{"score":8,"max_score":20},"%s":{"score":18,"max_score":20}}'
                    % (category_rows[0]["id"], category_rows[1]["id"]),
                    newest,
                ),
            )
            from services.dashboard import category_learning_analysis
            analysis = category_learning_analysis(conn, user_id)

        self.assertEqual(analysis["latest_attempt_id"], newest)
        self.assertEqual(analysis["previous_percentage"], 70)
        self.assertEqual(analysis["weakest"]["name"], category_rows[0]["name"])
        self.assertEqual(analysis["weakest"]["percentage"], 40)

    def test_category_analysis_ignores_missing_or_invalid_breakdowns(self):
        with core.connect() as conn:
            user_id = conn.execute(
                "INSERT INTO users(name,email,password_hash) VALUES (?,?,?)",
                ("No Analysis", "no-analysis@example.test", "hash"),
            ).lastrowid
            set_id = conn.execute("SELECT id FROM question_sets LIMIT 1").fetchone()["id"]
            conn.execute(
                "INSERT INTO attempts(user_id,set_id,score,total,started_at,finished_at,score_breakdown_snapshot) VALUES (?,?,?,?,?,?,?)",
                (user_id, set_id, 10, 20, "2026-01-01 08:00:00", "2026-01-01 09:00:00", "not-json"),
            )
            from services.dashboard import category_learning_analysis
            self.assertIsNone(category_learning_analysis(conn, user_id))

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
