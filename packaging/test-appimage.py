#!/usr/bin/env python3
"""Exercise the bundled Python/GTK/WebKit, without using the source venv."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
image = Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory(prefix='notestr-image-test-') as work:
    subprocess.run([str(image), '--appimage-extract'], cwd=work,
                   stdout=subprocess.DEVNULL, check=True)
    app = Path(work) / 'squashfs-root'
    env = dict(os.environ, APPDIR=str(app))
    subprocess.run([str(app / 'AppRun'), '--check'], env=env, check=True)
    launcher = (app / 'AppRun').read_text().replace('-m nostr_notes "$@"', '"$@"')
    subprocess.run(['/bin/sh', '-c', launcher, 'AppRun-test',
                    str(root / 'tests/gtk_editor_smoke.py')], env=env, check=True)
    subprocess.run(['/bin/sh', '-c', launcher, 'AppRun-test', '-c',
                    "from nostr_notes.pdf_export import export_markdown_pdf; "
                    "from pathlib import Path; import sys; "
                    "p = export_markdown_pdf('# Test AppImage\\n\\nCafé et code.', sys.argv[1]); "
                    "assert Path(p).read_bytes().startswith(b'%PDF-'); print('Export PDF embarqué OK.')",
                    str(Path(work) / 'test.pdf')], env=env, check=True)
