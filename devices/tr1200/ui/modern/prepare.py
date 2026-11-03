#!/usr/bin/env python3
"""Build an offline Cudy adaptation of the fixed shadcn theme source. No router access."""
import argparse
import hashlib
import json
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=REPO/'work/tr1200-modern-theme-build')
    parser.add_argument('--apk', type=Path, default=REPO/'work/tr1200-v0.1.1-imagebuilder/staging_dir/host/bin/apk')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True,exist_ok=True)
    lock = json.loads((HERE/'source.lock.json').read_text())
    item = lock['source_archive']
    archive = REPO/item['path']
    if archive.stat().st_size != item['bytes'] or hashlib.blake2b(archive.read_bytes(),digest_size=32).hexdigest() != item['content_id']:
        raise SystemExit('Upstream source archive verification failed.')
    if not args.apk.is_file() or not shutil.which('fakeroot'):
        raise SystemExit('An APK v3 host tool and fakeroot are required.')
    with tempfile.TemporaryDirectory(prefix='shadcn-build-',dir=output) as temporary:
        temp = Path(temporary)
        with tarfile.open(archive) as tar:
            tar.extractall(temp,filter='data')
        source = temp/'luci-theme-shadcn'
        stage = temp/'package-root'
        shutil.copytree(source/'htdocs',stage/'www')
        shutil.copytree(source/'root',stage,dirs_exist_ok=True)
        templates = stage/'usr/share/ucode/luci/template/themes/shadcn'
        shutil.copytree(source/'ucode/template/themes/shadcn',templates)
        media = stage/'www/luci-static/shadcn'
        for font in media.glob('*.woff2'):
            font.unlink()
        (media/'images/login-bg.jpeg').unlink()
        shutil.copy2(HERE/'assets/login-bg.svg',media/'images/login-bg.svg')
        for name in ['cudy.css','cudy-wifi.svg','cudy-wifi-off.svg']:
            shutil.copy2(HERE/'assets'/name,media/name)
        header = templates/'header.ut'
        text = header.read_text()
        text = text.replace('width=device-width, initial-scale=1.0, user-scalable=no','width=device-width, initial-scale=1.0')
        text = text.replace('</head>','<link rel="stylesheet" href="{{ media }}/cudy.css?v=3">\n\t</head>')
        text = text.replace('{# PKG_VERSION #}','0.6.1-cudy.3')
        scripts = '''\t\t<script src="{{ dispatcher.build_url('admin/translations', dispatcher.lang) }}"></script>
\t\t<script src="{{ resource }}/cbi.js"></script>'''
        if scripts not in text:
            raise SystemExit('Upstream login script marker changed.')
        text = text.replace(scripts,'\t\t{% if (!blank_page): %}\n'+scripts+'\n\t\t{% endif %}')
        text = text.replace("{{ _('Type to filter…') }}","{{ substr(dispatcher.lang, 0, 2) == 'zh' ? '搜索页面…' : _('Type to filter…') }}")
        header.write_text(text)
        login = templates/'sysauth.ut'
        text = login.read_text().replace('images/login-bg.jpeg','images/login-bg.svg')
        text = text.replace("include('header', { blank_page: true })","include('themes/' + theme + '/header', { blank_page: true })")
        login.write_text(text)
        documentation = stage/'usr/share/doc/luci-theme-shadcn-cudy'
        documentation.mkdir(parents=True)
        shutil.copy2(source/'LICENSE',documentation/'LICENSE')
        post = temp/'postinst'
        post.write_text('''#!/bin/sh
[ -n "${IPKG_INSTROOT:-}" ] && exit 0
uci -q set luci.themes.Shadcn=/luci-static/shadcn
uci -q commit luci
exit 0
''')
        shutil.copy2(post,stage/'etc/uci-defaults/30_luci-theme-shadcn')
        for path in [stage,*stage.rglob('*')]:
            if not path.is_symlink():
                path.chmod(0o755 if path.is_dir() or path.name=='30_luci-theme-shadcn' else 0o644)
        version = lock['package_version']
        package = output/('luci-theme-shadcn-cudy-'+version+'.apk')
        command = [str(args.apk.resolve()),'mkpkg','--files',str(stage),'--output',str(package),
                   '--script','post-install:'+str(post)]
        metadata = {'name':'luci-theme-shadcn-cudy','version':version,'arch':'noarch',
                    'description':'Modern LuCI shell adapted for Cudy small-flash routers',
                    'license':'Apache-2.0','url':lock['upstream'],'depends':'luci-base'}
        for key,value in metadata.items():
            command += ['--info',key+':'+value]
        result = subprocess.run(['fakeroot','sh','-c','chown -R 0:0 "$1"; shift; exec "$@"','sh',str(stage),*command],capture_output=True)
        if result.returncode:
            raise SystemExit('Theme packaging failed.')
        shutil.copytree(stage,output/'package-root',dirs_exist_ok=True)
        print('Built:',package)
        print('Download bytes:',package.stat().st_size)
        print('Runtime content bytes:',sum(path.stat().st_size for path in stage.rglob('*') if path.is_file()))
        print('No router was contacted. Use the documented installation and rollback procedure.')


if __name__ == '__main__':
    main()
