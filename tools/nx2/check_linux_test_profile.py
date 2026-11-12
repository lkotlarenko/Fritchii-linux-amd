#!/usr/bin/env python3
"""Reject copied Qt settings that would write outside an isolated test profile."""
import sys
from pathlib import Path

base = Path(sys.argv[1]).resolve()
path_keys = {
    'nand_directory', 'sdmc_directory', 'load_directory', 'dump_directory',
    'tas_directory', 'save_directory', 'screenshot_path',
}
for directory in ('data', 'config', 'cache'):
    root = base / directory
    if not root.is_dir() or not root.resolve().is_relative_to(base):
        sys.exit(f'Invalid test profile directory: {root}')
    for path in root.rglob('*'):
        if path.is_symlink() and not path.resolve().is_relative_to(base):
            sys.exit(f'Test profile symlink escapes the profile: {path}')
for ini in (base / 'config').rglob('*.ini'):
    for line in ini.read_text().splitlines():
        key, sep, value = line.partition('=')
        if not sep or key.rsplit('\\', 1)[-1] not in path_keys:
            continue
        value = value.strip().strip('"')
        if value and not Path(value).resolve().is_relative_to(base):
            sys.exit(f'{ini}: {key} points outside the test profile; fix the copied setting.')
