#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd -- "$root/dist/recipes"
if ! sha256sum --check --status SHA256SUMS; then
    printf 'Official shader recipe checksum failed; see dist/recipes/README.md.\n' >&2
    exit 1
fi
