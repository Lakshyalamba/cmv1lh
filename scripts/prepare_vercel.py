"""Prepare a self-contained local Vercel project, without calling Vercel.

First run npm ci and npm run build in frontend/. Then run this module.
"""
import hashlib
import json
from pathlib import Path
import shutil
import tarfile
from pipeline.fetch import ROOT
from pipeline.prepare import load_sources


def prepare(root=ROOT):
    root = Path(root)
    if not (root / 'frontend/dist/index.html').is_file():
        raise ValueError('Build frontend first: npm ci --prefix frontend; npm run build --prefix frontend')
    archive = root / 'data/snapshot.tar.gz'
    expected = (root / 'data/snapshot.sha256').read_text().split()[0]
    if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
        raise ValueError('Snapshot checksum mismatch')
    target = root / '.deploy/vercel'
    if target.exists():
        # Retain a future operator-approved Vercel project link, never put it in the payload manifest.
        for child in target.iterdir():
            if child.name == '.vercel':
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    target.mkdir(parents=True, exist_ok=True)
    for name in ['backend', 'pipeline']:
        shutil.copytree(root / name, target / name,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'Dockerfile'))
    with tarfile.open(archive, 'r:gz') as source:
        source.extractall(target, filter='data')
    load_sources(target)
    shutil.copytree(root / 'frontend/dist', target / 'static')
    for name in ['app.py', 'vercel.json', '.vercelignore']:
        shutil.copy(root / 'deployment/vercel' / name, target / name)
    shutil.copy(root / 'requirements.runtime.lock.txt', target / 'requirements.txt')
    (target / '.python-version').write_text('3.14\n')
    for name in ['README.md', 'THIRD_PARTY_NOTICES.md']:
        shutil.copy(root / name, target / name)
    shutil.copy(root / 'data/LICENSE.md', target / 'data/LICENSE.md')
    files = [p for p in target.rglob('*') if p.is_file() and '.vercel' not in p.relative_to(target).parts]
    manifest = {p.relative_to(target).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    result = {'project': '.deploy/vercel', 'source_files': len(files),
              'source_bytes': sum(p.stat().st_size for p in files),
              'snapshot_sha256': expected, 'sha256': manifest}
    # The manifest lives outside the project and is not part of its byte count.
    (root / '.deploy/vercel-manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'sha256'}, indent=2))
    return target


if __name__ == '__main__':
    prepare()
