import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];PLUGIN=ROOT/'plugin.video.animevietsub'
class Item:
    def __init__(self,**kw):self.kw=kw;self.properties={}
    def setArt(self,*x):pass
    def setInfo(self,*x):pass
    def setProperty(self,k,v):self.properties[k]=v
    def setContentLookup(self,*x):pass
    def setMimeType(self,*x):pass
class KodiRoutes(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.items=[];self.resolved=[];self.ends=[]
        settings={'base_url':'https://animevietsub.sale/','timeout':'20','quality':'0'}
        addon=types.SimpleNamespace(getAddonInfo=lambda k:str(PLUGIN if k=='path' else self.temp.name),getSetting=lambda k:settings.get(k,''),setSetting=lambda *a:None,openSettings=lambda:None)
        xbmc=types.SimpleNamespace(LOGWARNING=2,log=lambda *a:None,executebuiltin=lambda *a:None,getCondVisibility=lambda *a:False)
        xbmcgui=types.SimpleNamespace(ListItem=Item,Dialog=lambda:types.SimpleNamespace(ok=lambda *a:None))
        xbmcplugin=types.SimpleNamespace(addDirectoryItem=lambda *a:self.items.append(a),setContent=lambda *a:None,endOfDirectory=lambda *a,**kw:self.ends.append((a,kw)),setResolvedUrl=lambda *a:self.resolved.append(a))
        modules={'xbmc':xbmc,'xbmcgui':xbmcgui,'xbmcplugin':xbmcplugin,'xbmcaddon':types.SimpleNamespace(Addon=lambda:addon),'xbmcvfs':types.SimpleNamespace(translatePath=lambda x:x)}
        self.patches=patch.dict(sys.modules,modules);self.patches.start();self.args=patch.object(sys,'argv',['plugin://plugin.video.animevietsub','1','']);self.args.start()
        spec=importlib.util.spec_from_file_location('av_plugin_test',PLUGIN/'addon.py');self.mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.mod)
    def tearDown(self):self.args.stop();self.patches.stop();self.temp.cleanup()
    def test_home_menu(self):self.mod.main();self.assertEqual(len(self.items),6);self.assertTrue(self.ends)
    def test_episode_routes_have_playable_items(self):
        self.mod.episode_entries([{'title':'Tập 1','server':'api','id':'1','hash':'h'}],title='Tên phim')
        self.assertEqual(len(self.items),1);self.assertFalse(self.items[0][3]);self.assertEqual(self.items[0][2].properties['IsPlayable'],'true')
    def test_native_hls_play_resolution(self):
        self.mod.client=lambda:types.SimpleNamespace(resolve=lambda ep:([{'url':'https://cdn.example/v.m3u8','type':'hls','label':'720p'}],'https://animevietsub.sale/phim/a/'),stream_headers=lambda u,r:{'Referer':r})
        self.mod.play(json.dumps({'id':'1'}),'Tên phim');self.assertTrue(self.resolved[0][1]);self.assertTrue(self.resolved[0][2].kw['path'].startswith('https://cdn.example/v.m3u8|'))
if __name__=='__main__':unittest.main()
