# Working on Fritchii Linux AMD

Read `docs/Coding.md` for C++ guidance. Keep comments focused and avoid unrelated
rewrites. Before work, read `LINUX_PERFORMANCE_HANDOFF.md`, `LINUX_PORT_PROGRESS.md`,
`README-LINUX.md`, `docs/linux/PERFORMANCE.md` and the optimization ledger. Check
`build/performance/LIVE_STATUS.md`, Git state and running processes before testing.

## Source base and upstream work

The published branch is `main`. This is a Linux port of official Fritchii's Windows
`oot-gather-fix` branch, not generic Lichii. Verify the official revision/tag before
an update. Preserve Zelda optimizations, dynamic FPS, shader preparation and v54
cache behavior. Review upstream diffs, PRs and dependencies before adapting fixes;
consult Frizti/Fritchii, zortos293/Lichii and Djihads80/Eglantine as appropriate.
Do not merge unrelated upstream architecture over Fritchii just to fix compilation.

## Data and runtime safety

- Never modify personal saves, NAND, SDMC, game files, keys or working caches during
  experiments. Do not download games, console keys or firmware.
- Use isolated copied profiles and `tools/nx2/check_linux_test_profile.py`. Verify
  absolute Qt NAND/SDMC/load/dump/TAS paths and symlinks before launching.
- Never run conflicting emulator instances on one profile. Respect profile locks
  and active preparation; let it finish. Control only explicitly authorized test
  instances, never another person's running game.
- Preserve a verified executable/AppImage rollback. Remove obsolete generated files
  only with an explicit reviewed allowlist; do not delete live caches or snapshots.
- Request approval for system packages, privileged actions or system configuration.
  Do not change perf security, kernel scheduling or global Vulkan settings silently.

## Build and validation

```sh
./scripts/build-linux.sh -DENABLE_DEBUG_TOOLS=OFF
python3 tools/nx2/test_linux_benchmark.py
python3 tools/nx2/test_release_privacy.py
python3 tools/nx2/test_debug_mcp.py
./scripts/fetch-appimage-tools.sh
./scripts/package-appimage.sh
QT_QPA_PLATFORM=wayland ./scripts/test-linux-appimage.sh
QT_QPA_PLATFORM=xcb ./scripts/test-linux-appimage.sh
```

Default builds use two jobs, Clang Release and full Qt6. Keep heavy diagnostics and
sanitizers in separate builds. The Python debug-adapter tests need loopback sockets;
sandbox denial is not a product regression. Successful test/packaging temporary
outputs are removed; failed runs preserve evidence. See `docs/linux/RELEASING.md`.

## Performance investigations

Follow PROFILE → IDENTIFY → IMPLEMENT → VERIFY → BENCHMARK → KEEP/REVERT.
Record baseline, conditions, raw evidence and correctness limits in the ledger.
Do not claim FPS gains from compiler flags, a microbenchmark or accumulated thread
waits alone. Compare identical scene/save/settings/cache state and matched durations.

Use `tools/nx2/linux_benchmark.py` for frame percentiles, CPU/GPU activity,
PSS/SwapPss and process/thread faults. It is read-only. Use lightweight application
profiling if perf sampling is denied; never invent a sample profile. Fine GPU
profiling adds overhead and belongs in separate diagnostic runs.

Existing opt-in tools include `EDEN_NX2_GPU_PROFILE=1|2`,
`FRITCHII_PIPELINE_DIAGNOSTICS=1`, `MESA_SHADER_CACHE_SHOW_STATS=true` and
`EDEN_NX2_DEBUG_SERVER=127.0.0.1:PORT`. The debug adapter is
`tools/nx2/debug_mcp.py`; protocol and rendering tools are documented under
`docs/nx2/`. Prefer status/logs/counters over repeated screenshots. Use a small
capture only when it resolves a specific scene/rendering question.

Never drop necessary draws, discard valid guest memory or relax GPU visibility /
fence ordering to improve FPS. No naive thread pinning or real-time scheduling.
Retain pageout/cold/off modes for controlled comparisons; do not repeat rejected
experiments without new evidence.

## Publication privacy and handoff

No private home paths, host/account identifiers, emails, credentials, game paths,
saves, screenshots, captures or raw local logs belong in published source, history
or release assets. Historical local handoffs stay under ignored `build/`. A clean
public branch must not accidentally make private development history reachable.
Do not push every local branch/tag. Preserve upstream licensing and attribution.

Compiler prefix mapping and `tools/nx2/audit_linux_release.py` check packaged files;
inspect source/history as well. Publish only the intended AppImage and checksum.
GitHub Actions uploads fresh CI logs, not the owner's local build tree.

Update handoff/progress/ledger at meaningful checkpoints. Record current artifact,
active processes, remaining tests and the precise next experiment. Distinguish
completed checks from assumptions; no full-playthrough or universal FPS guarantee.
