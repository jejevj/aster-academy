"""Question, bank, and attempt persistence queries.

These functions accept the caller's SQLite connection so existing transaction
boundaries remain owned by the HTTP request/service layer.
"""
from __future__ import annotations

import json
import random


def question_editor_data(conn, set_id, question_id=None):
    """Load normalized records needed to render the question editor."""
    q = conn.execute("SELECT * FROM questions WHERE id=?", (question_id,)).fetchone() if question_id else None
    categories = conn.execute('SELECT c.id,c.key,c.name,p.name parent_name,COALESCE(p.key,c.key) score_key FROM question_categories c LEFT JOIN question_categories p ON p.id=c.parent_id WHERE c.active=1 ORDER BY COALESCE(p.position,c.position),c.parent_id IS NOT NULL,c.position,c.id').fetchall()
    profiles = conn.execute("SELECT p.id,p.name FROM exam_rule_profiles p WHERE p.active=1 AND EXISTS(SELECT 1 FROM category_scoring_rules r JOIN question_categories c ON c.id=r.category_id WHERE r.profile_id=p.id AND r.scoring_mode='option_points' AND (c.key='tkp' OR c.parent_id=(SELECT id FROM question_categories WHERE key='tkp'))) ORDER BY p.year DESC,p.id").fetchall()
    score_profile = conn.execute("SELECT p.id FROM question_option_scores s JOIN question_options o ON o.id=s.option_id JOIN exam_rule_profiles p ON p.id=s.profile_id WHERE o.question_id=? LIMIT 1", (question_id,)).fetchone() if question_id else None
    default_profile = conn.execute("SELECT id FROM exam_rule_profiles WHERE key='skd_2026_general'").fetchone()
    owner = conn.execute('SELECT id FROM question_banks WHERE legacy_question_set_id=?', (set_id,)).fetchone()
    banks = conn.execute('SELECT id,name FROM question_banks WHERE id<>? AND status="active" ORDER BY name', (owner['id'] if owner else -1,)).fetchall()
    memberships = conn.execute('SELECT bank_id FROM question_bank_memberships WHERE question_id=?', (question_id,)).fetchall() if question_id else []
    stored_scores = []
    profile_id = score_profile['id'] if score_profile else (default_profile['id'] if default_profile else None)
    if question_id and profile_id:
        stored_scores = conn.execute('SELECT o.option_key,s.score_value FROM question_options o JOIN question_option_scores s ON s.option_id=o.id WHERE o.question_id=? AND s.profile_id=?', (question_id, profile_id)).fetchall()
    return {'question': q, 'categories': categories, 'profiles': profiles, 'profile_id': profile_id,
            'banks': banks, 'memberships': memberships, 'stored_scores': stored_scores}


def ensure_legacy_question_bank(conn, set_id, parent_bank_id=None):
    source=conn.execute('SELECT id,slug,title,summary FROM question_sets WHERE id=?',(set_id,)).fetchone()
    if not source:return None
    bank=conn.execute('SELECT id FROM question_banks WHERE legacy_question_set_id=?',(set_id,)).fetchone()
    if not bank:
        slug=source['slug']
        if conn.execute('SELECT 1 FROM question_banks WHERE slug=?',(slug,)).fetchone():slug=f'legacy-{set_id}-{slug}'
        conn.execute('INSERT INTO question_banks(legacy_question_set_id,slug,name,description) VALUES (?,?,?,?)',(set_id,slug,source['title'],source['summary']))
        bank=conn.execute('SELECT id FROM question_banks WHERE legacy_question_set_id=?',(set_id,)).fetchone()
    if parent_bank_id:
        parent=conn.execute('SELECT id FROM question_banks WHERE id=? AND status="active"',(parent_bank_id,)).fetchone()
        if not parent or parent['id']==bank['id']:raise ValueError('Bank induk tidak valid.')
        cursor=parent['id']
        while cursor:
            if cursor==bank['id']:raise ValueError('Relasi bank tidak boleh membentuk siklus.')
            row=conn.execute('SELECT parent_bank_id FROM question_banks WHERE id=?',(cursor,)).fetchone();cursor=row['parent_bank_id'] if row else None
        conn.execute('UPDATE question_banks SET parent_bank_id=? WHERE id=?',(parent['id'],bank['id']))
    conn.execute('UPDATE questions SET owner_bank_id=COALESCE(owner_bank_id,?) WHERE set_id=?',(bank['id'],set_id))
    conn.execute('INSERT OR IGNORE INTO question_bank_memberships(bank_id,question_id,is_owner,position) SELECT ?,id,1,position FROM questions WHERE set_id=?',(bank['id'],set_id))
    return bank['id']


def parent_bank_data(conn, set_id):
    bank=conn.execute('SELECT id,parent_bank_id FROM question_banks WHERE legacy_question_set_id=?',(set_id,)).fetchone()
    current=bank['id'] if bank else -1
    rows=conn.execute('SELECT id,name FROM question_banks WHERE status="active" AND id<>? ORDER BY name',(current,)).fetchall()
    return (bank['parent_bank_id'] if bank else None, rows)


def attempt_snapshot_data(conn, attempt_id, set_id, profile_id=None):
    """Fetch source, blueprint, ordered pools, and scoring records for a snapshot."""
    source=conn.execute('SELECT duration_min FROM question_sets WHERE id=?',(set_id,)).fetchone()
    blueprint=conn.execute('SELECT * FROM exam_blueprints WHERE key=?',('set-'+str(set_id),)).fetchone()
    bank=conn.execute('SELECT id FROM question_banks WHERE legacy_question_set_id=?',(set_id,)).fetchone() if blueprint else None
    categories=conn.execute('SELECT * FROM exam_blueprint_categories WHERE blueprint_id=? ORDER BY position,id',(blueprint['id'],)).fetchall() if blueprint else []
    pools=[]
    for row in categories:
        pool=conn.execute('SELECT q.* FROM question_bank_memberships m JOIN questions q ON q.id=m.question_id WHERE m.bank_id=? AND (q.category_id=? OR q.category_id IN (SELECT id FROM question_categories WHERE parent_id=?)) AND q.status=\'active\' ORDER BY m.position,q.position,q.id',(bank['id'] if bank else -1,row['category_id'],row['category_id'])).fetchall()
        pools.append((row,pool))
    questions=conn.execute('SELECT * FROM questions WHERE set_id=? AND status=\'active\' ORDER BY position,id',(set_id,)).fetchall() if not blueprint else []
    return source, blueprint, categories, pools, questions


def scoring_rule(conn, profile_id, category_id):
    return conn.execute('SELECT r.* FROM category_scoring_rules r WHERE r.profile_id=? AND r.category_id IN (?,(SELECT parent_id FROM question_categories WHERE id=?)) ORDER BY (r.category_id=?) DESC LIMIT 1',(profile_id,category_id,category_id,category_id)).fetchone()


def option_scores(conn, question_id, profile_id):
    return conn.execute('SELECT o.option_key,os.score_value FROM question_options o JOIN question_option_scores os ON os.option_id=o.id WHERE o.question_id=? AND os.profile_id=?',(question_id,profile_id)).fetchall()


def category_name(conn, category_id):
    return conn.execute('SELECT name FROM question_categories WHERE id=?',(category_id,)).fetchone()


def rule_thresholds(conn, profile_id):
    return conn.execute('SELECT threshold_key,label,minimum_score,category_id FROM exam_rule_thresholds WHERE profile_id=? ORDER BY category_id,threshold_key',(profile_id,)).fetchall()


def rule_profile(conn, profile_id):
    return conn.execute('SELECT name,total_questions,max_score FROM exam_rule_profiles WHERE id=?',(profile_id,)).fetchone()


def set_duration(conn, set_id):
    return conn.execute('SELECT duration_min FROM question_sets WHERE id=?',(set_id,)).fetchone()
