"""Build the local v1 release package and verify its upload checksums."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
EPUB = 'the-world-as-will-and-representation-volume-i.epub'
FILES = [EPUB, 'cover.jpg', 'RELEASE_NOTES.md', 'LICENSE.txt']


def main():
    config = json.loads((ROOT / 'release.json').read_text(encoding='utf8'))
    DIST.mkdir(exist_ok=True)
    subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'scripts/build_cover.py')], cwd=ROOT, check=True)
    subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'scripts/export_translated_chapters_to_epub.py'),
                    '--metadata-file', str(ROOT / 'release.json'), '--output', str(DIST / EPUB)], cwd=ROOT, check=True)
    shutil.copyfile(ROOT / config['cover'], DIST / 'cover.jpg')
    shutil.copyfile(ROOT / '_docs/release_notes.md', DIST / 'RELEASE_NOTES.md')
    shutil.copyfile(ROOT / 'LICENSE.txt', DIST / 'LICENSE.txt')
    sums = ''.join(f'{hashlib.sha256((DIST / name).read_bytes()).hexdigest()}  {name}\n' for name in FILES)
    (DIST / 'SHA256SUMS').write_text(sums, encoding='ascii')
    for line in (DIST / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        assert digest == hashlib.sha256((DIST / name).read_bytes()).hexdigest(), name
    unexpected = set(p.name for p in DIST.iterdir()) - set(FILES + ['SHA256SUMS'])
    if unexpected:
        raise ValueError(f'Unexpected release assets: {sorted(unexpected)}')
    print(f'Release v{config["release_version"]}, publication date {config["date"]}: five upload-ready files; checksums verified.')


if __name__ == '__main__':
    main()
