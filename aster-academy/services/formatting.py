from __future__ import annotations
import html

def e(x): return html.escape(str(x or ''),quote=True)

def money(v): return 'Akses dikelola admin' if not v else 'Rp'+format(v,',').replace(',','.')
