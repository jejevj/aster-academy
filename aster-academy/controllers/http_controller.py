from __future__ import annotations
from http.server import BaseHTTPRequestHandler
from core import *

class App(BaseHTTPRequestHandler):
    server_version='AsterAcademy/1.0'
    def send_html(self, body, status=200, cookies=()):
        b=body.encode(); self.send_response(status); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.send_header('X-Content-Type-Options','nosniff'); self.send_header('Referrer-Policy','strict-origin-when-cross-origin')
        for k,v in cookies: self.send_header('Set-Cookie',f'{k}={v}')
        self.end_headers(); self.wfile.write(b)
    def send_bytes(self, body, mime='application/octet-stream', status=200):
        self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(body)));self.send_header('X-Content-Type-Options','nosniff');self.send_header('Cache-Control','public, max-age=86400');self.end_headers();self.wfile.write(body)
    def send_json(self, payload, status=200):
        body=__import__('json').dumps(payload,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
    def redirect(self,url): self.send_response(303); self.send_header('Location',url); self.end_headers()
    def opaque_path(self, kind, object_id, pattern, conn=None):
        if conn is not None: token=ref_for(conn,kind,int(object_id))
        else:
            with connect() as c: token=ref_for(c,kind,int(object_id))
        if not token: raise ValueError(f'Referensi {kind} tidak ditemukan.')
        return pattern.format(token)
    def bank_path_for_set(self, set_id, suffix='', conn=None):
        if conn is None:
            with connect() as c: return self.bank_path_for_set(set_id,suffix,c)
        c=conn
        if c is not None:
            bank=c.execute('SELECT id FROM question_banks WHERE legacy_question_set_id=?',(set_id,)).fetchone()
            token=ref_for(c,'bank',bank['id']) if bank else None
        if not token: raise ValueError('Referensi bank tidak ditemukan.')
        return f'/admin/bank-soal/{token}{suffix}'
    def resolve_public_path(self,path):
        """Translate supported opaque route segments; reject numeric legacy URLs."""
        # This is a static create form route, not an opaque bank reference.
        # Keep it out of the generic /admin/bank-soal/{token} resolver.
        if path == '/admin/bank-soal/baru': return path
        # Lesson completion stays on its opaque route. POST resolves the token
        # to an internal database key only after the request reaches the handler.
        match=re.fullmatch(r'^/pelajaran/([^/]+)/selesai$',path)
        if match:
            with connect() as c: lesson_id=resolve_ref(c,'lesson',match.group(1))
            return path if lesson_id is not None else None
        patterns=[
            (r'^/admin/artikel/([^/]+)/edit$','article',r'/admin/artikel/{}/edit'),
            (r'^/admin/jadwal/([^/]+)/edit$','live_session',r'/admin/jadwal/{}/edit'),
            (r'^/admin/bank-soal/([^/]+)/blueprint$','bank',r'/admin/bank-soal/{}/blueprint'),
            (r'^/admin/bank-soal/([^/]+)/edit$','bank',r'/admin/bank-soal/{}/edit'),
            (r'^/admin/bank-soal/([^/]+)/soal/baru$','bank',r'/admin/bank-soal/{}/soal/baru'),
            (r'^/admin/bank-soal/soal/([^/]+)/edit$','question',r'/admin/bank-soal/soal/{}/edit'),
            (r'^/admin/bank-soal/([^/]+)$','bank',r'/admin/bank-soal/{}'),
            (r'^/admin/kursus/([^/]+)/edit$','course',r'/admin/kursus/{}/edit'),
            (r'^/admin/kursus/([^/]+)/modul/baru$','course',r'/admin/kursus/{}/modul/baru'),
            (r'^/admin/modul/([^/]+)/edit$','module',r'/admin/modul/{}/edit'),
            (r'^/admin/modul/([^/]+)/pelajaran/baru$','module',r'/admin/modul/{}/pelajaran/baru'),
            (r'^/admin/pelajaran/([^/]+)/edit$','lesson',r'/admin/pelajaran/{}/edit'),
            (r'^/tryout/([^/]+)/mulai$','tryout',r'/tryout/{}/mulai'),
            (r'^/tryout/([^/]+)/(soal|jawab|selesai)$','attempt',None),
            (r'^/tryout/result/([^/]+)$','attempt',r'/tryout/result/{}'),
        ]
        for pattern,kind,target in patterns:
            match=re.fullmatch(pattern,path)
            if not match:continue
            token=match.group(1)
            with connect() as c: object_id=resolve_ref(c,kind,token)
            if object_id is None:return None
            if kind=='bank':
                with connect() as c:
                    bank=c.execute('SELECT legacy_question_set_id FROM question_banks WHERE id=?',(object_id,)).fetchone()
                if not bank or bank['legacy_question_set_id'] is None:return None
                object_id=bank['legacy_question_set_id']
            if target:return target.format(object_id)
            return f'/tryout/{object_id}/{match.group(2)}'
        # Legacy numeric identifiers in object routes are never accepted.
        if re.match(r'^/(?:admin/bank-soal|admin/kursus|admin/modul|admin/pelajaran|admin/artikel|admin/jadwal|tryout|pelajaran)/\d+(?:/|$)',path):return None
        if re.fullmatch(r'^/(?:belajar|learn)/[^/]+/\d+$',path):return None
        return path
    def user(self):
        cookie=SimpleCookie(); cookie.load(self.headers.get('Cookie','')); tok=cookie.get(COOKIE)
        if not tok:return None
        with connect() as c:
            return c.execute('SELECT u.*,s.csrf FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>?',(hashlib.sha256(tok.value.encode()).hexdigest(),int(time.time()))).fetchone()
    def issue_session(self,user_id):
        raw=secrets.token_urlsafe(32); csrf=secrets.token_urlsafe(24)
        with connect() as c:c.execute('INSERT INTO sessions(token_hash,user_id,csrf,expires_at) VALUES (?,?,?,?)',(hashlib.sha256(raw.encode()).hexdigest(),user_id,csrf,int(time.time())+60*60*24*14))
        return [(COOKIE,raw+'; Path=/; HttpOnly; SameSite=Lax'),('aster_csrf',csrf+'; Path=/; SameSite=Lax')]
    def csrf_ok(self,form,user):
        cookie=SimpleCookie();cookie.load(self.headers.get('Cookie','')); c=cookie.get('aster_csrf')
        expected=user['csrf'] if user else (c.value if c else '')
        return bool(expected and secrets.compare_digest(form.get('csrf',form.get('csrf_token','')),expected))
    def can(self,user,permission):
        if not user or not permission:return False
        role=user['role']
        if role=='super_admin':return True
        if permission.startswith('roles.'):return False
        with connect() as c:
            return bool(c.execute('SELECT 1 FROM role_permissions WHERE role_key=? AND permission_key=? AND enabled=1',(role,permission)).fetchone())
    def admin_allowed(self,user,method,path,form=None):
        if not user:return False
        permissions=required_permissions(method,path,form)
        with connect() as c:
            menu_perm=route_permission(c,user['role'],path)
            if menu_perm is False:return False
            if menu_perm and user['role']!='super_admin' and not self.can(user,menu_perm):return False
        if not permissions:return bool(menu_perm)
        return all(self.can(user,p) for p in permissions)
    def sidebar_menu_html(self,conn,user,path):
        if not user:return ''
        from services.menu_service import visible_menus
        items=visible_menus(conn,user['role'])
        buckets={}
        for item in items:
            group=(item['group_name'] or 'Administrasi').strip() or 'Administrasi'
            buckets.setdefault(group,[]).append(item)
        preferred_groups=('Ringkasan','Pembelajaran','Evaluasi','Operasional','Pengaturan','Administrasi')
        groups=[group for group in preferred_groups if group in buckets]
        groups.extend(group for group in buckets if group not in groups)
        out=[]
        for group in groups:
            entries=buckets[group]
            links=[];active_group=False
            for item in entries:
                href=item['path']
                active=path==href or path.startswith(href.rstrip('/')+'/')
                active_group|=active
                icon=item['icon'] or '•'
                links.append(f'<a class="{"is-active" if active else ""}" href="{e(href)}"><span class="admin-icon" aria-hidden="true">{e(icon)}</span>{e(item["label"])}</a>')
            if group=='Ringkasan':out.extend(links)
            else:out.append(f'<details class="admin-nav-group" {"open" if active_group else ""}><summary>{e(group)}<span class="nav-chevron">⌄</span></summary><div class="admin-subnav">{"".join(links)}</div></details>')
        return ''.join(out)+'<a href="/"><span class="admin-icon" aria-hidden="true">↗</span>Lihat situs</a>'
    def role_matrix(self,conn):
        rows=[]
        for role,label in ROLE_LABELS.items():
            grants={r['permission_key'] for r in conn.execute('SELECT permission_key FROM role_permissions WHERE role_key=? AND enabled=1',(role,))}
            for resource,actions in RESOURCE_ACTIONS.items():
                cells=[]
                special=next((a for a in ('publish','approve','manage','upload') if a in actions),None)
                columns=('view','create','update','delete',special)
                for action in columns:
                    if action is None or action not in actions:
                        cells.append('<td><span class="locked">—</span></td>')
                        continue
                    key=f'{resource}.{action}'
                    if role=='super_admin':
                        cell='<span class="locked">Selalu aktif</span>'
                    elif resource=='roles':
                        cell='<span class="locked">Super Admin saja</span>'
                    else:
                        checked=' checked' if key in grants else ''
                        cell=f'<input type="checkbox" name="permission_{role}_{resource}_{action}" value="1" aria-label="{e(label)} · {e(resource)} · {e(PERMISSION_LABELS[action])}"{checked}>'
                    cells.append(f'<td>'+cell+'</td>')
                rows.append(f'<tr><th scope="row">{e(label)} · {e(resource.replace("_"," ").title())}</th>'+''.join(cells)+'</tr>')
        return ''.join(rows)
    def breadcrumb(self,path):
        trails={
            '/admin':('Ikhtisar',),'/admin/program':('Pembelajaran','Program'),
            '/admin/permintaan-akses':('Pembelajaran','Permintaan akses'),
            '/admin/kategori-soal':('Evaluasi','Kategori Soal'),
            '/admin/akses-role':('Pengaturan','Akses & Role'),'/profil':('Pengaturan','Profil'),
        }
        if path.startswith('/admin/bank-soal'): trail=('Evaluasi','Bank Soal')
        else: trail=trails.get(path,('Administrasi',))
        items=['<a href="/admin">Admin</a>']+[f'<span aria-hidden="true">›</span><span>{e(label)}</span>' for label in trail]
        return ''.join(items)
    def template(self,name,values=None):
        p=TEMPLATES/(name+'.html')
        if not p.exists():return self.fallback(name,values or {})
        s=p.read_text(encoding='utf-8'); vals=dict(values or {})
        # Templates receive stable opaque URL references while numeric keys
        # remain available only for hidden POST fields and DB operations.
        token_sources={'SET_TOKEN':('SET_ID','bank'),'BANK_TOKEN':('BANK_ID','bank'),
            'COURSE_TOKEN':('COURSE_ID','course'),'MODULE_TOKEN':('MODULE_ID','module'),
            'LESSON_TOKEN':('LESSON_ID','lesson'),'QUESTION_TOKEN':('QUESTION_ID','question'),
            'TRYOUT_TOKEN':('TRYOUT_ID','tryout'),'ATTEMPT_TOKEN':('ATTEMPT_ID','attempt')}
        for token_name,(id_name,kind) in token_sources.items():
            raw=vals.get(id_name)
            if raw and str(raw).isdigit():
                with connect() as conn: vals[token_name]=ref_for(conn,kind,int(raw)) or ''
        # All admin screens share one sidebar component. Keeping the component
        # here lets legacy page templates retain their content while the
        # navigation and responsive behavior stay consistent.
        if name.startswith('admin_'):
            sidebar_path=TEMPLATES/'admin_sidebar.html'
            if sidebar_path.exists():
                sidebar=sidebar_path.read_text(encoding='utf-8')
                for key,value in vals.items(): sidebar=sidebar.replace('{{'+key+'}}',str(value))
                sidebar=re.sub(r'{{[A-Z0-9_]+}}','',sidebar)
                # Replace the first navigation aside regardless of legacy page
                # markup (some older pages used an unclassed <aside>).
                s,count=re.subn(r'<aside\b[^>]*>.*?</aside>',lambda _:sidebar,s,count=1,flags=re.S)
                if count:
                    s=s.replace('<div class="shell">','<div class="admin-shell">',1)
                    s=s.replace('<div class="main">','<div class="admin-main">',1)
                    if 'class="admin-backdrop"' not in s:
                        s=s.replace('<div class="admin-shell">','<div class="admin-backdrop" data-admin-close></div><div class="admin-shell">',1)
                    if 'data-admin-open' not in s:
                        s=s.replace('<header class="admin-topbar"><div>','<header class="admin-topbar"><div><button class="admin-mobile-trigger" type="button" aria-label="Buka menu" aria-controls="adminSidebar" aria-expanded="false" data-admin-open>☰</button>',1)
                        if 'data-admin-open' not in s:
                            s=s.replace('<header>','<header class="admin-topbar"><button class="admin-mobile-trigger" type="button" aria-label="Buka menu" aria-controls="adminSidebar" aria-expanded="false" data-admin-open>☰</button>',1)
                    if 'class="admin-page"' not in s:
                        s=s.replace('<main>','<main class="admin-page">',1)
                    shared_shell='''<style>
 .admin-shell{display:grid;grid-template-columns:264px minmax(0,1fr);min-height:100vh;background:#f6f8fc}.admin-sidebar{position:sticky;top:0;display:flex;height:100vh;flex-direction:column;border-right:1px solid #e2eaf4;background:#fff;padding:22px 16px}.admin-brand{display:flex;align-items:center;gap:11px;padding:2px 9px 26px;color:#15345d;font-weight:800}.admin-mark{display:grid;width:38px;height:38px;place-items:center;border-radius:12px;background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#fff;font-weight:800}.admin-label{padding:0 11px;color:#94a3b8;font-size:10px;font-weight:800;letter-spacing:.16em}.admin-nav{display:grid;gap:5px;margin-top:10px}.admin-nav a{display:flex;align-items:center;gap:11px;border-radius:11px;padding:11px;color:#52657f;font-size:14px;font-weight:650;text-decoration:none}.admin-nav a:hover,.admin-nav a.is-active{background:#eff6ff;color:#1d4ed8}.admin-nav-group{margin-top:6px}.admin-nav-group>summary{display:flex;align-items:center;gap:11px;padding:9px 11px;border-radius:11px;color:#52657f;font-size:14px;font-weight:700;cursor:pointer;list-style:none}.admin-nav-group>summary::-webkit-details-marker{display:none}.admin-nav-group>summary:hover{background:#f4f7fb}.nav-chevron{margin-left:auto;transition:transform .18s}.admin-nav-group[open] .nav-chevron{transform:rotate(180deg)}.admin-subnav{display:grid;gap:3px;margin:3px 0 8px 38px;padding-left:11px;border-left:1px solid #dce6f2}.admin-subnav a{padding:8px 10px;font-size:13px}.admin-breadcrumb{display:flex;align-items:center;gap:8px;margin:0 0 22px;color:#64748b;font-size:13px}.admin-breadcrumb a{color:#2563eb;font-weight:650}.admin-breadcrumb span:last-child{color:#15345d;font-weight:700}.admin-icon{display:grid;width:27px;height:27px;place-items:center;border-radius:8px;background:#f1f5f9;color:#52657f}.admin-nav a.is-active .admin-icon{background:#dbeafe;color:#1d4ed8}.admin-side-bottom{margin-top:auto;border-top:1px solid #edf1f6;padding:16px 8px 2px}.admin-user{overflow:hidden;color:#15345d;font-size:13px;font-weight:700;text-overflow:ellipsis;white-space:nowrap}.admin-side-bottom a{display:block;margin-top:11px;color:#64748b;font-size:12px}.admin-main{min-width:0}.admin-page{max-width:1440px;margin:0 auto;padding:34px clamp(20px,4vw,48px) 60px}.admin-mobile-trigger,.admin-backdrop{display:none}.admin-group-title{display:block;margin:18px 10px 5px;color:#94a3b8;font-size:10px;font-weight:800;letter-spacing:.14em;text-transform:uppercase}
@media(max-width:1040px){.admin-shell{grid-template-columns:1fr!important}.admin-sidebar{position:fixed!important;z-index:40!important;inset:0 auto 0 0!important;width:min(300px,86vw)!important;height:100dvh!important;transform:translateX(-105%);transition:transform .22s ease;box-shadow:12px 0 40px rgba(15,35,68,.18);overflow-y:auto}.admin-sidebar.is-open{transform:translateX(0)}.admin-backdrop{position:fixed;z-index:35;inset:0;display:block;background:rgba(15,35,68,.48);opacity:0;visibility:hidden;transition:opacity .2s}.admin-backdrop.is-visible{opacity:1;visibility:visible}.admin-side-bottom{display:block!important}.admin-mobile-logout{display:none!important}.admin-nav{display:grid!important;gap:4px!important;margin-top:8px!important}.admin-nav a{flex:auto!important;white-space:normal!important}.admin-topbar{position:sticky!important;min-height:62px}.admin-mobile-trigger{display:inline-flex;align-items:center;justify-content:center;width:40px;height:40px;margin-right:10px;border:1px solid #dce6f2;border-radius:11px;background:#fff;color:#1d4ed8;font-size:20px}.admin-group-title{display:block!important}}
@media(min-width:1041px){.admin-mobile-trigger,.admin-backdrop{display:none!important}.admin-group-title{display:block;margin:18px 10px 5px;color:#94a3b8;font-size:10px;font-weight:800;letter-spacing:.14em;text-transform:uppercase}}
</style><script>(()=>{const side=document.querySelector('#adminSidebar'),shade=document.querySelector('.admin-backdrop'),open=document.querySelector('[data-admin-open]');if(!side||!shade||!open)return;const close=()=>{side.classList.remove('is-open');shade.classList.remove('is-visible');open.setAttribute('aria-expanded','false');document.body.style.overflow=''};open.addEventListener('click',()=>{side.classList.add('is-open');shade.classList.add('is-visible');open.setAttribute('aria-expanded','true');document.body.style.overflow='hidden'});shade.addEventListener('click',close);document.addEventListener('keydown',e=>{if(e.key==='Escape')close()});side.querySelectorAll('a').forEach(a=>a.addEventListener('click',close))})();</script>'''
                    s=s.replace('</head>',shared_shell+'</head>',1)
        for k,v in vals.items():s=s.replace('{{'+k+'}}',str(v))
        s=re.sub(r'{{[A-Z0-9_]+}}','',s)
        crumb=vals.get('ADMIN_BREADCRUMB','')
        if name.startswith('admin_') and crumb and '<nav class="admin-breadcrumb"' not in s:
            s=s.replace('<main class="admin-page">','<main class="admin-page"><nav class="admin-breadcrumb" aria-label="Breadcrumb">'+str(crumb)+'</nav>',1)
        csrf=vals.get('CSRF_TOKEN','')
        if csrf:s=re.sub(r'(<form\b(?=[^>]*\bmethod="post")[^>]*>)',lambda m:m.group(1) if ('name="csrf"' in m.group(1) or 'name="csrf_token"' in m.group(1)) else m.group(1)+f'<input type="hidden" name="csrf" value="{e(csrf)}">',s,flags=re.I)
        return self.opaque_urls(s)
    def opaque_urls(self, markup):
        """Convert generated legacy href/action paths to stable opaque refs."""
        patterns=[
            (r'(/admin/bank-soal/)(\d+)(/blueprint|/edit|/soal/baru|)', 'bank'),
            (r'(/admin/bank-soal/soal/)(\d+)(/edit)', 'question'),
            (r'(/admin/kursus/)(\d+)(/edit|/modul/baru)', 'course'),
            (r'(/admin/modul/)(\d+)(/edit|/pelajaran/baru)', 'module'),
            (r'(/admin/pelajaran/)(\d+)(/edit)', 'lesson'),
            (r'(/tryout/)(\d+)(/mulai|/soal|/jawab|/selesai)', None),
            (r'(/tryout/result/)(\d+)(?=[\"?])', 'attempt'),
            (r'(/pelajaran/)(\d+)(/selesai)', 'lesson'),
        ]
        for pattern,kind in patterns:
            def repl(m):
                raw=m.group(2); k=kind or ('tryout' if m.group(3)=='/mulai' else 'attempt')
                with connect() as c:
                    object_id=int(raw)
                    if k=='bank':
                        row=c.execute('SELECT id FROM question_banks WHERE legacy_question_set_id=?',(object_id,)).fetchone()
                        object_id=row['id'] if row else -1
                    token=ref_for(c,k,object_id)
                return (m.group(1)+token+m.group(3)) if token else m.group(0)
            markup=re.sub(pattern,repl,markup)
        return markup
    def fallback(self,title,values):
        body=values.get('CONTENT','')
        return f'''<!doctype html><html lang="id"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)} · Aster Academy</title><script src="https://cdn.tailwindcss.com"></script><style>body{{background:#07152d}}.glass{{background:#ffffff0d;border:1px solid #ffffff20;backdrop-filter:blur(16px)}}</style></head><body class="min-h-screen text-white"><header class="mx-auto flex max-w-6xl justify-between p-6"><a href="/" class="font-bold">Aster Academy</a><nav class="flex gap-4 text-sm"><a href="/programs">Program</a><a href="/tryouts">Tryout</a><a href="/schedule">Jadwal</a><a href="/articles">Artikel</a><a href="/dashboard">Dashboard</a><a href="/admin">Admin</a></nav></header><main class="mx-auto max-w-6xl px-6 py-10"><h1 class="text-4xl font-bold">{e(title)}</h1>{body}</main></body></html>'''
    def get(self, path, query):
        assets={
            '/static/question-tables.js':('static/question-tables.js','text/javascript; charset=utf-8'),
            '/static/question-tables.css':('static/question-tables.css','text/css; charset=utf-8'),
        }
        if path in assets:
            asset,mime=assets[path]
            try: body=(BASE/asset).read_bytes()
            except OSError:self.send_html('Not found',404);return
            self.send_bytes(body,mime);return
        resolved=self.resolve_public_path(path)
        if resolved is None:self.send_html('Not found',404);return
        path=resolved
        u=self.user(); csrf=u['csrf'] if u else secrets.token_urlsafe(24); setcookie=[]
        if not u:
            c=SimpleCookie();c.load(self.headers.get('Cookie',''))
            if not c.get('aster_csrf'):setcookie=[('aster_csrf',csrf+'; Path=/; SameSite=Lax')]
            else:csrf=c['aster_csrf'].value
        def send(name,values=None,status=200):
            roles={'DASHBOARD':'dashboard.view','PROGRAM':'programs.view','PROGRAM_CREATE':'programs.create','MODULE':'modules.view','LESSON':'lessons.view','BANK':'question_banks.view','BANK_CREATE':'question_banks.create','QUESTION':'questions.view','QUESTION_CREATE':'questions.create','CATEGORIES':'question_categories.view','BLUEPRINT':'question_banks.update','ENROLLMENTS':'enrollments.view','ARTICLE':'articles.view','LIVE':'live_sessions.view','USERS':'users.view','ROLES':'roles.view','PROFILE':'profile.view'}
            nav={f'NAV_{key}_CLASS':('' if self.can(u,perm) and (key!='ROLES' or (u and u['role']=='super_admin')) else 'hidden') for key,perm in roles.items()}
            profile_allowed=bool(u and (u['role']=='super_admin' or self.can(u,'profile.view')))
            base={'CSRF_TOKEN':e(csrf),'USER_NAME':e(u['name'] if u else ''),'USER_EMAIL':e(u['email'] if u else ''),'USER_ROLE_LABEL':ROLE_LABELS.get(u['role'],'Student / Mentee') if u else '', 'ADMIN_DASHBOARD_ACTIVE':'is-active' if path=='/admin' else '','ADMIN_PROGRAM_ACTIVE':'is-active' if path=='/admin/program' else '','ADMIN_ENROLLMENT_ACTIVE':'is-active' if path=='/admin/permintaan-akses' else '','ADMIN_CATEGORY_ACTIVE':'is-active' if path=='/admin/kategori-soal' else '','ADMIN_ROLES_ACTIVE':'is-active' if path=='/admin/akses-role' else '','ADMIN_BANK_ACTIVE':'is-active' if path.startswith('/admin/bank-soal') else '','ADMIN_PROFILE_ACTIVE':'is-active' if path=='/profil' else '','BANK_UPDATE_CLASS':'' if self.can(u,'question_banks.update') else 'hidden','BANK_DELETE_CLASS':'' if self.can(u,'question_banks.delete') else 'hidden','QUESTION_CREATE_CLASS':'' if self.can(u,'questions.create') else 'hidden','QUESTION_UPDATE_CLASS':'' if self.can(u,'questions.update') else 'hidden','QUESTION_DELETE_CLASS':'' if self.can(u,'questions.delete') else 'hidden','PUBLIC_AUTH_ACTIONS':('<a href="/profil" class="btn-secondary text-sm">Profil</a>' if profile_allowed else ('<a href="/masuk" class="btn-secondary text-sm">Masuk</a><a href="/daftar" class="btn text-sm">Daftar gratis</a>' if not u else '')),'ADMIN_LEARNING_OPEN':'open' if path in ('/admin/program','/admin/permintaan-akses') or path.startswith('/admin/kursus') else '', 'ADMIN_EVALUATION_OPEN':'open' if path.startswith(('/admin/bank-soal','/admin/kategori-soal','/admin/blueprint-tryout')) else '', 'ADMIN_SETTINGS_OPEN':'open' if path in ('/admin/akses-role','/profil') else '', 'ADMIN_BREADCRUMB':self.breadcrumb(path), 'SIDEBAR_MENU_TREE':self.sidebar_menu_html(c,u,path), 'YEAR':'2026',**nav}
            rendered=self.template(name,{**base,**(values or {})})
            if name=='admin_dashboard':
                if not self.can(u,'programs.view') or path=='/admin/permintaan-akses': rendered=re.sub(r'<section id="programs".*?</section>','',rendered,flags=re.S)
                if not self.can(u,'enrollments.view') or path=='/admin/program': rendered=re.sub(r'<section id="requests".*?</section>','',rendered,flags=re.S)
                if path in ('/admin/program','/admin/permintaan-akses'):
                    rendered=re.sub(r'<div class="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">.*?</div>','',rendered,count=1,flags=re.S)
                    label='Program' if path=='/admin/program' else 'Permintaan akses'
                    rendered=rendered.replace('Dashboard admin',label,1).replace('Ringkasan aktivitas Aster Academy.','Kelola '+label.lower()+'.',1)
            self.send_html(rendered,status,setcookie)
        if path.startswith('/admin') and not self.admin_allowed(u,'GET',path):
            if not u:self.redirect('/masuk');return
            self.send_html('Forbidden',403);return
        with connect() as c:
            vendor_assets={
                '/assets/vendor/datatables/jquery-3.7.1.min.js':('static/vendor/datatables/jquery-3.7.1.min.js','text/javascript; charset=utf-8'),
                '/assets/vendor/datatables/dataTables.min.js':('static/vendor/datatables/dataTables.min.js','text/javascript; charset=utf-8'),
                '/assets/vendor/datatables/dataTables.dataTables.min.css':('static/vendor/datatables/dataTables.dataTables.min.css','text/css; charset=utf-8'),
            }
            if path in vendor_assets:
                relative,mime=vendor_assets[path]
                asset_path=BASE/relative
                if not asset_path.is_file():self.send_html('Not found',404);return
                self.send_bytes(asset_path.read_bytes(),mime);return
            if path.startswith('/media/'):
                filename=path.rsplit('/',1)[-1]
                if not re.fullmatch(r'[a-f0-9]{32}\.(?:png|jpg|webp|gif)',filename):self.send_html('Not found',404);return
                asset=c.execute('SELECT storage_key,mime_type FROM media_assets WHERE storage_key=?',(filename,)).fetchone()
                file_path=BASE/'media'/filename
                if not asset or not file_path.is_file():self.send_html('Not found',404);return
                self.send_bytes(file_path.read_bytes(),asset['mime_type']);return
            if path=='/':
                rows=c.execute("SELECT p.*,i.name institution FROM programs p LEFT JOIN institutions i ON i.id=p.institution_id WHERE p.status='published' ORDER BY p.id DESC").fetchall()
                featured=rows[0] if rows else None
                sessions=c.execute('SELECT * FROM live_sessions WHERE published=1 AND starts_at>=datetime("now") ORDER BY starts_at LIMIT 3').fetchall()
                articles=c.execute('SELECT * FROM articles WHERE published=1 ORDER BY created_at DESC LIMIT 3').fetchall()
                session_cards=''.join(f'<article class="rounded-2xl border border-slate-200 bg-white p-5"><p class="tag">{e(x["subject"])}</p><h3 class="mt-3 text-lg font-bold text-[#15345d]">{e(x["title"])}</h3><p class="muted mt-2 text-sm">{e(x["starts_at"])} · {x["duration_min"]} menit · {e(x["mentor"])}</p></article>' for x in sessions) or '<p class="muted rounded-2xl border border-dashed border-slate-300 p-6 md:col-span-3">Jadwal kelas berikutnya akan diumumkan di sini.</p>'
                article_cards=''.join(f'<a class="rounded-2xl border border-slate-200 bg-white p-5 transition hover:border-blue-300" href="/artikel/{e(x["slug"])}"><p class="text-sm font-bold text-blue-700">{e(x["category"])}</p><h3 class="mt-3 text-lg font-bold text-[#15345d]">{e(x["title"])}</h3><p class="muted mt-2 text-sm leading-6">{e(x["summary"])}</p></a>' for x in articles) or '<p class="muted rounded-2xl border border-dashed border-slate-300 p-6 md:col-span-3">Panduan belajar akan segera hadir.</p>'
                send('home',{'COURSE_COUNT':str(len(rows)),'TRYOUT_COUNT':str(c.execute('SELECT COUNT(*) FROM question_sets WHERE published=1').fetchone()[0]),'COURSE_CARDS':self.cards(rows,'program'),'UPCOMING_SESSIONS':session_cards,'LATEST_ARTICLES':article_cards,'FEATURED_COURSE_TITLE':e(featured['title'] if featured else 'Pilih program pertamamu'),'FEATURED_COURSE_DESCRIPTION':e(featured['summary'] if featured else 'Jelajahi program belajar Aster.'),'FEATURED_COURSE_SLUG':e(featured['slug'] if featured else ''),'FEATURED_PROGRESS':'0'});return
            if path in ('/program','/programs','/courses'):
                term=query.get('q',[''])[0];sql="SELECT p.*,i.name institution FROM programs p LEFT JOIN institutions i ON i.id=p.institution_id WHERE p.status='published'"; args=[]
                category=query.get('category',[''])[0]
                if term:sql+=' AND (p.title LIKE ? OR p.summary LIKE ? OR i.name LIKE ?)';args.extend([f'%{term}%']*3)
                if category:sql+=' AND (p.category=? OR i.slug=?)';args.extend([category,category])
                rows=c.execute(sql+' ORDER BY p.id DESC',args).fetchall();cats=c.execute("SELECT DISTINCT category FROM programs WHERE category<>'' AND status='published' ORDER BY category").fetchall();opts=''.join(f'<option value="{e(x["category"])}" {"selected" if category==x["category"] else ""}>{e(x["category"])}</option>' for x in cats);grid='mx-auto max-w-2xl' if len(rows)<=1 else ('mx-auto max-w-5xl sm:grid-cols-2' if len(rows)==2 else 'md:grid-cols-2 lg:grid-cols-3');send('program_catalog',{'COURSE_CARDS':self.cards(rows,'program'),'COURSE_GRID_CLASS':grid,'QUERY':e(term),'CATEGORY_OPTIONS':opts});return
            if path.startswith('/program/') or path.startswith('/programs/'):
                slug=path.split('/')[-1];p=c.execute("SELECT p.*,i.name institution FROM programs p LEFT JOIN institutions i ON i.id=p.institution_id WHERE p.slug=? AND p.status='published'",(slug,)).fetchone()
                if not p:self.send_html('Not found',404);return
                mods=c.execute('SELECT * FROM modules WHERE program_id=? ORDER BY position,id',(p['id'],)).fetchall(); blocks=[]
                for m in mods:
                    ls=c.execute('SELECT * FROM lessons WHERE module_id=? ORDER BY position,id',(m['id'],)).fetchall();blocks.append(f'<details class="glass card" open><summary class="cursor-pointer font-semibold">{e(m["title"])}</summary><ul class="mt-3 space-y-2">'+''.join(f'<li class="text-sm text-slate-300">{e(x["title"])} <span class="muted">· {x["duration_min"]} menit</span></li>' for x in ls)+'</ul></details>')
                lesson_count=c.execute('SELECT COUNT(*) FROM lessons l JOIN modules m ON m.id=l.module_id WHERE m.program_id=?',(p['id'],)).fetchone()[0]
                outcomes=''.join(f'<li>• {e(x)}</li>' for x in ['Memahami konsep inti dan strategi pengerjaan.','Berlatih dengan materi bertahap dan evaluasi rutin.','Mengenali area yang perlu diperdalam.'])
                status=c.execute('SELECT status FROM enrollments WHERE user_id=? AND program_id=?',(u['id'],p['id'])).fetchone() if u else None
                send('program_detail',{'COURSE_TITLE':e(p['title']),'COURSE_DESCRIPTION':e(p['description'] or p['summary']),'COURSE_CATEGORY':e(p['category'] or p['institution'] or 'Persiapan seleksi'),'COURSE_LEVEL':e(p['level']),'COURSE_DURATION':e(p['duration']),'COURSE_PRICE_LABEL':money(p['price']),'COURSE_ID':str(p['id']),'COURSE_LESSON_COUNT':str(lesson_count),'MODULE_LIST':'\n'.join(blocks),'LEARNING_OUTCOMES':outcomes,'COURSE_ACCESS_NOTE':'Pendaftaran akses tanpa pembayaran di MVP.','COURSE_ENROLL_NOTE':'Akses aktif setelah disetujui admin.','ENROLL_BUTTON_LABEL':'Minta akses program' if not status else ('Akses sedang ditinjau' if status['status']=='pending' else 'Program ada di dashboard')});return
            if path in ('/tryout','/tryouts'):
                term=query.get('q',[''])[0];rows=c.execute('SELECT s.*,COUNT(q.id) question_count FROM question_sets s LEFT JOIN questions q ON q.set_id=s.id WHERE s.published=1 AND s.title LIKE ? GROUP BY s.id ORDER BY s.id DESC',(f'%{term}%',)).fetchall();send('tryout_catalog',{'TRYOUT_CARDS':self.cards(rows,'tryout'),'QUERY':e(term)});return
            if path.startswith('/tryout/result/'):
                if not u:self.redirect('/masuk');return
                aid=path.split('/')[-1];a=c.execute('SELECT a.*,s.title FROM attempts a JOIN question_sets s ON s.id=a.set_id WHERE a.id=? AND a.user_id=?',(aid,u['id'])).fetchone()
                if not a:self.send_html('Not found',404);return
                attempt_items=c.execute('SELECT aq.*,aa.answer,aa.awarded_score FROM attempt_questions aq LEFT JOIN attempt_answers aa ON aa.attempt_id=aq.attempt_id AND aa.question_id=aq.question_id WHERE aq.attempt_id=? ORDER BY aq.position',(aid,)).fetchall()
                if attempt_items:
                    def _render_item(aq_row):
                        snap = json.loads(aq_row['question_snapshot'])
                        scoring = json.loads(aq_row['scoring_snapshot'])
                        prompt_html = sanitize_rich_html(snap.get('prompt', ''))
                        ans_user = e(aq_row['answer'] or 'Kosong')
                        ans_key = e(snap.get('answer', '—'))
                        awarded = e(aq_row['awarded_score'] if aq_row['awarded_score'] is not None else 0)
                        expl_html = sanitize_rich_html(snap.get('explanation', ''))
                        return f'<article class="glass card"><div class="question-rich">{prompt_html}</div><p class="muted mt-2 text-sm">Jawaban kamu: {ans_user} · Kunci: {ans_key} · Poin: {awarded}</p><div class="muted mt-2 text-sm">{expl_html}</div></article>'
                    blocks = ''.join(_render_item(x) for x in attempt_items)
                else:
                    review=c.execute('SELECT q.prompt,q.explanation,aa.answer,aa.correct,q.answer correct_answer FROM attempt_answers aa JOIN questions q ON q.id=aa.question_id WHERE aa.attempt_id=? ORDER BY q.position',(aid,)).fetchall();blocks=''.join(f'<article class="glass card"><p class="font-semibold">{e(x["prompt"])}</p><p class="muted mt-2 text-sm">Jawaban kamu: {e(x["answer"] or "Belum dijawab")} · Kunci: {e(x["correct_answer"])}</p><p class="muted mt-2 text-sm">{e(x["explanation"])}</p></article>' for x in review)
                rule_snapshot=json.loads(a['rule_snapshot'] or '{}');breakdown=json.loads(a['score_breakdown_snapshot'] or '{}');category_rules=rule_snapshot.get('categories',{});thresholds=rule_snapshot.get('thresholds',[]);profile_meta=rule_snapshot.get('profile') or {};score_cards=[];threshold_checks=[];quota_mismatch=False
                for key,value in breakdown.items():
                    rule=category_rules.get(str(key),{});category_name=rule.get('name') or c.execute('SELECT name FROM question_categories WHERE id=?',(key,)).fetchone()
                    if isinstance(category_name,sqlite3.Row):category_name=category_name['name']
                    if not category_name:category_name='Kategori'
                    passing=rule.get('passing_score')
                    quota_matches=(value.get('count',0)==rule.get('item_count')==rule.get('selected_count'))
                    if passing is not None and quota_matches:
                        status=f'· Ambang {passing} {"tercapai" if value["score"]>=passing else "belum tercapai"}';threshold_checks.append(value['score']>=passing)
                    elif passing is not None:
                        status=f'· Ambang profil perlu {rule.get("item_count")} soal';quota_mismatch=True
                    else:status='· Tanpa ambang kategori'
                    score_cards.append(f'<article class="glass card"><p class="muted text-sm">{e(category_name)}</p><p class="mt-1 text-2xl font-extrabold">{value["score"]} <span class="muted text-sm font-semibold">/ {value["max_score"]}</span></p><p class="muted mt-1 text-xs">{value["answered"]} soal dijawab {status}</p></article>')
                total_count=sum(int(x.get('count',0)) for x in breakdown.values())
                total_quota_matches=bool(profile_meta and total_count==profile_meta.get('total_questions') and int(a['total'])==profile_meta.get('max_score'))
                for threshold in thresholds:
                    if threshold['category_id'] is not None or int(threshold['minimum_score'])<=0:continue
                    if not total_quota_matches:quota_mismatch=True;continue
                    met=a['score']>=threshold['minimum_score'];threshold_checks.append(met);score_cards.append(f'<article class="glass card"><p class="muted text-sm">{e(threshold["label"])}</p><p class="mt-1 text-2xl font-extrabold">{a["score"]} <span class="muted text-sm font-semibold">/ minimal {threshold["minimum_score"]}</span></p><p class="muted mt-1 text-xs">{ "Target tercapai" if met else "Target belum tercapai" }</p></article>')
                summary_cards='<div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">'+''.join(score_cards)+'</div>' if score_cards else ''
                if a['rule_profile_id'] and threshold_checks:
                    result_headline='Semua ambang profil tercapai' if all(threshold_checks) else 'Masih ada ambang yang belum tercapai'
                    result_summary='Ringkasan ini membandingkan skor latihan dengan profil aturan yang dipilih; hasilnya bukan keputusan seleksi resmi.'
                elif a['rule_profile_id'] and quota_mismatch:
                    result_headline='Skor latihan tersimpan';result_summary='Ambang profil tidak dibandingkan karena jumlah soal atau nilai maksimum sesi berbeda dari profil aturan.'
                else:result_headline='Hasil latihanmu';result_summary='Tinjau skor per kategori dan pelajari pembahasan untuk memperkuat pemahaman.'
                send('tryout_results',{'TRYOUT_TITLE':e(a['title']),'SCORE':str(a['score']),'MAX_SCORE':str(a['total']),'RESULT_LABEL':f'{round(100*a["score"]/max(a["total"],1))}% dari nilai maksimum','RESULT_HEADLINE':result_headline,'RESULT_SUMMARY':result_summary,'COMPLETED_AT':e(a['finished_at'] or a['started_at']),'TIME_SPENT':'—','SECTION_RESULTS':summary_cards+blocks});return
            if path.startswith('/tryout/') and path.endswith('/soal'):
                if not u:self.redirect('/masuk');return
                aid=path.strip('/').split('/')[1];a=c.execute('SELECT * FROM attempts WHERE id=? AND user_id=?',(aid,u['id'])).fetchone()
                if not a:self.send_html('Not found',404);return
                if a['finished_at']:self.redirect(self.opaque_path('attempt',aid,'/tryout/result/{}',c));return
                aqs=c.execute('SELECT aq.*,q.answer FROM attempt_questions aq LEFT JOIN questions q ON q.id=aq.question_id WHERE aq.attempt_id=? ORDER BY aq.position',(aid,)).fetchall()
                len_qs = 0
                if aqs:
                    idx = max(1, min(int(query.get('n', ['1'])[0]), len(aqs)))
                    aq = aqs[idx - 1]
                    qjson = json.loads(aq['question_snapshot'])
                    optjson = json.loads(aq['options_snapshot'])
                    qid = aq['question_id']
                    prev = c.execute('SELECT answer FROM attempt_answers WHERE attempt_id=? AND question_id=?', (aid, qid)).fetchone()
                    opt_list = []
                    for letter in 'ABCDE':
                        text_val = optjson.get(letter)
                        if text_val:
                            checked_attr = 'checked' if (prev and prev['answer'] == letter) else ''
                            sanitized_text = sanitize_rich_html(text_val)
                            opt_list.append(f'<label class="glass flex cursor-pointer gap-3 rounded-xl p-4"><input type="radio" name="answer" value="{letter}" {checked_attr}><span><b>{letter}.</b> {sanitized_text}</span></label>')
                    opts = ''.join(opt_list)
                    question_html = sanitize_rich_html(qjson.get('prompt', ''))
                else:
                    qs=c.execute('SELECT * FROM questions WHERE set_id=? ORDER BY position,id',(a['set_id'],)).fetchall()
                    if not qs:self.send_html('Tryout ini belum memiliki soal.',409);return
                    idx=max(1,min(int(query.get('n',['1'])[0]),len(qs)));q=qs[idx-1];qid=q['id'];prev=c.execute('SELECT answer FROM attempt_answers WHERE attempt_id=? AND question_id=?',(aid,qid)).fetchone();opts=''.join(f'<label class="glass flex cursor-pointer gap-3 rounded-xl p-4"><input type="radio" name="answer" value="{letter}" {"checked" if prev and prev["answer"]==letter else ""}><span><b>{letter}.</b> {sanitize_rich_html(q["option_"+letter.lower()])}</span></label>' for letter in 'ABCDE' if q['option_'+letter.lower()]);question_html=sanitize_rich_html(q['content_html'] or q['prompt']);len_qs=len(qs)
                title=c.execute('SELECT title FROM question_sets WHERE id=?',(a['set_id'],)).fetchone()['title'];total_questions=len(aqs) if aqs else len_qs;remaining=attempt_seconds_remaining(c,a);send('tryout_player',{'TRYOUT_TITLE':e(title),'SECTION_TITLE':'Latihan','TIME_REMAINING':f'{remaining//60:02}:{remaining%60:02}','TIME_REMAINING_SECONDS':str(remaining),'QUESTION_NUMBER':str(idx),'QUESTION_TOTAL':str(total_questions),'SECTION_PROGRESS':str(round(idx*100/max(total_questions,1))),'QUESTION_TEXT':question_html,'ANSWER_OPTIONS':opts,'ATTEMPT_ID':str(aid),'ATTEMPT_TOKEN':ref_for(c,'attempt',aid),'CSRF_TOKEN':e(csrf),'QUESTION_ID':str(qid)});return
            if path.startswith('/tryout/'):
                slug=path.split('/')[-1];s=c.execute('SELECT * FROM question_sets WHERE slug=? AND published=1',(slug,)).fetchone()
                if not s:self.send_html('Not found',404);return
                qs=c.execute('SELECT * FROM questions WHERE set_id=? ORDER BY position,id',(s['id'],)).fetchall();send('tryout_detail',{'TRYOUT_TITLE':e(s['title']),'TRYOUT_DESCRIPTION':e(s['summary']),'TRYOUT_CATEGORY':'Latihan CAT','TRYOUT_ID':str(s['id']),'TRYOUT_STATISTICS':f'<span class="tag">{len(qs)} soal</span><span class="tag">{s["duration_min"]} menit</span>','TRYOUT_SECTIONS':'<p class="muted">Latihan mandiri</p>','TRYOUT_ACCESS_NOTE':'Sesi dan hasil tryout akan tersimpan ke akunmu.' if u else 'Masuk diperlukan untuk memulai tryout dan menyimpan hasilnya.'});return
            if path=='/jadwal':
                month=query.get('month',[''])[0]
                args=[];sql='SELECT * FROM live_sessions WHERE published=1 AND starts_at>=datetime("now")'
                if month:
                    if not re.fullmatch(r'\d{4}-\d{2}',month):self.send_html('Bulan tidak valid.',400);return
                    year,mon=map(int,month.split('-'))
                    if not 1<=mon<=12:self.send_html('Bulan tidak valid.',400);return
                    next_month=f'{year+1:04}-01-01' if mon==12 else f'{year:04}-{mon+1:02}-01'
                    sql+=' AND starts_at>=? AND starts_at<?';args.extend([f'{year:04}-{mon:02}-01',next_month])
                rows=c.execute(sql+' ORDER BY starts_at',args).fetchall();send('live_schedule',{'SCHEDULE_EVENTS':''.join(f'<article class="glass card"><p class="tag">{e(x["subject"])}</p><h2 class="mt-3 text-xl font-semibold">{e(x["title"])}</h2><p class="muted mt-2">{e(x["starts_at"])} · {x["duration_min"]} menit · {e(x["mentor"])}</p></article>' for x in rows) or '<p class="muted">Belum ada jadwal kelas pada periode ini.</p>','MONTH_VALUE':e(month)});return
            if path=='/artikel':
                term=query.get('q',[''])[0];rows=c.execute('SELECT * FROM articles WHERE published=1 AND (title LIKE ? OR summary LIKE ? OR category LIKE ?) ORDER BY created_at DESC',(f'%{term}%',)*3).fetchall();send('articles',{'ARTICLE_CARDS':''.join(f'<a class="glass card block" href="/artikel/{e(x["slug"])}"><p class="tag">{e(x["category"])}</p><h2 class="mt-3 text-xl font-semibold">{e(x["title"])}</h2><p class="muted mt-2">{e(x["summary"])}</p></a>' for x in rows),'QUERY':e(term),'PAGINATION':''});return
            if path.startswith('/artikel/'):
                a=c.execute('SELECT * FROM articles WHERE slug=? AND published=1',(path.split('/')[-1],)).fetchone()
                if not a:self.send_html('Not found',404);return
                article_body=sanitize_rich_html(a['body']).replace('\n','<br>')
                send('article_detail',{'ARTICLE_TITLE':e(a['title']),'ARTICLE_BODY_HTML':article_body,'ARTICLE_CATEGORY':e(a['category']),'ARTICLE_EXCERPT':sanitize_rich_html(a['summary']),'ARTICLE_AUTHOR':'Aster Academy','ARTICLE_PUBLISHED_AT':e(a['created_at']),'ARTICLE_READ_TIME':'3 menit'});return
            if path in ('/daftar','/signup'):send('signup',{'AUTH_EXTRA_FIELDS':'','AUTH_INTRO':'Buat akun untuk menyimpan program dan progres belajarmu.','AUTH_SWITCH_TEXT':'Sudah punya akun?','AUTH_SWITCH_LABEL':'Masuk','AUTH_SWITCH_URL':'/masuk','NAME_VALUE':'','EMAIL_VALUE':'','FORM_ERROR':'','PASSWORD_AUTOCOMPLETE':'new-password','SUBMIT_LABEL':'Buat akun'});return
            if path in ('/masuk','/login'):send('login',{'AUTH_EXTRA_FIELDS':'','AUTH_INTRO':'Masuk untuk melanjutkan persiapanmu.','AUTH_SWITCH_TEXT':'Belum punya akun?','AUTH_SWITCH_LABEL':'Daftar','AUTH_SWITCH_URL':'/daftar','EMAIL_VALUE':'','FORM_ERROR':'','PASSWORD_AUTOCOMPLETE':'current-password','SUBMIT_LABEL':'Masuk'});return
            if path in ('/dashboard','/ruang-belajar'):
                if not u:self.redirect('/masuk');return
                if u['role'] in ('super_admin','admin','teacher') and any(self.can(u,p) for p in ('dashboard.view','programs.view','question_banks.view','enrollments.view')):self.redirect('/admin');return
                rows=c.execute('''SELECT p.*,i.name institution,
                    (SELECT COUNT(*) FROM lessons l JOIN modules m ON m.id=l.module_id WHERE m.program_id=p.id) lesson_total,
                    (SELECT COUNT(*) FROM lesson_progress lp JOIN lessons l ON l.id=lp.lesson_id JOIN modules m ON m.id=l.module_id WHERE m.program_id=p.id AND lp.user_id=en.user_id) lesson_done
                    FROM enrollments en JOIN programs p ON p.id=en.program_id LEFT JOIN institutions i ON i.id=p.institution_id WHERE en.user_id=? AND en.status="active"''',(u['id'],)).fetchall()
                pending=c.execute('SELECT COUNT(*) FROM enrollments WHERE user_id=? AND status="pending"',(u['id'],)).fetchone()[0]
                recent_attempts = recent_attempt_summaries(c, u['id'])
                learning_analysis = category_learning_analysis(c, u['id'])
                recent_results = ''.join(
                    f'<a class="glass card block transition hover:border-blue-300" href="{self.opaque_path("attempt", item["id"], "/tryout/result/{}", c)}"><div class="flex items-center justify-between gap-3"><div><p class="text-sm font-bold text-[#15345d]">{e(item["title"])}</p><p class="muted mt-1 text-sm">Selesai {e(item["finished_at"])}</p></div><div class="text-right"><p class="text-lg font-extrabold text-blue-800">{item["score"]} / {item["total"]}</p><p class="muted text-xs">{item["percentage"]}%</p></div></div></a>'
                    for item in recent_attempts
                ) or '<p class="muted">Belum ada hasil tryout. Mulai latihan untuk melihat perkembangan nilaimu di sini.</p>'
                schedule_rows = c.execute('SELECT title,subject,starts_at,duration_min,mentor FROM live_sessions WHERE published=1 AND starts_at>=datetime("now") ORDER BY starts_at LIMIT 3').fetchall()
                upcoming_classes = ''.join(
                    f'<article class="glass card"><p class="text-sm font-bold text-[#15345d]">{e(item["title"])}</p><p class="muted mt-1 text-sm">{e(item["subject"])} · {e(item["starts_at"])} · {item["duration_min"]} menit</p><p class="muted mt-1 text-xs">Mentor: {e(item["mentor"] or "Aster Academy")}</p></article>'
                    for item in schedule_rows
                ) or '<p class="muted">Belum ada jadwal kelas. Periksa kembali saat sesi baru diterbitkan.</p>'
                if learning_analysis:
                    weakest = learning_analysis['weakest']
                    previous = learning_analysis['previous_percentage']
                    progress_text = (
                        f'Nilai tryout terakhir {learning_analysis["latest_percentage"]}%; sebelumnya {previous}%.'
                        if previous is not None
                        else f'Nilai tryout terakhir {learning_analysis["latest_percentage"]}%.'
                    )
                    learning_guidance = (
                        '<article class="glass card">'
                        '<p class="tag">REKOMENDASI BELAJAR</p>'
                        f'<h3 class="mt-3 text-lg font-bold">Perkuat {e(weakest["name"])}</h3>'
                        f'<p class="muted mt-2">Skor kategori ini {weakest["percentage"]}% ({weakest["score"]:g}/{weakest["max_score"]:g}). {progress_text}</p>'
                        '<p class="muted mt-2 text-sm">Gunakan hasil ini untuk menentukan materi dan latihan berikutnya; ini bukan prediksi kelulusan.</p>'
                        '<a class="btn-secondary mt-4 inline-flex" href="/tryout">Latihan kategori terkait</a>'
                        '</article>'
                    )
                else:
                    learning_guidance = '<article class="glass card"><p class="tag">REKOMENDASI BELAJAR</p><h3 class="mt-3 text-lg font-bold">Belum ada analisis kategori</h3><p class="muted mt-2">Selesaikan tryout yang memakai blueprint kategori untuk memperoleh rekomendasi belajar yang terukur.</p><a class="btn-secondary mt-4 inline-flex" href="/tryout">Mulai tryout</a></article>'
                send('student_dashboard',{'STUDENT_NAME':e(u['name']),'ENROLLED_COURSE_CARDS':self.cards(rows,'program'),'DASHBOARD_STAT_CARDS':'<div class="glass card">Program aktif: '+str(len(rows))+'</div>'+('<div class="glass card">Permintaan akses menunggu persetujuan admin.</div>' if pending else ''),'RECENT_TRYOUT_RESULTS':recent_results,'LEARNING_GUIDANCE':learning_guidance,'UPCOMING_CLASSES':upcoming_classes});return
            if path.startswith('/belajar/') or path.startswith('/learn/'):
                if not u:self.redirect('/masuk');return
                parts=path.strip('/').split('/');slug=parts[1] if len(parts)>1 else '';lid=parts[2] if len(parts)>2 else ''
                p=c.execute('SELECT p.* FROM programs p JOIN enrollments en ON en.program_id=p.id WHERE p.slug=? AND en.user_id=? AND en.status="active"',(slug,u['id'])).fetchone()
                lesson_id=resolve_ref(c,'lesson',lid) if lid else None
                if p and not lid:
                    first=c.execute('SELECT l.id FROM lessons l JOIN modules m ON m.id=l.module_id WHERE m.program_id=? ORDER BY m.position,l.position LIMIT 1',(p['id'],)).fetchone()
                    lesson_id=first['id'] if first else None
                lesson=c.execute('SELECT l.*,m.title module_title FROM lessons l JOIN modules m ON m.id=l.module_id WHERE l.id=? AND m.program_id=?',(lesson_id,p['id'] if p else -1)).fetchone() if lesson_id is not None else None
                if not p or not lesson:self.send_html('Not found',404);return
                vid=lesson['video_url'].split('v=')[-1].split('&')[0] if 'v=' in lesson['video_url'] else lesson['video_url'].split('/')[-1];embed='https://www.youtube-nocookie.com/embed/'+re.sub(r'[^A-Za-z0-9_-]','',vid)
                all_lessons=c.execute('SELECT l.id,l.title,m.title module_title,EXISTS(SELECT 1 FROM lesson_progress lp WHERE lp.lesson_id=l.id AND lp.user_id=?) done FROM lessons l JOIN modules m ON m.id=l.module_id WHERE m.program_id=? ORDER BY m.position,l.position',(u['id'],p['id'])).fetchall();sidebar=''.join(f'<a class="block rounded-lg p-3 text-sm {"text-emerald-200" if x["done"] else "text-slate-300"}" href="/belajar/{e(slug)}/{ref_for(c,"lesson",x["id"])}">{e(x["module_title"])} · {e(x["title"])}{" ✓" if x["done"] else ""}</a>' for x in all_lessons);send('lesson_player',{'COURSE_TITLE':e(p['title']),'LESSON_TITLE':e(lesson['title']),'LESSON_DESCRIPTION':e(lesson['body']),'MODULE_TITLE':e(lesson['module_title']),'YOUTUBE_EMBED_URL':e(embed),'LESSON_ID':str(lesson['id']),'LESSON_TOKEN':ref_for(c,'lesson',lesson['id']),'LESSON_RESOURCES':e(lesson['resource_url']),'LESSON_SIDEBAR':sidebar});return
            if path=='/profil':
                if not u:self.redirect('/masuk');return
                if not self.can(u,'profile.view'):self.send_html('Forbidden',403);return
                status=query.get('status',[''])[0]
                send('admin_profile',{'PROFILE_ERROR':'','PROFILE_MESSAGE':f'<p class="notice notice-success" role="status">{e(status)}</p>' if status else '', 'PROFILE_UPDATE_CLASS':'' if self.can(u,'profile.update') else 'hidden', 'PROFILE_READONLY_NOTICE':'<p class="notice">Akun ini memiliki akses lihat saja. Hubungi Super Admin untuk meminta perubahan profil.</p>' if not self.can(u,'profile.update') else ''});return
            if path in ('/admin','/admin/program','/admin/permintaan-akses'):
                show_programs=self.can(u,'programs.view');show_enrollments=self.can(u,'enrollments.view')
                ps=c.execute('SELECT p.*,i.name institution FROM programs p LEFT JOIN institutions i ON i.id=p.institution_id ORDER BY p.id DESC').fetchall() if show_programs else []
                program_action=lambda x:(f'<a class="font-semibold text-blue-700" href="/admin/kursus/{x["id"]}/edit">Kelola →</a>' if self.can(u,'programs.update') else '<span class="text-slate-400">—</span>')
                rows=''.join(f'<tr><td class="px-5 py-4 font-semibold text-slate-800">{e(x["title"])}</td><td class="px-5 py-4"><span class="rounded-full px-2.5 py-1 text-xs font-semibold {"bg-emerald-50 text-emerald-700" if x["status"]=="published" else "bg-slate-100 text-slate-600"}">{"Terbit" if x["status"]=="published" else "Draft"}</span></td><td class="px-5 py-4">{program_action(x)}</td></tr>' for x in ps) or '<tr><td class="px-6 py-10 text-center" colspan="3"><p class="font-semibold text-slate-700">Belum ada program</p><p class="mt-1 text-sm text-slate-500">Tambahkan program pertama untuk mulai menyusun materi.</p><a class="btn mt-4 {{NAV_PROGRAM_CREATE_CLASS}}" href="/admin/kursus/baru">Tambah program</a></td></tr>'
                pending=c.execute('SELECT en.id,u.name,u.email,p.title FROM enrollments en JOIN users u ON u.id=en.user_id JOIN programs p ON p.id=en.program_id WHERE en.status="pending" ORDER BY en.id').fetchall() if show_enrollments else []
                activity=''.join((f'<form class="glass card flex items-center justify-between gap-3" method="post" action="/admin/enrollment/approve"><input type="hidden" name="enrollment_id" value="{x["id"]}"><span>{e(x["name"])} · {e(x["email"])} — {e(x["title"])}</span><button class="btn" type="submit">Beri akses</button></form>' if self.can(u,'enrollments.approve') else f'<article class="glass card"><p>{e(x["name"])} · {e(x["email"])} — {e(x["title"])}</p><p class="mt-2 text-sm text-slate-500">Menunggu persetujuan</p></article>') for x in pending) or '<div class="rounded-2xl border border-dashed border-slate-300 bg-white p-6"><p class="font-semibold text-[#15345d]">Belum ada permintaan akses</p><p class="mt-1 text-sm text-slate-500">Permintaan dari pelajar akan muncul di sini untuk ditinjau.</p></div>'
                metric_rows=[]
                if show_programs:metric_rows.append(('Program',len(ps),'Semua status'))
                if self.can(u,'users.view'):
                    students=c.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0]
                    metric_rows.append(('Pelajar',students,'Akun terdaftar'))
                if show_enrollments:metric_rows.append(('Permintaan akses',len(pending),'Menunggu ditinjau'))
                if self.can(u,'lessons.view'):
                    lessons=c.execute('SELECT COUNT(*) FROM lessons').fetchone()[0]
                    metric_rows.append(('Pelajaran',lessons,'Materi tersusun'))
                stats=''.join(f'<article class="glass card"><p class="muted text-sm">{label}</p><p class="mt-2 text-3xl font-extrabold text-[#15345d]">{value}</p><p class="muted mt-1 text-xs">{note}</p></article>' for label,value,note in metric_rows)
                send('admin_dashboard',{'ADMIN_COURSE_ROWS':rows if show_programs else '', 'ADMIN_RECENT_ACTIVITY':activity if show_enrollments else '', 'ADMIN_PROGRAM_BLOCK_CLASS':'' if show_programs else 'hidden','ADMIN_ENROLLMENT_BLOCK_CLASS':'' if show_enrollments else 'hidden','ADMIN_STATS':stats});return
            if path == '/admin/akses-role':
                matrix=self.role_matrix(c)
                from services.menu_service import role_menu_tree
                curr_role = query.get('role', ['admin'])[0]
                contract=role_menu_tree(c, curr_role)
                role_opts_list = []
                for x in contract['roles']:
                    sel_attr = 'selected' if x['key'] == curr_role else ''
                    role_opts_list.append(f'<option value="{e(x["key"])}" {sel_attr}>{e(x["label"])}</option>')
                role_options = ''.join(role_opts_list)
                menu_json=json.dumps(contract['menus'],ensure_ascii=False).replace('<','\\u003c')
                send('admin_roles',{'ROLE_MATRIX':matrix,'ROLE_NOTICE':'','ROLE_OPTIONS_JSON':role_options,'MENU_TREE_JSON':menu_json})
                return
            if path=='/admin/artikel':
                rows=c.execute('SELECT * FROM articles ORDER BY published DESC,created_at DESC,id DESC').fetchall();html_rows=[]
                for x in rows:
                    token=ref_for(c,'article',x['id']);status='Terbit' if x['published'] else 'Draf';actions=[]
                    if self.can(u,'articles.update'):actions.append(f'<a href="/admin/artikel/{token}/edit">Edit</a>')
                    if self.can(u,'articles.publish'):actions.append(f'<form method="post" action="/admin/artikel/status" class="inline"><input type="hidden" name="article_id" value="{x["id"]}"><input type="hidden" name="published" value="{0 if x["published"] else 1}"><button type="submit">{"Batalkan terbit" if x["published"] else "Terbitkan"}</button></form>')
                    if self.can(u,'articles.delete'):actions.append(f'<form method="post" action="/admin/artikel/hapus" class="inline"><input type="hidden" name="article_id" value="{x["id"]}"><button type="submit">Hapus</button></form>')
                    html_rows.append(f'<tr><td>{e(x["title"])}</td><td>{e(x["category"])}</td><td>{status}</td><td>{e(x["updated_at"] or x["created_at"])}</td><td>{" · ".join(actions) or "—"}</td></tr>')
                send('admin_articles',{'ARTICLE_ROWS':''.join(html_rows) or '<tr><td colspan="5">Belum ada artikel.</td></tr>','ARTICLE_CREATE_CLASS':'' if self.can(u,'articles.create') else 'hidden'});return
            if path=='/admin/artikel/baru':
                send('admin_article_form',{'FORM_HEADING':'Tambah artikel','ARTICLE_ID':'','TITLE':'','SLUG':'','CATEGORY':'','SUMMARY':'','BODY':'','PUBLISHED_CHECKED':'','ARTICLE_PUBLISH_CLASS':'' if self.can(u,'articles.publish') else 'hidden','FORM_ERROR':''});return
            if path.startswith('/admin/artikel/') and path.endswith('/edit'):
                article_id=path.split('/')[3];row=c.execute('SELECT * FROM articles WHERE id=?',(article_id,)).fetchone()
                if not row:self.send_html('Not found',404);return
                send('admin_article_form',{'FORM_HEADING':'Edit artikel','ARTICLE_ID':str(row['id']),'TITLE':e(row['title']),'SLUG':e(row['slug']),'CATEGORY':e(row['category']),'SUMMARY':e(row['summary']),'BODY':e(row['body']),'PUBLISHED_CHECKED':'checked' if row['published'] else '','ARTICLE_PUBLISH_CLASS':'' if self.can(u,'articles.publish') else 'hidden','FORM_ERROR':''});return
            if path=='/admin/jadwal':
                rows=c.execute('SELECT * FROM live_sessions ORDER BY starts_at DESC,id DESC').fetchall();html_rows=[]
                for x in rows:
                    token=ref_for(c,'live_session',x['id']);status='Terbit' if x['published'] else 'Draf';actions=[]
                    if self.can(u,'live_sessions.update'):actions.append(f'<a href="/admin/jadwal/{token}/edit">Edit</a>')
                    if self.can(u,'live_sessions.publish'):actions.append(f'<form method="post" action="/admin/jadwal/status" class="inline"><input type="hidden" name="session_id" value="{x["id"]}"><input type="hidden" name="published" value="{0 if x["published"] else 1}"><button type="submit">{"Batalkan terbit" if x["published"] else "Terbitkan"}</button></form>')
                    if self.can(u,'live_sessions.delete'):actions.append(f'<form method="post" action="/admin/jadwal/hapus" class="inline"><input type="hidden" name="session_id" value="{x["id"]}"><button type="submit">Hapus</button></form>')
                    html_rows.append(f'<tr><td>{e(x["title"])}<br><small>{e(x["subject"])}</small></td><td>{e(x["starts_at"])} · {x["duration_min"]} menit</td><td>{e(x["mentor"])}</td><td>{status}</td><td>{" · ".join(actions) or "—"}</td></tr>')
                send('admin_live_sessions',{'LIVE_ROWS':''.join(html_rows) or '<tr><td colspan="5">Belum ada jadwal.</td></tr>','LIVE_CREATE_CLASS':'' if self.can(u,'live_sessions.create') else 'hidden'});return
            if path=='/admin/jadwal/baru':
                send('admin_live_session_form',{'FORM_HEADING':'Tambah jadwal','SESSION_ID':'','TITLE':'','SUBJECT':'','STARTS_AT':'','DURATION_MIN':'90','MENTOR':'','JOIN_URL':'','PUBLISHED_CHECKED':'','LIVE_PUBLISH_CLASS':'' if self.can(u,'live_sessions.publish') else 'hidden','FORM_ERROR':''});return
            if path.startswith('/admin/jadwal/') and path.endswith('/edit'):
                session_id=path.split('/')[3];row=c.execute('SELECT * FROM live_sessions WHERE id=?',(session_id,)).fetchone()
                if not row:self.send_html('Not found',404);return
                starts=str(row['starts_at']).replace(' ','T')[:16]
                send('admin_live_session_form',{'FORM_HEADING':'Edit jadwal','SESSION_ID':str(row['id']),'TITLE':e(row['title']),'SUBJECT':e(row['subject']),'STARTS_AT':e(starts),'DURATION_MIN':str(row['duration_min']),'MENTOR':e(row['mentor']),'JOIN_URL':e(row['join_url']),'PUBLISHED_CHECKED':'checked' if row['published'] else '','LIVE_PUBLISH_CLASS':'' if self.can(u,'live_sessions.publish') else 'hidden','FORM_ERROR':''});return
            registered = c.execute('SELECT route_key,label FROM route_menu_registry WHERE path=? AND active=1', (path,)).fetchone()
            if registered:
                from services.menu_scaffold import template_name_for_route_key
                template_name = template_name_for_route_key(registered['route_key'])
                if (TEMPLATES / f'{template_name}.html').is_file():
                    send(template_name, {'ADMIN_PAGE_TITLE': e(registered['label'])})
                    return
            if path=='/admin/kategori-soal':
                profiles=c.execute('SELECT * FROM exam_rule_profiles WHERE active=1 ORDER BY year DESC,id').fetchall()
                profile_key=query.get('profile',[''])[0]
                profile=c.execute('SELECT * FROM exam_rule_profiles WHERE key=?',(profile_key,)).fetchone() if profile_key else (profiles[0] if profiles else None)
                categories=c.execute("SELECT cat.*,parent.name parent_name,COALESCE(rule.item_count,parent_rule.item_count) item_count,COALESCE(rule.correct_score,parent_rule.correct_score) correct_score,COALESCE(rule.incorrect_score,parent_rule.incorrect_score) incorrect_score,COALESCE(rule.blank_score,parent_rule.blank_score) blank_score,COALESCE(rule.max_score,parent_rule.max_score) max_score,COALESCE(rule.passing_score,parent_rule.passing_score) passing_score,COALESCE(rule.scoring_mode,parent_rule.scoring_mode) scoring_mode,COALESCE(rule.option_score_min,parent_rule.option_score_min) option_score_min,COALESCE(rule.option_score_max,parent_rule.option_score_max) option_score_max FROM question_categories cat LEFT JOIN question_categories parent ON parent.id=cat.parent_id LEFT JOIN category_scoring_rules rule ON rule.category_id=cat.id AND rule.profile_id=? LEFT JOIN category_scoring_rules parent_rule ON parent_rule.category_id=cat.parent_id AND parent_rule.profile_id=? ORDER BY COALESCE(parent.position,cat.position),cat.parent_id IS NOT NULL,cat.position,cat.id",(profile['id'] if profile else -1,profile['id'] if profile else -1)).fetchall()
                edit_key=query.get('edit',[''])[0];edit=c.execute('SELECT * FROM question_categories WHERE key=?',(edit_key,)).fetchone() if edit_key and not edit_key.isdigit() else None
                rule=c.execute('SELECT * FROM category_scoring_rules WHERE category_id=? AND profile_id=?',(edit['id'] if edit else -1,profile['id'] if profile else -1)).fetchone()
                inherited_rule=c.execute('SELECT * FROM category_scoring_rules WHERE category_id=? AND profile_id=?',(edit['parent_id'] if edit and edit['parent_id'] else -1,profile['id'] if profile else -1)).fetchone()
                # A child with no profile-specific rule edits the effective parent values.
                editor=rule or inherited_rule or {}
                parent_options=''.join(f'<option value="{x["id"]}" {"selected" if edit and edit["parent_id"]==x["id"] else ""}>{e(x["name"])}</option>' for x in categories if not x["parent_id"] and (not edit or x["id"]!=edit["id"]))
                core_keys={'twk','tiu','tkp','unclassified'}
                profile_options=''.join(f'<option value="{x["id"]}" {"selected" if profile and profile["id"]==x["id"] else ""}>{e(x["name"])}</option>' for x in profiles)
                if profile:
                    source_link=f'<a class="mt-2 inline-flex font-semibold text-blue-700 underline" href="{e(profile["source_url"])}" target="_blank" rel="noopener noreferrer">Buka sumber resmi ↗</a>' if profile['source_url'].startswith('https://') else ''
                    profile_info=f'<div class="notice mt-4"><p><b>{e(profile["name"])}</b> · Profil tahun {profile["year"]} · {e(profile["version"])}</p><p class="mt-2">{e(profile["source_name"] or "Sumber belum dicatat")}</p>{source_link}<p class="mt-2">{e(profile["notes"])}</p></div>'
                else:profile_info='<div class="notice mt-4">Pilih atau buat profil aturan agar bobot dan ambang dapat ditampilkan.</div>'
                def category_row(x):
                    is_core=x['key'] in core_keys
                    delete=(f'<form method="post" action="/admin/kategori-soal/hapus" class="ml-2 inline"><input type="hidden" name="id" value="{x["id"]}"><button class="text-rose-700" type="submit">Hapus</button></form>' if not is_core and self.can(u,'question_categories.delete') else ('<span class="ml-2 text-xs text-slate-400">Kategori inti</span>' if is_core else ''))
                    if x['scoring_mode']=='option_points':
                        weight=f'Opsi {x["option_score_min"] or 0}–{x["option_score_max"] or 0} · kosong {x["blank_score"] if x["blank_score"] is not None else 0} · maks {x["max_score"] if x["max_score"] is not None else "—"} · ambang {x["passing_score"] if x["passing_score"] is not None else "—"}'
                    else:
                        weight=f'Benar {x["correct_score"] if x["correct_score"] is not None else "—"} · salah {x["incorrect_score"] if x["incorrect_score"] is not None else "—"} · kosong {x["blank_score"] if x["blank_score"] is not None else "—"} · maks {x["max_score"] if x["max_score"] is not None else "—"} · ambang {x["passing_score"] if x["passing_score"] is not None else "—"}'
                    edit_link=(f'<a class="font-semibold text-blue-700" href="/admin/kategori-soal?edit={e(x["key"])}&amp;profile={e(profile["key"] if profile else "")}">Ubah</a>' if self.can(u,'question_categories.update') else '')
                    return f'<tr><td class="font-semibold">{e(x["name"])}</td><td><code>{e(x["key"])}</code></td><td>{e(x["parent_name"] or "Kategori utama")}</td><td>{x["item_count"] if x["item_count"] is not None else "—"}</td><td>{e(weight)}</td><td>{"Aktif" if x["active"] else "Nonaktif"}</td><td>{edit_link}{delete}</td></tr>'
                category_rows=''.join(category_row(x) for x in categories) or '<tr><td colspan="7" class="p-6 text-center">Belum ada kategori soal.</td></tr>'
                is_core=bool(edit and edit['key'] in core_keys)
                can_edit=bool(edit and self.can(u,'question_categories.update'))
                can_create=bool(not edit and self.can(u,'question_categories.create'))
                show_form=can_edit if edit else can_create
                send('admin_question_categories',{'CATEGORY_ROWS':category_rows,'PROFILE_INFO':profile_info,'CATEGORY_FORM_CLASS':'' if show_form else 'hidden','CATEGORY_FORM_BUTTON_CLASS':'' if show_form else 'hidden','FORM_HEADING':'Ubah kategori' if edit else 'Tambah kategori','CATEGORY_ID':str(edit['id'] if edit else ''),'CATEGORY_CODE':e(edit['key'] if edit else ''),'CATEGORY_KEY_DISABLED':'disabled' if is_core else '','CATEGORY_KEY_HIDDEN':f'<input type="hidden" name="key" value="{e(edit["key"])}">' if is_core else '','CATEGORY_NAME':e(edit['name'] if edit else ''),'CATEGORY_DESCRIPTION':e(edit['description'] if edit else ''),'CATEGORY_POSITION':str(edit['position'] if edit else 0),'CATEGORY_ACTIVE_CHECKED':'checked' if not edit or edit['active'] else '','CATEGORY_ACTIVE_DISABLED':'disabled' if is_core else '','CATEGORY_ACTIVE_HIDDEN':'<input type="hidden" name="active" value="1">' if is_core else '','CATEGORY_PARENT_DISABLED':'disabled' if is_core else '','CATEGORY_PARENT_HIDDEN':'<input type="hidden" name="parent_id" value="">' if is_core else '','PARENT_CATEGORY_OPTIONS':parent_options,'PROFILE_OPTIONS':profile_options,'ITEM_COUNT':str(editor['item_count'] if editor else 0),'CORRECT_SCORE':str(editor['correct_score'] if editor else 5),'INCORRECT_SCORE':str(editor['incorrect_score'] if editor else 0),'BLANK_SCORE':str(editor['blank_score'] if editor else 0),'MAX_SCORE':str(editor['max_score'] if editor else 0),'PASSING_SCORE':str(editor['passing_score'] if editor and editor['passing_score'] is not None else ''),'MODE_CORRECTNESS_SELECTED':'selected' if not editor or editor['scoring_mode']=='correctness' else '','MODE_OPTION_SELECTED':'selected' if editor and editor['scoring_mode']=='option_points' else '','FORM_ERROR':''});return
            if re.fullmatch(r'/admin/bank-soal/\d+/blueprint',path):
                sid=int(path.split('/')[3]);s=c.execute('SELECT * FROM question_sets WHERE id=?',(sid,)).fetchone()
                if not s:self.send_html('Bank soal tidak ditemukan.',404);return
                bp=c.execute('SELECT * FROM exam_blueprints WHERE key=?',('set-'+str(sid),)).fetchone()
                selected={x['category_id']:x for x in c.execute('SELECT * FROM exam_blueprint_categories WHERE blueprint_id=?',(bp['id'] if bp else -1,))}
                cats=c.execute("SELECT * FROM question_categories WHERE active=1 AND parent_id IS NULL AND key<>'unclassified' ORDER BY position,id").fetchall()
                ordered_cats=sorted((x for x in cats if x['id'] in selected),key=lambda x:(selected[x['id']]['position'],selected[x['id']]['id']))
                category_rows=''.join(f'<div class="category-row" draggable="true" data-category-id="{x["id"]}"><button type="button" class="drag-handle" aria-label="Geser kategori">⠿</button><div><span class="help block" data-order-label>{index+1}</span><b>{e(x["name"])}</b><input type="checkbox" name="category_{x["id"]}" value="1" checked hidden></div><label class="text-xs font-semibold">Jumlah soal<input class="field mt-1" type="number" name="count_{x["id"]}" min="1" max="500" value="{selected[x["id"]]["question_count"]}" required></label><div class="flex items-center gap-1"><input type="hidden" name="order_{x["id"]}" data-position value="{index+1}"><button type="button" data-up class="btn2" aria-label="Naikkan kategori">↑</button><button type="button" data-down class="btn2" aria-label="Turunkan kategori">↓</button><button type="button" data-remove class="btn2" aria-label="Hapus kategori">×</button></div></div>' for index,x in enumerate(ordered_cats))
                available=''.join(f'<option value="{x["id"]}" data-label="{e(x["name"])}">{e(x["name"])}</option>' for x in cats if x['id'] not in selected)
                profiles=c.execute('SELECT * FROM exam_rule_profiles WHERE active=1 ORDER BY year DESC,id').fetchall()
                profile_options=''.join(f'<option value="{x["id"]}" {"selected" if bp and bp["profile_id"]==x["id"] else ""}>{e(x["name"])}</option>' for x in profiles)
                send('admin_tryout_blueprint',{'SET_ID':str(sid),'BLUEPRINT_TITLE':e(bp['name'] if bp else s['title']+' · Tryout'),'DURATION_MINUTES':str(bp['duration_min'] if bp and bp['duration_min'] else s['duration_min']),'MODE_RANDOM_CHECKED':'checked' if bp and bp['selection_mode']=='random' else '','BLUEPRINT_CATEGORY_ROWS':category_rows,'AVAILABLE_CATEGORY_OPTIONS':available,'CATEGORY_COUNT':str(len(selected)),'EXAM_PROFILE_OPTIONS':profile_options,'FORM_ERROR':''});return
            if path=='/admin/bank-soal':
                sets=c.execute('''SELECT s.*,COUNT(DISTINCT q.id) question_count,COUNT(DISTINCT a.id) attempt_count FROM question_sets s LEFT JOIN questions q ON q.set_id=s.id LEFT JOIN attempts a ON a.set_id=s.id GROUP BY s.id ORDER BY s.id DESC''').fetchall()
                row_items = []
                can_update = self.can(u, "question_banks.update")
                for x in sets:
                    status_lbl = "Terbit" if x["published"] else "Draft"
                    bp_link = f'<a class="font-semibold text-blue-700" href="/admin/bank-soal/{x["id"]}/blueprint">Blueprint</a>' if can_update else ""
                    row_items.append(f'<tr><td class="px-5 py-4"><a class="font-semibold text-blue-800" href="/admin/bank-soal/{x["id"]}">{e(x["title"])}</a><p class="mt-1 text-sm text-slate-500">{e(x["slug"])}</p></td><td class="px-5 py-4">{x["question_count"]}</td><td class="px-5 py-4">{x["duration_min"]} menit</td><td class="px-5 py-4">{status_lbl}</td><td class="px-5 py-4">{x["attempt_count"]}</td><td class="px-5 py-4"><div class="flex flex-wrap gap-3"><a class="font-semibold text-blue-700" href="/admin/bank-soal/{x["id"]}">Kelola soal</a>{bp_link}</div></td></tr>')
                rows=''.join(row_items)
                send('admin_question_bank',{'BANK_ROWS':rows});return
            if path=='/admin/bank-soal/baru':
                
                send('admin_question_set_form',{'FORM_HEADING':'Buat paket soal','FORM_ACTION':'/admin/bank-soal/paket/simpan','SET_ID':'','SET_TITLE':'','SET_SLUG':'','SET_SUMMARY':'','SET_DURATION':'30','SET_PUBLISHED':'','PARENT_BANK_OPTIONS':parent_bank_options(c,0),'FORM_ERROR':''});return
            if path.startswith('/admin/bank-soal/') and path.endswith('/edit') and path.split('/')[3].isdigit():
                
                sid=path.split('/')[3];s=c.execute('SELECT * FROM question_sets WHERE id=?',(sid,)).fetchone()
                if not s:self.send_html('Not found',404);return
                history=c.execute('SELECT COUNT(*) FROM attempts WHERE set_id=?',(sid,)).fetchone()[0]
                send('admin_question_set_form',{'FORM_HEADING':'Edit paket soal','FORM_ACTION':'/admin/bank-soal/paket/simpan','SET_ID':str(s['id']),'SET_TITLE':e(s['title']),'SET_SLUG':e(s['slug']),'SET_SUMMARY':e(s['summary']),'SET_DURATION':str(s['duration_min']),'SET_PUBLISHED':'checked' if s['published'] else '', 'PARENT_BANK_OPTIONS':parent_bank_options(c,s['id']),'FORM_ERROR':'<p class="rounded-xl bg-amber-50 p-4 text-sm text-amber-800">Paket ini sudah memiliki riwayat attempt. Seluruh data paket dibekukan agar hasil lama tetap konsisten.</p>' if history else '', 'FORM_DISABLED':'disabled' if history else ''});return
            if path.startswith('/admin/bank-soal/') and path.count('/')==3 and path.split('/')[-1].isdigit():
                
                sid=path.split('/')[-1];s=c.execute('SELECT * FROM question_sets WHERE id=?',(sid,)).fetchone()
                if not s:self.send_html('Not found',404);return
                bank=c.execute('SELECT id FROM question_banks WHERE legacy_question_set_id=?',(sid,)).fetchone();qs=c.execute('SELECT q.*,bm.position bank_position,cat.name category_name,COUNT(aa.question_id) answer_count FROM question_bank_memberships bm JOIN questions q ON q.id=bm.question_id LEFT JOIN question_categories cat ON cat.id=q.category_id LEFT JOIN attempt_answers aa ON aa.question_id=q.id WHERE bm.bank_id=? GROUP BY q.id ORDER BY bm.position,q.position,q.id',(bank['id'] if bank else -1,)).fetchall()
                locked=c.execute('SELECT COUNT(*) FROM attempts WHERE set_id=?',(sid,)).fetchone()[0]
                row_html=[]
                can_update_q = self.can(u, 'questions.update')
                can_delete_q = self.can(u, 'questions.delete')
                for x in qs:
                    edit_action = (f'<a class="font-semibold text-blue-700" href="/admin/bank-soal/soal/{x["id"]}/edit">Edit →</a>' if can_update_q else '—')
                    dis_attr = "disabled title='Paket dengan riwayat attempt dikunci'" if locked else ""
                    delete_action = (f'<form method="post" action="/admin/bank-soal/soal/hapus"><input type="hidden" name="question_id" value="{x["id"]}"><button class="font-semibold text-rose-600" type="submit" onclick="return confirm(&quot;Hapus soal ini?&quot;)" {dis_attr}>Hapus</button></form>' if can_delete_q else '—')
                    row_html.append(f'<tr data-question-id="{x["id"]}"><td class="px-3 py-4"><button type="button" class="drag-handle cursor-grab text-slate-500" draggable="true" aria-label="Seret untuk mengurutkan soal" title="Seret untuk mengurutkan soal">⠿</button></td><td>{x["bank_position"]}</td><td class="px-5 py-4"><div class="question-preview max-w-2xl font-semibold leading-6 text-slate-800">{sanitize_rich_html(x["content_html"] or x["prompt"])}</div><p class="mt-1 text-xs text-slate-500">{e(x["category_name"] or "Belum diklasifikasikan")} · Posisi {x["bank_position"]} · Kunci {e(x["answer"])}</p></td><td class="px-5 py-4">{edit_action}</td><td class="px-5 py-4">{delete_action}</td></tr>')
                rows=''.join(row_html)
                send('admin_question_list',{'SET_TITLE':e(s['title']),'SET_ID':str(sid),'SET_SUMMARY':e(s['summary']),'SET_STATUS':'Terbit' if s['published'] else 'Draft','QUESTION_ROWS':rows,'ATTEMPT_COUNT':str(locked),'BANK_ERROR':'','LOCK_NOTICE':'<div class="notice mt-5">Paket ini memiliki riwayat attempt. Paket dan soal dikunci agar skor, jawaban, serta pembahasan lama tidak berubah.</div>' if locked else '', 'DELETE_DISABLED':'disabled' if locked else '', 'DELETE_NOTE':'Riwayat tryout mengunci paket.' if locked else 'Paket tanpa riwayat dapat dihapus beserta soal.'});return
            if path.startswith('/admin/bank-soal/') and path.endswith('/soal/baru'):
                
                sid=path.split('/')[3];s=c.execute('SELECT id,title FROM question_sets WHERE id=?',(sid,)).fetchone()
                if not s:self.send_html('Not found',404);return
                pos=c.execute('SELECT COALESCE(MAX(position),0)+1 FROM questions WHERE set_id=?',(sid,)).fetchone()[0]
                values=question_editor_values(c,sid);values['SET_TITLE']=e(s['title']);send('admin_question_form',values);return
            if path.startswith('/admin/bank-soal/soal/') and path.endswith('/edit'):
                
                qid=path.split('/')[4];q=c.execute('SELECT q.*,s.title set_title FROM questions q JOIN question_sets s ON s.id=q.set_id WHERE q.id=?',(qid,)).fetchone()
                if not q:self.send_html('Not found',404);return
                locked=bool(c.execute('SELECT COUNT(*) FROM attempts WHERE set_id=?',(q['set_id'],)).fetchone()[0] or c.execute('SELECT COUNT(*) FROM attempt_questions WHERE question_id=?',(qid,)).fetchone()[0])
                send('admin_question_form',question_editor_values(c,q['set_id'],q,locked));return
            if path=='/admin/kursus/baru':
                
                send('admin_course_form',{'FORM_ACTION':'/admin/kursus/simpan','FORM_HEADING':'Tambah program','COURSE_ID':'','COURSE_TITLE':'','COURSE_SLUG':'','COURSE_DESCRIPTION':'','COURSE_CATEGORY':'','COURSE_PRICE_LABEL':'','COURSE_COVER_URL':'','LEVEL_OPTIONS':'<option>Pemula</option><option>Menengah</option><option>Semua tingkat</option>','STATUS_OPTIONS':'<option value="draft">Draft</option><option value="published">Terbit</option>','COURSE_MODULE_ROWS':''});return
            if path.startswith('/admin/kursus/') and path.endswith('/modul/baru'):
                
                pid=path.split('/')[3];p=c.execute('SELECT id FROM programs WHERE id=?',(pid,)).fetchone()
                if not p:self.send_html('Not found',404);return
                send('admin_module_form',{'FORM_ACTION':'/admin/modul/simpan','FORM_HEADING':'Tambah modul','COURSE_ID':str(pid),'MODULE_ID':'','MODULE_TITLE':'','MODULE_DESCRIPTION':'','MODULE_POSITION':'1','MODULE_PUBLISHED_CHECKED':'checked','MODULE_LESSON_ROWS':''});return
            if path.startswith('/admin/kursus/') and path.endswith('/edit'):
                
                pid=path.split('/')[3];p=c.execute('SELECT * FROM programs WHERE id=?',(pid,)).fetchone()
                if not p:self.send_html('Not found',404);return
                ms=c.execute('SELECT * FROM modules WHERE program_id=? ORDER BY position,id',(pid,)).fetchall();mr=''.join(f'<a class="glass block rounded-xl p-4" href="/admin/modul/{m["id"]}/edit">{e(m["title"])} · edit modul/pelajaran</a>' for m in ms)
                send('admin_course_form',{'FORM_ACTION':'/admin/kursus/simpan','FORM_HEADING':'Ubah program','COURSE_ID':str(pid),'COURSE_TITLE':e(p['title']),'COURSE_SLUG':e(p['slug']),'COURSE_DESCRIPTION':e(p['description']),'COURSE_CATEGORY':e(p['category']),'COURSE_PRICE_LABEL':money(p['price']),'COURSE_COVER_URL':e(p['cover_url']),'LEVEL_OPTIONS':f'<option selected>{e(p["level"])}</option><option>Pemula</option><option>Menengah</option><option>Semua tingkat</option>','STATUS_OPTIONS':f'<option value="draft" {"selected" if p["status"]=="draft" else ""}>Draft</option><option value="published" {"selected" if p["status"]=="published" else ""}>Terbit</option>','COURSE_MODULE_ROWS':mr});return
            if path.startswith('/admin/modul/') and path.endswith('/edit'):
                
                mid=path.split('/')[3];m=c.execute('SELECT * FROM modules WHERE id=?',(mid,)).fetchone()
                if not m:self.send_html('Not found',404);return
                lessons=c.execute('SELECT * FROM lessons WHERE module_id=? ORDER BY position,id',(mid,)).fetchall();lr=''.join(f'<a class="glass block rounded-xl p-3" href="/admin/pelajaran/{l["id"]}/edit">{e(l["title"])}</a>' for l in lessons)
                send('admin_module_form',{'FORM_ACTION':'/admin/modul/simpan','FORM_HEADING':'Edit modul','COURSE_ID':str(m['program_id']),'MODULE_ID':str(mid),'MODULE_TITLE':e(m['title']),'MODULE_DESCRIPTION':'','MODULE_POSITION':str(m['position']),'MODULE_PUBLISHED_CHECKED':'checked','MODULE_LESSON_ROWS':lr});return
            if path.startswith('/admin/modul/') and path.endswith('/pelajaran/baru'):
                
                mid=path.split('/')[3];m=c.execute('SELECT * FROM modules WHERE id=?',(mid,)).fetchone();send('admin_lesson_form',{'FORM_ACTION':'/admin/pelajaran/simpan','FORM_HEADING':'Tambah pelajaran','COURSE_ID':str(m['program_id'] if m else ''),'MODULE_ID':mid,'LESSON_ID':'','LESSON_TITLE':'','LESSON_DESCRIPTION':'','LESSON_DURATION':'0','LESSON_POSITION':'1','LESSON_RESOURCES':'','YOUTUBE_ID':'','LESSON_PUBLISHED_CHECKED':'checked'});return
            if path.startswith('/admin/pelajaran/') and path.endswith('/edit'):
                
                lid=path.split('/')[3];l=c.execute('SELECT l.*,m.program_id FROM lessons l JOIN modules m ON m.id=l.module_id WHERE l.id=?',(lid,)).fetchone();vid=l['video_url'].split('/')[-1] if l else '';send('admin_lesson_form',{'FORM_ACTION':'/admin/pelajaran/simpan','FORM_HEADING':'Edit pelajaran','COURSE_ID':str(l['program_id'] if l else ''),'MODULE_ID':str(l['module_id'] if l else ''),'LESSON_ID':lid,'LESSON_TITLE':e(l['title'] if l else ''),'LESSON_DESCRIPTION':e(l['body'] if l else ''),'LESSON_DURATION':str(l['duration_min'] if l else 0),'LESSON_POSITION':str(l['position'] if l else 1),'LESSON_RESOURCES':e(l['resource_url'] if l else ''),'YOUTUBE_ID':e(vid),'LESSON_PUBLISHED_CHECKED':'checked'});return
                if not u:self.redirect('/login');return
                aid=path.strip('/').split('/')[-2];a=c.execute('SELECT * FROM attempts WHERE id=? AND user_id=?',(aid,u['id'])).fetchone()
                if not a:self.send_html('Not found',404);return
                details=c.execute('SELECT q.prompt,q.explanation,aa.answer,aa.correct,q.answer correct_answer FROM attempt_answers aa JOIN questions q ON q.id=aa.question_id WHERE aa.attempt_id=? ORDER BY q.position',(aid,)).fetchall();send('tryout-result',{'SCORE':str(a['score']),'TOTAL':str(a['total']),'ANSWER_REVIEW':''.join(f'<div class="glass mt-3 rounded-xl p-4"><b>{e(d["prompt"])}</b><p class="mt-2 text-sm">Jawaban kamu: {e(d["answer"])} · Kunci: {e(d["correct_answer"])}</p><p class="mt-1 text-sm text-blue-100/60">{e(d["explanation"])}</p></div>' for d in details)});return
            if path.startswith('/tryouts/'):
                slug=path.split('/')[-1];s=c.execute('SELECT * FROM question_sets WHERE slug=? AND published=1',(slug,)).fetchone()
                if not s:self.send_html('Not found',404);return
                qs=c.execute('SELECT * FROM questions WHERE set_id=? ORDER BY position,id',(s['id'],)).fetchall();send('tryout-detail',{'TRYOUT_TITLE':e(s['title']),'TRYOUT_SUMMARY':e(s['summary']),'DURATION':str(s['duration_min']),'QUESTION_COUNT':str(len(qs)),'SET_ID':str(s['id']),'CSRF_TOKEN':e(csrf)});return
            if path=='/schedule':
                rows=c.execute('SELECT * FROM live_sessions WHERE published=1 AND starts_at>=datetime("now") ORDER BY starts_at').fetchall();send('schedule',{'SESSION_CARDS':''.join(f'<article class="glass rounded-2xl p-5"><p class="text-xs text-sky-200">{e(x["starts_at"])} · {x["duration_min"]} menit</p><h2 class="mt-2 text-xl font-semibold">{e(x["title"])}</h2><p class="mt-1 text-sm text-white/55">{e(x["subject"])} · {e(x["mentor"])}</p></article>' for x in rows)});return
            if path=='/articles':
                rows=c.execute('SELECT * FROM articles WHERE published=1 ORDER BY created_at DESC').fetchall();send('articles',{'ARTICLE_CARDS':''.join(f'<a class="glass block rounded-2xl p-5" href="/articles/{e(x["slug"])}"><p class="text-xs text-sky-200">{e(x["category"])}</p><h2 class="mt-2 text-xl font-semibold">{e(x["title"])}</h2><p class="mt-2 text-sm text-white/55">{e(x["summary"])}</p></a>' for x in rows)});return
            if path.startswith('/articles/'):
                a=c.execute('SELECT * FROM articles WHERE slug=? AND published=1',(path.split('/')[-1],)).fetchone()
                if not a:self.send_html('Not found',404);return
                send('article-detail',{'ARTICLE_TITLE':e(a['title']),'ARTICLE_BODY':e(a['body']),'CATEGORY':e(a['category'])});return
            if path=='/signup':send('auth',{'AUTH_TITLE':'Buat akun pelajar','FORM_ACTION':'/signup','AUTH_MODE':'signup'});return
            if path=='/login':send('auth',{'AUTH_TITLE':'Masuk ke Aster','FORM_ACTION':'/login','AUTH_MODE':'login'});return
            if path=='/dashboard':
                if not u:self.redirect('/login');return
                if u['role'] in ('super_admin','admin','teacher') and any(self.can(u,p) for p in ('dashboard.view','programs.view','question_banks.view','enrollments.view')):self.redirect('/admin');return
                rows=c.execute('SELECT p.*,e.created_at FROM enrollments e JOIN programs p ON p.id=e.program_id WHERE e.user_id=? AND e.status="active"',(u['id'],)).fetchall(); send('dashboard',{'ENROLLED_PROGRAMS':self.cards(rows,'program'),'USER_NAME':e(u['name'])});return
            if path.startswith('/learn/'):
                if not u:self.redirect('/login');return
                parts=path.strip('/').split('/');slug=parts[1] if len(parts)>1 else ''; lesson_id=parts[2] if len(parts)>2 else ''
                p=c.execute('SELECT p.* FROM programs p JOIN enrollments en ON en.program_id=p.id WHERE p.slug=? AND en.user_id=? AND en.status="active"',(slug,u['id'])).fetchone()
                lesson=c.execute('SELECT l.*,m.title module_title FROM lessons l JOIN modules m ON m.id=l.module_id WHERE l.id=? AND m.program_id=?',(lesson_id,p['id'] if p else -1)).fetchone() if lesson_id.isdigit() else None
                if not p or not lesson:self.send_html('Not found',404);return
                video=lesson['video_url'];video=re.sub(r'(?:watch\\?v=|youtu\\.be/)([\\w-]+).*',r'https://www.youtube-nocookie.com/embed/\\1',video)
                send('lesson',{'PROGRAM_TITLE':e(p['title']),'LESSON_TITLE':e(lesson['title']),'LESSON_BODY':e(lesson['body']),'VIDEO_URL':e(video),'LESSON_ID':str(lesson['id']),'PROGRAM_SLUG':e(slug),'CSRF_TOKEN':e(csrf)});return
            if path=='/admin':
                
                ps=c.execute('SELECT p.*,i.name institution FROM programs p LEFT JOIN institutions i ON i.id=p.institution_id ORDER BY p.id DESC').fetchall();send('admin',{'ADMIN_PROGRAMS':self.cards(ps,'program',admin=True),'ADMIN_USER':e(u['name'])});return
        self.send_html('Not found',404)
    def cards(self,rows,kind,admin=False):
        out=[]
        for r in rows:
            if kind=='tryout':href='/tryout/'+e(r['slug']);title=e(r['title']);summary=e(r['summary']);meta=f'{r["question_count"]} soal · {r["duration_min"]} menit'
            else:href='/program/'+e(r['slug']);title=e(r['title']);summary=e(r['summary']);meta=e(r['institution'] or r['level'] or '')+' · '+money(r['price'])
            progress=''
            label='Lihat program' if kind=='program' else 'Mulai tryout'
            if kind=='program' and 'lesson_total' in r.keys():
                done=r['lesson_done'];total=r['lesson_total'];percent=round(100*done/total) if total else 0;href='/belajar/'+e(r['slug']);label='Lanjutkan belajar';progress=f'<div class="mt-4"><div class="flex justify-between text-xs text-slate-500"><span>Progres</span><span>{percent}%</span></div><div class="mt-2 h-1.5 rounded bg-slate-100"><div class="h-full rounded bg-blue-600" style="width:{percent}%"></div></div></div>'
                if total:
                    with connect() as c:
                        first=c.execute('SELECT l.id FROM lessons l JOIN modules m ON m.id=l.module_id WHERE m.program_id=? ORDER BY m.position,l.position LIMIT 1',(r['id'],)).fetchone()
                        token=ref_for(c,'lesson',first['id']) if first else None
                    if token:href+='/'+token
            if admin:href=f'/admin/kursus/{r["id"]}/edit'
            image=(f'<img src="{e(r["cover_url"])}" alt="" loading="lazy" class="h-full w-full object-cover">' if kind=='program' and 'cover_url' in r.keys() and r['cover_url'] else '')
            visual=image or '<div class="grid h-full place-items-center bg-gradient-to-br from-blue-50 via-indigo-50 to-sky-100"><span class="grid h-14 w-14 place-items-center rounded-2xl bg-white text-2xl font-black text-blue-700 shadow-sm">A</span></div>'
            out.append(f'<a href="{href}" class="group block overflow-hidden rounded-2xl border border-slate-200 bg-white text-left text-slate-800 shadow-sm transition duration-200 hover:-translate-y-1 hover:border-blue-200 hover:shadow-lg"><div class="h-36 overflow-hidden">{visual}</div><div class="p-5"><p class="text-xs font-semibold text-blue-700">{meta}</p><h3 class="mt-2 text-xl font-bold leading-snug text-[#15345d]">{title}</h3><p class="mt-2 line-clamp-3 text-sm leading-6 text-slate-600">{summary}</p>{progress}<span class="mt-5 inline-flex items-center gap-2 text-sm font-bold text-blue-700">{label}<span aria-hidden="true" class="transition group-hover:translate-x-1">→</span></span></div></a>')
        if out: return ''.join(out)
        if kind=='program':
            return '<div class="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center md:col-span-2 lg:col-span-3"><span class="mx-auto grid h-12 w-12 place-items-center rounded-xl bg-blue-50 text-xl text-blue-700">⌕</span><h3 class="mt-4 text-lg font-bold text-[#15345d]">Program belum tersedia</h3><p class="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-600">Program baru akan muncul setelah tim Aster menerbitkannya. Coba kembali nanti atau lihat latihan tryout yang tersedia.</p><a class="mt-4 inline-flex font-bold text-blue-700" href="/tryout">Jelajahi tryout →</a></div>'
        return '<div class="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center md:col-span-2 lg:col-span-3"><h3 class="text-lg font-bold text-[#15345d]">Belum ada latihan untuk ditampilkan</h3><p class="mt-2 text-sm text-slate-600">Tryout baru akan muncul di sini setelah diterbitkan.</p></div>'
    def do_GET(self):
        parsed=urlparse(self.path);self.get(parsed.path,parse_qs(parsed.query))
    def do_POST(self):
        try:form,files=parse_post_body(self)
        except ValueError as ex:self.send_html(e(str(ex)),413);return
        u=self.user()
        if not self.csrf_ok(form,u):self.send_html('Permintaan tidak valid. Muat ulang halaman.',403);return
        path=urlparse(self.path).path
        resolved=self.resolve_public_path(path)
        if resolved is None:self.send_html('Not found',404);return
        path=resolved
        if path in ('/signup','/login','/daftar','/masuk'):
            name=form.get('name','').strip();email=form.get('email','').strip().lower();pw=form.get('password','')
            signup=path in ('/signup','/daftar')
            if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',email) or len(pw)<10 or (signup and not name):self.send_html(self.template('signup' if signup else 'login',{'FORM_ERROR':'<p class="text-rose-300">Periksa data; kata sandi minimal 10 karakter.</p>','AUTH_INTRO':'Silakan coba lagi.','AUTH_SWITCH_TEXT':'','AUTH_SWITCH_LABEL':'','AUTH_SWITCH_URL':'#','EMAIL_VALUE':e(email),'NAME_VALUE':e(name),'PASSWORD_AUTOCOMPLETE':'new-password' if signup else 'current-password','SUBMIT_LABEL':'Buat akun' if signup else 'Masuk'}),400);return
            with connect() as c:
                if signup:
                    try:uid=c.execute('INSERT INTO users(name,email,password_hash) VALUES (?,?,?)',(name,email,passhash(pw))).lastrowid
                    except sqlite3.IntegrityError:self.send_html('Email sudah terdaftar. <a href="/login">Masuk</a>',409);return
                else:
                    row=c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
                    if not row or not verify(pw,row['password_hash']):
                        time.sleep(0.5)
                        self.send_html('Email atau kata sandi salah. <a href="/login">Coba lagi</a>',401);return
                    uid=row['id']
            cookies=self.issue_session(uid);self.send_response(303);self.send_header('Location','/dashboard');[self.send_header('Set-Cookie',f'{k}={v}') for k,v in cookies];self.end_headers();return
        if path in ('/profil/update','/profil/password'):
            if not u or not self.can(u,'profile.update'):self.send_html('Forbidden',403);return
            if path=='/profil/update':
                name=form.get('display_name','').strip();email=form.get('email','').strip().lower()
                if not name or len(name)>100 or not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',email):self.send_html('Nama dan alamat email valid wajib diisi.',400);return
                try:
                    with connect() as c:c.execute('UPDATE users SET name=?,email=? WHERE id=?',(name,email,u['id']))
                except sqlite3.IntegrityError:self.send_html('Email tersebut sudah digunakan.',409);return
                self.redirect('/profil?status=Informasi+akun+berhasil+diperbarui');return
            current=form.get('current_password','');new=form.get('new_password','');confirm=form.get('confirm_password','')
            if not verify(current,u['password_hash']) or len(new)<10 or new!=confirm:self.send_html('Kata sandi saat ini salah atau kata sandi baru tidak cocok (minimal 10 karakter).',400);return
            ck=SimpleCookie();ck.load(self.headers.get('Cookie',''));tok=ck.get(COOKIE);keep_hash=hashlib.sha256(tok.value.encode()).hexdigest() if tok else ''
            with connect() as c:
                c.execute('UPDATE users SET password_hash=? WHERE id=?',(passhash(new),u['id']))
                if keep_hash:c.execute('DELETE FROM sessions WHERE user_id=? AND token_hash<>?',(u['id'],keep_hash))
            self.redirect('/profil?status=Kata+sandi+berhasil+diperbarui');return
        if path=='/logout':
            if u:
                ck=SimpleCookie();ck.load(self.headers.get('Cookie',''));tok=ck.get(COOKIE)
                if tok:
                    with connect() as c:c.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(tok.value.encode()).hexdigest(),))
            self.send_response(303);self.send_header('Location','/');self.send_header('Set-Cookie',f'{COOKIE}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax');self.end_headers();return
        if path.startswith('/admin') and not self.admin_allowed(u,'POST',path,form):
            self.send_html('Forbidden',403);return
        if path.startswith('/admin/menu/'):
            if not u or u['role']!='super_admin': self.send_html('Forbidden',403);return
            try:
                with connect() as c:
                    c.execute('BEGIN IMMEDIATE')
                    if path=='/admin/menu/simpan':
                        from services.menu_service import save_menu
                        from services.menu_scaffold import ensure_menu_scaffold
                        save_menu(c,form)
                        ensure_menu_scaffold(TEMPLATES, form.get('route_key','').strip(), form.get('path','').strip(), form.get('label','').strip())
                    elif path=='/admin/menu/akses-role':
                        from services.menu_service import set_role_menus
                        role=form.get('role',''); keys=form.get('route_keys','').split(',') if form.get('route_keys') else []
                        set_role_menus(c,role,keys)
                    elif path=='/admin/menu/urut':
                        order=[x for x in form.get('route_keys','').split(',') if x]
                        known={r['route_key'] for r in c.execute('SELECT route_key FROM route_menu_registry')}
                        if len(order)!=len(set(order)) or set(order)!=known: raise ValueError('Urutan harus memuat setiap menu tepat satu kali.')
                        c.executemany('UPDATE route_menu_registry SET position=? WHERE route_key=?',((i*10,k) for i,k in enumerate(order,1)))
                    elif path=='/admin/menu/hapus':
                        key=form.get('route_key','')
                        if key in ('admin.dashboard','admin.roles'): raise ValueError('Menu inti tidak dapat dihapus.')
                        c.execute('DELETE FROM route_menu_registry WHERE route_key=?',(key,))
                    else: self.send_html('Not found',404);return
            except (ValueError,TypeError) as ex:self.send_html(e(str(ex)),400);return
            self.send_json({'ok':True});return
        if path=='/admin/artikel/simpan':
            article_id=form.get('article_id','');title=re.sub(r'<[^>]*>','',sanitize_rich_html(form.get('title','').strip())).strip();slug=form.get('slug','').strip().lower();category=re.sub(r'<[^>]*>','',sanitize_rich_html(form.get('category','').strip())).strip();summary=sanitize_rich_html(form.get('summary','').strip());body=sanitize_rich_html(form.get('body','').strip());published=form.get('published')=='1'
            if not title or len(title)>160 or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',slug) or len(slug)>160 or len(category)>100 or len(summary)>500 or not body or len(body)>20000:self.send_html('Data artikel tidak valid.',400);return
            if published and not self.can(u,'articles.publish'):self.send_html('Forbidden',403);return
            if article_id and not article_id.isdigit():self.send_html('Artikel tidak valid.',400);return
            with connect() as c:
                try:
                    if article_id:
                        if not c.execute('SELECT 1 FROM articles WHERE id=?',(article_id,)).fetchone():self.send_html('Not found',404);return
                        c.execute('UPDATE articles SET title=?,slug=?,category=?,summary=?,body=?,published=?,updated_at=CURRENT_TIMESTAMP WHERE id=?',(title,slug,category,summary,body,int(published),article_id))
                    else:c.execute('INSERT INTO articles(slug,title,summary,body,category,published,updated_at) VALUES (?,?,?,?,?,?,CURRENT_TIMESTAMP)',(slug,title,summary,body,category,int(published)))
                except sqlite3.IntegrityError:self.send_html('Slug artikel sudah digunakan.',409);return
            self.redirect('/admin/artikel');return
        if path in ('/admin/artikel/status','/admin/artikel/hapus'):
            article_id=form.get('article_id','')
            if not article_id.isdigit():self.send_html('Artikel tidak valid.',400);return
            with connect() as c:
                if path.endswith('status'):
                    if form.get('published') not in ('0','1'):self.send_html('Status tidak valid.',400);return
                    if not c.execute('UPDATE articles SET published=?,updated_at=CURRENT_TIMESTAMP WHERE id=?',(int(form['published']),article_id)).rowcount:self.send_html('Not found',404);return
                elif not c.execute('DELETE FROM articles WHERE id=?',(article_id,)).rowcount:self.send_html('Not found',404);return
            self.redirect('/admin/artikel');return
        if path=='/admin/jadwal/simpan':
            session_id=form.get('session_id','');title=form.get('title','').strip();subject=form.get('subject','').strip();starts=form.get('starts_at','').strip().replace('T',' ');mentor=form.get('mentor','').strip();join_url=form.get('join_url','').strip();published=form.get('published')=='1'
            try:duration=int(form.get('duration_min','')) ;datetime.strptime(starts,'%Y-%m-%d %H:%M')
            except ValueError:self.send_html('Waktu atau durasi jadwal tidak valid.',400);return
            if not title or len(title)>160 or len(subject)>100 or len(mentor)>100 or not 1<=duration<=600 or len(join_url)>500 or (join_url and not re.fullmatch(r'https://[^\s/@]+(?:/[^\s]*)?',join_url)) or (session_id and not session_id.isdigit()):self.send_html('Data jadwal tidak valid.',400);return
            if published and not self.can(u,'live_sessions.publish'):self.send_html('Forbidden',403);return
            with connect() as c:
                if session_id:
                    if not c.execute('SELECT 1 FROM live_sessions WHERE id=?',(session_id,)).fetchone():self.send_html('Not found',404);return
                    c.execute('UPDATE live_sessions SET title=?,subject=?,starts_at=?,duration_min=?,mentor=?,join_url=?,published=?,updated_at=CURRENT_TIMESTAMP WHERE id=?',(title,subject,starts,duration,mentor,join_url,int(published),session_id))
                else:c.execute('INSERT INTO live_sessions(title,subject,starts_at,duration_min,mentor,join_url,published,updated_at) VALUES (?,?,?,?,?,?,?,CURRENT_TIMESTAMP)',(title,subject,starts,duration,mentor,join_url,int(published)))
            self.redirect('/admin/jadwal');return
        if path in ('/admin/jadwal/status','/admin/jadwal/hapus'):
            session_id=form.get('session_id','')
            if not session_id.isdigit():self.send_html('Jadwal tidak valid.',400);return
            with connect() as c:
                if path.endswith('status'):
                    if form.get('published') not in ('0','1'):self.send_html('Status tidak valid.',400);return
                    if not c.execute('UPDATE live_sessions SET published=?,updated_at=CURRENT_TIMESTAMP WHERE id=?',(int(form['published']),session_id)).rowcount:self.send_html('Not found',404);return
                elif not c.execute('DELETE FROM live_sessions WHERE id=?',(session_id,)).rowcount:self.send_html('Not found',404);return
            self.redirect('/admin/jadwal');return
        if path=='/admin/kategori-soal/simpan':
            key=form.get('key','').strip().lower();name=form.get('name','').strip();description=form.get('description','').strip();parent_id=form.get('parent_id','')
            try:position=int(form.get('position','0'));profile_id=int(form.get('profile_id','0'));item_count=int(form.get('item_count','0'));correct=int(form.get('correct_score','0'));incorrect=int(form.get('incorrect_score','0'));blank=int(form.get('blank_score','0'));maximum=int(form.get('max_score','0'));passing=int(form['passing_score']) if form.get('passing_score','').strip() else None
            except ValueError:self.send_html('Nilai kategori tidak valid.',400);return
            if not re.fullmatch(r'[a-z0-9_-]{2,80}',key) or not name or len(name)>100 or len(description)>300 or not 0<=position<=10000 or not 0<=item_count<=500 or not -9999<=correct<=9999 or not -9999<=incorrect<=9999 or not -9999<=blank<=9999 or not 0<=maximum<=99999 or (passing is not None and not 0<=passing<=99999) or form.get('scoring_mode') not in ('correctness','option_points'):
                self.send_html('Periksa nama, kunci, posisi, dan angka aturan nilai.',400);return
            with connect() as c:
                parent=int(parent_id) if parent_id.isdigit() else None
                if parent and not c.execute('SELECT id FROM question_categories WHERE id=?',(parent,)).fetchone():self.send_html('Kategori induk tidak ditemukan.',400);return
                cid=form.get('id','')
                reserved={'twk','tiu','tkp','unclassified'}
                try:
                    if cid:
                        if not cid.isdigit() or parent==int(cid):self.send_html('Kategori tidak valid atau menjadi induknya sendiri.',400);return
                        existing=c.execute('SELECT key,parent_id,active FROM question_categories WHERE id=?',(cid,)).fetchone()
                        if not existing:self.send_html('Kategori tidak ditemukan.',404);return
                        if existing['key'] in reserved and (key!=existing['key'] or parent is not None or form.get('active')!='1'):
                            self.send_html('Kategori inti tetap aktif dengan kode dan struktur tetap; nama serta aturan skornya masih dapat diubah.',409);return
                        if key in reserved and key!=existing['key']:
                            self.send_html('Kode tersebut hanya dapat digunakan oleh kategori inti.',409);return
                        c.execute('UPDATE question_categories SET key=?,name=?,description=?,parent_id=?,position=?,active=? WHERE id=?',(key,name,description,parent,position,int(form.get('active')=='1'),cid))
                        if not c.execute('SELECT changes()').fetchone()[0]:self.send_html('Kategori tidak ditemukan.',404);return
                    else:
                        if key in reserved:self.send_html('Kode tersebut hanya dapat digunakan oleh kategori inti.',409);return
                        cid=c.execute('INSERT INTO question_categories(key,name,description,parent_id,position,active) VALUES (?,?,?,?,?,?)',(key,name,description,parent,position,int(form.get('active')=='1'))).lastrowid
                    if profile_id:
                        if not c.execute('SELECT id FROM exam_rule_profiles WHERE id=?',(profile_id,)).fetchone():self.send_html('Profil aturan tidak ditemukan.',400);return
                        mode=form.get('scoring_mode')
                        category_root=c.execute('SELECT COALESCE(parent.key,question_categories.key) root_key FROM question_categories LEFT JOIN question_categories parent ON parent.id=question_categories.parent_id WHERE question_categories.id=?',(cid,)).fetchone()['root_key']
                        if mode=='option_points' and category_root!='tkp':self.send_html('Mode poin per opsi hanya tersedia untuk kategori TKP dan subkategorinya.',400);return
                        opt_min=1 if mode=='option_points' else None;opt_max=5 if mode=='option_points' else None
                        c.execute('''INSERT INTO category_scoring_rules(profile_id,category_id,item_count,correct_score,incorrect_score,blank_score,max_score,passing_score,scoring_mode,option_score_min,option_score_max) VALUES (?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(profile_id,category_id) DO UPDATE SET item_count=excluded.item_count,correct_score=excluded.correct_score,incorrect_score=excluded.incorrect_score,blank_score=excluded.blank_score,max_score=excluded.max_score,passing_score=excluded.passing_score,scoring_mode=excluded.scoring_mode,option_score_min=excluded.option_score_min,option_score_max=excluded.option_score_max''',(profile_id,cid,item_count,correct,incorrect,blank,maximum,passing,mode,opt_min,opt_max))
                except sqlite3.IntegrityError:self.send_html('Kunci kategori sudah digunakan atau kategori terkait dengan aturan yang tidak dapat dihapus.',409);return
            with connect() as c:
                saved_key=c.execute('SELECT key FROM question_categories WHERE id=?',(cid,)).fetchone()
                saved_profile=c.execute('SELECT key FROM exam_rule_profiles WHERE id=?',(profile_id,)).fetchone() if profile_id else None
            self.redirect('/admin/kategori-soal?edit='+urlencode({'edit':saved_key['key'] if saved_key else '', 'profile':saved_profile['key'] if saved_profile else ''})[5:]);return
        if path=='/admin/kategori-soal/hapus':
            cid=form.get('id','')
            if not cid.isdigit():self.send_html('Kategori tidak valid.',400);return
            with connect() as c:
                category=c.execute('SELECT key FROM question_categories WHERE id=?',(cid,)).fetchone()
                if category and category['key'] in ('twk','tiu','tkp','unclassified'):
                    self.send_html('Kategori inti tidak dapat dihapus. Nonaktifkan hanya kategori tambahan yang tidak lagi digunakan.',409);return
                used=c.execute('SELECT (SELECT COUNT(*) FROM questions WHERE category_id=?)+(SELECT COUNT(*) FROM question_categories WHERE parent_id=?)+(SELECT COUNT(*) FROM exam_blueprint_categories WHERE category_id=?)+(SELECT COUNT(*) FROM category_scoring_rules WHERE category_id=?)',(cid,cid,cid,cid)).fetchone()[0]
                if used:self.send_html('Kategori masih digunakan; nonaktifkan agar riwayat dan blueprint tetap utuh.',409);return
                c.execute('DELETE FROM question_categories WHERE id=?',(cid,))
            self.redirect('/admin/kategori-soal');return
        if path=='/admin/media/soal':
            upload=files.get('image') or files.get('file')
            if not upload:self.send_html('Pilih gambar yang akan diunggah.',400);return
            original,mime,payload=upload
            signatures={'image/png':payload.startswith(b'\x89PNG\r\n\x1a\n'),'image/jpeg':payload.startswith(b'\xff\xd8\xff'),'image/gif':payload.startswith((b'GIF87a',b'GIF89a')),'image/webp':len(payload)>=12 and payload[:4]==b'RIFF' and payload[8:12]==b'WEBP'}
            alt=form.get('alt_text','').strip()
            if len(payload)>5*1024*1024 or not payload or mime not in signatures or not signatures[mime]:self.send_html('Gambar harus PNG, JPEG, WebP, atau GIF yang valid dan maksimal 5 MB.',415);return
            if not alt or len(alt)>250:self.send_html('Teks alternatif gambar wajib diisi (maksimal 250 karakter).',400);return
            qid=form.get('question_id','');usage=form.get('usage','stem')
            if qid:
                if not qid.isdigit():self.send_html('Soal media tidak valid.',400);return
                if usage not in ('stem','option','explanation','instruction') or (usage=='option' and form.get('option_key') not in tuple('ABCDE')):self.send_html('Tujuan gambar tidak valid.',400);return
                with connect() as c:
                    q=c.execute('SELECT id,set_id FROM questions WHERE id=?',(qid,)).fetchone()
                    if not q:self.send_html('Soal tidak ditemukan.',404);return
                    if c.execute('SELECT COUNT(*) FROM attempts WHERE set_id=?',(q['set_id'],)).fetchone()[0] or c.execute('SELECT COUNT(*) FROM attempt_questions WHERE question_id=?',(qid,)).fetchone()[0]:self.send_html('Soal telah digunakan dalam attempt; media baru tidak dapat ditambahkan.',409);return
            ext={'image/png':'png','image/jpeg':'jpg','image/webp':'webp','image/gif':'gif'}[mime];filename=secrets.token_hex(16)+'.'+ext;alt=alt[:250]
            media_dir=BASE/'media';media_dir.mkdir(parents=True,exist_ok=True);(media_dir/filename).write_bytes(payload)
            try:
                with connect() as c:
                    c.execute('INSERT INTO media_assets(storage_key,original_name,mime_type,byte_size,alt_text,checksum_sha256,uploaded_by) VALUES (?,?,?,?,?,?,?)',(filename,Path(original).name[:250],mime,len(payload),alt,hashlib.sha256(payload).hexdigest(),u['id'] if u else None))
                    asset_id=c.execute('SELECT last_insert_rowid()').fetchone()[0]
                    if qid:
                        c.execute('INSERT OR IGNORE INTO question_media(question_id,asset_id,option_key,usage) VALUES (?,?,?,?)',(qid,asset_id,form.get('option_key') or None,usage))
            except Exception:
                try:(media_dir/filename).unlink(missing_ok=True)
                except OSError:pass
                raise
            self.send_json({'url':'/media/'+filename,'filename':filename,'alt':alt,'id':asset_id},201);return
        if path=='/admin/akses-role/simpan':
            with connect() as c:
                c.execute('BEGIN IMMEDIATE')
                for role in ('admin','teacher','student'):
                    grants=[]
                    for key in ALL_PERMISSIONS:
                        if key.startswith('roles.') or role=='super_admin':continue
                        resource,action=ALL_PERMISSIONS[key]
                        grants.append((int(form.get(f'permission_{role}_{resource}_{action}')=='1'),role,key))
                    c.executemany('UPDATE role_permissions SET enabled=? WHERE role_key=? AND permission_key=?',grants)
            self.redirect('/admin/akses-role?status=Perubahan+izin+tersimpan');return
        if path=='/enroll':
            if not u:self.redirect('/login');return
            pid=form.get('course_id') or form.get('program_id','')
            with connect() as c:
                exists=c.execute("SELECT id FROM programs WHERE id=? AND status='published'",(pid,)).fetchone()
                if exists:c.execute('INSERT OR IGNORE INTO enrollments(user_id,program_id,status) VALUES (?,?,?)',(u['id'],pid,'pending'))
            self.redirect('/dashboard');return
        if path=='/admin/enrollment/approve':
            
            with connect() as c:c.execute("UPDATE enrollments SET status='active' WHERE id=? AND status='pending'",(form.get('enrollment_id',''),))
            self.redirect('/admin');return
        lesson_completion=re.fullmatch(r'/pelajaran/([^/]+)/selesai',path)
        if path=='/progress' or lesson_completion:
            if not u:self.redirect('/login');return
            if lesson_completion:
                with connect() as c:lid=resolve_ref(c,'lesson',lesson_completion.group(1))
                if lid is None:self.send_html('Not found',404);return
            else:lid=form.get('lesson_id','')
            with connect() as c:
                c.execute('INSERT OR IGNORE INTO lesson_progress(user_id,lesson_id) SELECT ?,l.id FROM lessons l JOIN modules m ON m.id=l.module_id JOIN enrollments en ON en.program_id=m.program_id WHERE l.id=? AND en.user_id=? AND en.status="active"',(u['id'],lid,u['id']))
            self.redirect('/dashboard');return
        if re.fullmatch(r'/tryout/\d+/mulai',path):
            if not u:self.redirect('/masuk');return
            sid=path.split('/')[2]
            with connect() as c:
                s=c.execute('SELECT id FROM question_sets WHERE id=? AND published=1',(sid,)).fetchone()
                if not s:self.send_html('Tryout tidak ditemukan.',404);return
                c.execute('BEGIN IMMEDIATE')
                aid=c.execute('INSERT INTO attempts(user_id,set_id) VALUES (?,?)',(u['id'],sid)).lastrowid
                try:build_attempt_snapshot(c,aid,sid)
                except ValueError as ex:c.execute('DELETE FROM attempts WHERE id=?',(aid,));self.send_html(e(str(ex)),409);return
                # Persist the public reference in the same transaction as the attempt.
                start_url=self.opaque_path('attempt',aid,'/tryout/{}/soal?n=1',c)
            self.redirect(start_url);return
        if re.fullmatch(r'/tryout/\d+/jawab',path) or re.fullmatch(r'/tryout/\d+/selesai',path):
            if not u:self.redirect('/login');return
            aid=path.split('/')[2]
            with connect() as c:
                a=c.execute('SELECT * FROM attempts WHERE id=? AND user_id=? AND finished_at IS NULL',(aid,u['id'])).fetchone()
                if not a:self.send_html('Tryout tidak ditemukan atau sudah selesai.',404);return
                if attempt_seconds_remaining(c,a)<=0:
                    path=f'/tryout/{aid}/selesai';form['confirm_submit']='yes'
                qid=form.get('question_id');ans=form.get('answer','')
                aq_rows=c.execute('SELECT * FROM attempt_questions WHERE attempt_id=? ORDER BY position',(aid,)).fetchall()
                if aq_rows:
                    valid_ids={str(r['question_id']):r for r in aq_rows if r['question_id'] is not None}
                    if qid in valid_ids and ans in tuple('ABCDE'):
                        aq=valid_ids[qid];snap=json.loads(aq['question_snapshot']);scoring=json.loads(aq['scoring_snapshot']);answer_key=snap.get('answer','')
                        correct=int(ans==answer_key)
                        if scoring.get('mode')=='option_points':
                            awarded=scoring.get('option_scores',{}).get(ans)
                            if awarded is None:self.send_html('Bobot pilihan TKP belum lengkap. Hubungi pengelola sebelum mengerjakan sesi ini.',409);return
                        else:awarded=scoring.get('correct_score',1) if correct else scoring.get('incorrect_score',0)
                        c.execute('''INSERT INTO attempt_answers(attempt_id,question_id,answer,correct,option_key,awarded_score,answer_snapshot) VALUES (?,?,?,?,?,?,?) ON CONFLICT(attempt_id,question_id) DO UPDATE SET answer=excluded.answer,correct=excluded.correct,option_key=excluded.option_key,awarded_score=excluded.awarded_score,answer_snapshot=excluded.answer_snapshot''',(aid,qid,ans,correct,ans,awarded,json.dumps({'option':ans,'correct':bool(correct),'awarded_score':awarded},ensure_ascii=False)))
                    current=valid_ids.get(qid);cur=(current['position']-1) if current else 0
                    if form.get('autosave') == '1':
                        self.send_json({'saved': bool(qid in valid_ids and ans in tuple('ABCDE')), 'question_id': qid})
                        return
                    if path.endswith('/selesai') or form.get('confirm_submit')=='yes':
                        breakdown={};total_score=0
                        for aq in aq_rows:
                            scoring=json.loads(aq['scoring_snapshot']);key=str(aq['category_id'] or 'lainnya');row=c.execute('SELECT awarded_score,answer FROM attempt_answers WHERE attempt_id=? AND question_id=?',(aid,aq['question_id'])).fetchone()
                            if row and row['answer'] is not None:awarded=row['awarded_score'] if row['awarded_score'] is not None else 0
                            else:
                                awarded=scoring.get('blank_score',0)
                                if aq['question_id'] is not None:c.execute('INSERT INTO attempt_answers(attempt_id,question_id,answer,correct,awarded_score) VALUES (?,?,NULL,0,?) ON CONFLICT(attempt_id,question_id) DO UPDATE SET answer=NULL,correct=0,awarded_score=excluded.awarded_score',(aid,aq['question_id'],awarded))
                            total_score+=awarded;breakdown.setdefault(key,{'score':0,'max_score':0,'answered':0,'count':0});breakdown[key]['score']+=awarded;breakdown[key]['max_score']+=scoring.get('max_score',1);breakdown[key]['answered']+=int(bool(row and row['answer'] is not None));breakdown[key]['count']+=1
                        maximum=c.execute('SELECT total FROM attempts WHERE id=?',(aid,)).fetchone()[0]
                        c.execute('UPDATE attempts SET score=?,total=?,score_breakdown_snapshot=?,finished_at=CURRENT_TIMESTAMP WHERE id=?',(total_score,maximum,json.dumps(breakdown,ensure_ascii=False),aid));self.redirect(self.opaque_path('attempt',aid,'/tryout/result/{}',c));return
                    nxt=max(0,cur-1) if form.get('direction')=='previous' else min(len(aq_rows)-1,cur+1)
                else:
                    if qid and ans in tuple('ABCDE'):
                        qrow=c.execute('SELECT answer FROM questions WHERE id=? AND set_id=?',(qid,a['set_id'])).fetchone()
                        if qrow:c.execute('INSERT INTO attempt_answers(attempt_id,question_id,answer,correct,awarded_score) VALUES (?,?,?,?,?) ON CONFLICT(attempt_id,question_id) DO UPDATE SET answer=excluded.answer,correct=excluded.correct,awarded_score=excluded.awarded_score',(aid,qid,ans,int(qrow['answer']==ans),int(qrow['answer']==ans)))
                    qs=c.execute('SELECT id FROM questions WHERE set_id=? ORDER BY position,id',(a['set_id'],)).fetchall();qids=[x['id'] for x in qs];cur=qids.index(int(qid)) if qid and int(qid) in qids else 0
                    if path.endswith('/selesai') or form.get('confirm_submit')=='yes':
                        c.execute('UPDATE attempts SET score=(SELECT COALESCE(SUM(correct),0) FROM attempt_answers WHERE attempt_id=?),total=?,finished_at=CURRENT_TIMESTAMP WHERE id=?',(aid,len(qids),aid));self.redirect(self.opaque_path('attempt',aid,'/tryout/result/{}',c));return
                    nxt=max(0,cur-1) if form.get('direction')=='previous' else min(len(qids)-1,cur+1)
            self.redirect(self.opaque_path('attempt',aid,f'/tryout/{{}}/soal?n={nxt+1}',c));return
        if path.startswith('/admin/bank-soal/'):
            
            with connect() as c:
                if path=='/admin/bank-soal/soal/urut':
                    sid=form.get('set_id','');raw=form.get('order','').split(',')
                    if not sid.isdigit() or not raw or any(not item.isdigit() for item in raw) or len(set(raw))!=len(raw):self.send_html('Urutan soal tidak valid.',400);return
                    bank=c.execute('SELECT id FROM question_banks WHERE legacy_question_set_id=?',(sid,)).fetchone()
                    if not bank:self.send_html('Bank soal tidak ditemukan.',404);return
                    current=[str(r['question_id']) for r in c.execute('SELECT question_id FROM question_bank_memberships WHERE bank_id=? ORDER BY position,question_id',(bank['id'],)).fetchall()]
                    if set(current)!=set(raw):self.send_html('Daftar soal berubah. Muat ulang sebelum mengurutkan.',409);return
                    c.executemany('UPDATE question_bank_memberships SET position=? WHERE bank_id=? AND question_id=?',[(i,bank['id'],int(qid)) for i,qid in enumerate(raw,1)])
                    self.send_json({'saved':True,'count':len(raw)});return
                if path=='/admin/bank-soal/blueprint/simpan':
                    sid=form.get('set_id','');name=form.get('name','').strip();profile_id=form.get('profile_id','');mode='random' if form.get('randomize')=='1' else 'manual'
                    try:duration=int(form.get('duration_min','0'))
                    except ValueError:duration=0
                    if not sid.isdigit() or not name or len(name)>160 or not profile_id.isdigit() or not 1<=duration<=600:
                        self.send_html('Nama, profil aturan, dan durasi blueprint harus valid.',400);return
                    source=c.execute('SELECT * FROM question_sets WHERE id=?',(sid,)).fetchone()
                    profile=c.execute('SELECT * FROM exam_rule_profiles WHERE id=? AND active=1',(profile_id,)).fetchone()
                    bank=c.execute('SELECT * FROM question_banks WHERE legacy_question_set_id=?',(sid,)).fetchone()
                    if not source or not profile or not bank:self.send_html('Paket bank atau profil aturan tidak ditemukan.',404);return
                    chosen=[]
                    for row in c.execute('SELECT id,key,name FROM question_categories WHERE active=1 AND parent_id IS NULL AND key<>\'unclassified\'').fetchall():
                        if form.get(f'category_{row["id"]}')!='1':continue
                        try:count=int(form.get(f'count_{row["id"]}','0'));position=int(form.get(f'order_{row["id"]}','0'))
                        except ValueError:self.send_html('Jumlah dan urutan kategori harus berupa angka.',400);return
                        if not 1<=count<=500 or not 1<=position<=500:self.send_html('Jumlah soal dan urutan kategori harus lebih besar dari nol.',400);return
                        available=c.execute('SELECT COUNT(DISTINCT q.id) FROM question_bank_memberships m JOIN questions q ON q.id=m.question_id WHERE m.bank_id=? AND (q.category_id=? OR q.category_id IN (SELECT id FROM question_categories WHERE parent_id=?)) AND q.status=\'active\'',(bank['id'],row['id'],row['id'])).fetchone()[0]
                        if count>available:self.send_html(f'Kategori {e(row["name"])} meminta {count} soal, sementara bank ini memiliki {available} soal aktif.',409);return
                        if not c.execute('SELECT 1 FROM category_scoring_rules WHERE profile_id=? AND category_id=?',(profile_id,row['id'])).fetchone():self.send_html(f'Aturan skor untuk kategori {e(row["name"])} belum tersedia pada profil ini.',409);return
                        chosen.append((row['id'],position,count))
                    if not chosen:self.send_html('Pilih setidaknya satu kategori untuk blueprint.',400);return
                    if len({x[1] for x in chosen})!=len(chosen):self.send_html('Nomor urutan kategori tidak boleh sama.',400);return
                    c.execute('BEGIN IMMEDIATE')
                    c.execute('''INSERT INTO exam_blueprints(key,name,profile_id,duration_min,selection_mode,created_by)
                        VALUES (?,?,?,?,?,?) ON CONFLICT(key) DO UPDATE SET name=excluded.name,profile_id=excluded.profile_id,duration_min=excluded.duration_min,selection_mode=excluded.selection_mode,updated_at=CURRENT_TIMESTAMP''',('set-'+sid,name,profile_id,duration,mode,u['id']))
                    blueprint=c.execute('SELECT id FROM exam_blueprints WHERE key=?',('set-'+sid,)).fetchone()[0]
                    c.execute('INSERT OR IGNORE INTO exam_blueprint_banks(blueprint_id,bank_id,position) VALUES (?,?,0)',(blueprint,bank['id']))
                    c.execute('DELETE FROM exam_blueprint_categories WHERE blueprint_id=?',(blueprint,))
                    c.executemany('INSERT INTO exam_blueprint_categories(blueprint_id,category_id,position,question_count,selection_mode) VALUES (?,?,?,?,?)',[(blueprint,cid,pos,count,'inherit') for cid,pos,count in chosen])
                    c.execute('UPDATE question_sets SET duration_min=? WHERE id=?',(duration,sid))
                    self.redirect(self.bank_path_for_set(sid,'/blueprint?saved=1',c));return
                if path=='/admin/bank-soal/paket/simpan':
                    title=form.get('title','').strip();slug=re.sub(r'[^a-z0-9]+','-',(form.get('slug') or title).lower()).strip('-');summary=form.get('summary','').strip()
                    try:duration=int(form.get('duration_min','30'))
                    except ValueError:duration=0
                    sid=form.get('set_id','')
                    if not title or len(title)>160 or not slug or len(slug)>180 or not 1<=duration<=600:
                        self.send_html('Judul, slug, dan durasi 1–600 menit wajib valid.',400);return
                    if form.get('published')=='1':
                        question_count=c.execute('SELECT COUNT(*) FROM questions WHERE set_id=?',(sid,)).fetchone()[0] if sid.isdigit() else 0
                        if not question_count:self.send_html('Tambahkan minimal satu soal sebelum menerbitkan paket. Simpan sebagai draft terlebih dahulu.',409);return
                    if sid:
                        if not sid.isdigit():self.send_html('Paket soal tidak valid.',400);return
                        if c.execute('SELECT COUNT(*) FROM attempts WHERE set_id=?',(sid,)).fetchone()[0]:self.send_html('Paket memiliki riwayat attempt dan dibekukan.',409);return
                        try:c.execute('UPDATE question_sets SET title=?,slug=?,summary=?,duration_min=?,published=? WHERE id=?',(title,slug,summary,duration,int(form.get('published')=='1'),sid))
                        except sqlite3.IntegrityError:self.send_html('Slug paket sudah digunakan.',409);return
                        if c.execute('SELECT changes()').fetchone()[0]==0:self.send_html('Paket tidak ditemukan.',404);return
                        sid=int(sid)
                    else:
                        try:sid=c.execute('INSERT INTO question_sets(slug,title,summary,duration_min,published) VALUES (?,?,?,?,?)',(slug,title,summary,duration,int(form.get('published')=='1'))).lastrowid
                        except sqlite3.IntegrityError:self.send_html('Slug paket sudah digunakan.',409);return
                    parent_value=form.get('parent_bank_id','').strip()
                    try:bank_id=ensure_legacy_question_bank(c,sid,int(parent_value) if parent_value.isdigit() else None)
                    except ValueError as ex:self.send_html(e(str(ex)),400);return
                    if not parent_value:c.execute('UPDATE question_banks SET parent_bank_id=NULL WHERE id=?',(bank_id,))
                    self.redirect(self.bank_path_for_set(sid,conn=c));return
                if path=='/admin/bank-soal/paket/hapus':
                    sid=form.get('set_id','')
                    if not sid.isdigit():self.send_html('Paket soal tidak valid.',400);return
                    if c.execute('SELECT COUNT(*) FROM attempts WHERE set_id=?',(sid,)).fetchone()[0]:self.send_html('Paket tidak dapat dihapus karena sudah memiliki riwayat attempt.',409);return
                    bank=c.execute('SELECT id FROM question_banks WHERE legacy_question_set_id=?',(sid,)).fetchone()
                    if bank and c.execute('SELECT COUNT(*) FROM question_bank_memberships m JOIN questions q ON q.id=m.question_id WHERE q.set_id=? AND m.bank_id<>?',(sid,bank['id'])).fetchone()[0]:self.send_html('Bank ini memiliki soal yang digunakan ulang di bank lain. Hapus keanggotaan soal tersebut sebelum menghapus paket.',409);return
                    c.execute('DELETE FROM question_sets WHERE id=?',(sid,))
                    if c.execute('SELECT changes()').fetchone()[0]==0:self.send_html('Paket tidak ditemukan.',404);return
                    self.redirect('/admin/bank-soal');return
                if path=='/admin/bank-soal/soal/simpan':
                    sid=form.get('set_id','');qid=form.get('question_id','');answer=form.get('answer','');category_id=form.get('category_id','')
                    try:position=int(form.get('position','1'))
                    except ValueError:position=0
                    if not sid.isdigit() or not category_id.isdigit() or answer not in tuple('ABCDE') or not 1<=position<=10000:
                        self.send_html('Pilih bank, kategori, kunci jawaban, dan posisi yang valid.',400);return
                    set_row=c.execute('SELECT id FROM question_sets WHERE id=?',(sid,)).fetchone()
                    category=c.execute('SELECT id,key FROM question_categories WHERE id=? AND active=1',(category_id,)).fetchone()
                    if not set_row or not category:self.send_html('Bank atau kategori soal tidak ditemukan.',404);return
                    prompt=sanitize_rich_html(form.get('prompt','').strip());explanation=sanitize_rich_html(form.get('explanation','').strip())
                    options={letter:sanitize_rich_html(form.get('option_'+letter.lower(),'').strip()) for letter in 'ABCDE'}
                    plain=lambda value: re.sub(r'(?is)<[^>]*>|&nbsp;|\s+','',value or '')
                    category_root=c.execute('SELECT COALESCE((SELECT p.key FROM question_categories p WHERE p.id=c.parent_id),c.key) score_key FROM question_categories c WHERE c.id=?',(category_id,)).fetchone()['score_key']
                    required_letters='ABCDE'
                    if not plain(prompt) or len(prompt)>30000 or any(not plain(options[x]) or len(options[x])>10000 for x in required_letters) or len(explanation)>30000:
                        self.send_html('Isi soal dan semua pilihan yang diwajibkan kategori. Untuk TKP, pilihan A–E wajib diisi.',400);return
                    scoring_profile=form.get('scoring_profile_id','');root_id=c.execute('SELECT COALESCE(parent_id,id) root_id FROM question_categories WHERE id=?',(category_id,)).fetchone()['root_id']
                    if category_root=='tkp' and not scoring_profile:
                        default_profile=c.execute("SELECT id FROM exam_rule_profiles WHERE key='skd_2026_general'").fetchone();scoring_profile=str(default_profile['id']) if default_profile else ''
                    tkp=c.execute("SELECT 1 FROM category_scoring_rules WHERE profile_id=? AND category_id IN (?,?) AND scoring_mode='option_points' LIMIT 1",(scoring_profile,category_id,root_id)).fetchone() if category_root=='tkp' and scoring_profile.isdigit() else None
                    if category_root=='tkp' and not tkp:self.send_html('Pilih profil aturan TKP yang memiliki skema poin per opsi sebelum menyimpan soal.',409);return
                    scores={}
                    tkp_profile_ids=[]
                    if tkp:
                        try:scores={letter:int(form.get('score_'+letter.lower(),'0')) for letter in 'ABCDE'}
                        except ValueError:scores={}
                        if set(scores)!=set('ABCDE') or any(not 1<=v<=5 for v in scores.values()):self.send_html('Bobot setiap pilihan TKP harus antara 1 sampai 5.',400);return
                        source_rule=c.execute("SELECT item_count,max_score,option_score_min,option_score_max FROM category_scoring_rules WHERE profile_id=? AND category_id IN (?,?) AND scoring_mode='option_points' ORDER BY (category_id=?) DESC LIMIT 1",(scoring_profile,category_id,root_id,category_id)).fetchone()
                        for profile_row in c.execute("SELECT DISTINCT r.profile_id FROM category_scoring_rules r JOIN exam_rule_profiles p ON p.id=r.profile_id WHERE p.active=1 AND r.category_id IN (?,?) AND r.scoring_mode='option_points'",(category_id,root_id)).fetchall():
                            candidate=c.execute("SELECT item_count,max_score,option_score_min,option_score_max FROM category_scoring_rules WHERE profile_id=? AND category_id IN (?,?) AND scoring_mode='option_points' ORDER BY (category_id=?) DESC LIMIT 1",(profile_row['profile_id'],category_id,root_id,category_id)).fetchone()
                            if candidate and tuple(candidate)==tuple(source_rule):tkp_profile_ids.append(profile_row['profile_id'])
                    if c.execute('SELECT COUNT(*) FROM attempts WHERE set_id=?',(sid,)).fetchone()[0] or (qid and c.execute('SELECT COUNT(*) FROM attempt_questions WHERE question_id=?',(qid,)).fetchone()[0]):self.send_html('Paket atau soal memiliki riwayat attempt. Soal tidak dapat diubah.',409);return
                    if qid and not qid.isdigit():self.send_html('Soal tidak valid.',400);return
                    owner=c.execute('SELECT id FROM question_banks WHERE legacy_question_set_id=?',(sid,)).fetchone()
                    if not owner:self.send_html('Bank pemilik tidak ditemukan. Jalankan migrasi database kembali.',500);return
                    if qid:
                        if not c.execute('SELECT id FROM questions WHERE id=? AND set_id=?',(qid,sid)).fetchone():self.send_html('Soal tidak ditemukan pada paket ini.',404);return
                        c.execute("""UPDATE questions SET prompt=?,content_html=?,option_a=?,option_b=?,option_c=?,option_d=?,option_e=?,answer=?,explanation=?,position=?,category_id=?,owner_bank_id=?,version=version+1 WHERE id=? AND set_id=?""",(prompt,prompt,options['A'],options['B'],options['C'],options['D'],options['E'],answer,explanation,position,category_id,owner['id'],qid,sid));question_id=int(qid)
                    else:
                        question_id=c.execute("""INSERT INTO questions(set_id,prompt,content_html,option_a,option_b,option_c,option_d,option_e,answer,explanation,position,category_id,owner_bank_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",(sid,prompt,prompt,options['A'],options['B'],options['C'],options['D'],options['E'],answer,explanation,position,category_id,owner['id'])).lastrowid
                    c.execute('INSERT INTO question_bank_memberships(bank_id,question_id,is_owner,position) VALUES (?,?,1,?) ON CONFLICT(bank_id,question_id) DO UPDATE SET is_owner=1,position=excluded.position',(owner['id'],question_id,position))
                    for letter_index,letter in enumerate('ABCDE'):
                        if not options[letter] and letter=='E':continue
                        c.execute('''INSERT INTO question_options(question_id,option_key,body_html,position,is_correct) VALUES (?,?,?,?,?) ON CONFLICT(question_id,option_key) DO UPDATE SET body_html=excluded.body_html,position=excluded.position,is_correct=excluded.is_correct''',(question_id,letter,options[letter],letter_index+1,int(letter==answer)))
                        option=c.execute('SELECT id FROM question_options WHERE question_id=? AND option_key=?',(question_id,letter)).fetchone()
                        if tkp and options[letter]:
                            for score_profile_id in tkp_profile_ids:
                                if score_profile_id==int(scoring_profile):
                                    c.execute('INSERT INTO question_option_scores(profile_id,option_id,score_value) VALUES (?,?,?) ON CONFLICT(profile_id,option_id) DO UPDATE SET score_value=excluded.score_value',(score_profile_id,option['id'],scores[letter]))
                                else:
                                    c.execute('INSERT OR IGNORE INTO question_option_scores(profile_id,option_id,score_value) VALUES (?,?,?)',(score_profile_id,option['id'],scores[letter]))
                    c.execute('DELETE FROM question_media WHERE question_id=?',(question_id,))
                    for usage,option_key,content in [('stem',None,prompt),('explanation',None,explanation)]+[('option',letter,options[letter]) for letter in 'ABCDE']:
                        for filename in set(re.findall(r'/media/([a-f0-9]{32}\.(?:png|jpg|webp|gif))',content)):
                            asset=c.execute('SELECT id FROM media_assets WHERE storage_key=?',(filename,)).fetchone()
                            if asset:c.execute('INSERT OR IGNORE INTO question_media(question_id,asset_id,option_key,usage) VALUES (?,?,?,?)',(question_id,asset['id'],option_key,usage))
                    selected_banks={int(key[len('add_to_bank_'):]) for key,value in form.items() if key.startswith('add_to_bank_') and value=='1' and key[len('add_to_bank_'):].isdigit()}
                    valid_banks={r['id'] for r in c.execute('SELECT id FROM question_banks WHERE status="active" AND id<>?',(owner['id'],)).fetchall()}
                    if selected_banks-valid_banks:self.send_html('Bank tujuan tidak valid.',400);return
                    for bank_id in valid_banks:
                        if bank_id in selected_banks:c.execute('INSERT OR IGNORE INTO question_bank_memberships(bank_id,question_id,is_owner,position,added_by) VALUES (?,?,0,?,?)',(bank_id,question_id,position,u['id']))
                        else:c.execute('DELETE FROM question_bank_memberships WHERE bank_id=? AND question_id=? AND is_owner=0',(bank_id,question_id))
                    self.redirect(self.bank_path_for_set(sid,conn=c));return
                if path=='/admin/bank-soal/soal/hapus':
                    qid=form.get('question_id','')
                    if not qid.isdigit():self.send_html('Soal tidak valid.',400);return
                    q=c.execute('SELECT set_id FROM questions WHERE id=?',(qid,)).fetchone()
                    if not q:self.send_html('Soal tidak ditemukan.',404);return
                    sid=q['set_id']
                    if c.execute('SELECT COUNT(*) FROM attempts WHERE set_id=?',(sid,)).fetchone()[0] or c.execute('SELECT COUNT(*) FROM attempt_answers WHERE question_id=?',(qid,)).fetchone()[0] or c.execute('SELECT COUNT(*) FROM attempt_questions WHERE question_id=?',(qid,)).fetchone()[0]:self.send_html('Soal tidak dapat dihapus karena sudah terkait dengan riwayat tryout.',409);return
                    c.execute('DELETE FROM questions WHERE id=?',(qid,));self.redirect(self.bank_path_for_set(sid,conn=c));return
            self.send_html('Not found',404);return
        if path in ('/admin/kursus/simpan','/admin/programs/save'):
            
            title=form.get('title','').strip();desc=form.get('description','').strip();summary=desc[:220];slug=re.sub(r'[^a-z0-9]+','-',form.get('slug') or title.lower()).strip('-');price=max(0,int(re.sub(r'\D','',form.get('price_label','0')) or 0));status='published' if form.get('status')=='published' else 'draft';category=form.get('category','').strip();level=form.get('level','Semua tingkat').strip();cover=form.get('cover_url','').strip()
            if not title or not slug:self.send_html('Judul wajib diisi.',400);return
            with connect() as c:
                pid=form.get('course_id','')
                if pid.isdigit():c.execute('UPDATE programs SET slug=?,title=?,summary=?,description=?,category=?,cover_url=?,level=?,price=?,status=? WHERE id=?',(slug,title,summary,desc,category,cover,level,price,status,pid))
                else:c.execute('INSERT INTO programs(slug,title,summary,description,category,cover_url,level,price,status) VALUES (?,?,?,?,?,?,?,?,?)',(slug,title,summary,desc,category,cover,level,price,status))
            self.redirect('/admin');return
        if path=='/admin/modul/simpan':
            
            mid=form.get('module_id','');title=form.get('title','').strip();pid=form.get('course_id','')
            with connect() as c:
                if mid.isdigit():c.execute('UPDATE modules SET title=?,position=? WHERE id=?',(title,int(form.get('position','1') or 1),mid))
                else:c.execute('INSERT INTO modules(program_id,title,position) VALUES (?,?,?)',(pid,title,int(form.get('position','1') or 1)));mid=c.execute('SELECT last_insert_rowid()').fetchone()[0]
                edit_url=self.opaque_path('module',mid,'/admin/modul/{}/edit',c)
            self.redirect(edit_url);return
        if path=='/admin/pelajaran/simpan' or path=='/admin/lessons/save':
            
            mid=form.get('module_id','');title=form.get('title','').strip();body=form.get('description','').strip();vid=form.get('youtube_id','').strip();resource=form.get('resources','').strip();video='https://www.youtube-nocookie.com/embed/'+vid
            if not re.fullmatch(r'[A-Za-z0-9_-]{6,20}',vid):self.send_html('Masukkan ID video YouTube yang valid.',400);return
            with connect() as c:
                lid=form.get('lesson_id','')
                if lid.isdigit():c.execute('UPDATE lessons SET module_id=?,title=?,body=?,video_url=?,resource_url=?,duration_min=?,position=? WHERE id=?',(mid,title,body,video,resource,int(form.get('duration_minutes','0') or 0),int(form.get('position','1') or 1),lid))
                else:c.execute('INSERT INTO lessons(module_id,title,body,video_url,resource_url,duration_min,position) VALUES (?,?,?,?,?,?,?)',(mid,title,body,video,resource,int(form.get('duration_minutes','0') or 0),int(form.get('position','1') or 1)))
                edit_url=self.opaque_path('module',mid,'/admin/modul/{}/edit',c)
            self.redirect(edit_url);return
        self.send_html('Not found',404)

