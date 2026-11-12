#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
version=$(tr -d '\r\n' < "$root/dist/frizti_version.txt")
artifact=$(realpath -- "${1:-$root/artifacts/Fritchii-$version-linux-x86_64.AppImage}")
platform=${QT_QPA_PLATFORM:-xcb}
[[ "$platform" == wayland || "$platform" == xcb ]]
mkdir -p "$root/build/runtime-tests"
temporary=$(mktemp -d "$root/build/runtime-tests/appimage-smoke.XXXXXX")
report="$temporary/gui-report.txt"
# Qt flags must be split into individual compiler arguments.
read -r -a qt_flags <<< "$(pkg-config --cflags --libs Qt6Widgets)"
"${CXX:-clang++}" -std=c++20 -shared -fPIC "$root/tools/nx2/linux_gui_smoke.cpp" \
    -o "$temporary/smoke.so" "${qt_flags[@]}" -ldl
env XDG_DATA_HOME="$temporary/data" XDG_CONFIG_HOME="$temporary/config" \
    XDG_CACHE_HOME="$temporary/cache" QT_QPA_PLATFORM="$platform" DISABLE_LSFGVK=1 \
    FRITCHII_SMOKE_REPORT="$report" LD_PRELOAD="$temporary/smoke.so" \
    APPIMAGE_EXTRACT_AND_RUN=1 timeout --kill-after=10s 30s "$artifact" \
    > "$temporary/console.log" 2>&1
rg -F "platform=$platform" "$report"
rg -F "main=Fritchii | v$version |" "$report"
rg -x 'dialog=ConfigureDialog' "$report"
rg -x 'settings=opened' "$report"
cp -- "$report" "$root/build/runtime-tests/appimage-smoke-$platform.txt"
cp -- "$temporary/console.log" "$root/build/runtime-tests/appimage-smoke-$platform.log"
rm -rf -- "$temporary"
printf 'AppImage home/settings smoke passed (%s).\n' "$platform"
