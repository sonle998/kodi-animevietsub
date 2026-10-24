import importlib.util
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'plugin.video.animevietsub'))
from resources.lib.core import SourceError,parse_listing,parse_detail,parse_episodes,api_sources,media_sources,embedded_frames,site_url,ad_url
BASE='https://animevietsub.sale/'
class ParsingTests(unittest.TestCase):
    def test_listing_and_paging(self):
        card='<div class="TPostMv"><a href="/phim/test-a1/"><img data-src="/poster.jpg"><h2 class="Title">Tên phim</h2><span class="mli-eps">12</span></a></div>'
        items,pages=parse_listing(card+card+'<div class="pagination"><a href="/trang-2/">2</a></div>',BASE)
        self.assertEqual(len(items),1);self.assertEqual(items[0]['title'],'Tên phim');self.assertEqual(items[0]['poster'],BASE+'poster.jpg');self.assertEqual(pages[0]['url'],BASE+'trang-2/')
    def test_detail_and_api_episode_fields(self):
        doc='<h1 class="Title">A</h1><div class="Description">Câu chuyện</div><a class="watch_button_more" href="/phim/a/xem-phim.html">Xem</a><div id="list-server"><span class="episode"><a href="#" data-id="7" data-play="api" data-hash="hash123">2</a></span></div>'
        d=parse_detail(doc,BASE);e=d['episodes'][0]
        self.assertEqual(e['id'],'7');self.assertEqual(e['hash'],'hash123');self.assertEqual(e['title'],'Tập 2');self.assertTrue(d['watch'].endswith('xem-phim.html'))
    def test_plain_sources_and_ad_exclusion(self):
        d='<video><source src="https://cdn.example/film.m3u8?key=abc" type="application/x-mpegurl"></video><script>var popup="https://cdn.example/ad.mp4"; var config={file:"https://cdn.example/film.mp4"};</script>'
        src=media_sources(d,BASE);self.assertEqual(len(src),2);self.assertNotIn('https://cdn.example/ad.mp4',[s['url'] for s in src])
        self.assertEqual(media_sources('<video src="https://ad.doubleclick.net/ads/movie.mp4"></video>',BASE),[])
    def test_encrypted_source_not_fake_playable(self):
        src,frames,encrypted=api_sources({'link':[{'file':'encrypted_token','type':'hls'}]},BASE)
        self.assertFalse(src);self.assertFalse(frames);self.assertTrue(encrypted)
        src,_,encrypted=api_sources({'link':[{'file':'https://cdn.example/v.m3u8','label':'1080p'}]},BASE)
        self.assertEqual(src[0]['label'],'1080p');self.assertFalse(encrypted)
    def test_player_frames_exclude_ads(self):
        text='<iframe src="https://popads.net/popup"></iframe><div class="TPlayerCn"><iframe src="https://stream.googleapiscdn.com/video0.html"></iframe></div>'
        self.assertEqual(embedded_frames(text,BASE),['https://stream.googleapiscdn.com/video0.html'])
    def test_challenge_is_explicit(self):
        with self.assertRaises(SourceError):parse_listing('<title>Đang Kiểm Tra - AnimeVietsub</title>',BASE)
    def test_domain_boundary(self):
        self.assertTrue(site_url(BASE));self.assertTrue(site_url('https://animevietsub.xyz/phim/a/'));self.assertFalse(site_url('https://animevietsub.sale.evil.example/'));self.assertFalse(site_url('https://animevietsub.sale@evil.example/'));self.assertFalse(ad_url('https://notpopads.net/film.mp4'))
if __name__=='__main__':unittest.main()
