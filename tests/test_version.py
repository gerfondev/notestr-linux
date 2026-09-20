"""Keep the release documentation and packaging tied to the application version."""
from pathlib import Path
import re
import subprocess
import sys

from nostr_notes import __version__

ROOT = Path(__file__).resolve().parents[1]


def test_release_version_is_consistent():
    config = (ROOT / 'pyproject.toml').read_text()
    assert 'dynamic = ["version"]' in config
    assert 'version = {attr = "nostr_notes.__version__"}' in config
    for name in ('README.md', 'packaging/README.md'):
        document = (ROOT / name).read_text()
        versions = re.findall(r'Notestr-([\d.]+)-x86_64\.AppImage', document)
        assert versions and set(versions) == {__version__}
    assert f'Version du paquet Python : `{__version__}`' in (ROOT / 'README.md').read_text()
    result = subprocess.check_output(
        [sys.executable, '-m', 'nostr_notes', '--version'], text=True)
    assert result.strip() == f'Notestr {__version__}'
