#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
build=${FRITCHII_BUILD_DIR:-"$root/build/linux-release"}
artifact_dir=$(realpath -m -- "${FRITCHII_ARTIFACT_DIR:-$root/artifacts}")
tools=${FRITCHII_APPIMAGE_TOOLS:-"$root/build/appimage-tools"}
build=$(realpath -m -- "$build")
tools=$(realpath -m -- "$tools")
bash "$root/scripts/check-linux-recipes.sh"
for tool in linuxdeploy linuxdeploy-plugin-qt; do
    path="$tools/$tool-x86_64.AppImage"
    if [[ ! -x "$path" ]]; then
        printf 'Missing packaging tool: %s\nSee README-LINUX.md.\n' "$path" >&2
        exit 1
    fi
done
test -x "$build/bin/lichii"
# A fresh staging directory avoids carrying stale libraries between package builds.
stage=$(mktemp -d "$build/appimage-stage.XXXXXX")
appdir="$stage/Fritchii.AppDir"
mkdir -p "$appdir/usr/bin" "$appdir/usr/share/applications" "$artifact_dir"
cp "$root/scripts/run-linux.sh" "$appdir/usr/bin/fritchii"
if [[ -d "$root/dist/recipes" ]]; then
    cp -a "$root/dist/recipes" "$appdir/usr/bin/recipes"
fi
cat > "$appdir/AppRun" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
appdir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
export APPDIR="$appdir"
export PATH="$appdir/usr/bin:$PATH"
export LD_LIBRARY_PATH="$appdir/usr/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export QT_PLUGIN_PATH="$appdir/usr/plugins"
export QT_QPA_PLATFORM_PLUGIN_PATH="$appdir/usr/plugins/platforms"
for hook in "$appdir"/apprun-hooks/*.sh; do
    if [[ -f "$hook" ]]; then
        source "$hook"
    fi
done
exec "$appdir/usr/bin/fritchii" "$@"
EOF
chmod +x "$appdir/AppRun" "$appdir/usr/bin/fritchii"
cp "$root/dist/io.github.frizti.fritchii.desktop" "$stage/"
cp "$root/dist/lichii.png" "$stage/io.github.frizti.fritchii.png"
mkdir -p "$appdir/usr/share/doc/fritchii"
cp "$root/LICENSE.txt" "$root/README-LINUX.md" \
    "$appdir/usr/share/doc/fritchii/"
export APPIMAGE_EXTRACT_AND_RUN=1
# The bundled strip predates Arch's RELR ELF sections; leave host libraries intact.
export NO_STRIP=1
export FRITCHII_REAL_QMAKE=${QMAKE:-/usr/lib/qt6/bin/qmake}
qt_plugins=$("$FRITCHII_REAL_QMAKE" -query QT_INSTALL_PLUGINS)
export FRITCHII_QT_PLUGIN_DIR="$stage/qt-plugins"
mkdir -p "$FRITCHII_QT_PLUGIN_DIR/imageformats"
# Package Qt's codecs, not unrelated KDE image plugins installed on the host.
for entry in "$qt_plugins"/*; do
    name=${entry##*/}
    if [[ "$name" != imageformats ]]; then
        ln -s -- "$entry" "$FRITCHII_QT_PLUGIN_DIR/$name"
    fi
done
for codec in "$qt_plugins"/imageformats/libq*.so; do
    if [[ -f "$codec" ]]; then
        ln -s -- "$codec" "$FRITCHII_QT_PLUGIN_DIR/imageformats/"
    fi
done
cat > "$stage/qmake" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
if [[ "$*" == -query ]]; then
    while IFS= read -r line; do
        if [[ "$line" == QT_INSTALL_PLUGINS:* ]]; then
            printf 'QT_INSTALL_PLUGINS:%s\n' "$FRITCHII_QT_PLUGIN_DIR"
        else
            printf '%s\n' "$line"
        fi
    done < <("$FRITCHII_REAL_QMAKE" -query)
else
    exec "$FRITCHII_REAL_QMAKE" "$@"
fi
EOF
chmod +x "$stage/qmake"
export QMAKE="$stage/qmake"
export PATH="$tools:$PATH"
export EXTRA_PLATFORM_PLUGINS='libqwayland.so;libqxcb.so'
export ARCH=x86_64
version=$(tr -d '\r\n' < "$root/dist/frizti_version.txt")
[[ "$version" =~ ^[0-9]+\.[0-9]+(\.[0-9]+)?$ ]] || {
    printf 'Invalid Fritchii version: %s\n' "$version" >&2
    exit 1
}
export LDAI_VERSION="$version-linux-$(git -C "$root" rev-parse --short HEAD)"
export OUTPUT="$artifact_dir/Fritchii-$version-linux-x86_64.AppImage"
"$tools/linuxdeploy-x86_64.AppImage" --appdir "$appdir" \
    --executable "$build/bin/lichii" --executable "$build/bin/eden-cli" \
    --desktop-file "$stage/io.github.frizti.fritchii.desktop" \
    --icon-file "$stage/io.github.frizti.fritchii.png" \
    --plugin qt
integration=wayland-graphics-integration-client
if [[ -d "$qt_plugins/$integration" ]]; then
    mkdir -p "$appdir/usr/plugins/$integration"
    cp -a "$qt_plugins/$integration/." "$appdir/usr/plugins/$integration/"
    "$tools/linuxdeploy-x86_64.AppImage" --appdir "$appdir" \
        --deploy-deps-only "$appdir/usr/plugins/$integration" --output appimage
else
    "$tools/linuxdeploy-x86_64.AppImage" --appdir "$appdir" --output appimage
fi
python3 "$root/tools/nx2/audit_linux_release.py" "$appdir" --private-root "$root"
(cd "$artifact_dir" && sha256sum "${OUTPUT##*/}") > "$OUTPUT.sha256"
printf 'AppImage: %s\n' "$OUTPUT"
if [[ ${FRITCHII_KEEP_APPDIR:-0} == 1 ]]; then
    printf 'Staging directory: %s\n' "$stage"
else
    rm -rf -- "$stage"
fi
