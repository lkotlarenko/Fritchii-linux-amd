# Development handoff

## Source, artifacts and rules

Base: official Fritchii v5.8.4, Windows `oot-gather-fix`, revision
`4f5c53149b7e17d1c24445f68d79a83a3b2a17f9`. Published branch: `main` in
https://github.com/lkotlarenko/Fritchii-linux-amd. Preserve the Fritchii-specific
renderer, dynamic FPS, preparation and cache behavior.

- Native: `build/linux-release/bin/lichii`, launch with `./scripts/run-linux.sh`.
- Package: `artifacts/Fritchii-5.8.4-linux-x86_64.AppImage` plus checksum.
- Local verified rollback: `build/rollback-v5.7/`, including native/AppImage and
  recipe. It is intentionally not a public release asset.
- Local prepared profiles retained: `build/performance/profiles/v584-warm` and
  `v57-warm`. Other obsolete experiment cache copies were removed after validation;
  their configuration/save copies and reports remain.
- Historical private reports: `build/private-handoff-archive/pre-publication/`.
  They are ignored and must not be pushed. Existing local development history stays
  local; public history descends cleanly from the official base.

Check actual processes and `build/performance/LIVE_STATUS.md` before launching.
The documented v5.8.4 preparation finished; no pending preparation should be resumed
from an old PID. Do not infer that a historical live-status snapshot is current.

## Completed validation and performance findings

Release CTest passed 5/5 (949 main cases); native Wayland saved-game rendering and
AppImage Wayland/XWayland home/settings passed. Full RADV preparation completed
120,087 records with 37 failures, no skipped/unreached records and no exceptions in
502.6 s. Warm AppImage accepted the native stamp and loaded 1,462 boot builds in
4.1 s. Translator hash is `1149f06f2344b2f3`; use watcher `--translator`, not an old
release-only stamp. Recipe v54 bytes are retained.

The complete warm stationary forest window measured 25.665 FPS, approximate 1% low
12.296, P95 50.75–51.00 ms, P99 63.50–63.75 ms, worst 175.00–175.25 ms. It is one
observation, not a before/after gain. Logged middle-window pipeline counters did
not change; GPU busy averaged 68.73%, process CPU 567.25% of one logical core,
major faults 14,769. PSS fell while SwapPss rose. Paging and CPU/GPU synchronization
remain leads. See performance report/ledger for full metrics and caveats.

Source lookup optimization is accepted from real-function timings and hardware
instruction counts, not FPS. Cache-off 24.363 → 16.6005 ms, on 18.280 → 16.0395 ms
per five million calls; same checksums, remap/toggle tests pass. Lazy-load-only and
lambda variants were rejected. No fence relaxation, JIT experiment, unsafe compiler
flag or runtime affinity change is shipped.

Fine mode measured graphics stage binds 107.75 ms/s, uniforms 62.75 ms/s and compute
synchronization 42.10 ms/s over the selected diagnostic interval. Some scopes are
nested. The same load sequence was used without another camera screenshot, so this
is diagnostic evidence, not a matched FPS comparison.

## Exact local evidence and resumption

- Preparation: `build/performance/runs/prepared-v584/eden_log.txt`.
- Warm final game run: `build/performance/runs/warm-appimage-v584/` and
  `build/performance/measurements/v584-warm-appimage-outdoor/`.
- Fine scopes: `build/performance/runs/warm-fine-v584/fine-summary.json` and log.
- Translation comparisons: `build/performance/translation-benchmarks/` (timings,
  instruction counters, disassembly); obsolete baseline ELF copies were cleaned.
- Source baseline for the lookup is the official v5.8.4 function. The accepted
  function/test remain in this source tree and the clean public commit history.
- Frozen scene details and local game path are in the ignored launch helpers /
  retained profile data. Do not copy private paths, save/account identifiers or
  scene captures into public docs.

```sh
git status --short
git log -4 --oneline
cat build/performance/LIVE_STATUS.md
ps -C lichii -o pid,etime,pcpu,rss,args
python3 tools/nx2/check_linux_test_profile.py build/performance/profiles/v584-warm
./scripts/build-linux.sh -DENABLE_DEBUG_TOOLS=OFF
```

Existing ignored `build/performance/launch-test.sh` and
`launch-appimage-test.sh` use profile locks, copied saves and loopback port 6548.
Inspect them before use. The default prepared launcher is
`scripts/run-prepared-test.sh`, with `FRITCHII_TEST_PROFILE` override. No personal
writable saves are authorized for benchmarking. Test-only `confirmStop=2` disables
exit confirmation inside the isolated profile; it never changes personal settings.

## Next experiment and why

1. Finish the privacy-remapped rebuild, package audit and final runtime tests before
   uploading an artifact. The previous binary contained local source-path strings.
2. Verify publication/default branch/release workflow; keep the tested local artifact
   distinct from an untested CI rebuild. Do not overwrite an existing release asset.
3. Use the upgraded collector's `thread_faults_delta` in a completed warm game run.
   It now tracks thread start identity; old samples cannot retroactively attribute
   faults. This separates faults on critical GPU/guest threads from background ones.
4. Split uniform-buffer work into native-bank validation, stream comparison/copy,
   host synchronization and descriptor binding. Record calls/time without heavy
   default overhead, and correlate with the long-frame/fault windows.
5. Implement one measured redundant-work reduction, test ordering/remaps/guest-write
   visibility, benchmark repeated matched windows, and keep or revert it.
6. Continue to compute synchronization or guest polling after that evidence; do not
   convert accumulated waits into a guessed FPS opportunity.

Perf instruction counting on an owned child works, but sampling/attach and a parent
`perf record` launch were denied. Do not change security sysctls/capabilities silently.
Use in-process instrumentation; no sampled CPU call-stack profile exists yet.
The 37 missing recorded-pointer classifications need real live/recorded data, not
invented values. Full playthrough, unfamiliar-scene and cold-cache comparisons,
LTO/PGO and sanitizer campaigns remain outstanding.

## Cleanup and publication status

Reviewed cleanup removed about 806,000 files and five merged local branches. Current
and rollback caches plus one verified v5.7 artifact remain. Physical free space rose
600,473,600 bytes; reflink sharing makes apparent directory sizes misleading.
No personal data or filesystem snapshot was deleted. Allowlist and incremental audit
are under `build/CLEANUP_PLAN.json` and `build/CLEANUP_RESULT.json`.

README and Linux reports were rewritten from verified results; old private handoffs
remain ignored. Only clean history and audited artifact/checksum may be published.
Final artifact hashes, active processes, privacy rebuild tests and GitHub run status
must be refreshed at the end of the session.
