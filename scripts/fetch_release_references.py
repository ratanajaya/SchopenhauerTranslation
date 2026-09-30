"""Download public source witnesses and validation tools into a disposable cache."""
from pathlib import Path
import json
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.release-cache'
CACHE.mkdir(exist_ok=True)

def fetch(url, path):
    if not path.exists():
        request = urllib.request.Request(url, headers={'User-Agent': 'SchopenhauerTranslation/1.0 (source collation)'})
        with urllib.request.urlopen(request, timeout=60) as response:
            path.write_bytes(response.read())
    print(path.name)

for number in ('38427', '40097'):
    fetch(f'https://www.gutenberg.org/files/{number}/{number}-h/{number}-h.html', CACHE / f'pg{number}.html')
release_url = 'https://api.github.com/repos/w3c/epubcheck/releases/tags/v5.4.0'
with urllib.request.urlopen(release_url, timeout=30) as response:
    release = json.load(response)
asset = next(a for a in release['assets'] if a['name'] == 'epubcheck-5.4.0.zip')
archive = CACHE / asset['name']
fetch(asset['browser_download_url'], archive)
with zipfile.ZipFile(archive) as zipped:
    zipped.extractall(CACHE / 'epubcheck')
