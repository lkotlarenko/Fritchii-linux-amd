#!/usr/bin/env python3
"""Read-only Linux gameplay measurement; never launches/stops or configures the emulator."""

import argparse
import json
import math
import os
from pathlib import Path
import socket
import statistics
import time


def status(server):
    host, port = server.rsplit(":", 1)
    with socket.create_connection((host, int(port)), timeout=5) as sock:
        sock.sendall(b'{"id":1,"method":"status","params":{"fps_window_ms":0}}\n')
        raw = sock.makefile("rb").readline(2 ** 20)
    reply = json.loads(raw)
    if "error" in reply:
        raise RuntimeError(reply["error"])
    return reply["result"]


def fields(path):
    try:
        return dict(line.split(":", 1) for line in path.read_text().splitlines() if ":" in line)
    except (OSError, ProcessLookupError):
        return {}


def number(path):
    try:
        return int(path.read_text().strip())
    except (OSError, ValueError):
        return None


def proportional_memory(pid):
    stats = fields(Path("/proc") / str(pid) / "smaps_rollup")
    return {key: int(stats[key].split()[0]) / 1024 if key in stats else None
            for key in ("Pss", "SwapPss", "Pss_Anon", "Pss_Shmem", "Pss_File")}


def sample(pid, gpu):
    proc = Path("/proc") / str(pid)
    process_stat = (proc / "stat").read_text().rsplit(")", 1)[1].split()
    memory = fields(proc / "status")
    threads = {}
    for task in (proc / "task").iterdir():
        try:
            stat = (task / "stat").read_text()
            name = stat[stat.index("(") + 1:stat.rindex(")")]
            rest = stat[stat.rindex(")") + 2:].split()
            threads[task.name] = {"name": name, "ticks": int(rest[11]) + int(rest[12]),
                                  "start_ticks": int(rest[19]),
                                  "minor_faults": int(rest[7]), "major_faults": int(rest[9]),
                                  "state": rest[0], "cpu": int(rest[36]),
                                  "nice": int(rest[16]), "policy": int(rest[38])}
        except (OSError, ValueError, IndexError):
            continue
    vmstat = fields(Path("/proc/meminfo"))
    swaps = {}
    for line in Path("/proc/vmstat").read_text().splitlines():
        key, value = line.split()
        if key in ("pswpin", "pswpout", "pgmajfault"):
            swaps[key] = int(value)
    return {"time": time.monotonic(),
            "process_ticks": int(process_stat[11]) + int(process_stat[12]),
            "process_start_ticks": int(process_stat[19]),
            "minor_faults": int(process_stat[7]), "major_faults": int(process_stat[9]),
            "rss_kib": int(memory.get("VmRSS", "0").split()[0]),
            "swap_kib": int(memory.get("VmSwap", "0").split()[0]),
            "available_kib": int(vmstat["MemAvailable"].split()[0]), "vmstat": swaps,
            "threads": threads,
            "gpu": {name: number(gpu / name) for name in
                    ("gpu_busy_percent", "mem_info_vram_used", "mem_info_vram_total",
                     "mem_info_gtt_used")}}


def thread_deltas(samples):
    totals = {}
    for before, after in zip(samples, samples[1:]):
        for tid, current in after["threads"].items():
            previous = before["threads"].get(tid)
            if previous is None or previous["start_ticks"] != current["start_ticks"]:
                continue
            key = f'{tid}:{current["name"]}'
            counts = totals.setdefault(key, {k: 0 for k in ("ticks", "minor_faults", "major_faults")})
            for field in counts:
                counts[field] += max(0, current[field] - previous[field])
    return totals


def frame_summary(before, after):
    if before["scm_rev"] != after["scm_rev"] or after["presents"] < before["presents"]:
        raise RuntimeError("Emulator restarted during the measurement")
    for key in ("program_id", "host_pid", "frame_time_bucket_us"):
        if before.get(key) != after.get(key):
            raise RuntimeError(f"Session or counter format changed: {key}")
    if len(before["frame_times"]) != len(after["frame_times"]):
        raise RuntimeError("Histogram size changed")
    if not after.get("powered_on", True) or after["uptime_s"] <= before["uptime_s"]:
        raise RuntimeError("Session ended or restarted")
    counts = [b - a for a, b in zip(before["frame_times"], after["frame_times"])]
    if any(n < 0 for n in counts):
        raise RuntimeError("Frame counters reset during the measurement")
    total = sum(counts)
    width = after["frame_time_bucket_us"] / 1000
    def percentile(p):
        wanted = math.ceil(total * p)
        seen = 0
        for i, count in enumerate(counts):
            seen += count
            if seen >= wanted and total:
                return {"lower_ms": i * width,
                        "upper_ms": (i + 1) * width if i < len(counts) - 1 else None}
        return None
    # Mean of the slowest 1% using bucket midpoints; do not invent overflow durations.
    remaining = max(1, math.ceil(total * .01))
    worst_n = remaining
    worst_ms = 0
    for i in range(len(counts) - 1, -1, -1):
        take = min(remaining, counts[i])
        if take and i == len(counts) - 1:
            worst_ms = None
            break
        worst_ms += take * (i + .5) * width
        remaining -= take
        if remaining == 0:
            break
    elapsed = after["uptime_s"] - before["uptime_s"]
    return {"average_fps": (after["presents"] - before["presents"]) / elapsed,
            "duration_s": elapsed, "frame_intervals": total,
            "p95": percentile(.95), "p99": percentile(.99), "worst": percentile(1),
            "one_percent_low_fps_approx": 1000 * worst_n / worst_ms if worst_ms else None,
            "overflow_intervals": counts[-1], "bucket_width_ms": width,
            "note": "Present intervals, not GPU execution time; overflow percentiles are lower bounds."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", required=True, type=int)
    parser.add_argument("--server", default="127.0.0.1:6545")
    parser.add_argument("--seconds", type=int, default=60)
    parser.add_argument("--gpu", type=Path, help="DRM device sysfs directory; autodetect from process FDs")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not 5 <= args.seconds <= 3600:
        parser.error("--seconds must be 5..3600")
    args.out.mkdir(parents=True, exist_ok=False)
    if args.gpu is None:
        devices = set()
        for fd in (Path("/proc") / str(args.pid) / "fd").iterdir():
            try:
                target = Path(os.readlink(fd))
                if target.parent == Path("/dev/dri"):
                    device = Path("/sys/class/drm") / target.name / "device"
                    if (device / "gpu_busy_percent").exists():
                        devices.add(device.resolve())
            except OSError:
                continue
        if len(devices) != 1:
            raise RuntimeError("Cannot identify a unique process GPU; pass --gpu explicitly")
        args.gpu = devices.pop()
    identity = {"device_path": str(args.gpu.resolve())}
    for name in ("vendor", "device", "revision"):
        path = args.gpu / name
        identity[name] = path.read_text().strip() if path.exists() else None
    identity["driver"] = str((args.gpu / "driver").resolve())
    (args.out / "gpu-identity.json").write_text(json.dumps(identity, indent=2) + "\n")
    policies = {}
    for task in (Path("/proc") / str(args.pid) / "task").iterdir():
        details = fields(task / "status")
        if details:
            policies[task.name] = {k: details.get(k, "").strip() for k in
                                   ("Name", "Cpus_allowed_list", "Mems_allowed_list")}
    (args.out / "thread-affinity.json").write_text(json.dumps(policies, indent=2) + "\n")
    # Walk page tables outside the measured interval.
    memory_before = proportional_memory(args.pid)
    before = status(args.server)
    if before.get("host_pid") != args.pid:
        raise RuntimeError("--pid does not match the Linux debug server's host_pid")
    if before["paused"] or not before["powered_on"]:
        raise RuntimeError("Load the benchmark scene and unpause first")
    (args.out / "before.json").write_text(json.dumps(before))
    start = time.monotonic()
    samples = []
    with (args.out / "samples.jsonl").open("w") as out:
        while time.monotonic() - start < args.seconds:
            now = sample(args.pid, args.gpu)
            samples.append(now)
            out.write(json.dumps(now) + "\n")
            out.flush()
            time.sleep(min(1, max(0, args.seconds - (time.monotonic() - start))))
    after = status(args.server)
    (args.out / "after.json").write_text(json.dumps(after))
    summary = frame_summary(before, after)
    summary["proportional_memory_mib"] = {
        "before": memory_before, "after": proportional_memory(args.pid)}
    summary["build"] = before["build"]
    summary["scm_rev"] = before["scm_rev"]
    summary["program_id"] = before["program_id"]
    summary["paused_at_end"] = after["paused"]
    summary["max_rss_mib"] = max(s["rss_kib"] for s in samples) / 1024
    summary["max_swap_mib"] = max(s["swap_kib"] for s in samples) / 1024
    summary["vmstat_delta_system_wide"] = {
        k: samples[-1]["vmstat"][k] - samples[0]["vmstat"][k] for k in samples[0]["vmstat"]}
    summary["process_faults_delta"] = {
        k: samples[-1][k] - samples[0][k] for k in ("minor_faults", "major_faults")}
    for key in samples[0]["gpu"]:
        values = [s["gpu"][key] for s in samples if s["gpu"][key] is not None]
        summary[key] = {"mean": statistics.mean(values), "max": max(values)} if values else None
    ticks = os.sysconf("SC_CLK_TCK")
    thread_totals = thread_deltas(samples)
    elapsed = samples[-1]["time"] - samples[0]["time"]
    summary["thread_cpu_percent_one_core"] = {
        k: v["ticks"] / ticks / elapsed * 100
        for k, v in sorted(thread_totals.items(), key=lambda x: -x[1]["ticks"])}
    summary["thread_faults_delta"] = {
        k: {field: v[field] for field in ("minor_faults", "major_faults")}
        for k, v in sorted(thread_totals.items(), key=lambda x: -x[1]["major_faults"])}
    if samples[-1]["process_start_ticks"] != samples[0]["process_start_ticks"]:
        raise RuntimeError("Process identity changed during measurement")
    summary["process_cpu_percent_one_core"] = (
        (samples[-1]["process_ticks"] - samples[0]["process_ticks"]) / ticks / elapsed * 100)
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
