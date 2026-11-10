from __future__ import annotations
import hashlib, html, os, re, secrets, sqlite3, sys, time, mimetypes, json, random
from email.parser import BytesParser
from email.policy import default as email_policy
from html.parser import HTMLParser
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse, urlencode
from getpass import getpass
from datetime import datetime, timezone

from rbac_schema import ensure_rbac_schema
from question_schema import ensure_question_schema
from models.database import default_settings
from repositories.sqlite_repository import SQLiteRepository
from services.authentication import passhash, verify
from services.formatting import e, money
from services.question_service import (
    attempt_seconds_remaining, build_attempt_snapshot, ensure_legacy_question_bank,
    parent_bank_options, question_editor_values,
)
from services.dashboard import recent_attempt_summaries
from services.rich_text import RichTextSanitizer, sanitize_rich_html
from services.menu_service import route_permission
from repositories.public_reference_repository import ensure_schema as ensure_public_reference_schema
from services.public_references import ref_for, resolve_ref

BASE = Path(__file__).resolve().parent
TEMPLATES = BASE / 'templates'
DB_SETTINGS = default_settings(BASE)
DB = DB_SETTINGS.path
DATABASE_REPOSITORY = SQLiteRepository(DB_SETTINGS.path, DB_SETTINGS.timeout_seconds)
HOST, PORT = '127.0.0.1', int(os.environ.get('PORT', '8000'))
COOKIE = 'aster_session'

ROLE_LABELS = {'super_admin':'Super Admin','admin':'Admin','teacher':'Teacher / Mentor','student':'Student / Mentee'}
RESOURCE_ACTIONS = {
    'dashboard': ('view',), 'programs': ('view','create','update','delete','publish'),
    'modules': ('view','create','update','delete'), 'lessons': ('view','create','update','delete'),
    'question_banks': ('view','create','update','delete','publish'), 'questions': ('view','create','update','delete'),
    'question_categories': ('view','create','update','delete'), 'media': ('upload',),
    'enrollments': ('view','approve'), 'articles': ('view','create','update','delete','publish'),
    'live_sessions': ('view','create','update','delete','publish'), 'users': ('view','create','update','delete'),
    'roles': ('view','manage'), 'profile': ('view','update'),
}
PERMISSION_LABELS = {'view':'Lihat','create':'Buat','update':'Ubah','delete':'Hapus','publish':'Terbitkan','approve':'Setujui akses','manage':'Kelola izin','upload':'Unggah'}
ALL_PERMISSIONS = {f'{resource}.{action}': (resource, action) for resource, actions in RESOURCE_ACTIONS.items() for action in actions}
def connect():
    # Keep this compatibility wrapper: handlers and schema migrations retain
    # their established entry point while persistence is owned by repository.
    return DATABASE_REPOSITORY.connect()

def permission_for(method,path,form=None):
    form=form or {}
    if method=='POST' and path in ('/admin/menu/simpan','/admin/menu/akses-role','/admin/menu/urut','/admin/menu/hapus'): return 'roles.manage'
    if path=='/admin/akses-role': return 'roles.view' if method=='GET' else None
    if path=='/admin/akses-role/simpan': return 'roles.manage' if method=='POST' else None
    if path.startswith('/admin/menu/') and method=='POST': return 'roles.manage'
    if not path.startswith('/admin'): return None
    if method=='GET':
        if path=='/admin': return 'dashboard.view'
        if path=='/admin/program': return 'programs.view'
        if path=='/admin/permintaan-akses': return 'enrollments.view'
        if path=='/admin/blueprint-tryout': return 'question_banks.update'
        if path=='/admin/kategori-soal': return 'question_categories.view'
        if path.startswith('/media/'):
            return None
        if path=='/admin/bank-soal/blueprint': return 'question_banks.update'
        if re.fullmatch(r'/admin/bank-soal/\d+/blueprint',path): return 'question_banks.update'
        if path=='/admin/bank-soal/baru': return 'question_banks.create'
        if path=='/admin/bank-soal': return 'question_banks.view'
        if re.fullmatch(r'/admin/bank-soal/\d+/edit',path): return 'question_banks.update'
        if re.fullmatch(r'/admin/bank-soal/\d+/soal/baru',path): return 'questions.create'
        if re.fullmatch(r'/admin/bank-soal/soal/\d+/edit',path): return 'questions.update'
        if path.startswith('/admin/bank-soal/soal/'): return 'questions.view'
        if path.startswith('/admin/bank-soal/'): return 'question_banks.view'
        if path=='/admin/kursus/baru': return 'programs.create'
        if re.fullmatch(r'/admin/kursus/\d+/edit',path): return 'programs.update'
        if re.fullmatch(r'/admin/kursus/\d+/modul/baru',path): return 'modules.create'
        if re.fullmatch(r'/admin/modul/\d+/edit',path): return 'modules.update'
        if re.fullmatch(r'/admin/modul/\d+/pelajaran/baru',path): return 'lessons.create'
        if re.fullmatch(r'/admin/pelajaran/\d+/edit',path): return 'lessons.update'
        if path.startswith('/admin/kursus/'): return 'programs.view'
        if path.startswith('/admin/modul/'): return 'modules.view'
        if path.startswith('/admin/pelajaran/'): return 'lessons.view'
        if path.startswith('/admin/enrollment'): return 'enrollments.view'
        if path.startswith('/admin/artikel'): return 'articles.view'
        if path.startswith('/admin/jadwal') or path.startswith('/admin/live'): return 'live_sessions.view'
        if path.startswith('/admin/pengguna') or path.startswith('/admin/users'): return 'users.view'
        return 'dashboard.view' if path=='/admin' else None
    if method=='POST':
        if path in ('/admin/kategori-soal','/admin/kategori-soal/simpan'): return 'question_categories.update' if form.get('id') or form.get('category_id') else 'question_categories.create'
        if path=='/admin/kategori-soal/hapus': return 'question_categories.delete'
        if path=='/admin/blueprint-tryout' and form.get('_delete'): return 'question_banks.update'
        if path=='/admin/media/soal': return 'questions.update' if form.get('question_id') else 'questions.create'
        if path in ('/admin/bank-soal/blueprint/simpan','/admin/blueprint-tryout'): return 'question_banks.update'
        if path=='/admin/bank-soal/soal/masukkan': return 'questions.update'
        if path in ('/admin/kursus/simpan','/admin/programs/save'): return 'programs.update' if form.get('course_id') else 'programs.create'
        if path=='/admin/modul/simpan': return 'modules.update' if form.get('module_id') else 'modules.create'
        if path in ('/admin/pelajaran/simpan','/admin/lessons/save'): return 'lessons.update' if form.get('lesson_id') else 'lessons.create'
        if path=='/admin/enrollment/approve': return 'enrollments.approve'
        if path=='/admin/bank-soal/paket/simpan': return 'question_banks.update' if form.get('set_id') else 'question_banks.create'
        if path=='/admin/bank-soal/paket/hapus': return 'question_banks.delete'
        if path=='/admin/bank-soal/soal/simpan': return 'questions.update' if form.get('question_id') else 'questions.create'
        if path=='/admin/bank-soal/soal/hapus': return 'questions.delete'
        if path=='/admin/bank-soal/soal/urut': return 'questions.update'
        for prefix,resource in (('/admin/artikel/','articles'),('/admin/jadwal/','live_sessions'),('/admin/live/','live_sessions'),('/admin/pengguna/','users'),('/admin/users/','users')):
            if path.startswith(prefix):
                if path.endswith(('/hapus','/delete')): return resource+'.delete'
                if path.endswith(('/terbitkan','/publish')): return resource+'.publish'
                if resource=='users':return resource+('.update' if form.get('id') else '.create')
                return resource+('.update' if form.get('id') else '.create')
    return None

def required_permissions(method,path,form=None):
    form=form or {}; primary=permission_for(method,path,form)
    if not primary:return ()
    required=[primary]
    if method=='GET':
        for resource in ('programs','modules','lessons','question_banks','questions'):
            if primary.startswith(resource+'.') and primary!=resource+'.view':required.append(resource+'.view')
    if method=='POST' and path in ('/admin/kursus/simpan','/admin/programs/save') and form.get('status')=='published':required.append('programs.publish')
    if method=='POST' and path=='/admin/bank-soal/paket/simpan' and form.get('published')=='1':required.append('question_banks.publish')
    if method=='POST' and path=='/admin/media/soal':required.append('media.upload')
    return tuple(required)

def init_db():
    with connect() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE COLLATE NOCASE, password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'student', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS institutions(id INTEGER PRIMARY KEY, slug TEXT UNIQUE NOT NULL, name TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS programs(id INTEGER PRIMARY KEY, slug TEXT UNIQUE NOT NULL, title TEXT NOT NULL, summary TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', institution_id INTEGER REFERENCES institutions(id), category TEXT NOT NULL DEFAULT '', cover_url TEXT NOT NULL DEFAULT '', level TEXT NOT NULL DEFAULT 'Semua tingkat', duration TEXT NOT NULL DEFAULT '', price INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'draft', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS modules(id INTEGER PRIMARY KEY, program_id INTEGER NOT NULL REFERENCES programs(id) ON DELETE CASCADE, title TEXT NOT NULL, position INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS lessons(id INTEGER PRIMARY KEY, module_id INTEGER NOT NULL REFERENCES modules(id) ON DELETE CASCADE, title TEXT NOT NULL, body TEXT NOT NULL DEFAULT '', video_url TEXT NOT NULL DEFAULT '', resource_url TEXT NOT NULL DEFAULT '', duration_min INTEGER NOT NULL DEFAULT 0, position INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS packages(id INTEGER PRIMARY KEY, program_id INTEGER NOT NULL REFERENCES programs(id) ON DELETE CASCADE, title TEXT NOT NULL, price INTEGER NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS enrollments(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, program_id INTEGER NOT NULL REFERENCES programs(id) ON DELETE CASCADE, package_id INTEGER REFERENCES packages(id), status TEXT NOT NULL DEFAULT 'active', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(user_id,program_id));
        CREATE TABLE IF NOT EXISTS lesson_progress(user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE, completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(user_id,lesson_id));
        CREATE TABLE IF NOT EXISTS question_sets(id INTEGER PRIMARY KEY, slug TEXT UNIQUE NOT NULL, title TEXT NOT NULL, summary TEXT NOT NULL DEFAULT '', duration_min INTEGER NOT NULL DEFAULT 30, published INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS questions(id INTEGER PRIMARY KEY, set_id INTEGER NOT NULL REFERENCES question_sets(id) ON DELETE CASCADE, prompt TEXT NOT NULL, option_a TEXT NOT NULL, option_b TEXT NOT NULL, option_c TEXT NOT NULL, option_d TEXT NOT NULL, option_e TEXT NOT NULL DEFAULT '', answer TEXT NOT NULL, explanation TEXT NOT NULL DEFAULT '', position INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, set_id INTEGER NOT NULL REFERENCES question_sets(id), score INTEGER NOT NULL DEFAULT 0, total INTEGER NOT NULL DEFAULT 0, started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, finished_at TEXT);
        CREATE TABLE IF NOT EXISTS attempt_answers(attempt_id INTEGER NOT NULL REFERENCES attempts(id) ON DELETE CASCADE, question_id INTEGER NOT NULL REFERENCES questions(id), answer TEXT, correct INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(attempt_id,question_id));
        CREATE TABLE IF NOT EXISTS live_sessions(id INTEGER PRIMARY KEY, title TEXT NOT NULL, subject TEXT NOT NULL DEFAULT '', starts_at TEXT NOT NULL, duration_min INTEGER NOT NULL DEFAULT 90, mentor TEXT NOT NULL DEFAULT '', join_url TEXT NOT NULL DEFAULT '', published INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS articles(id INTEGER PRIMARY KEY, slug TEXT UNIQUE NOT NULL, title TEXT NOT NULL, summary TEXT NOT NULL DEFAULT '', body TEXT NOT NULL DEFAULT '', category TEXT NOT NULL DEFAULT '', published INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, csrf TEXT NOT NULL, expires_at INTEGER NOT NULL);
        ''')
        ensure_public_reference_schema(c)
        ensure_rbac_schema(c)
        ensure_question_schema(c)
        # Bridge the new question permissions into existing RBAC installations.
        for key,action,label in [('question_categories.view','view','Lihat kategori soal'),('question_categories.create','create','Buat kategori soal'),('question_categories.update','update','Ubah kategori soal'),('question_categories.delete','delete','Hapus kategori soal'),('media.upload','upload','Unggah media soal')]:
            menu=key.split('.')[0]
            c.execute('INSERT OR IGNORE INTO permissions(key,menu_key,label,action) VALUES (?,?,?,?)',(key,menu,label,action))
            for role in ('super_admin','admin','teacher','student'):
                enabled=int(role in ('super_admin','admin') or (role=='teacher' and key in ('question_categories.view','media.upload')))
                c.execute('INSERT OR IGNORE INTO role_permissions(role_key,permission_key,enabled) VALUES (?,?,?)',(role,key,enabled))
        program_cols={r['name'] for r in c.execute('PRAGMA table_info(programs)')}
        if 'category' not in program_cols:c.execute("ALTER TABLE programs ADD COLUMN category TEXT NOT NULL DEFAULT ''")
        if 'cover_url' not in program_cols:c.execute("ALTER TABLE programs ADD COLUMN cover_url TEXT NOT NULL DEFAULT ''")
        if c.execute('SELECT COUNT(*) FROM institutions').fetchone()[0]==0:
            c.executemany('INSERT INTO institutions(slug,name) VALUES (?,?)',[('stis','Polstat STIS'),('stan','PKN STAN'),('ipdn','IPDN'),('stmkg','STMKG')])
        if c.execute('SELECT COUNT(*) FROM programs').fetchone()[0]==0:
            stis=c.execute("SELECT id FROM institutions WHERE slug='stis'").fetchone()[0]
            c.execute("INSERT INTO programs(slug,title,summary,description,institution_id,category,level,duration,price,status) VALUES (?,?,?,?,?,?,?,?,?,?)",('persiapan-stis','Persiapan Polstat STIS','Program belajar terarah untuk menghadapi seleksi Polstat STIS.','Belajar konsep inti, latihan bertahap, tryout, dan pembahasan dalam satu program.',stis,'Polstat STIS','Pemula–Menengah','8 minggu',0,'published'))
            p=c.execute('SELECT id FROM programs WHERE slug=?',('persiapan-stis',)).fetchone()[0]
            m=c.execute('INSERT INTO modules(program_id,title,position) VALUES (?,?,?)',(p,'Fondasi numerik',1)).lastrowid
            c.execute('INSERT INTO lessons(module_id,title,body,video_url,duration_min,position) VALUES (?,?,?,?,?,?)',(m,'Memulai persiapan','Peta belajar dan cara menggunakan program ini.','https://www.youtube-nocookie.com/embed/VIDEO_ID',12,1))
        if c.execute('SELECT COUNT(*) FROM question_sets').fetchone()[0]==0:
            s=c.execute("INSERT INTO question_sets(slug,title,summary,duration_min,published) VALUES (?,?,?,?,1)",('latihan-tiu-dasar','Latihan TIU Dasar','Contoh latihan singkat untuk membiasakan diri dengan format soal.',10)).lastrowid
            c.execute('INSERT INTO questions(set_id,prompt,option_a,option_b,option_c,option_d,answer,explanation,position) VALUES (?,?,?,?,?,?,?,?,?)',(s,'Jika 3x + 4 = 19, nilai x adalah …','3','4','5','6','C','3x = 15, sehingga x = 5.',1))
        if c.execute('SELECT COUNT(*) FROM articles').fetchone()[0]==0:
            c.execute("INSERT INTO articles(slug,title,summary,body,category,published) VALUES (?,?,?,?,?,1)",('mulai-belajar','Cara memulai persiapan seleksi','Susun jadwal, pelajari konsep dasar, lalu ukur kemampuan dengan latihan rutin.','Mulai dari target yang jelas. Bagi materi menjadi sesi pendek, catat bagian yang belum dikuasai, dan evaluasi hasil latihan setiap pekan.','Strategi belajar'))
        # Seeded question sets above must also receive canonical bank/category links.
        ensure_question_schema(c)









def parse_post_body(handler):
    try:length=int(handler.headers.get('Content-Length','0'))
    except ValueError:length=0
    if length<0 or length>5*1024*1024+131072:raise ValueError('Ukuran unggahan melebihi batas 5 MB.')
    body=handler.rfile.read(length);ctype=handler.headers.get('Content-Type','')
    if ctype.lower().startswith('multipart/form-data'):
        raw=(f'Content-Type: {ctype}\r\nMIME-Version: 1.0\r\n\r\n').encode()+body
        msg=BytesParser(policy=email_policy).parsebytes(raw);form={};files={}
        for part in msg.iter_parts():
            name=part.get_param('name',header='content-disposition');filename=part.get_filename()
            if not name:continue
            payload=part.get_payload(decode=True) or b''
            if filename is not None:files[name]=(filename,part.get_content_type(),payload)
            else:form[name]=payload.decode(part.get_content_charset() or 'utf-8','replace')
        return form,files
    form={k:v[0] for k,v in parse_qs(body.decode('utf-8','replace'),keep_blank_values=True).items()}
    return form,{}


def bootstrap_admin():
    email=input('Email admin: ').strip().lower();name=input('Nama admin: ').strip() or 'Aster Admin';pw=getpass('Kata sandi (minimal 12 karakter): ')
    if len(pw)<12:raise SystemExit('Kata sandi minimal 12 karakter.')
    with connect() as c:
        c.execute("INSERT INTO users(name,email,password_hash,role) VALUES (?,?,?,'super_admin') ON CONFLICT(email) DO UPDATE SET role='super_admin'",(name,email,passhash(pw)))
    print('Super Admin siap. Jalankan kembali: python3 app.py')

