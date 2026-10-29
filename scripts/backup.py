#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Source-only snapshot backup; never bundles development history or config."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
# Explicit reviewable allowlist: never recursively copy arbitrary source trees.
FILES = ['LICENSE', 'NOTICE.md', 'assets/BRANDING.md', '.gitignore', 'README.md', 'retrobridge.py', 'fixtures/catalog.json',
         'fixtures/news.xml', 'fixtures/news.txt', 'schemas/signup.json',
         'schemas/feedback.json', 'schemas/subscription-state.json',
         'tests/test_pilot.py', 'scripts/backup.py',
         'CONTRIBUTING.md', 'SECURITY.md', 'docs/SUPPORT_MATRIX.md',
         'docs/GOVERNANCE_AND_ROADMAP.md',
         '.github/ISSUE_TEMPLATE/device-proposal.md',
         '.github/ISSUE_TEMPLATE/adapter-proposal.md',
         'assets/retrobridge-light.svg', 'assets/retrobridge-dark.svg']


def git(path, *args):
    return subprocess.run(['git', '-C', str(path), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def backup(destination):
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=False, mode=0o700)
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp) / 'snapshot'
        stage.mkdir()
        for name in FILES:
            src = ROOT / name
            if src.is_symlink() or not src.is_file() or src.stat().st_size > (8 if name.startswith("designs/") else 1) * 1024 * 1024:
                raise ValueError('Invalid allowlisted source: ' + name)
            dst = stage / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
        git(stage, 'init', '-b', 'main')
        git(stage, 'add', '--', *FILES)
        git(stage, '-c', 'user.name=Private source snapshot', '-c', 'user.email=snapshot@example.invalid',
            '-c', 'commit.gpgsign=false', 'commit', '-m', 'Reviewed source-only snapshot')
        bundle = destination / 'retrobridge-source.bundle'
        git(stage, 'bundle', 'create', str(bundle), 'main')
        manifest = {'format':1, 'sha256':hashlib.sha256(bundle.read_bytes()).hexdigest(),
                    'files': {name:hashlib.sha256((stage/name).read_bytes()).hexdigest() for name in FILES}}
        (destination/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return destination


def restore(source, destination):
    source, destination = source.resolve(), destination.resolve()
    if destination.exists():
        raise ValueError('Restore target must not exist')
    manifest = json.loads((source/'manifest.json').read_text())
    bundle = source/'retrobridge-source.bundle'
    if hashlib.sha256(bundle.read_bytes()).hexdigest() != manifest['sha256']:
        raise ValueError('Bundle checksum mismatch')
    # Only our exact source snapshot shape is accepted. Do not run restored code automatically.
    if set(manifest['files']) != set(FILES):
        raise ValueError('Unexpected manifest files')
    subprocess.run(['git', 'clone', '--no-local', '--branch', 'main', str(bundle), str(destination)], check=True, capture_output=True)
    git(destination, 'remote', 'remove', 'origin')
    if set(git(destination, 'ls-files').splitlines()) != set(FILES):
        raise ValueError('Unexpected source tree')
    for name, digest in manifest['files'].items():
        path = destination/name
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('Source checksum mismatch: '+name)
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    b = sub.add_parser('backup'); b.add_argument('destination', type=Path)
    r = sub.add_parser('restore'); r.add_argument('source', type=Path); r.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(backup(args.destination) if args.action == 'backup' else restore(args.source, args.destination))
