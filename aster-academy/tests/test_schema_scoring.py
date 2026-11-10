import unittest
import tempfile
import pathlib
import json
import core
from models.database import DatabaseSettings
from repositories.sqlite_repository import SQLiteRepository
from question_schema import ensure_question_schema
from rbac_schema import ensure_rbac_schema

class TestSchemaAndScoring(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.test_db = pathlib.Path(self.tmpdir.name) / "test_schema.sqlite3"
        self.orig_db = core.DB
        self.orig_repo = core.DATABASE_REPOSITORY
        core.DB = self.test_db
        core.DATABASE_REPOSITORY = SQLiteRepository(self.test_db, 15)
        core.init_db()

    def tearDown(self):
        core.DB = self.orig_db
        core.DATABASE_REPOSITORY = self.orig_repo
        self.tmpdir.cleanup()

    def test_migrations_are_idempotent(self):
        with core.connect() as c:
            # Re-running migrations should succeed without breaking or throwing errors
            ensure_rbac_schema(c)
            ensure_question_schema(c)
            core.init_db()

    def test_exam_rule_profiles_seeded(self):
        with core.connect() as c:
            profiles = c.execute("SELECT key, name, duration_min, total_questions, max_score FROM exam_rule_profiles").fetchall()
            profile_keys = {p["key"] for p in profiles}
            self.assertIn("skd_2026_general", profile_keys)
            self.assertIn("skd_2026_affirmative", profile_keys)

            gen = next(p for p in profiles if p["key"] == "skd_2026_general")
            self.assertEqual(gen["duration_min"], 100)
            self.assertEqual(gen["total_questions"], 110)
            self.assertEqual(gen["max_score"], 550)

    def test_category_scoring_rules_seeded(self):
        with core.connect() as c:
            gen_profile = c.execute("SELECT id FROM exam_rule_profiles WHERE key='skd_2026_general'").fetchone()
            rules = c.execute("""
                SELECT c.key, r.item_count, r.correct_score, r.max_score, r.passing_score, r.scoring_mode
                FROM category_scoring_rules r
                JOIN question_categories c ON c.id = r.category_id
                WHERE r.profile_id = ?
            """, (gen_profile["id"],)).fetchall()

            rule_map = {r["key"]: r for r in rules}
            self.assertIn("twk", rule_map)
            self.assertIn("tiu", rule_map)
            self.assertIn("tkp", rule_map)

            # SKD 2026: TWK (30 soal, ambang 65), TIU (35 soal, ambang 80), TKP (45 soal, ambang 156)
            self.assertEqual(rule_map["twk"]["item_count"], 30)
            self.assertEqual(rule_map["twk"]["passing_score"], 65)
            self.assertEqual(rule_map["tiu"]["item_count"], 35)
            self.assertEqual(rule_map["tiu"]["passing_score"], 80)
            self.assertEqual(rule_map["tkp"]["item_count"], 45)
            self.assertEqual(rule_map["tkp"]["passing_score"], 156)
            self.assertEqual(rule_map["tkp"]["scoring_mode"], "option_points")

if __name__ == "__main__":
    unittest.main()
