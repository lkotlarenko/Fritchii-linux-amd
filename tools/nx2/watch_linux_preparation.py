#!/usr/bin/env python3
"""Maintain a lightweight local preparation checkpoint; never control the emulator."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import time

p = argparse.ArgumentParser()
p.add_argument('--pid', required=True, type=int)
p.add_argument('--cache', required=True, type=Path)
p.add_argument('--out', required=True, type=Path)
identity = p.add_mutually_exclusive_group()
identity.add_argument('--version', help='Require a legacy release stamp, such as 5.7')
identity.add_argument('--translator', help='Require the v5.8+ shader translator hash')
a = p.parse_args()
a.out.parent.mkdir(parents=True, exist_ok=True)


def read_checkpoint(path):
    try:
        return path.read_text(errors='replace').strip()
    except FileNotFoundError:
        return ''


for _ in range(1440):
    alive = Path(f'/proc/{a.pid}').exists()
    stamp = read_checkpoint(a.cache / 'precompiled_prepared.fork-v54.txt')
    fields = stamp.split(maxsplit=4)
    expected = f'shaders-{a.translator}' if a.translator else f'v{a.version}' if a.version else None
    prepared = bool(stamp) and (expected is None or fields[3:4] == [expected])
    progress = a.cache / 'precompiled_progress.fork-v54.txt'
    checkpoint = read_checkpoint(progress) or 'Not written yet'
    text = (f'# Live preparation checkpoint\n\nUpdated: {datetime.now(timezone.utc).isoformat()}\n\n'
            f'- PID: {a.pid}; process present: {alive}\n'
            f'- Final prepared stamp matches {expected or "(any)"}: {prepared}\n'
            '- Recipe scheduled: 120,124 records. Checkpoint is a restart low-water mark, not an exact success count.\n'
            f'- Cache: `{a.cache}`\n\nCheckpoint contents:\n\n```text\n{checkpoint}\n```\n\n'
            'A final stamp alone does not prove every pipeline succeeded. Inspect the final preparation summary in the emulator log.\n')
    temporary = a.out.with_suffix('.tmp')
    temporary.write_text(text)
    temporary.replace(a.out)
    if prepared or not alive:
        break
    time.sleep(30)
