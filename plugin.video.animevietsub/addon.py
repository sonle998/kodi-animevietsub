# SPDX-License-Identifier: GPL-3.0-only
import json
import os
import sys
from urllib.parse import urlencode,parse_qs,urlsplit
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

ADDON=xbmcaddon.Addon();HANDLE=int(sys.argv[1]);PLUGIN=sys.argv[0]
PATH=xbmcvfs.translatePath(ADDON.getAddonInfo('path'));sys.path.insert(0,PATH)
from resources.lib.core import SourceError,parse_listing,parse_detail,parse_episodes,categories,site_url,quality
from resources.lib.client import Client
ICON=os.path.join(PATH,'resources','icon.png');FANART=os.path.join(PATH,'resources','fanart.jpg')
PROFILE=xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))

def client():return Client(ADDON.getSetting('base_url') or 'https://animevietsub.sale/',PROFILE,ADDON.getSetting('timeout') or '20')
def link(action,**kw):return PLUGIN+'?'+urlencode(dict(action=action,**kw))
def entry(label,action,folder=True,poster='',plot='',**kw):
    item=xbmcgui.ListItem(label=label);item.setArt({'thumb':poster or ICON,'poster':poster or ICON,'icon':ICON,'fanart':FANART});item.setInfo('video',{'title':label,'plot':plot,'mediatype':'episode' if not folder else 'tvshow'})
    if not folder:item.setProperty('IsPlayable','true')
    xbmcplugin.addDirectoryItem(HANDLE,link(action,**kw),item,folder)
def finish(content='tvshows'):xbmcplugin.setContent(HANDLE,content);xbmcplugin.endOfDirectory(HANDLE)
def listing(url):
    text,actual=client().get(url);items,pages=parse_listing(text,actual)
    if not items:raise SourceError('Chưa đọc được danh sách phim. Website có thể yêu cầu xác minh hoặc đã đổi cấu trúc.')
    for film in items:entry(film['title']+(' — '+film['episode'] if film['episode'] else ''),'detail',poster=film['poster'],url=film['url'])
    for p in pages:entry('Trang '+p['title'],'list',url=p['url'])
    finish()
def episode_entries(episodes,title='',poster='',plot=''):
    servers=sorted(set(e['server'] for e in episodes));multi=len(servers)>1
    for ep in episodes:entry((ep['server']+' · ' if multi else '')+ep['title'],'play',False,poster,plot,episode=json.dumps(ep,ensure_ascii=False),title=title or ep['title'])

def detail(url):
    c=client();text,actual=c.get(url);info=parse_detail(text,actual)
    if info['episodes']:episode_entries(info['episodes'],info['title'],info['poster'],info['plot'])
    elif info['watch']:entry('▶ Xem phim — '+info['title'],'episodes',poster=info['poster'],plot=info['plot'],url=info['watch'],title=info['title'],poster_url=info['poster'])
    else:raise SourceError('Không tìm thấy nút xem hoặc danh sách tập trên trang này.')
    finish('episodes')
def episodes(url,title='',poster_url=''):
    text,actual=client().get(url);eps=parse_episodes(text,actual)
    if eps:episode_entries(eps,title,poster_url)
    else:entry('▶ Phát video','play',False,poster_url,episode=json.dumps({'url':actual,'page':actual}),title=title)
    finish('episodes')
def play(episode,title='AnimeVietsub'):
    c=client();sources,referer=c.resolve(json.loads(episode));sources.sort(key=quality,reverse=True);mode=ADDON.getSetting('quality') or '0'
    index=0
    if mode=='1':index=len(sources)-1
    elif mode=='2' and len(sources)>1:
        index=xbmcgui.Dialog().select('Chọn chất lượng',[s.get('label') or 'Tự động' for s in sources])
        if index<0:xbmcplugin.setResolvedUrl(HANDLE,False,xbmcgui.ListItem());return
    source=sources[index];url=source['url'];headers=urlencode(c.stream_headers(url,referer));item=xbmcgui.ListItem(label=title,path=url+'|'+headers);item.setInfo('video',{'title':title});item.setContentLookup(False)
    path=urlsplit(url).path.lower();kind=source.get('type','')
    if path.endswith('.mpd') or kind=='dash':
        if not xbmc.getCondVisibility('System.HasAddon(inputstream.adaptive)'):raise SourceError('Nguồn DASH cần InputStream Adaptive. Hãy cài từ kho chính thức Kodi rồi thử lại.')
        item.setProperty('inputstream','inputstream.adaptive');item.setProperty('inputstream.adaptive.manifest_type','mpd');item.setProperty('inputstream.adaptive.stream_headers',headers);item.setProperty('inputstream.adaptive.manifest_headers',headers);item.setMimeType('application/dash+xml')
    elif path.endswith('.m3u8') or kind=='hls':item.setMimeType('application/vnd.apple.mpegurl')
    xbmcplugin.setResolvedUrl(HANDLE,True,item)
def main():
    q={k:v[0] for k,v in parse_qs(sys.argv[2][1:] if len(sys.argv)>2 else '').items()};action=q.pop('action','home')
    try:
        if action=='home':
            entry('Mới cập nhật','list',url='/');entry('Tìm kiếm','search');entry('Thể loại / danh mục','categories');entry('Nhập liên kết phim','enter');entry('Cập nhật tên miền qua link dự phòng','fallback');entry('Cài đặt','settings');finish();return
        if action=='list':listing(q['url'])
        elif action=='detail':detail(q['url'])
        elif action=='episodes':episodes(q['url'],q.get('title',''),q.get('poster_url',''))
        elif action=='play':play(q['episode'],q.get('title','AnimeVietsub'))
        elif action=='categories':
            text,actual=client().get('/');items=categories(text,actual)
            if not items:raise SourceError('Không đọc được danh mục từ website.')
            for x in items:entry(x['title'],'list',url=x['url'])
            finish()
        elif action=='search':
            value=xbmcgui.Dialog().input('Nhập tên phim')
            if not value:finish();return
            text,actual=client().search(value);items,_=parse_listing(text,actual)
            if not items:raise SourceError('Không có kết quả hoặc website đã đổi API tìm kiếm.')
            for film in items:entry(film['title'],'detail',poster=film['poster'],url=film['url'])
            finish()
        elif action=='enter':
            value=xbmcgui.Dialog().input('Dán link phim AnimeVietsub')
            if not value:finish();return
            if not site_url(value):raise SourceError('Chỉ nhận liên kết HTTPS của AnimeVietsub.')
            detail(value)
        elif action=='fallback':
            domain=client().fallback();ADDON.setSetting('base_url',domain);xbmcgui.Dialog().ok('AnimeVietsub','Đã lưu tên miền: '+domain);finish();xbmc.executebuiltin('Container.Refresh')
        elif action=='settings':ADDON.openSettings();finish()
        else:raise SourceError('Mục này không hợp lệ. Hãy quay về menu chính.')
    except Exception as e:
        # Do not log signed URLs, form tokens or cookies.
        message=str(e) if isinstance(e,SourceError) else 'Không xử lý được dữ liệu website. Bản addon đang thử nghiệm; vui lòng báo mục/tập bị lỗi.'
        xbmc.log('AnimeVietsub: '+type(e).__name__,xbmc.LOGWARNING);xbmcgui.Dialog().ok('AnimeVietsub',message)
        if action=='play':xbmcplugin.setResolvedUrl(HANDLE,False,xbmcgui.ListItem())
        else:xbmcplugin.endOfDirectory(HANDLE,succeeded=False)
if __name__=='__main__':main()
