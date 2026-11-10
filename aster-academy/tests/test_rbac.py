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

    def test_sidebar_menu_uses_only_role_visible_registry_items(self):
        handler = App.__new__(App)
        with core.connect() as conn:
            student_menu = handler.sidebar_menu_html(conn, {"role": "student"}, "/admin")
            admin_menu = handler.sidebar_menu_html(conn, {"role": "admin"}, "/admin")

        self.assertNotIn("Bank soal", student_menu)
        self.assertNotIn("Akses dan role", student_menu)
        self.assertIn("Bank soal", admin_menu)
        self.assertIn("Pembelajaran", admin_menu)
        self.assertIn("Evaluasi", admin_menu)

    def test_registered_menu_groups_render_without_controller_aliases(self):
        handler = App.__new__(App)
        with core.connect() as conn:
            conn.execute(
                "INSERT INTO route_menu_registry(route_key,path,label,required_permission,group_name,position,icon,active) VALUES (?,?,?,?,?,?,?,1)",
                ("admin.custom", "/admin/custom", "Menu Kustom", "dashboard.view", "Operasional", 15, "★"),
            )
            conn.execute(
                "INSERT INTO role_menu_access(role_key,route_key,enabled) VALUES (?,?,1)",
                ("admin", "admin.custom"),
            )
            markup = handler.sidebar_menu_html(conn, {"role": "admin"}, "/admin/custom")

        self.assertIn("Operasional", markup)
        self.assertIn("Menu Kustom", markup)
        self.assertIn('href="/admin/custom"', markup)
        self.assertIn('class="is-active"', markup)

    def test_authorized_registered_menu_is_accessible_without_static_alias(self):
        handler = App.__new__(App)
        admin = {"role": "admin"}
        with core.connect() as conn:
            conn.execute(
                "INSERT INTO route_menu_registry(route_key,path,label,required_permission,group_name,position,icon,active) VALUES (?,?,?,?,?,?,?,1)",
                ("admin.custom", "/admin/custom", "Menu Kustom", "dashboard.view", "Operasional", 15, "★"),
            )
            conn.execute(
                "INSERT INTO role_menu_access(role_key,route_key,enabled) VALUES (?,?,1)",
                ("admin", "admin.custom"),
            )
        self.assertTrue(handler.admin_allowed(admin, "GET", "/admin/custom"))

    def test_new_menu_scaffold_uses_safe_route_key_and_does_not_overwrite(self):
        from services.menu_scaffold import ensure_menu_scaffold
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            path = ensure_menu_scaffold(root, "admin.reports", "/admin/reports", "Laporan")
            self.assertEqual(path, root / "admin_reports.html")
            self.assertIn("Laporan", path.read_text())
            path.write_text("manual template")
            self.assertEqual(ensure_menu_scaffold(root, "admin.reports", "/admin/reports", "Baru"), path)
            self.assertEqual(path.read_text(), "manual template")

if __name__ == "__main__":
    unittest.main()
