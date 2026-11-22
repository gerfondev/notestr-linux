#!/usr/bin/env python3
"""Build the reviewed WebKitGTK source on Ubuntu 24.04, outside personal data directories.

Requires the Ubuntu webkit2gtk build dependencies, cmake, ninja-build and lld.
No packages are installed by this script. Download the official source archive from
https://webkitgtk.org/releases/webkitgtk-2.54.3.tar.xz before running it.
The output is a DESTDIR installation tree, not a system installation.
"""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import tarfile

VERSION = '2.54.3'
SHA256 = '2779c1b46f88762e8400650271ba14452dc4e30b37059981552d8b562b7d0862'
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
source_tree = work / f'webkitgtk-{VERSION}'
cursor_source = source_tree / 'Source/WebKit/UIProcess/API/gtk/WebKitWebViewBase.cpp'
cursor_text = cursor_source.read_text()
cursor_old = '    auto& platformImage = nativeImage->platformImage();\n'
cursor_new = '    auto platformImage = nativeImage->platformImage();\n'
if cursor_text.count(cursor_old) != 1:
    raise SystemExit('Unexpected WebKit cursor source; refusing to apply the reviewed local patch')
cursor_source.write_text(cursor_text.replace(cursor_old, cursor_new, 1))
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
