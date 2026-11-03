#!/usr/bin/env python3
"""Build the compact core from archived upstream source, without accessing a router."""
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
WORK = REPO / 'work/tr1200-passwall-source-build'


def verified(path, item):
    return path.is_file() and path.stat().st_size == item['bytes'] and hashlib.blake2b(path.read_bytes(), digest_size=32).hexdigest() == item['content_id']


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    lock = json.loads((HERE / 'sources.lock.json').read_text())
    source = next(x for x in lock['archives'] if x['name'] == 'sing-box-1.13.21')
    archive = REPO / source['path']
    if not verified(archive, source):
        raise SystemExit('Source archive verification failed.')
    src = WORK / 'sing-box-1.13.21'
    if not src.exists():
        subprocess.run(['tar','-xzf',str(archive),'-C',str(WORK)],check=True)
    upx_item = next(x for x in lock['tools'] if x['name'] == 'upx')
    upx_archive = WORK / upx_item['filename']
    if not upx_archive.exists():
        with urllib.request.urlopen(upx_item['url'], timeout=60) as response:
            upx_archive.write_bytes(response.read())
    if not verified(upx_archive, upx_item):
        raise SystemExit('Compression tool verification failed.')
    upx = WORK / 'upx'
    with tarfile.open(upx_archive) as tar:
        member = next(x for x in tar if x.isfile() and x.name.endswith('/upx'))
        upx.write_bytes(tar.extractfile(member).read())
    upx.chmod(0o755)
    cfg = json.loads((HERE / 'core-build.json').read_text())
    env = dict(os.environ, GOTOOLCHAIN=cfg['go_toolchain'], GOOS='linux', GOARCH='mipsle',
               GOMIPS='softfloat', CGO_ENABLED='0', GOMAXPROCS='8',
               GOCACHE=str(WORK/'go-cache'), GOMODCACHE=str(WORK/'go-mod-cache'), GOPATH=str(WORK/'go-work'))
    binary = WORK / 'sing-box'
    args = ['go','build','-p','8','-trimpath','-buildvcs=false','-gcflags='+cfg['gcflags'],
            '-tags',cfg['tags'],'-ldflags',cfg['ldflags'],'-o',str(binary),'./cmd/sing-box']
    for label, command, cwd in [('compile',args,src),('compress',[str(upx),'--lzma','-9',str(binary)],WORK),('test',[str(upx),'-t',str(binary)],WORK)]:
        with (WORK/(label+'.log')).open('wb') as log:
            result = subprocess.run(command,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:
            raise SystemExit(label+' failed; inspect the local log.')
    print('Compact core built:', binary, 'bytes:', binary.stat().st_size)


if __name__ == '__main__':
    main()
