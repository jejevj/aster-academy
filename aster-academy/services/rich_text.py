from __future__ import annotations
import re
from html.parser import HTMLParser
from services.formatting import e

class RichTextSanitizer(HTMLParser):
    ALLOWED={'p','br','strong','b','em','i','u','ul','ol','li','blockquote','h2','h3','pre','code','div','span','a','img'}
    VOID={'br','img'}
    def __init__(self):super().__init__(convert_charrefs=True);self.parts=[];self.blocked=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style','iframe','object','svg','math'):self.blocked+=1;return
        if self.blocked or tag not in self.ALLOWED:return
        a=dict(attrs)
        if tag=='img':
            src=a.get('src','');m=re.fullmatch(r'/media/([a-f0-9]{32}\.(?:png|jpg|webp|gif))',src)
            if m:self.parts.append(f'<img src="{m.group(0)}" alt="{e(a.get("alt",""))}" loading="lazy">')
            return
        if tag=='a':
            href=a.get('href','')
            if re.match(r'^https?://[^\s]+$',href,re.I):self.parts.append(f'<a href="{e(href)}" rel="nofollow noopener noreferrer">')
            else:self.parts.append('<a>')
            return
        self.parts.append(f'<{tag}>')
    def handle_endtag(self,tag):
        if tag in ('script','style','iframe','object','svg','math'):
            self.blocked=max(0,self.blocked-1);return
        if not self.blocked and tag in self.ALLOWED and tag not in self.VOID:self.parts.append(f'</{tag}>')
    def handle_data(self,data):
        if not self.blocked:self.parts.append(e(data))
    def value(self):return ''.join(self.parts)

def sanitize_rich_html(value):
    parser=RichTextSanitizer()
    try:parser.feed(value or '');parser.close();return parser.value()
    except Exception:return e(value)
