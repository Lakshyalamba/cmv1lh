"""Create a deterministic, tracked deployment snapshot from validated Phase 1 data.

Run from the repository root: python -m scripts.package_data
"""
import gzip
import hashlib
import io
from pathlib import Path
import tarfile
from pipeline.fetch import ROOT
from pipeline.prepare import load_sources


def package(root: Path = ROOT):
    load_sources(root)  # Preserve complete manifest, checksum and normalization checks.
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w') as archive:
        for path in sorted((root / 'data/raw').glob('*.json')):
            content = path.read_bytes()
            info = tarfile.TarInfo(path.relative_to(root).as_posix())
            info.size = len(content)
            info.mode = 0o644
            info.mtime = 0
            archive.addfile(info, io.BytesIO(content))
    target = root / 'data/snapshot.tar.gz'
    target.write_bytes(gzip.compress(buffer.getvalue(), mtime=0))
    (root / 'data/snapshot.sha256').write_text(hashlib.sha256(target.read_bytes()).hexdigest() + '  data/snapshot.tar.gz\n')
    print(f'Validated deployment snapshot: {target.name} ({target.stat().st_size} bytes)')


if __name__ == '__main__':
    package()
