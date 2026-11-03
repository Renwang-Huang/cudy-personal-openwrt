#!/usr/bin/env python3
"""Build the DHCP/nftset DNS variant with the official SDK; never accesses a router."""
import hashlib
import json
import shutil
import subprocess
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
WORK = REPO / 'work/tr1200-passwall-dns-build'


def verified(path, item):
    return path.is_file() and path.stat().st_size == item['bytes'] and hashlib.blake2b(path.read_bytes(), digest_size=32).hexdigest() == item['content_id']


def logged(name, command, cwd):
    with (WORK/(name+'.log')).open('wb') as log:
        result = subprocess.run(command,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:
        raise SystemExit(name+' failed; inspect the local log.')


def main():
    WORK.mkdir(parents=True,exist_ok=True)
    lock = json.loads((HERE/'sources.lock.json').read_text())
    item = next(x for x in lock['tools'] if x['name']=='sdk')
    archive = WORK/item['filename']
    if not archive.exists():
        with urllib.request.urlopen(item['url'],timeout=120) as response, archive.open('wb') as output:
            shutil.copyfileobj(response,output)
    if not verified(archive,item):
        raise SystemExit('SDK archive verification failed.')
    sdk = WORK/'sdk'
    if not (sdk/'Makefile').exists():
        sdk.mkdir(exist_ok=True)
        logged('extract-sdk',['tar','--zstd','-xf',str(archive),'--strip-components=1','-C',str(sdk)],WORK)
    recipe = next(x for x in lock['archives'] if x['name']=='dnsmasq-custom-recipe')
    commit = recipe['commit']
    (sdk/'feeds.conf').write_text('src-git --root=package base https://github.com/openwrt/openwrt.git^'+commit+'\n')
    logged('fetch-recipes',['./scripts/feeds','update','base'],sdk)
    logged('install-dns-recipe',['./scripts/feeds','install','-f','dnsmasq'],sdk)
    path = REPO/recipe['path']
    if not verified(path,recipe):
        raise SystemExit('Custom recipe verification failed.')
    logged('restore-recipe',['tar','-xzf',str(path),'-C',str(sdk/'feeds/base/package/network/services')],WORK)
    source = next(x for x in lock['archives'] if x['name']=='dnsmasq-source')
    path = REPO/source['path']
    if not verified(path,source):
        raise SystemExit('DNS source verification failed.')
    (sdk/'dl').mkdir(exist_ok=True)
    shutil.copy2(path,sdk/'dl'/path.name)
    config = 'CONFIG_PACKAGE_dnsmasq-full=m\n# CONFIG_PACKAGE_dnsmasq is not set\n'
    config += (HERE/'dnsmasq.config').read_text()
    (sdk/'.config').write_text(config)
    logged('defconfig',['make','defconfig'],sdk)
    logged('compile',['make','-j8','package/feeds/base/dnsmasq/compile','V=s'],sdk)
    packages = list((sdk/'bin').rglob('dnsmasq-full-2.93-r99.apk'))
    if len(packages)!=1:
        raise SystemExit('Expected one custom DNS package.')
    print('Custom DNS package built:',packages[0])


if __name__ == '__main__':
    main()
