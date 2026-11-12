#!/usr/bin/env bash
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if [[ -x "$script_dir/lichii" ]]; then
    binary="$script_dir/lichii"
else
    binary="${FRITCHII_BUILD_DIR:-$script_dir/../build/linux-release}/bin/lichii"
fi
if [[ ! -x "$binary" ]]; then
    printf 'Fritchii executable missing: %s\nRun scripts/build-linux.sh first.\n' "$binary" >&2
    exit 1
fi
binary=$(realpath -- "$binary")
args=()
for arg in "$@"; do
    if [[ -e "$arg" ]]; then
        args+=("$(realpath -- "$arg")")
    else
        args+=("$arg")
    fi
done
# Keep Fritchii separate from existing Eden/Lichii installations.
export XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/fritchii-native"
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}/fritchii-native"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}/fritchii-native"
mkdir -p -- "$XDG_DATA_HOME" "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME"
# Avoid the inherited current-directory portable-user lookup.
cd -- "$XDG_DATA_HOME"
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-wayland;xcb}"
exec "$binary" "${args[@]}"
