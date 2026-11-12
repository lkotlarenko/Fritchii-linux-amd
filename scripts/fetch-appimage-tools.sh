#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
tools=$(realpath -m -- "${FRITCHII_APPIMAGE_TOOLS:-$root/build/appimage-tools}")
mkdir -p "$tools"
temporary=$(mktemp -d "$tools/.download.XXXXXX")
trap 'rm -rf -- "$temporary"' EXIT
while read -r digest name; do
    [[ "$digest" =~ ^[0-9a-f]{64}$ && "$name" =~ ^linuxdeploy(-plugin-qt)?-x86_64.AppImage$ ]]
    path="$tools/$name"
    if [[ -f "$path" ]]; then
        printf '%s  %s\n' "$digest" "$path" | sha256sum --check --status || {
            printf 'Existing tool checksum differs: %s. Use a new FRITCHII_APPIMAGE_TOOLS directory.\n' "$path" >&2
            exit 1
        }
        continue
    fi
    repository=linuxdeploy
    [[ "$name" != *plugin-qt* ]] || repository=linuxdeploy-plugin-qt
    curl --fail --location --retry 3 --output "$temporary/$name" \
        "https://github.com/linuxdeploy/$repository/releases/download/continuous/$name"
    printf '%s  %s\n' "$digest" "$temporary/$name" | sha256sum --check --status
    chmod +x "$temporary/$name"
    mv -- "$temporary/$name" "$path"
done < "$root/dist/linux-appimage-tools.sha256"
printf 'Verified AppImage tools in %s\n' "$tools"
