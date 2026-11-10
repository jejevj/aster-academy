"""Persistence for opaque, type-scoped public object references."""
import secrets

TABLES = {
    'bank': ('question_banks', 'id'), 'course': ('programs', 'id'),
    'module': ('modules', 'id'), 'lesson': ('lessons', 'id'),
    'question': ('questions', 'id'), 'tryout': ('question_sets', 'id'),
    'attempt': ('attempts', 'id'),
}

def ensure_schema(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS public_references (
        kind TEXT NOT NULL, object_id INTEGER NOT NULL, token TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(kind, object_id))''')

def by_id(conn, kind, object_id):
    if kind not in TABLES: return None
    row=conn.execute('SELECT token FROM public_references WHERE kind=? AND object_id=?',(kind,object_id)).fetchone()
    if row:return row['token']
    table,key=TABLES[kind]
    if not conn.execute(f'SELECT 1 FROM {table} WHERE {key}=?',(object_id,)).fetchone():return None
    while True:
        token=secrets.token_urlsafe(24)
        try:
            conn.execute('INSERT INTO public_references(kind,object_id,token) VALUES (?,?,?)',(kind,object_id,token))
            return token
        except Exception as ex:
            if 'UNIQUE' not in str(ex): raise

def by_token(conn, kind, token):
    if kind not in TABLES or not token or token.isdigit():return None
    row=conn.execute('SELECT object_id FROM public_references WHERE kind=? AND token=?',(kind,token)).fetchone()
    return row['object_id'] if row else None
