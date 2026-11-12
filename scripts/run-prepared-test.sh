#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
version=$(tr -d '\r\n' < "$root/dist/frizti_version.txt")
profile=${FRITCHII_TEST_PROFILE:-v584-warm}
[[ "$profile" =~ ^[a-zA-Z0-9_-]+$ ]] || { printf 'Invalid test profile name.\n' >&2; exit 1; }
base="$root/build/performance/profiles/$profile"
[[ -d "$base/data/fritchii-native/eden/nand" ]] || { printf 'Prepared test profile is missing.\n' >&2; exit 1; }
exec 9> "$base/.test-profile.lock"
flock -n 9 || { printf 'This test profile is already in use. Close its emulator first.\n' >&2; exit 1; }
python3 "$root/tools/nx2/check_linux_test_profile.py" "$base"
export XDG_DATA_HOME="$base/data"
export XDG_CONFIG_HOME="$base/config"
export XDG_CACHE_HOME="$base/cache"
export DISABLE_LSFGVK=1
export FRITCHII_PIPELINE_DIAGNOSTICS=1
export MESA_SHADER_CACHE_SHOW_STATS=true
exec "$root/artifacts/Fritchii-$version-linux-x86_64.AppImage" "$@"
