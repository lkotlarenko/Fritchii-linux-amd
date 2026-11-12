# Optimization ledger

Base: official Fritchii v5.8.4. Measurements are local engineering evidence,
not promised FPS gains. Private raw logs/captures and historical handoffs remain
under ignored `build/`; they are not published or included in release artifacts.

## GPU address translation

**Function:** `MemoryManager::GpuToCpuAddress` and its graphics/compute resource
callers. Official EXP63 code computed TLS slot/hash/owner and read the shared mapping
epoch even when the cache was disabled. Clang's hot layout retained unnecessary
work on that path.

**Accepted change:** guard the cache probe, keep a nullable cache slot for miss
insertion, and retain one original page-table walk. The enabled cache still checks
owner/page/epoch and retains acquire ordering. No mappings, invalidation semantics,
error handling or rendering synchronization were relaxed.

The real-function test performs five million calls per timing, alternating cache
off/on twice per process. Three process repeats give six samples per mode:

| Condition | Baseline median | Accepted median | Change |
|---|---:|---:|---:|
| Cache disabled | 24.363 ms | 16.6005 ms | 31.9% less elapsed time |
| Cache enabled | 18.280 ms | 16.0395 ms | 12.3% less elapsed time |

All checksums matched. A separate mixed 20-million-call owned-child hardware-counter
run, pinned only for the microbenchmark, measured:

| Counter | Baseline | Accepted |
|---|---:|---:|
| User instructions | 1,846,689,229 | 1,536,686,658 |
| User cycles | 470,401,941 | 403,805,598 |

That is 16.8% fewer instructions in this benchmark, **not a 16.8% gameplay gain**.
The test covers small/big remaps, missing mappings, manager isolation and live toggles.
Final unremapped Release CTest passed 5/5; the publication privacy rebuild must pass
again. No emulator threads were pinned.

Rejected variants:

- Conditional epoch load alone increased mixed instructions by about ten million.
- An early-return/page-walk lambda improved cache-off timing but regressed cache-on
  timing; disassembly showed extra saved-register pressure. It was removed.

Reproduction, from an isolated temporary XDG root:

```sh
mkdir -p build/performance/unit-profile
XDG_DATA_HOME="$PWD/build/performance/unit-profile/data" \
XDG_CONFIG_HOME="$PWD/build/performance/unit-profile/config" \
XDG_CACHE_HOME="$PWD/build/performance/unit-profile/cache" \
FRITCHII_TRANSLATION_BENCHMARK=1 \
  build/linux-release/bin/tests '[translation_cache]'
```

## Shader preparation and cache reuse

Keep the Linux RADV eligibility fix, driver/device UUID suffix, bounded worker pool
and v54 recipe. Adopt v5.8.4's translator-hash stamp rather than resetting preparation
for every release number. Native preparation: 120,087 prepared, 37 failed, no device
skips/unreached, 502.6 s. Warm AppImage reused that stamp and loaded 1,462 boot builds
in 4.1 s without full preparation. The 37 missing recorded-pointer classifications
remain unresolved; no guessed classifications or dropped draws were introduced.

## Paging experiment — no default change

The earlier pageout/cold comparison measured 28.43 versus 28.99 FPS, approximate
1% low 16.37 versus 19.24, and 1,516 versus 743 major faults. Cold mode increased
RSS and did not establish a major mean-FPS improvement. Keep pageout as default and
cold/off available for controlled investigation. Do not repeat without new evidence.
Never discard live writable guest pages. Prefer PSS/SwapPss to alias-inflated RSS.

## Synchronization diagnostic — no relaxed waits

EXP12=3 measured the writer boundary while retaining the required complete drain.
The remaining tail was usually only a few ms/s. Different diagnostic durations,
paging changes and camera uncertainty prevented an FPS claim. Restore mode 0; do
not enable relaxed modes 1/2 or infer recoverable throughput from summed waits.

Upstream investigations reviewed actual code/diffs, not titles:

- Lichii #191: readback batching improved throughput but corrupted exposure.
- #227: narrow writer tracking can return stale macro values.
- #540 / PR #687: delayed semaphore retry is already present; retain it.
- PR #1028: async readback ideas are already partly adapted; do not double-port.
- PR #1056: moving memory-reading macros requires effects/register/shadow-state
  synchronization; no unsafe partial architectural port was kept.
- PR #1036: wholesale cache replacement conflicts with Fritchii's v54 preparation.
- PR #1016 and #961: Windows-specific timing/trimming work is not automatically
  applicable to Linux. Live writable memory cannot be discarded safely.

## JIT warm queue — rejected for release

Replacing vector front erasure with deque pops greatly reduced synthetic queue work
at large depths. Matched gameplay did not establish a benefit; a candidate/control
comparison was confounded by load path, process uptime and paging. The experiment
was reverted. Real queue-depth/load-hitch evidence is needed before retrying.

## Diagnostic improvements — retained

Linux timelines now use real thread names/TIDs instead of an unhelpful shared label.
The collector reports worst frame buckets, endpoint PSS/SwapPss, correct GPU identity,
CPU policies and faults. It now also attributes minor/major faults to observed threads
and rejects TID reuse through start-time checks. Eight collector unit tests pass;
completed gameplay attribution is still pending for the new fields.

A separate v5.8.4 fine profile measured stage-buffer binding 107.75 ms/s, including
62.75 ms/s in uniform work; compute synchronization 42.10 ms/s. This identifies the
next instrumentation target, not a safe shortcut. See [PERFORMANCE.md](PERFORMANCE.md)
for the conditions and limits. Parent perf sampling remained denied; user-space
owned-child instruction counting worked. No security settings were changed.

## Release hygiene and privacy — validation in progress

Successful test runs and packaging now remove their temporary outputs. Failures
preserve evidence; staging can be retained explicitly. A reviewed local cleanup
removed roughly 806,000 files and five merged branch refs while retaining current /
rollback caches, saves, reports and a verified v5.7 rollback.

A privacy audit found local checkout strings in the prior ELF. Linux compiler file
prefix mapping removes these at compilation, including dependency diagnostics.
Packaging scans its unpacked tree for private paths and user-data filenames before
success. Five privacy-check tests cover chunk boundaries, clean files, user-data
names and symlink behavior. These checks do not justify uploading arbitrary local
files. Only the intended AppImage/checksum will be published, from clean public
history based on the official source. Final remapped build/runtime results must be
recorded before publication.
