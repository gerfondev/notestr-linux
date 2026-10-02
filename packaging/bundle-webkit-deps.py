#!/usr/bin/env python3
"""Add missing WebKit ELF dependencies from the reviewed Ubuntu build root."""
import argparse, hashlib, json, re, shutil, subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('appdir',type=Path);p.add_argument('rootfs',type=Path);a=p.parse_args()
lib=Path('usr/lib/x86_64-linux-gnu');skip=re.compile(r'^(ld-linux|lib(c|m|pthread|dl|rt|resolv|nss_[^.]+)\.so)')
added={};pending=list((a.appdir/lib).glob('libwebkitgtk*.so*'));seen=set()
while pending:
 binary=pending.pop()
 if binary.name in seen:continue
 seen.add(binary.name)
 data=subprocess.check_output(['readelf','-d',str(binary)],text=True)
 for name in re.findall(r'\(NEEDED\).*\[(.*?)\]',data):
  if skip.match(name):continue
  target=a.appdir/lib/name
  if not target.exists():
   source=a.rootfs/lib/name
   if not source.exists():raise SystemExit('Missing dependency: '+name)
   shutil.copyfile(source,target)
   matches=[]
   for listing in (a.rootfs/'var/lib/dpkg/info').glob('*.list'):
    if '/'+str(lib/name) in listing.read_text().splitlines():matches.append(listing.name.removesuffix('.list'))
   if len(matches)!=1:raise SystemExit('Unknown package for '+name)
   package=matches[0].split(':')[0]
   status=(a.rootfs/'var/lib/dpkg/status').read_text()
   block=next(b for b in status.split('\n\n') if b.startswith('Package: '+package+'\n'))
   version=re.search(r'^Version: (.*)$',block,re.M).group(1)
   notice=a.rootfs/'usr/share/doc'/package/'copyright'
   shutil.copyfile(notice,a.appdir/'usr/share/doc/bundled-copyright'/(package+'.copyright'))
   added[name]={'package':package,'version':version,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
  pending.append(target)
(a.appdir/'usr/share/doc/webkit-extra-dependencies.json').write_text(json.dumps(added,indent=2)+'\n')
print(json.dumps(added,indent=2))
