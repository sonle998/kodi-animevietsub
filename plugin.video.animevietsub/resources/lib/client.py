# SPDX-License-Identifier: GPL-3.0-only
import gzip
import http.cookiejar
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from .core import SourceError, site_url, ad_url, media_sources, api_sources, embedded_frames, is_media

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if not newurl.startswith(('http://','https://')) or ad_url(newurl):raise SourceError('Đã chặn chuyển hướng quảng cáo hoặc giao thức không hợp lệ.')
        return super().redirect_request(req,fp,code,msg,headers,newurl)

USER_AGENT='Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
class Client:
    def __init__(self,base,profile,timeout=20):
        if not site_url(base):raise SourceError('Địa chỉ phải là tên miền HTTPS của AnimeVietsub.')
        self.base=base.rstrip('/')+'/';self.timeout=max(5,min(int(timeout),60));self.profile=profile
        os.makedirs(profile,exist_ok=True);self.cookies=http.cookiejar.MozillaCookieJar(os.path.join(profile,'cookies.txt'))
        try:self.cookies.load(ignore_discard=True)
        except (OSError,http.cookiejar.LoadError):pass
        self.opener=urllib.request.build_opener(SafeRedirect(),urllib.request.HTTPCookieProcessor(self.cookies))
    def request(self,url,data=None,referer=None):
        if not url.startswith(('https://','http://')) or ad_url(url):raise SourceError('Không tải URL quảng cáo hoặc URL không hợp lệ.')
        encoded=urllib.parse.urlencode(data).encode() if data is not None else None
        headers={'User-Agent':USER_AGENT,'Referer':referer or self.base,'Accept-Encoding':'gzip'}
        if encoded is not None:headers.update({'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8','X-Requested-With':'XMLHttpRequest','Origin':self.base.rstrip('/')})
        try:
            with self.opener.open(urllib.request.Request(url,encoded,headers),timeout=self.timeout) as response:
                final=response.geturl();raw=response.read(8*1024*1024+1)
                if len(raw)>8*1024*1024:raise SourceError('Tài liệu quá lớn; ngừng đọc để tránh đầy bộ nhớ.')
                if response.headers.get('Content-Encoding','').lower()=='gzip':raw=gzip.decompress(raw)
                if len(raw)>8*1024*1024:raise SourceError('Tài liệu giải nén quá lớn.')
                text=raw.decode(response.headers.get_content_charset() or 'utf-8',errors='replace')
            try:self.cookies.save(ignore_discard=True)
            except OSError:pass
            return text,final
        except urllib.error.HTTPError as e:
            if e.code in (403,429):raise SourceError('Website từ chối truy cập hoặc yêu cầu xác minh (HTTP %s). Kodi không tự vượt xác minh.'%e.code)
            raise SourceError('Máy chủ trả HTTP %s.'%e.code)
        except (urllib.error.URLError,TimeoutError,OSError) as e:raise SourceError('Không tải được trang. Kiểm tra mạng và tên miền trong Cài đặt.') from e
    def get(self,path):return self.request(urllib.parse.urljoin(self.base,path))
    def search(self,query):return self.request(urllib.parse.urljoin(self.base,'ajax/suggest'),{'ajaxSearch':'1','keysearch':query})
    def fallback(self):
        _,url=self.request('https://bit.ly/animevietsubtv')
        if not site_url(url):raise SourceError('Link dự phòng chưa chuyển tới tên miền AnimeVietsub hợp lệ.')
        u=urllib.parse.urlsplit(url);return '%s://%s/'%(u.scheme,u.netloc)
    def stream_headers(self,url,referer):
        headers={'User-Agent':USER_AGENT,'Referer':referer}
        origin=urllib.parse.urlsplit(referer);headers['Origin']='%s://%s'%(origin.scheme,origin.netloc)
        r=urllib.request.Request(url);self.cookies.add_cookie_header(r)
        if r.get_header('Cookie'):headers['Cookie']=r.get_header('Cookie')
        return headers
    def resolve(self,episode):
        page=episode.get('page') or episode.get('url') or self.base;choices=[];frames=[];encrypted=False
        if episode.get('id') and episode.get('hash'):
            text,_=self.request(urllib.parse.urljoin(self.base,'ajax/player'),{'id':episode['id'],'play':episode.get('play',''),'link':episode['hash'],'backuplinks':'1'},page)
            try:payload=json.loads(text)
            except ValueError:
                # Detect HTML verification before reporting a JSON error.
                media_sources(text,page)
                raise SourceError('API không trả JSON nguồn phát; có thể cần xác minh hoặc website đã đổi cấu trúc.')
            choices,frames,encrypted=api_sources(payload,page)
        if not choices:
            target=episode.get('url') or page;text,actual=self.request(target,referer=page)
            choices.extend(media_sources(text,actual));frames.extend(embedded_frames(text,actual))
        visited=set()
        def inspect(url,referer,depth):
            if depth>2 or url in visited or ad_url(url):return []
            visited.add(url)
            if is_media(url):return [{'url':url,'label':'Tự động','type':''}]
            try:
                text,actual=self.request(url,referer=referer);direct=media_sources(text,actual)
                if direct:return direct
                found=[]
                for child in embedded_frames(text,actual):found.extend(inspect(child,actual,depth+1))
                return found
            except SourceError:return []
        for frame in frames:
            if not choices:choices.extend(inspect(frame,page,0))
        if not choices:
            if encrypted:raise SourceError('Máy chủ trả nguồn mã hóa riêng, bản addon này chưa hỗ trợ. Hãy chọn máy chủ khác. Không có URL phát trực tiếp để giao cho Kodi.')
            raise SourceError('Chưa tìm được nguồn video trực tiếp tương thích Kodi. Thử máy chủ khác; iframe cần chạy JavaScript không được thực thi trong Kodi.')
        result=[];seen=set()
        for c in choices:
            if c['url'] not in seen and not ad_url(c['url']):seen.add(c['url']);result.append(c)
        return result,page
