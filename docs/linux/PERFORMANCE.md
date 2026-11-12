# Linux performance investigation

## Scope and build

Current base is official Fritchii v5.8.4. Local validation uses a six-core Zen 2 CPU,
16 GiB RAM and an RX 7600 with Mesa RADV. Clang Release uses `-O3 -DNDEBUG`; no
imported Windows PGO, unsafe fast-math, thread pinning or relaxed fence mode is used.
The Linux port preserves Fritchii's Zelda and shader-preparation systems.

## Completed warm gameplay measurement

One 60-second stationary Kokiri Forest sample, after warm AppImage startup and
verifying the saved camera, produced:

| Metric | Observation |
|---|---:|
| Average FPS | 25.665 |
| Approximate 1% low FPS | 12.296 |
| P95 present interval | 50.75–51.00 ms |
| P99 present interval | 63.50–63.75 ms |
| Worst interval | 175.00–175.25 ms |
| GPU busy mean / peak | 68.73% / 96% |
| Process CPU, one logical core = 100% | 567.25% |
| GPU front / back CPU | 87.12% / 83.63% |
| Vulkan worker CPU | 30.68% |
| PSS, before → after | 5,580.76 → 4,502.35 MiB |
| SwapPss, before → after | 1,149.93 → 1,443.49 MiB |
| Process major / minor faults | 14,769 / 829,624 |
| Mean reported VRAM / GTT usage | 7,449,659,187 / 751,691,776 bytes |

Pipeline creation counters stayed unchanged in the logged samples inside that
window (approximately its middle 45 seconds). This does not prove zero unobserved
work at the window endpoints. Compiler workers consumed no sampled CPU time in the
collector. Shader preparation alone does not explain these remaining slow frames.

This is not a matched before/after FPS comparison against older versions. A prior
window was manually interrupted and discarded. Present intervals are not Vulkan
GPU execution times. Histograms use 0.25 ms buckets; 1% low is approximate. GPU and
VRAM sysfs counters can include other desktop activity; PSS/SwapPss are endpoint
samples. Background load and paging variance require repeated comparisons.

## Preparation and cache persistence

The RADV gate fix is retained. The official v5.8.4 recipe is byte-identical to the
packaged v54 recipe. Complete preparation with three workers produced:

- 120,087 prepared of 120,124 scheduled; 37 failed.
- Zero device skips, unreached records or preparation exceptions.
- 502.6 seconds with an existing cache; 94,301 builds under 20 ms (a timing heuristic,
  not a driver-reported hit count).
- One memory snapshot: 1,282,148 KiB PSS and 10,240 KiB SwapPss, not peak usage.
- Clean exit Mesa counters totaled 338,105 hits and zero misses in that run.

Named record failures lack storage-pointer classifications. Do not infer missing
facts or force them through translation; live environments can provide the missing
classification when needed. The 37 failures remain an explicit limitation.

Warm AppImage startup accepted the native prepared stamp, loaded 1,462 boot builds
in 4.1 seconds with zero failures, and skipped full preparation. The stamp follows
shader translator identity plus device/driver-cache identity, not merely release
number. Cache v54 and existing profile directories are retained.

## Fine profile and current leads

A separate diagnostic run enabled `EDEN_NX2_GPU_PROFILE=2`. Median per-second wall
zones over the selected 120–240 second process interval were:

| Zone | ms/s | calls/s |
|---|---:|---:|
| Bind graphics stage buffers | 107.75 | 97,451 |
| Uniform buffers, nested within stage binds | 62.75 | 97,451 |
| Storage-address binding construction | 24.15 | 97,451 |
| Compute pointer resolution | 28.10 | 3,116.5 |
| Compute synchronization | 42.10 | 3,116.5 |
| Back-thread method execution | 100.25 | 2,070,881 |
| Back split wait | 143.10 | 55,751 |

Some zones are nested, and waits can overlap other work. These values are not a
recoverable FPS budget. Storage-address construction is not a measured subdivision
of the remaining stage-buffer time. Fine profiling adds timestamp/counter overhead;
this run is not the uninstrumented FPS result above. Its camera followed the same
load sequence without an additional screenshot check.

The uniform path already reuses many stream allocations. Its byte counter measures
logical bytes bound, not actual memcpy/upload bandwidth. Source review must separate
native-bank validation, stream comparison/copy, host synchronization and descriptor
binding before changing behavior. Guest writes can occur between draws: GPU address
or once-per-frame equality is insufficient to skip validation.

Paging remains a strong lead, not a proven sole cause. The collector now records
per-thread minor/major fault deltas with thread start-time identity checks. This can
identify whether GPU, guest CPU or background threads incur the observed faults.
The new attribution still needs a completed gameplay run before conclusions.

## Measurement procedure

1. Use an isolated profile copied from a frozen save/settings/cache state. Validate
   with `tools/nx2/check_linux_test_profile.py`; inspect absolute Qt path overrides
   and symlinks. Never use personal writable saves for a benchmark.
2. Check for an active instance/preparation and acquire the profile lock. Do not
   start conflicting instances or delete caches. Create separate empty test caches
   for cold trials; retain warmed caches for warm trials.
3. Launch with a loopback debug server and pipeline diagnostics. Verify GPU/driver,
   target save/camera, resolution, frame limit and elapsed time after load.
4. Stop builds/packaging and disable heavyweight profiling for FPS comparisons.
5. Collect matching-duration samples, repeat enough to expose variance, and inspect
   rendering/correctness separately. Keep static, moving and unfamiliar-scene tests
   separate.

```sh
python3 tools/nx2/linux_benchmark.py --pid PID --server 127.0.0.1:6548 \
  --seconds 60 --out build/performance/measurements/unique-run-name
```

The collector never starts/stops or configures the emulator. It records frame
histograms, process/thread CPU and faults, affinity/policies, correct DRM device,
PSS/SwapPss and memory/GPU samples. It rejects restarted sessions and counter-format
changes. Thread counters cover consecutive observed samples, not unseen lifetimes.

CPU event sampling remains blocked by host security. Owned-child user-space hardware
instruction counting worked for the function benchmark; a disabled-until-ready
parent `perf record` launch still failed. No kernel permissions were changed, and
no empty perf file is treated as a profile.

## Next source-level experiment

First attribute major faults to actual threads, then split the uniform scope into
native-bank checking, stream reuse/copy and host synchronization with low-overhead,
opt-in counters. Correlate it with long frames and GPU submission. Investigate safe
elimination of repeated work only after identifying the dominant subpath.

Keep full synchronization drains. EXP12=3 diagnostic evidence did not establish a
large safe tail to remove; do not enable relaxed EXP12=1/2. Unsafe readback batching
has caused incorrect exposure upstream. Preserve dependency visibility and add
ordering tests before architectural changes.

The [ledger](OPTIMIZATION_LEDGER.md) records accepted/rejected experiments. Future
compiler/ThinLTO/Zen 2/PGO work belongs in separate builds with controlled benchmarks.
No 30/60 FPS performance guarantee or full-game correctness claim is established.
