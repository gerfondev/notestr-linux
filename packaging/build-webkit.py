#!/usr/bin/env python3
"""Build the reviewed WebKitGTK source on Ubuntu 24.04, outside personal data directories.

Requires the Ubuntu webkit2gtk build dependencies, cmake, ninja-build and lld.
No packages are installed by this script. Download the official source archive from
https://webkitgtk.org/releases/webkitgtk-2.54.0.tar.xz before running it.
The output is a DESTDIR installation tree, not a system installation.
"""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import tarfile

VERSION = '2.54.0'
SHA256 = '846fd19ccedbae1dbfe904f26dbf2d68a800a33a50caf2ad5222c8dcb3f25682'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('archive', type=Path)
parser.add_argument('workspace', type=Path)
parser.add_argument('--jobs', type=int, default=4)
args = parser.parse_args()
if hashlib.sha256(args.archive.read_bytes()).hexdigest() != SHA256:
    raise SystemExit('Unexpected WebKitGTK source checksum')
work = args.workspace.resolve()
work.mkdir(parents=True, exist_ok=True)
with tarfile.open(args.archive) as archive:
    archive.extractall(work, filter='data')
# The 2.54.0 video-only implementation lacks the guard present in its header.
media = work / f'webkitgtk-{VERSION}' / 'Source/WebCore/bindings/js/JSHTMLMediaElementCustom.cpp'
original = media.read_text()
patches = __import__('json').loads(Path(__file__).with_name('webkit-build-patches.json').read_text())
assert hashlib.sha256(original.encode()).hexdigest() == patches[0]['beforeSha256']
patched = original.replace('#include "JSHTMLMediaElement.h"', '#if ENABLE(VIDEO)\n#include "JSHTMLMediaElement.h"') + '\n#endif // ENABLE(VIDEO)\n'
assert hashlib.sha256(patched.encode()).hexdigest() == patches[0]['afterSha256']
media.write_text(patched)
options = {
    'PORT': 'GTK', 'CMAKE_BUILD_TYPE': 'Release', 'CMAKE_INSTALL_PREFIX': '/usr',
    'CMAKE_INSTALL_LIBDIR': 'lib/x86_64-linux-gnu',
    'CMAKE_INSTALL_LIBEXECDIR': 'lib/x86_64-linux-gnu',
    'LIBEXEC_INSTALL_DIR': '/usr/lib/x86_64-linux-gnu/webkitgtk-6.0',
    'USE_GTK4': 'ON', 'USE_LIBBACKTRACE': 'OFF', 'USE_LD_LLD': 'ON',
    'ENABLE_DOCUMENTATION': 'OFF', 'ENABLE_MINIBROWSER': 'OFF',
    'USE_GSTREAMER': 'OFF', 'ENABLE_API_TESTS': 'OFF', 'ENABLE_VIDEO': 'OFF', 'ENABLE_WEB_AUDIO': 'OFF',
    'ENABLE_WEBGL': 'OFF', 'ENABLE_GAMEPAD': 'OFF',
    'ENABLE_SPEECH_SYNTHESIS': 'OFF', 'ENABLE_WEBDRIVER': 'OFF',
    'CMAKE_C_FLAGS': f'-ffile-prefix-map={work}=.',
    'CMAKE_CXX_FLAGS': f'-ffile-prefix-map={work}=.',
}
build = work / 'webkit-build'
subprocess.run(['cmake', '-S', str(work / f'webkitgtk-{VERSION}'), '-B', str(build),
                '-G', 'Ninja', *(f'-D{k}={v}' for k, v in options.items())], check=True)
subprocess.run(['cmake', '--build', str(build), '--parallel', str(args.jobs)], check=True)
subprocess.run(['cmake', '--install', str(build)],
               env=dict(os.environ, DESTDIR=str(work / 'webkit-install')), check=True)
