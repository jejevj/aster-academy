"""SQLite schema and least-privilege defaults for Aster Academy RBAC.

Call :func:`ensure_rbac_schema` with the application's SQLite connection during
bootstrap. Existing ``users.role`` values are kept on the same users; known
legacy labels are normalized and unknown labels fall back to ``student``.
The helper does not create or promote an account. Integrators can assign the
bootstrap account ``users.role = 'super_admin'`` after creating it.

Default grants are inserted only when absent, so rerunning this helper safely
adds newly introduced permissions without overwriting a Super Admin's custom
role-permission choices.
"""

from __future__ import annotations

import sqlite3
from typing import Final


_ROLES: Final = (
    ("super_admin", "Super Admin", "Akses penuh dan bypass otorisasi."),
    ("admin", "Admin", "Mengelola konten dan persetujuan."),
    ("teacher", "Teacher / Mentor", "Mengelola materi dan soal yang ditugaskan."),
    ("student", "Student / Mentee", "Akses belajar tanpa menu administrasi."),
)

# Tuples are (key, menu_key, label, action).
_PERMISSIONS: Final = (
    ("dashboard.view", "dashboard", "Lihat dashboard", "view"),
    ("programs.view", "programs", "Lihat program", "view"),
    ("programs.create", "programs", "Tambah program", "create"),
    ("programs.update", "programs", "Ubah program", "update"),
    ("programs.delete", "programs", "Hapus program", "delete"),
    ("programs.publish", "programs", "Terbitkan program", "publish"),
    ("modules.view", "modules", "Lihat modul", "view"),
    ("modules.create", "modules", "Tambah modul", "create"),
    ("modules.update", "modules", "Ubah modul", "update"),
    ("modules.delete", "modules", "Hapus modul", "delete"),
    ("lessons.view", "lessons", "Lihat pelajaran", "view"),
    ("lessons.create", "lessons", "Tambah pelajaran", "create"),
    ("lessons.update", "lessons", "Ubah pelajaran", "update"),
    ("lessons.delete", "lessons", "Hapus pelajaran", "delete"),
    ("lessons.publish", "lessons", "Terbitkan pelajaran", "publish"),
    ("question_banks.view", "question_banks", "Lihat bank soal", "view"),
    ("question_banks.create", "question_banks", "Tambah bank soal", "create"),
    ("question_banks.update", "question_banks", "Ubah bank soal", "update"),
    ("question_banks.delete", "question_banks", "Hapus bank soal", "delete"),
    ("question_banks.publish", "question_banks", "Terbitkan paket soal", "publish"),
    ("questions.view", "questions", "Lihat soal", "view"),
    ("questions.create", "questions", "Tambah soal", "create"),
    ("questions.update", "questions", "Ubah soal", "update"),
    ("questions.delete", "questions", "Hapus soal", "delete"),
    ("question_categories.view", "question_categories", "Lihat kategori soal", "view"),
    ("question_categories.create", "question_categories", "Tambah kategori soal", "create"),
    ("question_categories.update", "question_categories", "Ubah kategori soal", "update"),
    ("question_categories.delete", "question_categories", "Hapus kategori soal", "delete"),
    ("enrollments.view", "enrollments", "Lihat permintaan akses", "view"),
    ("enrollments.approve", "enrollments", "Setujui permintaan akses", "approve"),
    ("articles.view", "articles", "Lihat artikel", "view"),
    ("articles.create", "articles", "Tambah artikel", "create"),
    ("articles.update", "articles", "Ubah artikel", "update"),
    ("articles.delete", "articles", "Hapus artikel", "delete"),
    ("articles.publish", "articles", "Terbitkan artikel", "publish"),
    ("live_sessions.view", "live_sessions", "Lihat sesi live", "view"),
    ("live_sessions.create", "live_sessions", "Tambah sesi live", "create"),
    ("live_sessions.update", "live_sessions", "Ubah sesi live", "update"),
    ("live_sessions.delete", "live_sessions", "Hapus sesi live", "delete"),
    ("live_sessions.publish", "live_sessions", "Terbitkan sesi live", "publish"),
    ("users.view", "users", "Lihat pengguna", "view"),
    ("users.create", "users", "Tambah pengguna", "create"),
    ("users.update", "users", "Ubah pengguna", "update"),
    ("users.delete", "users", "Hapus pengguna", "delete"),
    ("roles.view", "roles", "Lihat role dan izin", "view"),
    ("roles.manage", "roles", "Kelola role dan izin", "manage"),
    ("profile.view", "profile", "Lihat profil", "view"),
    ("profile.update", "profile", "Ubah profil", "update"),
)

# Stable route/menu registry. Permission checks remain independently enforced
# by app.permission_for/required_permissions; these rows configure navigation.
_ROUTES: Final = (
    ("admin.dashboard", "/admin", "Ikhtisar", "dashboard.view", "Ringkasan", 10, "⌂"),
    ("admin.programs", "/admin/program", "Program", "programs.view", "Pembelajaran", 20, "▤"),
    ("admin.question_banks", "/admin/bank-soal", "Bank soal", "question_banks.view", "Evaluasi", 30, "▦"),
    ("admin.categories", "/admin/kategori-soal", "Kategori soal", "question_categories.view", "Evaluasi", 35, "◫"),
    ("admin.articles", "/admin/artikel", "Artikel", "articles.view", "Operasional", 50, "✎"),
    ("admin.live_sessions", "/admin/jadwal", "Jadwal", "live_sessions.view", "Operasional", 60, "◷"),
    ("admin.enrollments", "/admin/permintaan-akses", "Permintaan akses", "enrollments.view", "Pembelajaran", 40, "✓"),
    ("admin.roles", "/admin/akses-role", "Akses dan role", "roles.view", "Pengaturan", 80, "♙"),
    ("account.profile", "/profil", "Profil", "profile.view", "Pengaturan", 90, "◎"),
)


def _default_grants() -> dict[str, set[str]]:
    """Return the initial role matrix; later changes remain database-managed."""
    all_keys = {permission[0] for permission in _PERMISSIONS}
    admin_content = {
        key
        for key in all_keys
        if key.split(".", 1)[0]
        in {"programs", "modules", "lessons", "question_banks", "questions", "question_categories", "articles", "live_sessions"}
    }
    teacher = {
        "dashboard.view",
        "programs.view",
        "modules.view",
        "lessons.view",
        "lessons.create",
        "lessons.update",
        "questions.view",
        "questions.create",
        "questions.update",
        "profile.view",
        "profile.update",
    }
    return {
        "super_admin": all_keys,
        "admin": admin_content
        | {
            "dashboard.view",
            "enrollments.view",
            "enrollments.approve",
            "profile.view",
            "profile.update",
        },
        "teacher": teacher,
        # Student has no administrative menu grants by default.
        "student": {"profile.view", "profile.update"},
    }


def ensure_rbac_schema(conn: sqlite3.Connection) -> None:
    """Create RBAC tables and seed roles, permissions, and default grants.

    The routine is idempotent and atomic. It expects the application's existing
    ``users`` table, when present, to have a text ``role`` column. SQLite
    foreign-key enforcement is enabled for this connection before schema work;
    call outside an active transaction if that pragma still needs to be set.
    """
    if not isinstance(conn, sqlite3.Connection):
        raise TypeError("conn must be a sqlite3.Connection")

    if not conn.in_transaction:
        conn.execute("PRAGMA foreign_keys = ON")
    if conn.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        raise RuntimeError("SQLite foreign keys must be enabled before RBAC schema setup")

    conn.execute("SAVEPOINT ensure_rbac_schema")
    try:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS roles (
                key TEXT PRIMARY KEY CHECK (key IN ('super_admin','admin','teacher','student')),
                label TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT ''
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS permissions (
                key TEXT PRIMARY KEY,
                menu_key TEXT NOT NULL,
                label TEXT NOT NULL,
                action TEXT NOT NULL
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS role_permissions (
                role_key TEXT NOT NULL,
                permission_key TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 0 CHECK (enabled IN (0,1)),
                PRIMARY KEY (role_key, permission_key),
                FOREIGN KEY (role_key) REFERENCES roles(key) ON UPDATE CASCADE ON DELETE CASCADE,
                FOREIGN KEY (permission_key) REFERENCES permissions(key) ON UPDATE CASCADE ON DELETE CASCADE
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS route_menu_registry (
                route_key TEXT PRIMARY KEY, path TEXT NOT NULL UNIQUE,
                label TEXT NOT NULL, required_permission TEXT NOT NULL,
                parent_key TEXT REFERENCES route_menu_registry(route_key) ON DELETE SET NULL,
                group_name TEXT NOT NULL DEFAULT '', position INTEGER NOT NULL DEFAULT 0,
                icon TEXT NOT NULL DEFAULT '', active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
                FOREIGN KEY(required_permission) REFERENCES permissions(key)
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS role_menu_access (
                role_key TEXT NOT NULL REFERENCES roles(key) ON UPDATE CASCADE ON DELETE CASCADE,
                route_key TEXT NOT NULL REFERENCES route_menu_registry(route_key) ON UPDATE CASCADE ON DELETE CASCADE,
                enabled INTEGER NOT NULL DEFAULT 0 CHECK(enabled IN (0,1)),
                PRIMARY KEY(role_key, route_key)
            )"""
        )

        conn.executemany(
            "INSERT INTO roles(key,label,description) VALUES (?,?,?) ON CONFLICT(key) DO NOTHING", _ROLES)
        # Permissions must exist before registry rows due to the FK.
        conn.executemany(
            "INSERT INTO permissions(key,menu_key,label,action) VALUES (?,?,?,?) ON CONFLICT(key) DO UPDATE SET menu_key=excluded.menu_key,label=excluded.label,action=excluded.action",
            _PERMISSIONS)
        columns={row[1] for row in conn.execute('PRAGMA table_info(route_menu_registry)')}
        for name, ddl in [('group_name', "TEXT NOT NULL DEFAULT ''"), ('icon', "TEXT NOT NULL DEFAULT ''"), ('active', 'INTEGER NOT NULL DEFAULT 1')]:
            if name not in columns: conn.execute(f'ALTER TABLE route_menu_registry ADD COLUMN {name} {ddl}')
        conn.executemany(
            """INSERT INTO route_menu_registry(route_key,path,label,required_permission,parent_key,group_name,position,icon,active)
               VALUES (?,?,?,?,?,?,?,?,1) ON CONFLICT(route_key) DO NOTHING""",
            ((key,path,label,perm,None,group,pos,icon) for key,path,label,perm,group,pos,icon in _ROUTES))
        # Apply the canonical grouping to implemented menus. Entries without an
        # implemented controller stay inactive until their vertical slice exists.
        for key, group, icon in ((row[0], row[4], row[6]) for row in _ROUTES):
            conn.execute("UPDATE route_menu_registry SET group_name=?,icon=?,active=1 WHERE route_key=?", (group, icon, key))
        conn.execute("UPDATE route_menu_registry SET active=0 WHERE route_key='admin.users'")
        # Correct legacy seeds that pointed at non-pages; preserve any later
        # administrator-customized paths.
        conn.execute("UPDATE route_menu_registry SET path='/admin/program',label='Program' WHERE route_key='admin.programs' AND path='/admin/kursus'")
        conn.execute("UPDATE route_menu_registry SET path='/admin/permintaan-akses',label='Permintaan akses' WHERE route_key='admin.enrollments' AND path='/admin/enrollment'")
        # First install receives role grants; subsequent runs preserve administrator choices.
        for role, _, _ in _ROLES:
            for route in _ROUTES:
                conn.execute('INSERT OR IGNORE INTO role_menu_access(role_key,route_key,enabled) VALUES (?,?,?)',
                    (role,route[0],int(route[3] in _default_grants()[role])))
        conn.executemany(
            "INSERT INTO role_permissions(role_key,permission_key,enabled) VALUES (?,?,?) ON CONFLICT(role_key,permission_key) DO NOTHING",
            ((role,perm,int(perm in _default_grants()[role])) for role,_,_ in _ROLES for perm,_,_,_ in _PERMISSIONS))

        # Preserve every account. Keep canonical keys, normalize common legacy
        # labels, and assign unknown legacy labels the least-privileged role.
        has_users = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchone()
        if has_users:
            columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
            if "role" in columns:
                conn.execute(
                    """UPDATE users SET role = CASE lower(trim(COALESCE(role,'')))
                         WHEN 'super_admin' THEN 'super_admin'
                         WHEN 'superadmin' THEN 'super_admin'
                         WHEN 'admin' THEN 'admin'
                         WHEN 'administrator' THEN 'admin'
                         WHEN 'teacher' THEN 'teacher'
                         WHEN 'mentor' THEN 'teacher'
                         WHEN 'student' THEN 'student'
                         WHEN 'mentee' THEN 'student'
                         WHEN 'learner' THEN 'student'
                         ELSE 'student'
                       END
                       WHERE role IS NULL OR lower(trim(role)) NOT IN
                         ('super_admin','superadmin','admin','administrator',
                          'teacher','mentor','student','mentee','learner')"""
                )
                conn.execute(
                    """UPDATE users SET role = CASE lower(trim(role))
                         WHEN 'superadmin' THEN 'super_admin'
                         WHEN 'administrator' THEN 'admin'
                         WHEN 'mentor' THEN 'teacher'
                         WHEN 'mentee' THEN 'student'
                         WHEN 'learner' THEN 'student'
                         ELSE lower(trim(role))
                       END
                       WHERE lower(trim(role)) IN
                         ('superadmin','administrator','mentor','mentee','learner')"""
                )

        grants = _default_grants()
        conn.executemany(
            "INSERT INTO role_permissions(role_key,permission_key,enabled) VALUES (?,?,?) ON CONFLICT(role_key,permission_key) DO NOTHING",
            (
                (role_key, permission_key, int(permission_key in grants[role_key]))
                for role_key, _, _ in _ROLES
                for permission_key, _, _, _ in _PERMISSIONS
            ),
        )
        conn.execute("RELEASE SAVEPOINT ensure_rbac_schema")
    except Exception:
        conn.execute("ROLLBACK TO SAVEPOINT ensure_rbac_schema")
        conn.execute("RELEASE SAVEPOINT ensure_rbac_schema")
        raise
