#!/usr/bin/env python3
"""Build on Ubuntu 24.04 amd64 using an installed project venv and official runtime."""
import hashlib
import ast
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if platform.machine() != 'x86_64' or sys.version_info[:2] != (3, 12):
    raise SystemExit('Build requires Linux amd64 and Python 3.12 (Ubuntu 24.04).')
if len(sys.argv) != 2:
    raise SystemExit('Usage: python3 packaging/build-appimage.py /path/to/runtime-x86_64')
runtime = Path(sys.argv[1]).resolve()
header = runtime.read_bytes()[:20]
if header[:4] != b'\x7fELF' or header[8:11] != b'AI\x02' or header[18:20] != b'>\x00':
    raise SystemExit('Expected an official type-2 amd64 AppImage runtime.')
version = next(ast.literal_eval(node.value) for node in ast.parse(
    (ROOT / 'src/nostr_notes/__init__.py').read_text()).body
    if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == '__version__' for target in node.targets))
out = ROOT / 'dist'
out.mkdir(exist_ok=True)
image = out / f'Notestr-{version}-x86_64.AppImage'
# Never reuse a venv's launchers, editable paths, caches, or local configuration.
ignore = shutil.ignore_patterns('__pycache__', '*.pyc', '*.pth', 'direct_url.json',
                                '__editable__*', 'pip', 'pip-*', 'pytest', '_pytest',
                                'pytest-*', 'nostr_private_notes*', 'test', 'tests', 'SelfTest')
with tempfile.TemporaryDirectory(prefix='notestr-appimage-') as work:
    app = Path(work) / 'Notestr.AppDir'
    copied_system_paths = set()
    def copy(source, target=None):
        source = Path(source)
        dest = app / (target or str(source).lstrip('/'))
        dest.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, dest, dirs_exist_ok=True, ignore=ignore)
        else:
            shutil.copy2(source, dest)
        if str(source).startswith(('/usr/', '/lib/')):
            if source.is_dir():
                for item in source.rglob('*'):
                    if item.is_file() and (dest / item.relative_to(source)).exists():
                        copied_system_paths.add(str(item))
            else:
                copied_system_paths.add(str(source))
        return dest
    copy('/usr/bin/python3.12', 'usr/bin/python3')
    copy('/usr/lib/python3.12')
    site = 'usr/lib/python3.12/site-packages'
    for name in ('gi', 'cairo'):
        source = Path('/usr/lib/python3/dist-packages') / name
        if source.exists():
            copy(source, f'{site}/{name}')
    # Resolve runtime requirements through the build venv, including packages
    # inherited from --system-site-packages (Markdown, Pillow, cryptography…).
    dependency_script = """
import importlib.metadata as md, json, tomllib
from packaging.requirements import Requirement
from pathlib import Path
pending = tomllib.loads(Path('pyproject.toml').read_text())['project']['dependencies']
seen, files = set(), []
while pending:
    req = Requirement(pending.pop())
    if req.marker and not req.marker.evaluate({'extra': ''}):
        continue
    dist = md.distribution(req.name)
    name = dist.metadata['Name'].lower()
    if name in seen:
        continue
    seen.add(name)
    pending.extend(dist.requires or [])
    if not dist.files:
        for name in (dist.read_text('top_level.txt') or '').splitlines():
            source = Path(dist.locate_file(name))
            if not source.exists():
                source = source.with_suffix('.py')
            if source.exists():
                files.append([str(source), source.name])
        metadata = Path(dist._path)
        files.append([str(metadata), metadata.name])
    for file in dist.files or []:
        source = Path(dist.locate_file(file))
        if '..' not in file.parts and not str(file).endswith(('.pyc', '.pth', 'direct_url.json')):
            files.append([str(source), str(file)])
print(json.dumps(files))
"""
    files = json.loads(subprocess.check_output(
        [str(ROOT / '.venv/bin/python'), '-c', dependency_script], cwd=ROOT, text=True))
    for source, relative in files:
        if (Path(source).exists() and not relative.endswith('.pyc')
                and not {'__pycache__', 'tests', 'test', 'SelfTest'}.intersection(Path(relative).parts)):
            copy(source, f'{site}/{relative}')
    copy(ROOT / 'src/nostr_notes', f'{site}/nostr_notes')
    lib = Path('/usr/lib/x86_64-linux-gnu')
    typelibs = ('Adw-1', 'Gtk-4.0', 'Gdk-4.0', 'Gsk-4.0', 'GLib-2.0',
                'GObject-2.0', 'Gio-2.0', 'GModule-2.0', 'Graphene-1.0',
                'Pango-1.0', 'PangoCairo-1.0', 'GdkPixbuf-2.0', 'cairo-1.0',
                'HarfBuzz-0.0', 'freetype2-2.0', 'WebKit-6.0', 'JavaScriptCore-6.0', 'Soup-3.0')
    for name in typelibs:
        copy(lib / 'girepository-1.0' / (name + '.typelib'))
    for name in ('webkitgtk-6.0', 'gio/modules', 'gdk-pixbuf-2.0'):
        copy(lib / name)
    schemas = app / 'usr/share/glib-2.0/schemas'
    for schema in Path('/usr/share/glib-2.0/schemas').glob('org.gtk.gtk4.*.gschema.xml'):
        copy(schema)
    subprocess.run(['glib-compile-schemas', str(schemas)], check=True)
    copy('/usr/share/icons/hicolor/index.theme')
    for name in ('icons/Adwaita', 'fonts/truetype/dejavu'):
        copy(Path('/usr/share') / name)
    # Libraries loaded via GI or dlopen are not visible in Python's ldd output.
    roots = ['libgtk-4.so.1', 'libadwaita-1.so.0', 'libwebkitgtk-6.0.so.4',
             'libgirepository-1.0.so.1', 'libgobject-2.0.so.0', 'libgio-2.0.so.0',
             'libpango-1.0.so.0', 'libpangocairo-1.0.so.0', 'libpangoft2-1.0.so.0',
             'libcairo.so.2', 'librsvg-2.so.2',
             'libsecret-1.so.0', 'libgdk_pixbuf-2.0.so.0', 'libgthread-2.0.so.0']
    for name in roots:
        copy(lib / name)
    # Keep glibc and the graphics driver stack supplied by the destination OS.
    excluded = re.compile(r'^(ld-linux|lib(c|m|pthread|dl|rt|resolv|nss_[^.]+)\.so)')
    pending = [p for p in app.rglob('*') if p.is_file() and ('.so' in p.name or p.parent.name in ('bin', 'webkitgtk-6.0'))]
    seen = set()
    while pending:
        binary = pending.pop()
        if binary in seen:
            continue
        seen.add(binary)
        result = subprocess.run(['ldd', str(binary)], capture_output=True, text=True)
        for dep in re.findall(r'=> (/\S+)', result.stdout):
            source = Path(dep)
            if excluded.match(source.name):
                continue
            dest = app / 'usr/lib/x86_64-linux-gnu' / source.name
            if not dest.exists():
                pending.append(copy(source, str(dest.relative_to(app))))
    # Include distribution copyright notices for redistributed native libraries.
    copyrights = app / 'usr/share/doc/bundled-copyright'
    copyrights.mkdir(parents=True)
    packages = set()
    paths = copied_system_paths | {p.removeprefix('/usr') for p in copied_system_paths if p.startswith('/usr/lib/')}
    for listing in Path('/var/lib/dpkg/info').glob('*.list'):
        if paths.intersection(listing.read_text().splitlines()):
            packages.add(listing.name.removesuffix('.list').split(':')[0])
    for package in sorted(packages):
        notice = Path('/usr/share/doc') / package / 'copyright'
        if not notice.is_file():
            raise SystemExit(f'Missing copyright notice for {package}')
        shutil.copyfile(notice, copyrights / (package + '.copyright'))
    copy(ROOT / 'packaging/AppRun', 'AppRun').chmod(0o755)
    copy(ROOT / 'packaging/fr.decentralia.NostrNotes.desktop', 'fr.decentralia.NostrNotes.desktop')
    icon = ROOT / 'src/nostr_notes/assets/fr.decentralia.NostrNotes.png'
    copy(icon, 'fr.decentralia.NostrNotes.png')
    copy(icon, '.DirIcon')
    payload = Path(work) / 'payload.squashfs'
    subprocess.run(['mksquashfs', str(app), str(payload), '-noappend', '-comp', 'zstd',
                    '-all-root', '-no-xattrs', '-processors', '2', '-quiet'], check=True)
    with image.open('wb') as target:
        target.write(runtime.read_bytes())
        with payload.open('rb') as source:
            shutil.copyfileobj(source, target)
    image.chmod(0o755)
checksum = hashlib.sha256(image.read_bytes()).hexdigest()
image.with_suffix('.AppImage.sha256').write_text(f'{checksum}  {image.name}\n')
print(f'Created dist/{image.name}')
