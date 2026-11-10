import unittest
import tempfile
import pathlib
import core
from models.database import DatabaseSettings
from repositories.sqlite_repository import SQLiteRepository
from controllers.http_controller import App

class TestRBACEnforcement(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.test_db = pathlib.Path(self.tmpdir.name) / "test_rbac.sqlite3"
        self.orig_db = core.DB
        self.orig_repo = core.DATABASE_REPOSITORY
        core.DB = self.test_db
        core.DATABASE_REPOSITORY = SQLiteRepository(self.test_db, 15)
        core.init_db()

    def tearDown(self):
        core.DB = self.orig_db
        core.DATABASE_REPOSITORY = self.orig_repo
        self.tmpdir.cleanup()

    def test_super_admin_has_full_permissions(self):
        handler = App.__new__(App)
        super_admin = {"role": "super_admin"}
        self.assertTrue(handler.can(super_admin, "dashboard.view"))
        self.assertTrue(handler.can(super_admin, "programs.publish"))
        self.assertTrue(handler.can(super_admin, "roles.manage"))

    def test_student_restricted_from_admin(self):
        handler = App.__new__(App)
        student = {"role": "student"}
        self.assertFalse(handler.can(student, "dashboard.view"))
        self.assertFalse(handler.can(student, "programs.create"))
        self.assertFalse(handler.can(student, "roles.manage"))
        self.assertFalse(handler.can(student, "enrollments.approve"))

    def test_admin_allowed_verification(self):
        handler = App.__new__(App)
        student = {"role": "student"}
        self.assertFalse(handler.admin_allowed(student, "GET", "/admin"))
        self.assertFalse(handler.admin_allowed(student, "POST", "/admin/kursus/simpan"))

if __name__ == "__main__":
    unittest.main()
