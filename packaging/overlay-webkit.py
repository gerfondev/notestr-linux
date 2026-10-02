#!/usr/bin/env python3
"""Overlay a reviewed WebKitGTK 2.54.0 DESTDIR tree onto a generated AppDir."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil


def overlay(app, installation):
    app, installation = Path(app), Path(installation)
    lib = Path('usr/lib/x86_64-linux-gnu')
    files = [p for p in installation.rglob('*') if p.is_file() and (
        p.name.startswith(('libwebkitgtk-6.0.so', 'libjavascriptcoregtk-6.0.so'))
        or (lib / 'webkitgtk-6.0') in p.relative_to(installation).parents
        or p.name in ('WebKit-6.0.typelib', 'JavaScriptCore-6.0.typelib')
        or ('locale' in p.parts and p.suffix == '.mo'))]
    if not all(any(p.name == name for p in files) for name in (
        'libwebkitgtk-6.0.so.4', 'libjavascriptcoregtk-6.0.so.1',
        'WebKit-6.0.typelib', 'JavaScriptCore-6.0.typelib',
        'WebKitWebProcess', 'WebKitNetworkProcess', 'libwebkitgtkinjectedbundle.so')):
        raise SystemExit('Incomplete WebKitGTK runtime installation')
    # Do not retain old engine helper binaries or the unused distribution MiniBrowser.
    helpers = app / lib / 'webkitgtk-6.0'
    if helpers.exists():
        shutil.rmtree(helpers)
    hashes = {}
    for source in files:
        relative = source.relative_to(installation)
        target = app / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink() or target.exists():
            target.unlink()
        if source.is_symlink():
            target.symlink_to(source.readlink())
        else:
            shutil.copyfile(source, target)
            target.chmod(source.stat().st_mode & 0o777)
        hashes[str(relative)] = hashlib.sha256(source.read_bytes()).hexdigest()
    source_tree = installation.parent / 'webkitgtk-2.54.0'
    if not source_tree.is_dir():
        raise SystemExit('Reviewed source tree required beside installation for licence notices')
    notices = app / 'usr/share/doc/webkitgtk-2.54.0-source-licenses'
    notices.mkdir(parents=True, exist_ok=True)
    for source in source_tree.rglob('*'):
        if source.is_file() and source.name.lower().startswith(('license', 'copying')):
            target = notices / source.relative_to(source_tree)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    (notices / 'SOURCE.txt').write_text(
        'WebKitGTK 2.54.0\nhttps://webkitgtk.org/releases/webkitgtk-2.54.0.tar.xz\n'
        'SHA-256: 846fd19ccedbae1dbfe904f26dbf2d68a800a33a50caf2ad5222c8dcb3f25682\n'
        'Build instructions: packaging/build-webkit.py in the Notestr source release.\n')
    report = {'component': 'WebKitGTK and JavaScriptCore', 'version': '2.54.0',
              'source': 'https://webkitgtk.org/releases/webkitgtk-2.54.0.tar.xz',
              'sourceSha256': '846fd19ccedbae1dbfe904f26dbf2d68a800a33a50caf2ad5222c8dcb3f25682',
              'advisory': 'WSA-2026-0006', 'files': hashes,
              'buildPatches': json.loads(Path(__file__).with_name('webkit-build-patches.json').read_text())}
    doc = app / 'usr/share/doc'
    doc.mkdir(parents=True, exist_ok=True)
    (doc / 'webkit-source-build.json').write_text(json.dumps(report, indent=2) + '\n')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('appdir', type=Path)
    parser.add_argument('installation', type=Path)
    args = parser.parse_args()
    overlay(args.appdir, args.installation)
