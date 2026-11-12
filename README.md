<!--
# SPDX-FileCopyrightText: Copyright 2025 Eden Emulator Project
# SPDX-License-Identifier: GPL-3.0-or-later

# SPDX-FileCopyrightText: 2018 yuzu Emulator Project
# SPDX-License-Identifier: GPL-2.0-or-later
-->

# Fritchii Linux AMD

A native Linux port of [Fritchii](https://github.com/Frizti/Fritchii), preserving
its Zelda optimizations, shader preparation, dynamic FPS controls and Qt6 GUI.
Current base: **official Fritchii v5.8.4**, Windows `oot-gather-fix` commit
`4f5c53149b7e17d1c24445f68d79a83a3b2a17f9`. This port does not replace Fritchii
with generic Lichii.

[Download Linux releases](https://github.com/lkotlarenko/Fritchii-linux-amd/releases)
· [Build and run](README-LINUX.md)
· [Performance measurements](docs/linux/OPTIMIZATION_LEDGER.md)
· [Development handoff](LINUX_PERFORMANCE_HANDOFF.md)

## Run

Download the x86_64 AppImage and its `.sha256` file from this fork's releases:

```sh
sha256sum --check Fritchii-5.8.4-linux-x86_64.AppImage.sha256
chmod +x Fritchii-5.8.4-linux-x86_64.AppImage
./Fritchii-5.8.4-linux-x86_64.AppImage
```

Target: current Arch Linux/CachyOS, Qt6, Vulkan and Mesa RADV, with native Wayland
and X11/XWayland support. Development testing uses an RX 7600 and Ryzen 5 4600G.
AMD is the tested target, not a mandatory vendor lock. Host Vulkan drivers are
required; the Arch-built package is not compatible with every older glibc distro.
If FUSE is unavailable, run with `APPIMAGE_EXTRACT_AND_RUN=1`.
Games, console keys, firmware and user profiles are not included.

## Saves and shaders

The supplied launcher preserves this port's existing XDG layout:

- Data/saves: `$XDG_DATA_HOME/fritchii-native/eden` (default `~/.local/share/fritchii-native/eden`).
- Settings: `$XDG_CONFIG_HOME/fritchii-native/eden` (default `~/.config/fritchii-native/eden`).
- Caches: `$XDG_CACHE_HOME/fritchii-native/eden` (default `~/.cache/fritchii-native/eden`).

Native and AppImage launches use the same layout. v5.8.4 keeps the Linux `eden`
leaf despite the Windows release's directory migration. Existing saves and v54
caches are retained. Full shader preparation runs before gameplay and can take
several minutes; a changed shader translator can require it once again. A warm
launch reuses the matching device/driver cache. Do not delete caches to update.
The automatic Windows updater is disabled; replace only the executable/AppImage.

## Validation and performance

The current local Release passes five CTest targets, including 949 main test
cases. Native Wayland saved-game rendering, AppImage warm-cache reuse, and
Wayland/XWayland home/settings smoke tests passed on the development machine.
Preparation completed 120,087 pipelines, with 37 retained record failures and
zero device skips; those unresolved records can compile when needed.

A verified stationary Kokiri Forest window measured **25.67 FPS**, approximately
**12.30 FPS 1% low**. This is one scene and one 60-second window, not a universal
FPS expectation or a before/after performance claim. Paging and CPU/GPU
synchronization remain substantial bottlenecks. The translation-lookup change
reduces measured function cost; its gameplay benefit is not established.
See the ledger for raw conditions, rejected experiments and remaining work.
No full playthrough or universal rendering guarantee is claimed.

## Build, update and contribute

See [README-LINUX.md](README-LINUX.md) for dependencies and scripts,
[release automation](docs/linux/RELEASING.md) for tagged AppImage releases, and
[docs/Coding.md](docs/Coding.md) for coding guidance. Linux release tags follow
`linux-v<upstream-version>-r<port-revision>`; publishing a tag builds/tests the
AppImage before release. CI performs an Xvfb GUI smoke, not a real-game GPU test.

Keep upstream updates and Linux optimizations reviewable, preserve Fritchii's
specialized behavior, and benchmark on isolated profile copies. Report Linux
issues [here](https://github.com/lkotlarenko/Fritchii-linux-amd/issues), including
build, driver, settings, reproduction steps and a log checked for private data.
Do not upload games, keys, firmware or account files.

## Credits and licensing

Fritchii is maintained upstream by Frizti and builds on
[Lichii](https://github.com/zortos293/Lichii), Eglantine, Eden, yuzu and Sudachi.
The Linux port also reviewed community work by
[xTopher1049](https://github.com/xTopher1049/Fritchii-linux) and
[Gusdevr](https://github.com/Gusdevr/fritchii-linux-build).
Inherited artwork is by YOB (yobslab); see [branding](dist/branding).
Source licenses and upstream notices remain in place; see [LICENSE.txt](LICENSE.txt).
This is an independent emulator fork, not affiliated with Nintendo.
