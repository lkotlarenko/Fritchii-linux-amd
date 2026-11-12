#!/usr/bin/env python3
"""Reject local private paths and user-data files in an unpacked release directory."""

import argparse
import os
from pathlib import Path
import sys


def find_marker(path, markers):
    overlap = max(map(len, markers), default=1) - 1
    tail = b""
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            data = tail + chunk
            if any(marker in data for marker in markers):
                return True
            tail = data[-overlap:] if overlap else b""
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--private-root", type=Path, action="append", default=[])
    args = parser.parse_args()
    directory = args.directory.resolve(strict=True)
    if not directory.is_dir():
        parser.error("directory must be an unpacked release tree")
    roots = [Path.home(), *args.private_root]
    # A root home in CI must not turn the entire filesystem into a forbidden marker.
    markers = [os.fsencode(str(path.resolve())) for path in roots if path.resolve() != Path("/")]
    forbidden_names = {"prod.keys", "title.keys", "hosts.yml", "authorized_keys", "id_rsa", "id_ed25519"}
    forbidden_suffixes = {".sav", ".nup", ".nsp", ".xci", ".nca", ".rdc", ".dmp"}
    failures = []
    checked = 0
    for path in directory.rglob("*"):
        relative = path.relative_to(directory)
        if path.name in forbidden_names or path.suffix.lower() in forbidden_suffixes:
            failures.append((relative, "user-data filename"))
        if path.is_symlink():
            if any(marker in os.fsencode(os.readlink(path)) for marker in markers):
                failures.append((relative, "private symlink target"))
        elif path.is_file():
            checked += 1
            if find_marker(path, markers):
                failures.append((relative, "private path marker"))
    for relative, reason in failures:
        # Report the packaged file, never the matched private string.
        print(f"FAIL: {relative}: {reason}", file=sys.stderr)
    if failures:
        return 1
    print(f"Release privacy check passed: {checked} files; no forbidden paths or user-data filenames.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
