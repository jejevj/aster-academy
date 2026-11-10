"""Persistence and validation for configurable role menus."""
from __future__ import annotations

import re

ROLE_KEYS = ('super_admin', 'admin', 'teacher', 'student')

def role_menu_tree(conn, role=None):
    roles = conn.execute('SELECT key,label,description FROM roles ORDER BY CASE key WHEN "super_admin" THEN 0 WHEN "admin" THEN 1 WHEN "teacher" THEN 2 ELSE 3 END').fetchall()
    rows = conn.execute('''SELECT m.*, COALESCE(a.enabled,0) AS enabled FROM route_menu_registry m
      LEFT JOIN role_menu_access a ON a.route_key=m.route_key AND a.role_key=?
      ORDER BY m.position,m.route_key''', (role or '',)).fetchall()
    return {'roles':[dict(r) for r in roles], 'menus':[dict(r) for r in rows]}

def visible_menus(conn, role):
    if role == 'super_admin':
        rows=conn.execute('SELECT * FROM route_menu_registry WHERE active=1 ORDER BY position,route_key').fetchall()
    else:
        rows=conn.execute('''SELECT m.* FROM route_menu_registry m JOIN role_menu_access a ON a.route_key=m.route_key
          JOIN role_permissions p ON p.role_key=a.role_key AND p.permission_key=m.required_permission
          WHERE a.role_key=? AND a.enabled=1 AND p.enabled=1 AND m.active=1 ORDER BY m.position,m.route_key''',(role,)).fetchall()
    return [dict(x) for x in rows]

def save_menu(conn, data):
    key=(data.get('route_key') or '').strip(); path=(data.get('path') or '').strip(); label=(data.get('label') or '').strip()
    perm=(data.get('required_permission') or '').strip(); parent=(data.get('parent_key') or '').strip() or None
    if not re.fullmatch(r'[a-zA-Z0-9_.-]{2,100}',key): raise ValueError('Kunci menu tidak valid.')
    if not path.startswith('/') or '?' in path or '#' in path or len(path)>250: raise ValueError('Path menu harus berupa path lokal yang valid.')
    if not label or len(label)>100: raise ValueError('Label wajib diisi (maksimal 100 karakter).')
    if not conn.execute('SELECT 1 FROM permissions WHERE key=?',(perm,)).fetchone(): raise ValueError('Permission route tidak dikenal.')
    if parent==key: raise ValueError('Menu tidak dapat menjadi parent dirinya sendiri.')
    if parent and not conn.execute('SELECT 1 FROM route_menu_registry WHERE route_key=?',(parent,)).fetchone(): raise ValueError('Parent menu tidak ditemukan.')
    if parent:
        ancestor=parent; seen={key}
        while ancestor:
            if ancestor in seen: raise ValueError('Parent menu membentuk siklus.')
            seen.add(ancestor); row=conn.execute('SELECT parent_key FROM route_menu_registry WHERE route_key=?',(ancestor,)).fetchone(); ancestor=row['parent_key'] if row else None
    position=max(0,int(data.get('position') or 0)); active=int(str(data.get('active','1')).lower() not in ('0','false','off',''))
    conn.execute('''INSERT INTO route_menu_registry(route_key,path,label,required_permission,parent_key,group_name,position,icon,active)
      VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(route_key) DO UPDATE SET path=excluded.path,label=excluded.label,
      required_permission=excluded.required_permission,parent_key=excluded.parent_key,group_name=excluded.group_name,
      position=excluded.position,icon=excluded.icon,active=excluded.active''',
      (key,path,label,perm,parent,(data.get('group_name') or '').strip()[:80],position,(data.get('icon') or '').strip()[:40],active))
    conn.execute('INSERT OR IGNORE INTO role_menu_access(role_key,route_key,enabled) SELECT key,?,0 FROM roles',(key,))

def set_role_menus(conn, role, allowed_keys):
    if role not in ROLE_KEYS or role=='super_admin': raise ValueError('Role tidak dapat diubah melalui checklist ini.')
    valid={r['route_key'] for r in conn.execute('SELECT route_key FROM route_menu_registry WHERE active=1')}
    requested=set(allowed_keys)
    if not requested<=valid: raise ValueError('Daftar berisi menu yang tidak dikenal atau nonaktif.')
    conn.execute('UPDATE role_menu_access SET enabled=0 WHERE role_key=?',(role,))
    conn.executemany('UPDATE role_menu_access SET enabled=1 WHERE role_key=? AND route_key=?',((role,k) for k in requested))

def route_permission(conn, role, path):
    """Resolve configured exact/prefix routes; returns False for inactive routes."""
    rows=conn.execute('SELECT route_key,path,required_permission,active FROM route_menu_registry ORDER BY length(path) DESC').fetchall()
    for row in rows:
        base=row['path'].rstrip('/')
        if path==base or path.startswith(base+'/'):
            if not row['active']: return False
            if role!='super_admin' and not conn.execute('''SELECT 1 FROM role_menu_access a JOIN role_permissions p
              ON p.role_key=a.role_key AND p.permission_key=? WHERE a.role_key=? AND a.route_key=? AND a.enabled=1 AND p.enabled=1''',
              (row['required_permission'],role,row['route_key'])).fetchone(): return False
            return row['required_permission']
    return None
