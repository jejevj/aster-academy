"""SQLite schema and non-destructive migration for question banks and exams.

Table contract
==============
* question_categories: hierarchical taxonomy. Parent rows are top-level categories
  (TWK/TIU/TKP); children are study subcategories. `Belum diklasifikasi` is a
  deliberate fallback and does not guess a legacy question's subject.
* question_banks: hierarchical, independently manageable bank containers.
  `legacy_question_set_id` maps the old question_sets row without changing its ID.
* question_bank_memberships: many-to-many bank reuse. The question's
  `owner_bank_id` is canonical ownership; `is_owner` marks that membership.
* questions: legacy columns remain intact. Added canonical bank/category,
  rich-text body, answer type, difficulty, lifecycle, and version columns.
* question_options: normalized A-E/other option content; preserves rich text and
  per-option correctness while old option_a..option_d columns remain readable.
* media_assets / question_media: asset metadata and ordered links to a question,
  option, or explanation. Files stay in application storage, not SQLite blobs.
* exam_rule_profiles: versioned scoring/selection preset and official source.
  category_scoring_rules stores category maxima, thresholds, correct/blank
  values, and TKP option-score range. question_option_scores stores the actual
  per-option TKP points for a profile/question option (never inferred by letter).
* exam_blueprints / exam_blueprint_categories: reusable exam configuration,
  selected source banks, category order, quotas, and manual/random mode.
* attempt_questions: immutable-at-start question/option/rule snapshot and order.
  Existing attempts/attempt_answers remain authoritative legacy history; added
  snapshot columns are nullable so migration never fabricates past exam content.

`ensure_question_schema(conn)` is safe to call repeatedly. It only creates
missing objects/adds missing columns, inserts seed rows with conflict-do-nothing,
and attaches legacy questions to their original set's bank plus the explicit
fallback category. It never replaces existing user data or edited rule values.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Iterable


_UNCLASSIFIED = ("unclassified", "Belum diklasifikasi", "Soal lama atau soal yang belum diberi kategori.")
_CATEGORIES = (
    ("twk", "TWK", "Tes Wawasan Kebangsaan", 10, None),
    ("tiu", "TIU", "Tes Intelegensia Umum", 20, None),
    ("tkp", "TKP", "Tes Karakteristik Pribadi", 30, None),
    # Study taxonomy only; this does not claim official item quotas by subtopic.
    ("twk_nasionalisme", "Nasionalisme", "Subkategori belajar TWK.", 10, "twk"),
    ("twk_integritas", "Integritas", "Subkategori belajar TWK.", 20, "twk"),
    ("twk_bela_negara", "Bela Negara", "Subkategori belajar TWK.", 30, "twk"),
    ("twk_pilar_negara", "Pilar Negara", "Subkategori belajar TWK.", 40, "twk"),
    ("twk_bahasa", "Bahasa Indonesia", "Subkategori belajar TWK.", 50, "twk"),
    ("tiu_verbal", "Verbal", "Subkategori belajar TIU.", 10, "tiu"),
    ("tiu_numerik", "Numerik", "Subkategori belajar TIU.", 20, "tiu"),
    ("tiu_figural", "Figural", "Subkategori belajar TIU.", 30, "tiu"),
    ("tkp_pelayanan", "Pelayanan Publik", "Subkategori belajar TKP.", 10, "tkp"),
    ("tkp_jejaring", "Jejaring Kerja", "Subkategori belajar TKP.", 20, "tkp"),
    ("tkp_sosial", "Sosial Budaya", "Subkategori belajar TKP.", 30, "tkp"),
    ("tkp_teknologi", "Teknologi Informasi dan Komunikasi", "Subkategori belajar TKP.", 40, "tkp"),
    ("tkp_profesionalisme", "Profesionalisme", "Subkategori belajar TKP.", 50, "tkp"),
    ("tkp_antiradikalisme", "Anti-radikalisme", "Subkategori belajar TKP.", 60, "tkp"),
)


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    if not _table_exists(conn, table):
        return set()
    return {row[1] for row in conn.execute(f'PRAGMA table_info("{table}")')}


def _add_columns(conn: sqlite3.Connection, table: str, definitions: Iterable[tuple[str, str]]) -> None:
    present = _columns(conn, table)
    for name, declaration in definitions:
        if name not in present:
            conn.execute(f'ALTER TABLE "{table}" ADD COLUMN "{name}" {declaration}')
            present.add(name)


def _create_tables(conn: sqlite3.Connection) -> None:
    ddl = (
        """CREATE TABLE IF NOT EXISTS question_categories (
            id INTEGER PRIMARY KEY, key TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '', parent_id INTEGER REFERENCES question_categories(id),
            position INTEGER NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
        """CREATE TABLE IF NOT EXISTS question_banks (
            id INTEGER PRIMARY KEY, parent_bank_id INTEGER REFERENCES question_banks(id) ON DELETE SET NULL,
            legacy_question_set_id INTEGER UNIQUE REFERENCES question_sets(id) ON DELETE SET NULL,
            slug TEXT NOT NULL UNIQUE, name TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
            owner_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','archived')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
        """CREATE TABLE IF NOT EXISTS question_bank_memberships (
            bank_id INTEGER NOT NULL REFERENCES question_banks(id) ON DELETE CASCADE,
            question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
            is_owner INTEGER NOT NULL DEFAULT 0 CHECK(is_owner IN (0,1)),
            position INTEGER NOT NULL DEFAULT 0, added_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(bank_id,question_id))""",
        """CREATE TABLE IF NOT EXISTS question_options (
            id INTEGER PRIMARY KEY, question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
            option_key TEXT NOT NULL, body_html TEXT NOT NULL DEFAULT '', position INTEGER NOT NULL DEFAULT 0,
            is_correct INTEGER NOT NULL DEFAULT 0 CHECK(is_correct IN (0,1)),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(question_id,option_key))""",
        """CREATE TABLE IF NOT EXISTS media_assets (
            id INTEGER PRIMARY KEY, storage_key TEXT NOT NULL UNIQUE, original_name TEXT NOT NULL DEFAULT '',
            mime_type TEXT NOT NULL, byte_size INTEGER NOT NULL CHECK(byte_size >= 0),
            width INTEGER, height INTEGER, alt_text TEXT NOT NULL DEFAULT '',
            checksum_sha256 TEXT, uploaded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
        """CREATE TABLE IF NOT EXISTS question_media (
            id INTEGER PRIMARY KEY, question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
            asset_id INTEGER NOT NULL REFERENCES media_assets(id) ON DELETE RESTRICT,
            option_key TEXT, usage TEXT NOT NULL DEFAULT 'stem'
              CHECK(usage IN ('stem','option','explanation','instruction')),
            position INTEGER NOT NULL DEFAULT 0, UNIQUE(question_id,asset_id,option_key,usage))""",
        """CREATE TABLE IF NOT EXISTS exam_rule_profiles (
            id INTEGER PRIMARY KEY, key TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
            exam_type TEXT NOT NULL DEFAULT 'SKD', year INTEGER NOT NULL,
            version TEXT NOT NULL DEFAULT '1', source_name TEXT NOT NULL DEFAULT '',
            source_url TEXT NOT NULL DEFAULT '', effective_from TEXT, effective_until TEXT,
            duration_min INTEGER NOT NULL, total_questions INTEGER NOT NULL,
            max_score INTEGER NOT NULL, passing_mode TEXT NOT NULL DEFAULT 'all_categories',
            active INTEGER NOT NULL DEFAULT 1, notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
        """CREATE TABLE IF NOT EXISTS category_scoring_rules (
            id INTEGER PRIMARY KEY, profile_id INTEGER NOT NULL REFERENCES exam_rule_profiles(id) ON DELETE CASCADE,
            category_id INTEGER NOT NULL REFERENCES question_categories(id) ON DELETE RESTRICT,
            item_count INTEGER NOT NULL, correct_score INTEGER NOT NULL DEFAULT 0,
            incorrect_score INTEGER NOT NULL DEFAULT 0, blank_score INTEGER NOT NULL DEFAULT 0,
            max_score INTEGER NOT NULL, passing_score INTEGER,
            scoring_mode TEXT NOT NULL DEFAULT 'correctness'
              CHECK(scoring_mode IN ('correctness','option_points')),
            option_score_min INTEGER, option_score_max INTEGER,
            UNIQUE(profile_id,category_id))""",
        """CREATE TABLE IF NOT EXISTS question_option_scores (
            id INTEGER PRIMARY KEY, profile_id INTEGER NOT NULL REFERENCES exam_rule_profiles(id) ON DELETE CASCADE,
            option_id INTEGER NOT NULL REFERENCES question_options(id) ON DELETE CASCADE,
            score_value INTEGER NOT NULL CHECK(score_value >= 0),
            UNIQUE(profile_id,option_id))""",
        """CREATE TABLE IF NOT EXISTS exam_rule_thresholds (
            id INTEGER PRIMARY KEY, profile_id INTEGER NOT NULL REFERENCES exam_rule_profiles(id) ON DELETE CASCADE,
            threshold_key TEXT NOT NULL, label TEXT NOT NULL, minimum_score INTEGER NOT NULL,
            category_id INTEGER REFERENCES question_categories(id) ON DELETE CASCADE,
            UNIQUE(profile_id,threshold_key))""",
        """CREATE TABLE IF NOT EXISTS exam_blueprints (
            id INTEGER PRIMARY KEY, key TEXT UNIQUE, name TEXT NOT NULL,
            profile_id INTEGER REFERENCES exam_rule_profiles(id) ON DELETE RESTRICT,
            description TEXT NOT NULL DEFAULT '', duration_min INTEGER,
            selection_mode TEXT NOT NULL DEFAULT 'manual' CHECK(selection_mode IN ('manual','random')),
            published INTEGER NOT NULL DEFAULT 0, created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
        """CREATE TABLE IF NOT EXISTS exam_blueprint_banks (
            blueprint_id INTEGER NOT NULL REFERENCES exam_blueprints(id) ON DELETE CASCADE,
            bank_id INTEGER NOT NULL REFERENCES question_banks(id) ON DELETE RESTRICT,
            position INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(blueprint_id,bank_id))""",
        """CREATE TABLE IF NOT EXISTS exam_blueprint_categories (
            id INTEGER PRIMARY KEY, blueprint_id INTEGER NOT NULL REFERENCES exam_blueprints(id) ON DELETE CASCADE,
            category_id INTEGER NOT NULL REFERENCES question_categories(id) ON DELETE RESTRICT,
            position INTEGER NOT NULL, question_count INTEGER NOT NULL,
            selection_mode TEXT NOT NULL DEFAULT 'inherit' CHECK(selection_mode IN ('inherit','manual','random')),
            UNIQUE(blueprint_id,category_id), UNIQUE(blueprint_id,position))""",
        """CREATE TABLE IF NOT EXISTS attempt_questions (
            id INTEGER PRIMARY KEY, attempt_id INTEGER NOT NULL REFERENCES attempts(id) ON DELETE CASCADE,
            question_id INTEGER REFERENCES questions(id) ON DELETE SET NULL,
            category_id INTEGER REFERENCES question_categories(id) ON DELETE SET NULL,
            position INTEGER NOT NULL, category_position INTEGER,
            question_snapshot TEXT NOT NULL, options_snapshot TEXT NOT NULL DEFAULT '[]',
            scoring_snapshot TEXT NOT NULL DEFAULT '{}', question_version INTEGER,
            selected_option_key TEXT, awarded_score INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(attempt_id,position), UNIQUE(attempt_id,question_id))""",
    )
    for statement in ddl:
        conn.execute(statement)


def _seed_taxonomy(conn: sqlite3.Connection) -> None:
    conn.execute("INSERT INTO question_categories(key,name,description,position) VALUES (?,?,?,?) ON CONFLICT(key) DO NOTHING", (_UNCLASSIFIED[0], _UNCLASSIFIED[1], _UNCLASSIFIED[2], 0))
    ids: dict[str, int] = {}
    for key, name, description, position, parent_key in _CATEGORIES:
        parent_id = ids.get(parent_key) if parent_key else None
        conn.execute("INSERT INTO question_categories(key,name,description,parent_id,position) VALUES (?,?,?,?,?) ON CONFLICT(key) DO NOTHING", (key, name, description, parent_id, position))
        row = conn.execute("SELECT id FROM question_categories WHERE key=?", (key,)).fetchone()
        ids[key] = row[0]
    # Repair only seeded taxonomy links if a prior interrupted migration inserted them first.
    for key, _, _, _, parent_key in _CATEGORIES:
        if parent_key:
            conn.execute("UPDATE question_categories SET parent_id=(SELECT id FROM question_categories WHERE key=?) WHERE key=? AND parent_id IS NULL", (parent_key, key))


def _seed_skd_2026(conn: sqlite3.Connection) -> None:
    source = "KepmenPANRB No. 406 Tahun 2026; PermenPANRB No. 13 Tahun 2026"
    url = "https://jdih.menpan.go.id/dokumen-hukum/keputusan-menteri-pendayagunaan-aparatur-negara-dan-reformasi-birokrasi-nomor-406-tahun-2026-tentang-2121"
    conn.execute("""INSERT INTO exam_rule_profiles
        (key,name,exam_type,year,version,source_name,source_url,duration_min,total_questions,max_score,passing_mode,notes)
        VALUES ('skd_2026_general','SKD Sekolah Kedinasan 2026 · Umum','SKD',2026,'1',?,?,100,110,550,'all_categories',?)
        ON CONFLICT(key) DO NOTHING""", (source, url, "Preset mengikuti nilai dalam PLAN. Ambang tiap materi wajib dipenuhi."))
    conn.execute("""INSERT INTO exam_rule_profiles
        (key,name,exam_type,year,version,source_name,source_url,duration_min,total_questions,max_score,passing_mode,notes)
        VALUES ('skd_2026_affirmative','SKD Sekolah Kedinasan 2026 · Afirmasi','SKD',2026,'1',?,?,100,110,550,'total_and_category',?)
        ON CONFLICT(key) DO NOTHING""", (source, url, "Profil afirmasi terpisah: nilai kumulatif minimal 281 dan TIU minimal 55."))
    for pkey in ("skd_2026_general", "skd_2026_affirmative"):
        profile_id = conn.execute("SELECT id FROM exam_rule_profiles WHERE key=?", (pkey,)).fetchone()[0]
        for ckey, count, maximum, passing, mode in (("twk",30,150,65,"correctness"),("tiu",35,175,80,"correctness"),("tkp",45,225,156,"option_points")):
            category_id = conn.execute("SELECT id FROM question_categories WHERE key=?", (ckey,)).fetchone()[0]
            conn.execute("""INSERT INTO category_scoring_rules
                (profile_id,category_id,item_count,correct_score,incorrect_score,blank_score,max_score,passing_score,scoring_mode,option_score_min,option_score_max)
                VALUES (?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(profile_id,category_id) DO NOTHING""",
                (profile_id,category_id,count,5 if ckey != "tkp" else 0,0,0,maximum,passing,"option_points" if ckey == "tkp" else mode,1 if ckey == "tkp" else None,5 if ckey == "tkp" else None))
        if pkey == "skd_2026_affirmative":
            conn.execute("UPDATE category_scoring_rules SET passing_score=NULL WHERE profile_id=? AND category_id IN (SELECT id FROM question_categories WHERE key IN ('twk','tkp'))", (profile_id,))
            conn.execute("UPDATE category_scoring_rules SET passing_score=55 WHERE profile_id=? AND category_id=(SELECT id FROM question_categories WHERE key='tiu')", (profile_id,))
        conn.execute("INSERT INTO exam_rule_thresholds(profile_id,threshold_key,label,minimum_score) VALUES (?,?,?,?) ON CONFLICT(profile_id,threshold_key) DO NOTHING", (profile_id,"total","Nilai kumulatif minimum",281 if pkey.endswith("affirmative") else 0))
        if pkey.endswith("affirmative"):
            tiu = conn.execute("SELECT id FROM question_categories WHERE key='tiu'").fetchone()[0]
            conn.execute("INSERT INTO exam_rule_thresholds(profile_id,threshold_key,label,minimum_score,category_id) VALUES (?,?,?,?,?) ON CONFLICT(profile_id,threshold_key) DO NOTHING", (profile_id,"affirmative_tiu","Ambang TIU afirmasi",55,tiu))


def _migrate_legacy(conn: sqlite3.Connection) -> None:
    # Keep all old columns/data; these additions provide the new canonical links.
    _add_columns(conn, "questions", (
        ("option_e", "TEXT NOT NULL DEFAULT ''"),
        ("owner_bank_id", "INTEGER REFERENCES question_banks(id) ON DELETE SET NULL"),
        ("category_id", "INTEGER REFERENCES question_categories(id) ON DELETE SET NULL"),
        ("subcategory_id", "INTEGER REFERENCES question_categories(id) ON DELETE SET NULL"),
        ("content_html", "TEXT NOT NULL DEFAULT ''"),
        ("question_type", "TEXT NOT NULL DEFAULT 'single_choice'"),
        ("difficulty", "TEXT NOT NULL DEFAULT 'unrated'"),
        ("status", "TEXT NOT NULL DEFAULT 'active'"),
        ("version", "INTEGER NOT NULL DEFAULT 1"),
    ))
    _add_columns(conn, "attempts", (
        ("rule_profile_id", "INTEGER REFERENCES exam_rule_profiles(id) ON DELETE SET NULL"),
        ("blueprint_id", "INTEGER REFERENCES exam_blueprints(id) ON DELETE SET NULL"),
        ("score_breakdown_snapshot", "TEXT NOT NULL DEFAULT '{}'"),
        ("rule_snapshot", "TEXT NOT NULL DEFAULT '{}'"),
    ))
    _add_columns(conn, "attempt_answers", (
        ("option_key", "TEXT"), ("awarded_score", "INTEGER"),
        ("answer_snapshot", "TEXT"),
    ))
    fallback_id = conn.execute("SELECT id FROM question_categories WHERE key=?", (_UNCLASSIFIED[0],)).fetchone()[0]
    if _table_exists(conn, "question_sets"):
        for s in conn.execute("SELECT id,slug,title,summary FROM question_sets ORDER BY id").fetchall():
            bank = conn.execute("SELECT id FROM question_banks WHERE legacy_question_set_id=?", (s["id"],)).fetchone()
            if bank is None:
                slug = (s["slug"] or f"legacy-set-{s['id']}")[:180]
                # Avoid collisions without mutating existing bank slugs.
                if conn.execute("SELECT 1 FROM question_banks WHERE slug=?", (slug,)).fetchone():
                    slug = f"legacy-{s['id']}-{slug}"
                conn.execute("""INSERT INTO question_banks(legacy_question_set_id,slug,name,description)
                    VALUES (?,?,?,?) ON CONFLICT(legacy_question_set_id) DO NOTHING""",
                    (s["id"],slug,s["title"],s["summary"] or ""))
                bank = conn.execute("SELECT id FROM question_banks WHERE legacy_question_set_id=?", (s["id"],)).fetchone()
            bank_id = bank[0]
            if _table_exists(conn, "questions"):
                for q in conn.execute("SELECT id,position FROM questions WHERE set_id=? ORDER BY position,id", (s["id"],)).fetchall():
                    conn.execute("UPDATE questions SET owner_bank_id=COALESCE(owner_bank_id,?), category_id=COALESCE(category_id,?) WHERE id=?", (bank_id,fallback_id,q["id"]))
                    conn.execute("""INSERT INTO question_bank_memberships(bank_id,question_id,is_owner,position)
                        VALUES (?,?,1,?) ON CONFLICT(bank_id,question_id) DO NOTHING""", (bank_id,q["id"],q["position"]))
    # Populate normalized options once from legacy A-D fields; do not overwrite editor data.
    if _table_exists(conn, "questions"):
        for q in conn.execute("SELECT id,option_a,option_b,option_c,option_d,option_e,answer FROM questions").fetchall():
            for pos, letter in enumerate(("A","B","C","D","E"), 1):
                body = q[f"option_{letter.lower()}"] or ""
                conn.execute("""INSERT INTO question_options(question_id,option_key,body_html,position,is_correct)
                    VALUES (?,?,?,?,?) ON CONFLICT(question_id,option_key) DO NOTHING""", (q["id"],letter,body,pos,int((q["answer"] or "").strip().upper()==letter)))


def _indexes(conn: sqlite3.Connection) -> None:
    for sql in (
        "CREATE INDEX IF NOT EXISTS idx_question_categories_parent ON question_categories(parent_id,position)",
        "CREATE INDEX IF NOT EXISTS idx_question_banks_parent ON question_banks(parent_bank_id,name)",
        "CREATE INDEX IF NOT EXISTS idx_question_memberships_question ON question_bank_memberships(question_id)",
        "CREATE INDEX IF NOT EXISTS idx_questions_category_bank ON questions(category_id,owner_bank_id,status)",
        "CREATE INDEX IF NOT EXISTS idx_question_options_question ON question_options(question_id,position)",
        "CREATE INDEX IF NOT EXISTS idx_question_media_question ON question_media(question_id,usage,position)",
        "CREATE INDEX IF NOT EXISTS idx_rule_scoring_profile ON category_scoring_rules(profile_id,category_id)",
        "CREATE INDEX IF NOT EXISTS idx_blueprint_categories_order ON exam_blueprint_categories(blueprint_id,position)",
        "CREATE INDEX IF NOT EXISTS idx_attempt_questions_order ON attempt_questions(attempt_id,position)",
    ):
        conn.execute(sql)


def ensure_question_schema(conn: sqlite3.Connection) -> None:
    """Create/migrate the question domain on an existing SQLite connection.

    Requires legacy `questions`, `question_sets`, `attempts`, and `attempt_answers`
    tables to exist, as in the current Aster Academy database. If called within a
    transaction, all migration work remains inside that transaction; otherwise a
    savepoint makes the schema/data migration atomic. Existing rule-profile rows
    and edited scoring rows are never updated by seeding.
    """
    conn.execute("SAVEPOINT ensure_question_schema")
    try:
        _create_tables(conn)
        _seed_taxonomy(conn)
        _seed_skd_2026(conn)
        _migrate_legacy(conn)
        _indexes(conn)
    except Exception:
        conn.execute("ROLLBACK TO ensure_question_schema")
        conn.execute("RELEASE ensure_question_schema")
        raise
    else:
        conn.execute("RELEASE ensure_question_schema")
