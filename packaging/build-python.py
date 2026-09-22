#!/usr/bin/env python3
"""Build Python archives without the build account's owner metadata."""
import ast
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

root = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, '-m', 'build', '--no-isolation'], cwd=root, check=True)
version = next(ast.literal_eval(node.value) for node in ast.parse(
    (root / 'src/nostr_notes/__init__.py').read_text()).body
    if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == '__version__' for target in node.targets))
archives = list((root / 'dist').glob(f'*-{version}.tar.gz'))
if len(archives) != 1:
    raise SystemExit('Expected exactly one source archive for this version.')
archive = archives[0]
with tempfile.TemporaryDirectory(prefix='notestr-sdist-') as work:
    clean = Path(work) / archive.name
    with tarfile.open(archive, 'r:gz') as source, tarfile.open(clean, 'w:gz') as target:
        for member in source:
            member.uid = member.gid = 0
            member.uname = member.gname = 'root'
            member.pax_headers = {key: value for key, value in member.pax_headers.items()
                                  if key in ('path', 'linkpath', 'mtime', 'size')}
            target.addfile(member, source.extractfile(member) if member.isfile() else None)
    archive.write_bytes(clean.read_bytes())
print('Python archives built; source archive owner metadata anonymized.')
