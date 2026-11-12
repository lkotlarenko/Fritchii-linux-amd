# Native Fritchii on Linux

This fork ports **official Fritchii v5.8.4** (`4f5c53149b7e17d1c24445f68d79a83a3b2a17f9`)
from its Windows `oot-gather-fix` branch. Fritchii's Zelda optimizations, dynamic FPS,
shader preparation, Qt interface and v54 shader records are retained.

[Downloads](https://github.com/lkotlarenko/Fritchii-linux-amd/releases) ·
[Performance](docs/linux/PERFORMANCE.md) · [Releasing](docs/linux/RELEASING.md) ·
[Handoff](LINUX_PERFORMANCE_HANDOFF.md)

## Install and run an AppImage

Download the AppImage and checksum from this fork's release page, then:

```sh
sha256sum --check Fritchii-5.8.4-linux-x86_64.AppImage.sha256
chmod +x Fritchii-5.8.4-linux-x86_64.AppImage
./Fritchii-5.8.4-linux-x86_64.AppImage
```

The package targets current x86_64 Arch/CachyOS. It bundles Qt and application
libraries, but uses the host's Vulkan/Mesa driver and glibc. Older Linux distributions
are not automatically supported. No NVIDIA-only dependency is required.

The launcher prefers native Wayland and allows xcb fallback. Select explicitly with:

```sh
QT_QPA_PLATFORM=wayland ./Fritchii-5.8.4-linux-x86_64.AppImage
QT_QPA_PLATFORM=xcb ./Fritchii-5.8.4-linux-x86_64.AppImage
APPIMAGE_EXTRACT_AND_RUN=1 ./Fritchii-5.8.4-linux-x86_64.AppImage
```

The last form avoids a FUSE requirement. Games, firmware and keys are not included
or downloaded by the build/release scripts. Add your own locally obtained game
through the GUI or pass its path as a quoted argument.

## Data and updates

Always use the supplied launcher, including for native builds. It keeps this port
separate from other emulator installations:

| Purpose | Default path |
|---|---|
| Data, NAND, saves | `~/.local/share/fritchii-native/eden` |
| Configuration | `~/.config/fritchii-native/eden` |
| Shader/driver caches | `~/.cache/fritchii-native/eden` |

Custom `XDG_DATA_HOME`, `XDG_CONFIG_HOME` and `XDG_CACHE_HOME` are supported; the
launcher appends `fritchii-native`, then the application uses `eden`. Native and
AppImage launches share this layout. v5.8.4 deliberately preserves the Linux
`eden` leaf despite the upstream Windows migration to `fritchii`. Import discovery
excludes the current data directory. Launching the raw internal ELF bypasses this
namespace and is not the normal installation method.

To update, close the application, retain a working previous artifact and back up
important data, verify the new checksum, then replace only the AppImage/executable.
Do not delete caches, saves, NAND or SDMC to install an update. The Windows automatic
updater is disabled in these builds. An older artifact remains a rollback option;
restoring source alone is not an executable rollback.

## Shader preparation

The official OoT v54 recipe is included and checksum-verified. Linux RADV is eligible
for complete preparation, including the AMD dynamic-state handling inherited from
Fritchii. Preparation uses a bounded pool of three workers on the tested six-core
system. It can take several minutes; do not start a second instance on the profile.

The preparation stamp includes the shader translator identity and Vulkan device /
driver-cache identity. A translator or driver change can require preparation once,
without deleting existing caches. Warm native/AppImage reuse was verified: 1,462
startup pipelines in 4.1 seconds, followed by skipping complete preparation.
Retained-cache preparation completed 120,087 records with 37 failed and zero device
skips in 502.6 seconds. Those recorded-pointer failures remain under investigation;
preparation completion is not proof that every shader variant was built.

## Build from source

Use Clang, CMake >=3.31, Ninja and Qt6 with Core, Gui, Widgets, Concurrent, Network,
DBus and Charts. Arch package names for a fresh development environment include:

```text
base-devel clang lld cmake ninja git python pkgconf
qt6-base qt6-charts qt6-tools sdl3 ffmpeg openssl zlib lz4
libusb libpulse alsa-lib libxkbcommon libxkbcommon-x11
vulkan-headers vulkan-icd-loader vulkan-radeon vulkan-tools
glslang spirv-tools nasm autoconf automake libtool boost
```

Install packages deliberately through your distribution; scripts do not alter
system configuration or install packages on the local machine. Qt Wayland support
is in qt6-base on the tested Arch system; some distributions package it separately.

```sh
git clone https://github.com/lkotlarenko/Fritchii-linux-amd.git
cd Fritchii-linux-amd
./scripts/build-linux.sh -DENABLE_DEBUG_TOOLS=OFF
./scripts/run-linux.sh
```

The build is out of tree in `build/linux-release`, uses Clang Release, `-O3 -DNDEBUG`,
bundled fmt, full Qt and two jobs by default. All five CTest targets run with isolated
XDG directories. Successful test data is removed; failures retain it for inspection.
Linux compiler prefix mapping removes local checkout paths from compiled diagnostics.
The updater stays disabled. No imported PGO, unsafe fast-math or runtime affinity
change is applied.

Use `JOBS=2` on a 16 GiB machine. `FRITCHII_BUILD_DIR` selects a separate build directory;
`CC`/`CXX` select compatible compilers. Additional arguments go to CMake. Keep distinct
build directories for compiler/LTO/PGO experiments and measure before adopting them.

## Package and validate

```sh
./scripts/fetch-appimage-tools.sh
./scripts/package-appimage.sh
QT_QPA_PLATFORM=wayland ./scripts/test-linux-appimage.sh
QT_QPA_PLATFORM=xcb ./scripts/test-linux-appimage.sh
```

Packaging tools are verified against `dist/linux-appimage-tools.sha256`; changed
upstream downloads fail closed. Packaging can fetch the AppImage runtime. The output
is `artifacts/Fritchii-5.8.4-linux-x86_64.AppImage` and its `.sha256` sidecar.

The package bundles Wayland/xcb plugins and Qt's own image codecs, avoiding unrelated
host KDE image plugins. It preserves modern ELF RELR data by disabling the packaging
tool's old strip implementation. An unpacked-tree privacy audit rejects local paths
and user-data filenames. Successful staging is removed; `FRITCHII_KEEP_APPDIR=1`
retains it for investigation. Failures retain staging.

The screenshot-free GUI smoke uses a newly created empty profile, opens home and
Settings, and closes. It never loads a game or uses personal saves. CI runs its xcb
variant under Xvfb. GUI smoke and CTest do not replace real-game rendering validation.

## Performance, diagnostics and maintenance

See [PERFORMANCE.md](docs/linux/PERFORMANCE.md) for measurement procedures and limits,
[OPTIMIZATION_LEDGER.md](docs/linux/OPTIMIZATION_LEDGER.md) for accepted/rejected work,
and [LINUX_PORT_PROGRESS.md](LINUX_PORT_PROGRESS.md) for completed and pending tasks.
The verified warm forest sample measured 25.67 FPS with substantial remaining paging
and synchronization costs; no universal FPS or full-playthrough guarantee is made.

`FRITCHII_COLD_MEMORY_MODE=pageout|cold|off` retains the existing controlled experiments;
pageout remains the default. Never discard live writable guest pages. Do not relax
GPU visibility/fence requirements to improve a counter.

Keep one active build, current prepared test profile and verified rollback. Retire
obsolete experimental cache copies and packaging stages after validation; do not
apply broad wildcard cleanup to emulator data. Historical local logs/captures and
handoffs are private and must not be published. See the release guide for clean
history, artifact audits and future upstream updates.
