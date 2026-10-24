# SPDX-License-Identifier: GPL-3.0-only
"""HTML and playback parsing; does not execute website JavaScript or decrypt protected sources."""
import html
import json
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

class SourceError(Exception):
    pass

class Node:
    def __init__(self, tag='', attrs=(), parent=None):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs), parent, []
    def text(self):
        return re.sub(r'\s+', ' ', ''.join(c.text() if isinstance(c, Node) else c for c in self.children)).strip()
    def has(self, cls):
        return cls in self.attrs.get('class', '').split()
    def nodes(self, tag=None, cls=None, ident=None):
        result=[]
        for child in self.children:
            if isinstance(child, Node):
                if (not tag or child.tag==tag) and (not cls or child.has(cls)) and (not ident or child.attrs.get('id')==ident):
                    result.append(child)
                result.extend(child.nodes(tag, cls, ident))
        return result
    def first(self, **kw):
        found=self.nodes(**kw)
        return found[0] if found else None
    def ancestor(self, cls):
        p=self.parent
        while p:
            if p.has(cls): return p
            p=p.parent
        return None

class Tree(HTMLParser):
    VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.root=Node('document'); self.current=self.root
        self.feed(text); self.close()
    def handle_starttag(self, tag, attrs):
        n=Node(tag, attrs, self.current); self.current.children.append(n)
        if tag not in self.VOID: self.current=n
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag,attrs)
        if tag not in self.VOID:self.handle_endtag(tag)
    def handle_endtag(self, tag):
        p=self.current
        while p.parent:
            if p.tag==tag:self.current=p.parent;return
            p=p.parent
    def handle_data(self, data):self.current.children.append(data)

def document(text):
    root=Tree(text).root
    title=root.first(tag='title'); title=title.text().lower() if title else ''
    if ('just a moment' in title or 'đang kiểm tra' in title or 'xác minh' in title or
        'xác minh người dùng việt nam' in root.text().lower() or root.first(ident='challenge-running')):
        raise SourceError('Website yêu cầu xác minh mà Kodi không thực hiện được. Hãy thử tên miền dự phòng; addon không tự vượt xác minh.')
    return root

def site_url(url):
    p=urlsplit(url)
    return p.scheme=='https' and not p.username and bool(re.fullmatch(r'(?:[a-z0-9-]+\.)*animevietsub\.[a-z]{2,}(?:\.[a-z]{2,})?', (p.hostname or '').lower()))

def clean_url(value,base):
    u=urljoin(base,html.unescape(value or '').strip())
    return u if urlsplit(u).scheme in ('https','http') and urlsplit(u).hostname else ''

def parse_listing(text,base):
    root=document(text); out=[];seen=set()
    cards=[n for n in root.nodes() if n.has('TPostMv') or n.has('TPost')]
    # Search suggestions often use plain list rows instead of TPost cards.
    if not cards: cards=[n for n in root.nodes(tag='li') if n.first(tag='img')]
    for card in cards:
        a=card.first(tag='a');im=card.first(tag='img');name=card.first(cls='Title')
        if not a or not im:continue
        url=clean_url(a.attrs.get('href'),base)
        if not site_url(url) or '/phim/' not in url or url in seen:continue
        title=name.text() if name else (im.attrs.get('alt') or a.attrs.get('title') or a.text())
        if not title:continue
        seen.add(url);episode=card.first(cls='mli-eps')
        out.append({'url':url,'title':title,'poster':clean_url(im.attrs.get('data-src') or im.attrs.get('data-original') or im.attrs.get('src'),base),'episode':episode.text() if episode else ''})
    pages=[]
    for n in root.nodes():
        if any(n.has(c) for c in ('pagination','wp-pagenavi','PageNav','pagenavi')):
            for a in n.nodes(tag='a'):
                u=clean_url(a.attrs.get('href'),base)
                if site_url(u) and u!=base and not any(x['url']==u for x in pages):pages.append({'url':u,'title':a.text() or 'Trang tiếp'})
    return out,pages

def parse_detail(text,base):
    root=document(text);t=root.first(cls='Title') or root.first(tag='h1');desc=root.first(cls='Description');image=root.first(cls='Image');im=image.first(tag='img') if image else None
    a=root.first(cls='watch_button_more')
    if not a:
        a=next((x for x in root.nodes(tag='a') if re.fullmatch(r'(?:▶\s*)?(?:xem phim|xem ngay)',x.text(),re.I)),None)
    watch=clean_url(a.attrs.get('href'),base) if a else ''
    return {'title':t.text() if t else 'AnimeVietsub','plot':desc.text() if desc else '', 'poster':clean_url(im.attrs.get('data-src') or im.attrs.get('src'),base) if im else '', 'watch':watch if site_url(watch) else '', 'episodes':parse_episodes(text,base)}

def parse_episodes(text,base):
    root=document(text);region=root.first(ident='list-server');out=[];seen=set()
    if not region:return out
    for a in region.nodes(tag='a'):
        data=a.attrs;ident=data.get('data-id','');play=data.get('data-play','');token=data.get('data-hash') or data.get('data-href','');raw=data.get('href','');url=clean_url(raw,base)
        if not ident and (not raw or raw.startswith(('#','javascript:')) or not site_url(url)):continue
        key=(ident,play,token,url)
        if key in seen:continue
        seen.add(key);name=a.text() or ident
        if re.fullmatch(r'\d+(?:\.\d+)?',name):name='Tập '+name
        out.append({'title':name,'id':ident,'play':play,'hash':token,'url':url if raw and not raw.startswith(('#','javascript:')) and site_url(url) else base,'page':base,'server':play or 'Mặc định'})
    return out

def categories(text,base):
    root=document(text);out=[];seen=set()
    for a in root.nodes(tag='a'):
        url=clean_url(a.attrs.get('href'),base)
        if site_url(url) and any(p in urlsplit(url).path for p in ('/the-loai/','/dang-anime/','/danh-sach/','/season/')) and url not in seen:
            seen.add(url);out.append({'title':a.text() or urlsplit(url).path,'url':url})
    return out

AD_HOSTS={'ad.doubleclick.net','g.doubleclick.net','pagead2.googlesyndication.com','tpc.googlesyndication.com','popads.net','popcash.net','bom88.pw'}
def ad_url(u):
    host=(urlsplit(u).hostname or '').lower();path=urlsplit(u).path.lower()
    return any(host==h or host.endswith('.'+h) for h in AD_HOSTS) or bool(re.search(r'/(?:ads|vast|quangcao)/',path))

def is_media(url):
    return bool(re.search(r'\.(?:m3u8|mp4|mpd|webm|m4v|mkv)(?:[?#]|$)',url,re.I))

def media_sources(text,base):
    """Only explicit media declarations; never harvest arbitrary URLs or adverts from scripts."""
    root=document(text);out=[];seen=set()
    def add(raw,label='',kind=''):
        url=clean_url(raw.replace('\\/','/'),base)
        if url and not ad_url(url) and (is_media(url) or kind in ('hls','mp4','dash','application/vnd.apple.mpegurl','application/x-mpegurl','video/mp4','application/dash+xml')) and url not in seen:
            seen.add(url);out.append({'url':url,'label':label or 'Tự động','type':kind})
    for v in root.nodes(tag='video')+root.nodes(tag='source'):
        if v.attrs.get('src'):add(v.attrs['src'],v.attrs.get('label',''),v.attrs.get('type',''))
    for script in root.nodes(tag='script'):
        # Source declarations used by JWPlayer/VideoJS. No eval, packer or arbitrary JS execution.
        raw=''.join(c for c in script.children if isinstance(c,str))
        for m in re.finditer(r'''(?:\bfile|\bsrc)\s*:\s*(["'])(https?:.*?|//.*?)\1''',raw,re.I):
            add(m.group(2))
    return out

def embedded_frames(text,base):
    root=document(text);frames=[]
    containers=[n for n in root.nodes() if n.attrs.get('id') in ('player','player-area','player-container','player-wrapper','watch-player') or n.has('TPlayerCn') or n.has('TPlayer')]
    scope=containers or [root]
    for box in scope:
        for f in box.nodes(tag='iframe'):
            url=clean_url(f.attrs.get('src') or f.attrs.get('data-src'),base)
            if url and not ad_url(url) and not f.ancestor('Ads') and url not in frames:frames.append(url)
    return frames[:4]

def api_sources(payload,base):
    if not isinstance(payload,dict):raise SourceError('API trình phát trả dữ liệu không đúng định dạng.')
    result=[];encrypted=False;frames=[]
    links=payload.get('link') or payload.get('sources') or []
    if isinstance(links,str):
        if '<iframe' in links.lower():frames=embedded_frames(links,base)
        else:
            u=clean_url(links,base)
            if is_media(u) and not ad_url(u):result=[{'url':u,'label':'Tự động','type':''}]
            elif urlsplit(u).scheme in ('http','https') and payload.get('playTech')=='iframe' and links.startswith(('http','//')):frames=[u]
            else:encrypted=True
    elif isinstance(links,list):
        for item in links:
            if not isinstance(item,dict):continue
            raw=item.get('file') or item.get('src') or ''
            if not raw.startswith(('http://','https://','//')):encrypted=True;continue
            u=clean_url(raw,base);kind=item.get('type','')
            if not ad_url(u) and (is_media(u) or kind in ('hls','mp4','dash')):result.append({'url':u,'label':str(item.get('label') or 'Tự động'),'type':kind})
    return result,frames,encrypted

def quality(source):
    m=re.search(r'(\d{3,4})',source.get('label',''))
    if m:return int(m.group(1))
    return 1080 if 'FHD' in source.get('label','').upper() else 720 if 'HD' in source.get('label','').upper() else 0
