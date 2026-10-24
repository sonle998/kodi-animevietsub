import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('build_repo',ROOT/'tools/build_repo.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
class RepositoryTests(unittest.TestCase):
    def test_local_zip_contains_valid_feed_and_plugin(self):
        with tempfile.TemporaryDirectory() as out:
            plugin,repo=builder.build(out)
            with zipfile.ZipFile(repo) as z:
                xml=ET.fromstring(z.read('repository.animevietsub/addon.xml'))
                self.assertTrue(xml.find('.//info').text.startswith('special://home/addons/repository.animevietsub/'))
                raw=z.read('repository.animevietsub/repo/addons.xml');expected=z.read('repository.animevietsub/repo/addons.xml.md5').decode().strip();self.assertEqual(hashlib.md5(raw).hexdigest(),expected)
                payload=z.read('repository.animevietsub/repo/packages/plugin.video.animevietsub/plugin.video.animevietsub-0.1.0.zip')
                self.assertEqual(payload,plugin.read_bytes())
    def test_hosted_layout_has_no_placeholder(self):
        with tempfile.TemporaryDirectory() as out:
            plugin,repo=builder.build(out,'https://test.invalid/anime/')
            with zipfile.ZipFile(repo) as z:
                doc=ET.fromstring(z.read('repository.animevietsub/addon.xml'));self.assertEqual(doc.find('.//info').text,'https://test.invalid/anime/addons.xml')
            feed=Path(out)/'site';doc=ET.parse(feed/'addons.xml');self.assertEqual(len(doc.findall('addon')),2)
            for addon in doc.findall('addon'):
                package=feed/'packages'/addon.attrib['id']/(addon.attrib['id']+'-'+addon.attrib['version']+'.zip')
                self.assertTrue(package.exists());self.assertEqual(hashlib.sha256(package.read_bytes()).hexdigest(),Path(str(package)+'.sha256').read_text().strip())
if __name__=='__main__':unittest.main()
