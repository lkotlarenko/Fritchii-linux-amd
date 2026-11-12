# Linux port progress

## Current base and preserved behavior

Official Fritchii **v5.8.4**, Windows branch `oot-gather-fix`, revision
`4f5c53149b7e17d1c24445f68d79a83a3b2a17f9`.
The port preserves Fritchii's Zelda renderer/CPU optimizations, dynamic FPS and
30/60 controls, shader preparation, v54 cache records, graphical home screen,
AMD handling and save compatibility. Generic Lichii was not merged over it.

## Completed implementation

- Native Linux executable discovery, platform variables and Vulkan/X11 compilation
  fixes; full Qt6 frontend, bundled fmt, isolated out-of-tree Release build.
- RADV complete-preparation eligibility, bounded Linux compiler workers, official
  recipe packaging, device/driver UUID preparation identity and diagnostic counters.
- v5.8.4 translator-based stamp adopted without discarding caches. Linux's existing
  `fritchii-native/eden` layout retained; self-import/migration candidates excluded.
- GPU address translation avoids inactive-cache bookkeeping. Tests cover small/big
  remaps, unmapped ranges, multiple managers and live experiment toggles.
- Linux thread/TID attribution and benchmark PSS/SwapPss/worst-frame reporting.
- Process-local pageout/cold/off comparison modes, retaining the established default.
- Native launcher, AppImage packaging, checksum-pinned packaging tools, screenshot-free
  GUI smoke, compiler path remapping and release privacy checks.
- Tagged Linux GitHub release workflow with restricted permissions and build/test gates.

## Verified results

| Check | Result |
|---|---|
| Release CTest | 5/5 targets; main suite 949 cases / 70,795,211 assertions |
| Other CTest suites | Shader 851 assertions; migration 389; updater 1,298; import 64 |
| Python diagnostics | Debug adapter 15/15; benchmark collector 8/8 |
| Shader preparation | 120,087 prepared, 37 failed, zero skipped/unreached, 502.6 s |
| Warm native-to-AppImage reuse | Accepted stamp; 1,462 startup builds in 4.1 s, no failures |
| Vulkan selection | RX 7600, Mesa RADV; no software/integrated-device substitution |
| Real saved-game rendering | Stationary Kokiri Forest entrance rendered on an isolated copy |
| AppImage GUI | Home and Settings passed on Wayland and XWayland |
| Warm gameplay window | 25.67 FPS over 60 s; approximate 1% low 12.30 FPS |

The initial timed run was interrupted by a manual window close and is not a benchmark.
The completed warm result is a scene observation, not a controlled FPS improvement
claim. See [PERFORMANCE.md](docs/linux/PERFORMANCE.md) and the
[optimization ledger](docs/linux/OPTIMIZATION_LEDGER.md).

## Cleanup and publication privacy

A reviewed allowlist removed roughly 806,000 files, reducing the local tree from
1,039,437 to about 233,000 files at the cleanup checkpoint. Removed obsolete test
cache copies, old AppImage stages, temporary test directories, superseded binaries /
reference downloads, temporary publishing tools and five merged local branches.
Observed free space increased by 600,473,600 bytes; shared/reflinked files made the
apparent deleted size much larger. No filesystem snapshots were removed.

Current and rollback prepared caches, one verified v5.7 executable/AppImage,
all personal data, save copies, measurements and private historical reports remain
local. Packaging/test scripts now remove successful temporary outputs. Cleanup
allowlist and audit remain under ignored `build/`; they are not release assets.

Publication uses a clean history descending from the public official base, excluding
private local development commits. README/Linux docs were rewritten; historical
handoffs stay in ignored local storage. Games, keys, firmware, profiles, captures,
raw local logs, account identifiers and credentials are excluded. Linux path mapping
and the package audit prevent local home/checkout paths leaking in compiled files.

## Outstanding work and next commands

- Complete the privacy-remapped Release rebuild and repeat package/runtime audits.
- Publish the validated source/artifact and verify the new GitHub workflow on the fork.
- Investigate tracked uniform/native-bank costs, compute synchronization and paging
  from the measured fine profile; preserve synchronization ordering.
- Determine missing pointer classifications for the 37 recorded preparation failures.
- Obtain a permitted CPU sample or add narrow application instrumentation; hardware
  event sampling remains blocked despite a working owned-child instruction counter.
- Run repeated matched cold/warm/static/route comparisons before claiming FPS gains.

```sh
git status --short
git log -4 --oneline
cat build/performance/LIVE_STATUS.md
./scripts/build-linux.sh -DENABLE_DEBUG_TOOLS=OFF
./scripts/package-appimage.sh
```

Inspect process/profile locks before any game launch. Never benchmark against personal
writable saves. See [the handoff](LINUX_PERFORMANCE_HANDOFF.md) for the precise next
experiment and local evidence locations.
