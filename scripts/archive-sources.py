#!/usr/bin/env python3
"""Archive fixed upstream Git commits without executing any downloaded code."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

project = Path(__file__).resolve().parents[1]
source_file = project / 'reference/sources.json'
sources = json.loads(source_file.read_text())['sources']
destination = project / 'reference/sources'
destination.mkdir(parents=True, exist_ok=True)

def archive_source(item):
    filename = f"{item['name']}-{item['commit']}.tar.gz"
    path = destination / filename
    url = f"https://codeload.github.com/{item['repository']}/tar.gz/{item['commit']}"
    if not path.exists():
        partial = path.with_name(path.name + '.part')
        subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error',
                        '--retry', '3', '--connect-timeout', '15', '--max-time', '300',
                        '--output', str(partial), url], check=True)
        with tarfile.open(partial, 'r:gz') as archive:
            if not archive.getmembers():
                raise ValueError('Empty source archive')
        partial.rename(path)
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    result = dict(item, filename=filename, url=url, bytes=path.stat().st_size,
                  sha256=digest.hexdigest())
    print(f"Archived {item['name']}: {path.stat().st_size} bytes", flush=True)
    return result

with ThreadPoolExecutor(max_workers=3) as executor:
    archived = list(executor.map(archive_source, sources))
(project / 'reference/archives.lock.json').write_text(
    json.dumps({'sources': archived}, ensure_ascii=False, indent=2) + '\n')
(destination / 'SHA256SUMS').write_text(''.join(
    f"{item['sha256']}  {item['filename']}\n" for item in archived))
