#!/usr/bin/env python3
"""Rebuild the GitHub Pages feed in docs/ before committing a new addon version."""
from pathlib import Path
import shutil
import tempfile
from build_repo import build, ROOT
BASE='https://sonle998.github.io/kodi-animevietsub/'
with tempfile.TemporaryDirectory() as tmp:
    build(tmp,BASE)
    docs=ROOT/'docs'
    if docs.exists():shutil.rmtree(docs)
    shutil.copytree(Path(tmp)/'site',docs)
    (docs/'.nojekyll').touch()
print('Updated docs/ for '+BASE+'; commit and push these files to publish.')
