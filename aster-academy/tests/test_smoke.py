import unittest
import tempfile
import pathlib
import json
import core
from models.database import DatabaseSettings
from repositories.sqlite_repository import SQLiteRepository
from services.public_references import ref_for, resolve_ref
from services.question_service import build_attempt_snapshot

class AsterCoreSmokeTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.test_db = pathlib.Path(self.tmpdir.name) / "test_aster.sqlite3"
        self.orig_db = core.DB
        self.orig_repo = core.DATABASE_REPOSITORY
        core.DB = self.test_db
        core.DATABASE_REPOSITORY = SQLiteRepository(self.test_db, 15)
        core.init_db()

    def tearDown(self):
        core.DB = self.orig_db
        core.DATABASE_REPOSITORY = self.orig_repo
        self.tmpdir.cleanup()

    def test_init_db_creates_core_tables(self):
        with core.connect() as c:
            tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            for required in ["users", "programs", "modules", "lessons", "question_sets", "question_banks", "questions", "exam_rule_profiles", "public_references"]:
                self.assertIn(required, tables, f"Tabel {required} wajib ada di database.")

    def test_opaque_reference_contract(self):
        with core.connect() as c:
            row = c.execute("SELECT id FROM question_sets LIMIT 1").fetchone()
            self.assertIsNotNone(row, "Harus ada data awal question_sets.")
            set_id = row["id"]
            token = ref_for(c, "tryout", set_id)
            self.assertIsNotNone(token, "Token opaque untuk tryout harus terbentuk.")
            assert token is not None
            self.assertFalse(token.isdigit(), "Token opaque tidak boleh berupa angka integer telanjang.")
            resolved = resolve_ref(c, "tryout", token)
            self.assertEqual(resolved, set_id, "Token opaque harus ter-resolve kembali ke ID asal.")
            self.assertIsNone(resolve_ref(c, "tryout", str(set_id)), "Token berupa angka harus ditolak oleh resolver opaque.")

    def test_attempt_snapshot_creation(self):
        with core.connect() as c:
            user = c.execute("SELECT id FROM users LIMIT 1").fetchone()
            qset = c.execute("SELECT id FROM question_sets LIMIT 1").fetchone()
            uid = user["id"] if user else c.execute("INSERT INTO users(name,email,password_hash) VALUES ('Test','test@example.com','hash')").lastrowid
            sid = qset["id"]
            aid = c.execute("INSERT INTO attempts(user_id,set_id) VALUES (?,?)", (uid, sid)).lastrowid
            count = build_attempt_snapshot(c, aid, sid)
            self.assertGreater(count, 0, "Snapshot harus mengunci minimal satu soal.")
            snapshot_rows = c.execute("SELECT * FROM attempt_questions WHERE attempt_id=?", (aid,)).fetchall()
            self.assertEqual(len(snapshot_rows), count, "Jumlah baris attempt_questions harus sama dengan soal terpilih.")

if __name__ == "__main__":
    unittest.main()
