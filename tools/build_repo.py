#!/usr/bin/env python3
"""Build installable addon, local self-contained repository, or a hosted repository."""
import argparse
import hashlib
import html
from pathlib import Path
import shutil
import zipfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
PLUGIN='plugin.video.animevietsub'
REPO='repository.animevietsub'
VERSION='0.1.0'
def zipdir(folder,output):
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for f in sorted(folder.rglob('*')):
            if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc':z.write(f,folder.name+'/'+str(f.relative_to(folder)))
    Path(str(output)+'.sha256').write_text(hashlib.sha256(output.read_bytes()).hexdigest()+'\n')

def repo_xml(base):
    b=html.escape(base.rstrip('/')+'/',quote=True)
    return '''<?xml version="1.0" encoding="UTF-8"?>
<addon id="repository.animevietsub" name="AnimeVietsub Repository" version="0.1.0" provider-name="Thắng Phùng">
 <extension point="xbmc.addon.repository"><dir minversion="19.0.0"><info>%saddons.xml</info><checksum>%saddons.xml.md5</checksum><datadir>%spackages/</datadir><hashes>sha256</hashes></dir></extension>
 <extension point="xbmc.addon.metadata"><summary lang="vi_VN">Kho addon AnimeVietsub — thử nghiệm</summary><summary lang="en_GB">AnimeVietsub repository — experimental</summary><description lang="vi_VN">Kho cài addon AnimeVietsub cho Kodi 19 trở lên.</description><description lang="en_GB">Repository for the AnimeVietsub addon for Kodi 19 and newer.</description><platform>all</platform><license>GPL-3.0-only</license><assets><icon>resources/icon.png</icon></assets></extension>
</addon>'''%(b,b,b)

def index(destination,metadatas):
    destination.mkdir(parents=True,exist_ok=True)
    root=ET.Element('addons')
    for path in metadatas:root.append(ET.parse(path).getroot())
    raw=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    (destination/'addons.xml').write_bytes(raw)
    (destination/'addons.xml.md5').write_text(hashlib.md5(raw).hexdigest()+'\n')
    (destination/'addons.xml.sha256').write_text(hashlib.sha256(raw).hexdigest()+'\n')

def build(output,base_url=None):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    staging=output/'_staging'
    if staging.exists():shutil.rmtree(staging)
    staging.mkdir();repository=staging/REPO;repository.mkdir();(repository/'resources').mkdir()
    shutil.copy2(ROOT/PLUGIN/'resources/icon.png',repository/'resources/icon.png')
    plugin_zip=output/(PLUGIN+'-'+VERSION+'.zip');zipdir(ROOT/PLUGIN,plugin_zip)
    local=base_url is None
    base=base_url or 'special://home/addons/'+REPO+'/repo/'
    if not local and not base.startswith(('https://','http://')):raise ValueError('base URL must be HTTP(S)')
    (repository/'addon.xml').write_text(repo_xml(base),encoding='utf-8')
    shutil.copy2(ROOT/'LICENSE',repository/'LICENSE')
    feed=(repository/'repo') if local else (output/'site')
    plugin_dir=feed/'packages'/PLUGIN;plugin_dir.mkdir(parents=True,exist_ok=True)
    shutil.copy2(plugin_zip,plugin_dir/plugin_zip.name);shutil.copy2(str(plugin_zip)+'.sha256',str(plugin_dir/plugin_zip.name)+'.sha256')
    shutil.copytree(ROOT/PLUGIN/'resources',plugin_dir/'resources',dirs_exist_ok=True)
    index(feed,[ROOT/PLUGIN/'addon.xml'] if local else [ROOT/PLUGIN/'addon.xml',repository/'addon.xml'])
    repository_zip=output/(REPO+'-'+VERSION+('-local' if local else '')+'.zip');zipdir(repository,repository_zip)
    if not local:
        repo_dir=feed/'packages'/REPO;repo_dir.mkdir(parents=True,exist_ok=True)
        shutil.copy2(repository_zip,repo_dir/(REPO+'-'+VERSION+'.zip'));shutil.copy2(str(repository_zip)+'.sha256',str(repo_dir/(REPO+'-'+VERSION+'.zip'))+'.sha256');shutil.copytree(repository/'resources',repo_dir/'resources',dirs_exist_ok=True)
        shutil.copy2(repository_zip,feed/repository_zip.name);shutil.copy2(plugin_zip,feed/plugin_zip.name)
        (feed/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>AnimeVietsub Kodi</title><h1>AnimeVietsub Kodi — thử nghiệm</h1><p>Kodi 19+ · Nguồn mã hóa riêng / trang xác minh chưa hỗ trợ.</p><p><a href="'+repository_zip.name+'">Cài repository ZIP</a></p><p><a href="'+plugin_zip.name+'">Cài addon ZIP trực tiếp</a></p><p><a href="addons.xml">addons.xml</a></p>',encoding='utf-8')
    shutil.rmtree(staging)
    return plugin_zip,repository_zip
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base-url');p.add_argument('--output',default=str(ROOT/'dist'));a=p.parse_args()
    for f in build(a.output,a.base_url):print(f)
